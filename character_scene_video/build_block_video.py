#!/usr/bin/env python3
"""Stage 6: concatenate an upload PART's per-chapter videos into one MP4 + description.

Chapter MP4s (from render_chapter.py) share codec/resolution/fps, so concatenation is a stream
copy — no re-encode, runs in seconds. The `0:00 Chapter N: Title` description lines come from
ffprobe durations of the ACTUAL chapter files, so YouTube's auto chapter markers land exactly on
the cuts. (YouTube needs the first marker at 0:00 and 3+ increasing timestamps — a 50-chapter
part clears that easily.)

A part is a chapter range listed under its volume in projects/<name>/upload_meta.json; its
number K is the list position there. Output goes to its own folder:

    <video_out>/<Volume_dir>/parts/Part_K_chAAA-BBB/Part_K_chAAA-BBB.mp4  (+ _description.txt)

    py -3.12 character_scene_video/build_block_video.py 214 266 --plan   # readiness check, writes nothing
    py -3.12 character_scene_video/build_block_video.py 214 266          # Part_1_ch214-266.mp4 + _description.txt
    py -3.12 character_scene_video/build_block_video.py 214 240 --part 9 # ad-hoc range not in upload_meta
    (add --project NAME for a non-default project; --force to overwrite an existing part)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import charvid_project  # noqa: E402


def probe(path):
    """-> (duration_sec, {codec_type: stream-param signature}) for timestamps + uniformity checks."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels",
         "-of", "json", str(path)], capture_output=True, text=True)
    data = json.loads(out.stdout)
    dur = float(data["format"]["duration"])
    sig = {}
    for s in data["streams"]:
        t = s.pop("codec_type")
        sig[t] = tuple(sorted(s.items()))
    return dur, sig


def stamp(sec):
    sec = int(sec)          # floor: a marker must not start after its chapter's first frame
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("first", type=int)
    ap.add_argument("last", type=int)
    ap.add_argument("--project", default=None)
    ap.add_argument("--plan", action="store_true", help="report readiness, write nothing")
    ap.add_argument("--force", action="store_true", help="overwrite an existing part MP4")
    ap.add_argument("--part", type=int,
                    help="part number (default: looked up by range in upload_meta.json)")
    a = ap.parse_args()
    P = charvid_project.load(a.project)

    chapters = list(range(a.first, a.last + 1))

    # a part is a per-volume upload artifact -- refuse ranges that cross a volume boundary
    vols = {P.volume_dir_of(ch) for ch in chapters}
    if len(vols) > 1:
        sys.exit(f"ch{a.first}-{a.last}: range spans volumes {sorted(vols)} -- "
                 "split at the volume boundary")

    part_no = a.part
    if part_no is None:
        hit = P.part_for_range(a.first, a.last)
        if not hit:
            sys.exit(f"ch{a.first}-{a.last} is not a part of volume {P.volume_no_of(a.first)} in "
                     f"upload_meta.json -- add it there (parts are numbered by list order) "
                     f"or pass --part K for an ad-hoc range")
        part_no = hit[0]
    stemname = P.part_stem(part_no, a.first, a.last)
    out_dir = P.part_dir(part_no, a.first, a.last)

    files = {ch: P.chapter_video(ch) for ch in chapters}
    missing = [ch for ch, f in files.items() if not f.exists()]

    print(f"{stemname}: {len(chapters) - len(missing)}/{len(chapters)} chapter videos present")
    if missing:
        rng = f"{missing[0]}-{missing[-1]}" if len(missing) > 1 else str(missing[0])
        print(f"  missing: {rng} -> render first: "
              f"py -3.12 character_scene_video/render_chapter.py {missing[0]} {missing[-1]}")
        if not a.plan:
            sys.exit(1)

    # probe what exists; stream copy needs identical codec params across every input
    durs, sigs = {}, {}
    for ch in chapters:
        if files[ch].exists():
            durs[ch], sigs[ch] = probe(files[ch])
    if sigs:
        ref_ch = min(sigs)
        bad = [ch for ch, s in sigs.items() if s != sigs[ref_ch]]
        if bad:
            print(f"  STREAM MISMATCH vs ch{ref_ch}: {bad} -- re-render these before concat")
            if not a.plan:
                sys.exit(1)
        else:
            print(f"  stream params uniform across {len(sigs)} files")

    total = sum(durs.values())
    if total:
        print(f"  total (present files): {stamp(total)}  ({total / 3600:.2f} h)")
        if total > 11.9 * 3600:
            print("  WARNING: over YouTube's 12-hour limit -- split the block")

    # description with YouTube chapter markers
    lines, t = [], 0.0
    for ch in chapters:
        if ch not in durs:
            lines.append(f"?:?? Chapter {ch}: {P.title_of(ch)}  (video missing)")
            continue
        lines.append(f"{stamp(t)} Chapter {ch}: {P.title_of(ch)}")
        t += durs[ch]
    desc = "\n".join([f"{P.series_title} audiobook — Chapters {a.first}-{a.last}.", "", *lines, ""])

    if a.plan:
        print("  -- description preview (first 5 markers) --")
        for l in lines[:5]:
            print("   ", l)
        print("  plan only: nothing written")
        return

    out_mp4 = out_dir / f"{stemname}.mp4"
    if out_mp4.exists() and not a.force:
        print(f"  {out_mp4.name} exists -- use --force to overwrite")
        sys.exit(1)
    out_dir.mkdir(parents=True, exist_ok=True)
    listing = out_dir / f"_concat_{stemname}.txt"
    listing.write_text("\n".join(f"file '{files[ch].as_posix()}'" for ch in chapters) + "\n",
                       encoding="utf-8")
    r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-f", "concat", "-safe", "0", "-i", str(listing),
                        "-c", "copy", "-movflags", "+faststart", str(out_mp4)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FFMPEG FAILED\n{r.stderr[-1500:]}")
        sys.exit(1)
    listing.unlink(missing_ok=True)
    got, _ = probe(out_mp4)
    flag = "" if abs(got - total) < 2.0 else f"   <-- DURATION MISMATCH (expected {stamp(total)})"
    desc_file = out_dir / f"{stemname}_description.txt"
    desc_file.write_text(desc, encoding="utf-8")
    print(f"  wrote {out_mp4.name}  {stamp(got)}  {out_mp4.stat().st_size / 1e9:.2f} GB{flag}")
    print(f"  wrote {desc_file.name}  ({len(lines)} chapter markers)")


if __name__ == "__main__":
    main()
