#!/usr/bin/env python3
"""Prove what is rendered, instead of trusting logs or mtimes.

Two independent checks, both pixel comparisons (chapter-number overlay masked, mean abs diff < 3/255):

  --frames   For every distinct portrait set the built blocks use in the range, recompose the frame
             in memory and compare it with the cached PNG. Catches the in-place portrait replacement
             trap (same cache key, stale pixels). A stale frame => delete the PNG, then re-render every
             chapter that uses it.
  (default)  For every scene of every chapter in the range, decode the actual frame out of
             Chapter_N.mp4 at a point inside the scene and compare it with the (cached) frame the
             current block data resolves to. A mismatch => that chapter needs `render_chapter.py N N
             --force`. Also reports parts whose MP4 is older than any chapter inside them.

    py -3.12 character_scene_video/verify_render.py 214 482            # Vol 2, ~4 min
    py -3.12 character_scene_video/verify_render.py 214 482 --frames   # cache audit, seconds
    py -3.12 character_scene_video/verify_render.py 447 447 --json out.json

Frame-PNG mtimes are NOT a signal: compose_frames.ensure() writes only when the file is missing, so a
PNG's mtime is its creation time (2026-09-05 lesson: 209/269 chapters flagged, 0 actually stale).
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import charvid_project  # noqa: E402
import compose_frames as C  # noqa: E402

THRESH = 3.0
MASK = (130, 520)   # top-left overlay: chapter number + badge


def sec(t):
    p = [int(x) for x in t.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2]


def diff(a, b):
    a = np.asarray(a.convert("RGB"), dtype=np.int16)
    b = np.asarray(b.convert("RGB"), dtype=np.int16)
    if a.shape != b.shape:
        return 999.0
    a[:MASK[0], :MASK[1]] = 0
    b[:MASK[0], :MASK[1]] = 0
    return float(np.abs(a - b).mean())


def load_blocks(P, first, last):
    out = {}
    for f in P.block_jsons():
        for c in json.loads(f.read_text(encoding="utf-8")).get("chapters_detail", []):
            if first <= c["chapter"] <= last:
                out[c["chapter"]] = c
    return out


def scene_key(s):
    imgs = [i for i in s["images"] if not i.startswith("(")]
    return C.key_for(imgs, s.get("mentioned_images", []))[0] if imgs else None


def check_frames(P, blocks):
    """cached PNG vs fresh compose, per distinct portrait set. -> (sets, stale, missing)."""
    sets = {}
    for c in blocks.values():
        for s in c["scenes"]:
            imgs = [i for i in s["images"] if not i.startswith("(")]
            if imgs:
                d, names = C.key_for(imgs, s.get("mentioned_images", []))
                sets[d] = (names, s.get("mentioned_images", []))
    stale, missing = [], []
    for d, (names, ment) in sets.items():
        p = P.frames / f"{d}.png"
        if not p.exists():
            missing.append((d, names))
            continue
        C._BG = None
        fresh = C.compose(names, P, ment)
        dd = diff(Image.open(p), fresh)
        if dd >= THRESH:
            stale.append((d, names, dd))
    return sets, stale, missing


def check_video(P, blocks, tmp):
    """decoded video frame vs expected cached PNG, per scene. -> (ok, bad[(ch, s, why)])."""
    ok, bad = 0, []
    for ch in sorted(blocks):
        c = blocks[ch]
        mp4 = P.chapter_video(ch)
        if not mp4.exists():
            bad.append((ch, 0, "no MP4"))
            continue
        t0 = sec(c["scenes"][0]["start"])
        for i, s in enumerate(c["scenes"], 1):
            start = sec(s["start"]) - t0
            dur = sec(s["duration"]) if s.get("duration") else 60
            off = start + max(2, min(15, dur // 2))
            exp = C.frame_path(s["images"], P, s.get("mentioned_images", []))
            if not exp.exists():
                bad.append((ch, i, "expected frame PNG missing"))
                continue
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(off), "-i", str(mp4),
                                "-frames:v", "1", "-y", str(tmp)], capture_output=True)
            if r.returncode != 0 or not tmp.exists():
                bad.append((ch, i, "decode failed"))
                continue
            dd = diff(Image.open(tmp), Image.open(exp))
            if dd < THRESH:
                ok += 1
            else:
                bad.append((ch, i, f"diff={dd:.1f}"))
    return ok, bad


def check_parts(P, first, last):
    """parts whose MP4 is older than a chapter inside them. -> [(part_dir_name, [stale chapters])]"""
    out = []
    meta = P.upload_meta()
    vol_no = P.volume_no_of(first)
    for k, p in enumerate(meta["volumes"].get(str(vol_no), {}).get("parts", []), 1):
        if p["last"] < first or p["first"] > last:
            continue
        d = P.part_dir(k, p["first"], p["last"])
        mp4 = d / f"{P.part_stem(k, p['first'], p['last'])}.mp4"
        if not mp4.exists():
            out.append((d.name, ["(part MP4 missing)"]))
            continue
        pt = mp4.stat().st_mtime
        stale = [ch for ch in range(p["first"], p["last"] + 1)
                 if P.chapter_video(ch).exists() and P.chapter_video(ch).stat().st_mtime > pt]
        if stale:
            out.append((d.name, stale))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("first", type=int)
    ap.add_argument("last", type=int)
    ap.add_argument("--project", default=None)
    ap.add_argument("--frames", action="store_true", help="cache audit only (no video decoding)")
    ap.add_argument("--json", metavar="PATH", help="also write the findings as JSON")
    a = ap.parse_args()
    P = charvid_project.load(a.project)
    blocks = load_blocks(P, a.first, a.last)
    if not blocks:
        sys.exit(f"no built block covers ch{a.first}-{a.last} -- run build_block.py first")
    t = time.time()
    report = {"range": [a.first, a.last], "checked_at": time.strftime("%Y-%m-%d %H:%M")}

    sets, stale, missing = check_frames(P, blocks)
    print(f"FRAME CACHE  ch{a.first}-{a.last}: {len(sets)} distinct frames, "
          f"{len(stale)} STALE, {len(missing)} missing")
    for d, names, dd in stale:
        print(f"   STALE {d}.png  diff={dd:.1f}  {[n.rsplit('.', 1)[0] for n in names]}")
    for d, names in missing:
        print(f"   MISSING {d}.png  {[n.rsplit('.', 1)[0] for n in names]}")
    report["stale_frames"] = [{"png": f"{d}.png", "cast": names} for d, names, _ in stale]
    report["missing_frames"] = [{"png": f"{d}.png", "cast": names} for d, names in missing]
    bad_keys = {d for d, *_ in stale} | {d for d, _ in missing}
    if bad_keys:
        users = sorted({c["chapter"] for c in blocks.values() for s in c["scenes"]
                        if scene_key(s) in bad_keys})
        print(f"   -> delete the stale PNGs, then re-render --force: {users}")
        report["chapters_using_bad_frames"] = users

    bad, parts = [], []
    if not a.frames:
        tmp = Path(os.environ.get("TEMP", ".")) / "_verify_render_grab.png"
        ok, bad = check_video(P, blocks, tmp)
        by_ch = {}
        for ch, i, why in bad:
            by_ch.setdefault(ch, []).append(f"s{i} {why}")
        print(f"\nVIDEO  ch{a.first}-{a.last}: {ok} scenes match, {len(bad)} mismatch "
              f"in {len(by_ch)} chapters")
        for ch in sorted(by_ch):
            print(f"   ch{ch}: {', '.join(by_ch[ch])}")
        if by_ch:
            print(f"   -> re-render --force: {sorted(by_ch)}")
        report["video_ok"] = ok
        report["chapters_to_rerender"] = sorted(by_ch)
        report["video_mismatches"] = [{"chapter": ch, "scene": i, "why": why} for ch, i, why in bad]

        parts = check_parts(P, a.first, a.last)
        print(f"\nPARTS: {len(parts)} stale")
        for name, chs in parts:
            print(f"   {name}: newer chapters {chs}  -> build_block_video.py --force")
        report["stale_parts"] = [{"part": n, "newer_chapters": c} for n, c in parts]

    verdict = "CLEAN" if not (stale or missing or bad or parts) else "ACTION NEEDED"
    print(f"\nRESULT: {verdict}   ({time.time() - t:.0f}s)")
    report["verdict"] = verdict
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1), encoding="utf-8")
        print(f"wrote {a.json}")
    sys.exit(0 if verdict == "CLEAN" else 1)


if __name__ == "__main__":
    main()
