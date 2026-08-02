#!/usr/bin/env python3
"""Render one chapter's character-scene video: composited frames switched on the aligned
scene timestamps, muxed with the existing chapter MP3.

Matches the format of the existing book-1 videos (1920x1080, 1 fps, MP3 audio stream-copied) so
these drop into the same upload pipeline. 1 fps is not a compromise here: the picture only changes
at scene boundaries, so extra frames would be identical.

    py -3.12 character_scene_video/render_chapter.py 1 --preview
    py -3.12 character_scene_video/render_chapter.py 1
    py -3.12 character_scene_video/render_chapter.py 1 5        # a range
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

BLOCK_JSON = HERE / "timelines" / "block_01_ch001-050.json"
OUT_ROOT = Path("D:/PDFReader/lotm_book1_output/character_video")
FPS = 1
CQ = "26"          # nvenc quality level
CRF = "23"         # libx264 equivalent, matches the existing book-1 video_config

_ENCODER = None


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


def chapter_scenes(ch):
    data = json.loads(BLOCK_JSON.read_text(encoding="utf-8"))
    for c in data["chapters_detail"]:
        if c["chapter"] == ch:
            return c
    return None


def plan(ch):
    """-> (list of (frame_path, duration), chapter record). Consecutive identical frames merge."""
    rec = chapter_scenes(ch)
    if not rec:
        return None, None
    steps = []
    for s in rec["scenes"]:
        imgs = [i for i in s["images"] if not i.startswith("(")]
        if not imgs:
            if not steps:
                continue                      # nothing to hold yet; skip until we have a frame
            steps[-1][1] += s["chapter_end"] - s["chapter_start"]
            continue
        fp = frame_path(imgs)
        dur = s["chapter_end"] - s["chapter_start"]
        if steps and steps[-1][0] == fp:
            steps[-1][1] += dur               # same cast as previous scene -> one continuous shot
        else:
            steps.append([fp, dur, imgs])
    return steps, rec


def render(ch, force=False):
    steps, rec = plan(ch)
    if not steps:
        print(f"ch{ch}: no scenes/frames")
        return None
    _, mp3 = find_files(ch)
    if not mp3:
        print(f"ch{ch}: no audio")
        return None

    for _, _, imgs in steps:
        ensure(imgs)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    out = OUT_ROOT / f"Chapter_{ch}.mp4"
    if out.exists() and not force:
        print(f"ch{ch}: exists, skipping ({out})")
        return out

    listing = OUT_ROOT / f"_concat_ch{ch}.txt"
    lines = []
    for fp, dur, _ in steps:
        lines.append(f"file '{fp.as_posix()}'")
        lines.append(f"duration {dur:.3f}")
    # concat demuxer ignores the final entry's duration unless the file is repeated
    lines.append(f"file '{steps[-1][0].as_posix()}'")
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", str(listing),
           "-i", str(mp3),
           "-map", "0:v", "-map", "1:a",
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
    ap.add_argument("--preview", action="store_true", help="show the cut plan, render nothing")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    last = a.last or a.first

    for ch in range(a.first, last + 1):
        steps, rec = plan(ch)
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
        out = render(ch, force=a.force)
        if out:
            dur, size = probe(out)
            exp = rec["audio_duration"]
            flag = "" if abs(dur - exp) < 1.5 else f"   <-- DURATION MISMATCH (expected {exp:.1f}s)"
            print(f"ch{ch}: {out.name}  {dur:.1f}s  {size/1e6:.1f} MB  cuts={len(steps)}{flag}")


if __name__ == "__main__":
    main()
