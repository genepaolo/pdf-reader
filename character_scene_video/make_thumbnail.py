#!/usr/bin/env python3
"""Series-wide YouTube thumbnail for the LOTM volume block videos.

One shared background (user-chosen 2026-08-27: the Fool-above-his-personas puppet-stage promo art,
installed at tts_pipeline/assets/channel/thumbnail_bg_fool_stage.png) so every volume upload is
instantly recognizable as the same series; only the text block changes per volume.

    py -3.12 character_scene_video/make_thumbnail.py 1 --name "The Clown" --chapters 213 --hours 43
    -> <video_out>/<Volume_dir>/thumbnails/thumb_vol01.jpg  (1280x720; volume-aware since the
       2026-08-28 by-volume reorg; --project selects the charvid project)

Volumes upload as PARTS (YouTube's 12 h cap, enforced 2026-08-28), so there is a part variant —
same template, red line gains the part number, info line carries the chapter range:

    py -3.12 character_scene_video/make_thumbnail.py 1 --name "The Clown" --part 3 --of 4 \
        --range "101-157" --hours 11
    -> thumbnails/thumb_vol01_p3.jpg

Layout rules (thumbnail meta): big blocked type, hard black strokes, everything kept out of the
bottom-right corner where YouTube stamps the duration (the duration IS the selling point).
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import charvid_project  # noqa: E402

BG = HERE.parent / "tts_pipeline" / "assets" / "channel" / "thumbnail_bg_fool_stage.png"
LOGO = HERE.parent / "tts_pipeline" / "assets" / "channel" / "bread_moretti_logo.png"

W, H = 1280, 720
GOLD = (222, 185, 75)
RED = (225, 45, 45)


def font(name, size):
    return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("volume", type=int)
    ap.add_argument("--name", required=True, help='volume name, e.g. "The Clown"')
    ap.add_argument("--chapters", type=int, help="chapter count (whole-volume thumbnail)")
    ap.add_argument("--hours", type=int, required=True)
    ap.add_argument("--part", type=int, help="part number (per-part thumbnail)")
    ap.add_argument("--of", type=int, default=4, help="total parts")
    ap.add_argument("--range", dest="chrange", help='chapter range for the info line, e.g. "101-157"')
    ap.add_argument("--project", default=None)
    a = ap.parse_args()
    if not a.part and not a.chapters:
        ap.error("need --chapters (whole volume) or --part + --range (part)")
    if a.part and not a.chrange:
        ap.error("--part needs --range")

    art = Image.open(BG).convert("RGB")
    # 16:9 crop, biased to keep the Fool's face and the persona silhouettes
    cw = art.width
    ch = int(cw * H / W)
    top = min(68, art.height - ch)
    canvas = art.crop((0, top, cw, top + ch)).resize((W, H), Image.LANCZOS)

    # legibility gradient: darken the lower-left text zone, leave face + right side untouched
    grad = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(grad)
    for y in range(H):
        base = int(max(0, (y / H - 0.42)) * 300)          # vertical: starts ~mid, strongest at bottom
        gd.line([(0, y), (W, y)], fill=min(base, 165))
    side = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(side)
    for x in range(W):
        sd.line([(x, 0), (x, H)], fill=int(max(0, (1 - x / 850)) * 110))  # left edge boost
    black = Image.new("RGB", (W, H), (0, 0, 0))
    canvas = Image.composite(black, canvas, grad)
    canvas = Image.composite(black, canvas, side)

    d = ImageDraw.Draw(canvas)
    x = 46
    # series line
    d.text((x, 330), "LORD OF THE MYSTERIES", font=font("arialbd.ttf", 46),
           fill=(240, 240, 240), stroke_width=5, stroke_fill=(0, 0, 0))
    # volume, huge
    d.text((x - 4, 386), f"VOLUME {a.volume}", font=font("impact.ttf", 130),
           fill=GOLD, stroke_width=10, stroke_fill=(0, 0, 0))
    # full audiobook (part uploads carry the part number here, in the same red block type)
    red_line = f"PART {a.part} — FULL AUDIOBOOK" if a.part else "FULL AUDIOBOOK"
    d.text((x, 528), red_line, font=font("impact.ttf", 74),
           fill=RED, stroke_width=8, stroke_fill=(0, 0, 0))
    # info line — stays on the LEFT half (duration stamp owns bottom-right)
    info = (f"{a.name}  ·  Ch {a.chrange.replace('-', '–')}  ·  {a.hours} Hours" if a.part
            else f"{a.name}  ·  {a.chapters} Chapters  ·  {a.hours} Hours")
    d.text((x + 2, 622), info,
           font=font("arialbd.ttf", 40), fill=(235, 235, 235), stroke_width=5, stroke_fill=(0, 0, 0))
    # channel badge
    logo = Image.open(LOGO).convert("RGBA").resize((84, 84))
    canvas.paste(logo, (42, 22), logo)

    P = charvid_project.load(a.project)
    # per-part subfolder (user decision 2026-09-02): each part's thumbnail lives with its own
    # A/B variants in thumbnails/part_<K>/, so variant sets stay manageable per upload part.
    # Volume-level (no --part) thumbnails stay at the thumbnails/ root.
    out_dir = P.video_out / P.volume_dir_by_no(a.volume) / "thumbnails"
    if a.part:
        out_dir = out_dir / f"part_{a.part}"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_p{a.part}" if a.part else ""
    out = out_dir / f"thumb_vol{a.volume:02d}{suffix}.jpg"
    canvas.save(out, quality=92)
    print(f"{out}  {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
