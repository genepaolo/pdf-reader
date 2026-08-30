#!/usr/bin/env python3
"""Render one chapter's character-scene video: composited frames switched on the aligned
scene timestamps, muxed with the existing chapter MP3.

Matches the format of the existing book-1 videos (1920x1080, 1 fps, MP3 audio stream-copied) so
these drop into the same upload pipeline. 1 fps is not a compromise here: the picture only changes
at scene boundaries, so extra frames would be identical.

    py -3.12 character_scene_video/render_chapter.py 1 --preview
    py -3.12 character_scene_video/render_chapter.py 1
    py -3.12 character_scene_video/render_chapter.py 1 5        # a range
    (add --project NAME for a non-default project)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from align_chapter import find_files                      # noqa: E402
from compose_frames import ensure, frame_path             # noqa: E402
import charvid_project                                    # noqa: E402

FPS = 1
CQ = "26"          # nvenc quality level
CRF = "23"         # libx264 equivalent, matches the existing book-1 video_config

_ENCODER = None
_BLOCK_CACHE = {}

# chapter label overlay (top-left): optional circular channel badge + chapter number.
# Per-project override via project.json "chapter_label":
#   {"enabled": true, "template": "#{ch}", "fontsize": 48,
#    "badge": "tts_pipeline/assets/channel/badge_circle.png", "badge_size": 76}
FONT_CANDIDATES = [Path("C:/Windows/Fonts/arialbd.ttf"),      # Arial Bold
                   Path("C:/Windows/Fonts/segoeuib.ttf")]     # Segoe UI Bold fallback
LABEL_X, LABEL_Y = 40, 26                                     # top-left anchor


def label_filter(ch, P):
    """-> (drawtext filter, badge path or None). Text vertically centres on the badge."""
    cfg = P.cfg.get("chapter_label", {})
    if not cfg.get("enabled", True):
        return None, None
    font = next((f for f in FONT_CANDIDATES if f.exists()), None)
    if font is None:
        print(f"ch{ch}: WARNING no bold font found, rendering without chapter label")
        return None, None
    fontfile = font.as_posix().replace(":", chr(92) + ":")
    text = cfg.get("template", "#{ch}").format(ch=ch)
    text = text.replace(chr(92), "").replace(":", chr(92) + ":").replace("'", "")
    size = cfg.get("fontsize", 48)
    badge = P._abs(cfg["badge"]) if cfg.get("badge") else None
    if badge is not None and not badge.exists():
        print(f"ch{ch}: WARNING badge {badge} missing, label without badge")
        badge = None
    if badge is not None:
        bs = cfg.get("badge_size", 76)
        tx, ty = LABEL_X + bs + 14, f"{LABEL_Y + bs // 2}-th/2"   # centre text on badge centre
    else:
        tx, ty = LABEL_X, LABEL_Y + 8
    draw = (f"drawtext=fontfile='{fontfile}':text='{text}':fontsize={size}:fontcolor=white:"
            f"x={tx}:y={ty}:shadowcolor=black@0.6:shadowx=2:shadowy=2")
    return draw, badge


def video_encoder():
    """Prefer NVENC, fall back to libx264. ffmpeg lists h264_nvenc even when the driver is
    absent, so probe by actually encoding a frame rather than trusting -encoders."""
    global _ENCODER
    if _ENCODER is None:
        test = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
             "-i", "color=c=black:s=64x64:d=0.1", "-c:v", "h264_nvenc", "-f", "null", "-"],
            capture_output=True, text=True)
        _ENCODER = "h264_nvenc" if test.returncode == 0 else "libx264"
    return _ENCODER


def encoder_args():
    if video_encoder() == "h264_nvenc":
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", CQ]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", CRF, "-tune", "stillimage"]


def chapter_scenes(ch, P):
    bj = P.block_json_for(ch)
    if bj is None:
        return None
    if bj not in _BLOCK_CACHE:
        _BLOCK_CACHE[bj] = json.loads(bj.read_text(encoding="utf-8"))
    for c in _BLOCK_CACHE[bj]["chapters_detail"]:
        if c["chapter"] == ch:
            return c
    return None


def plan(ch, P):
    """-> (list of (frame_path, duration), chapter record). Consecutive identical frames merge.
    Time before the first frame (a leading hold-previous with nothing to hold) is billed to the
    first real frame, so the visual track always covers the full audio."""
    rec = chapter_scenes(ch, P)
    if not rec:
        return None, None
    steps, lead = [], 0.0
    for s in rec["scenes"]:
        imgs = [i for i in s["images"] if not i.startswith("(")]
        dur = s["chapter_end"] - s["chapter_start"]
        if not imgs:
            if steps:
                steps[-1][1] += dur           # hold: extend the previous frame
            else:
                lead += dur                   # no frame yet: bill to the first real frame
            continue
        fp = frame_path(imgs, P)
        if steps and steps[-1][0] == fp:
            steps[-1][1] += dur + lead        # same cast as previous scene -> one continuous shot
        else:
            steps.append([fp, dur + lead, imgs])
        lead = 0.0
    return steps, rec


def render(ch, P, force=False):
    steps, rec = plan(ch, P)
    if not steps:
        print(f"ch{ch}: no scenes/frames")
        return None
    _, mp3 = find_files(ch, P)
    if not mp3:
        print(f"ch{ch}: no audio")
        return None

    for _, _, imgs in steps:
        ensure(imgs, P)

    out = P.chapter_video(ch)          # <video_out>/<Volume_dir>/Chapter_N.mp4
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not force:
        print(f"ch{ch}: exists, skipping ({out})")
        return out

    listing = out.parent / f"_concat_ch{ch}.txt"
    lines = []
    for fp, dur, _ in steps:
        lines.append(f"file '{fp.as_posix()}'")
        lines.append(f"duration {dur:.3f}")
    # concat demuxer ignores the final entry's duration unless the file is repeated
    lines.append(f"file '{steps[-1][0].as_posix()}'")
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")

    draw, badge = label_filter(ch, P)
    inputs = ["-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(mp3)]
    if draw and badge:
        # badge is input 2; overlay it, then draw the chapter number beside it
        inputs += ["-i", str(badge)]
        vmaps = ["-filter_complex",
                 f"[0:v][2:v]overlay={LABEL_X}:{LABEL_Y}[v1];[v1]{draw}[vout]",
                 "-map", "[vout]", "-map", "1:a"]
    elif draw:
        vmaps = ["-map", "0:v", "-map", "1:a", "-vf", draw]
    else:
        vmaps = ["-map", "0:v", "-map", "1:a"]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           *inputs,
           *vmaps,
           *encoder_args(),
           "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "copy", "-movflags", "+faststart", "-shortest", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ch{ch}: FFMPEG FAILED\n{r.stderr[-1500:]}")
        return None
    listing.unlink(missing_ok=True)
    return out


def probe(path):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size", "-of", "default=nw=1", str(path)],
                       capture_output=True, text=True).stdout
    d = dict(l.split("=") for l in o.strip().splitlines() if "=" in l)
    return float(d.get("duration", 0)), int(d.get("size", 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("first", type=int)
    ap.add_argument("last", type=int, nargs="?")
    ap.add_argument("--project", default=None)
    ap.add_argument("--preview", action="store_true", help="show the cut plan, render nothing")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    P = charvid_project.load(a.project)
    last = a.last or a.first

    for ch in range(a.first, last + 1):
        steps, rec = plan(ch, P)
        if not steps:
            print(f"ch{ch}: nothing to do")
            continue
        if a.preview:
            print(f"ch{ch} '{rec['title']}'  audio={rec['audio_duration']:.1f}s  "
                  f"timing={rec['timing']}  cuts={len(steps)}")
            t = 0.0
            for fp, dur, imgs in steps:
                print(f"   {t:8.1f}s +{dur:7.1f}s  {', '.join(i.rsplit('.',1)[0] for i in imgs)}")
                t += dur
            continue
        out = render(ch, P, force=a.force)
        if out:
            dur, size = probe(out)
            exp = rec["audio_duration"]
            flag = "" if abs(dur - exp) < 1.5 else f"   <-- DURATION MISMATCH (expected {exp:.1f}s)"
            print(f"ch{ch}: {out.name}  {dur:.1f}s  {size/1e6:.1f} MB  cuts={len(steps)}{flag}")


if __name__ == "__main__":
    main()
