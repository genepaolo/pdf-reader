#!/usr/bin/env python3
"""Composite one frame per distinct set of on-screen portraits.

Frames are cached by the sorted set of portrait filenames, so the ~10 000 scenes in a full book
collapse to a few hundred renders. Layout follows DESIGN.md section 6: normalise every portrait to a
common height, space them evenly on a 1920x1080 canvas, no name captions.

    py -3.12 character_scene_video/compose_frames.py --block            # all frames for block 1
    py -3.12 character_scene_video/compose_frames.py --contact-sheet     # one PNG to eyeball
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PORTRAITS = ROOT / "tts_pipeline" / "assets" / "characters" / "lotm"
FRAMES = HERE / "frames"
BLOCK_JSON = HERE / "timelines" / "block_01_ch001-050.json"

W, H = 1920, 1080
MARGIN_X, MARGIN_Y = 70, 55
GAP_X, GAP_Y = 44, 36
MAX_PORTRAIT_H = 950
MAX_PER_FRAME = 9          # DESIGN section 6: cap huge Tarot gatherings

BG_TOP = (18, 17, 24)
BG_BOTTOM = (9, 9, 13)


def background():
    """Dark vertical gradient -- portraits are the content, the backdrop must not compete."""
    bg = Image.new("RGB", (1, H))
    px = bg.load()
    for y in range(H):
        t = y / (H - 1)
        px[0, y] = tuple(round(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM))
    return bg.resize((W, H))


_BG = None


def rows_for(n):
    """DESIGN section 6: 1 centred, 2-4 one row, 5-8 two rows, 9+ grid."""
    if n <= 4:
        return [n]
    if n <= 8:
        half = (n + 1) // 2
        return [half, n - half]
    per = (n + 2) // 3
    return [per, per, n - 2 * per]


def _fit_row(imgs, avail_w, avail_h):
    """Scale a row of portraits to a shared height that fits the space. -> [(img, w, h)]"""
    aspects = [im.width / im.height for im in imgs]
    gaps = GAP_X * (len(imgs) - 1)
    h = min(MAX_PORTRAIT_H, avail_h, (avail_w - gaps) / sum(aspects))
    return [(im, max(1, round(h * a)), max(1, round(h))) for im, a in zip(imgs, aspects)]


def compose(filenames):
    """-> PIL image for this exact set of portraits."""
    global _BG
    if _BG is None:
        _BG = background()
    canvas = _BG.copy()

    names = list(filenames)[:MAX_PER_FRAME]
    imgs = []
    for fn in names:
        p = PORTRAITS / fn
        if p.exists():
            imgs.append(Image.open(p).convert("RGB"))
    if not imgs:
        return canvas

    layout = rows_for(len(imgs))
    avail_w = W - 2 * MARGIN_X
    avail_h = H - 2 * MARGIN_Y - GAP_Y * (len(layout) - 1)
    row_h = avail_h / len(layout)

    placed, i = [], 0
    for count in layout:
        placed.append(_fit_row(imgs[i:i + count], avail_w, row_h))
        i += count

    # vertically centre the whole stack, horizontally centre each row
    total_h = sum(max(h for _, _, h in row) for row in placed) + GAP_Y * (len(placed) - 1)
    y = (H - total_h) // 2
    draw = ImageDraw.Draw(canvas)
    for row in placed:
        rh = max(h for _, _, h in row)
        x = (W - (sum(w for _, w, _ in row) + GAP_X * (len(row) - 1))) // 2
        for im, w, h in row:
            resized = im.resize((w, h), Image.LANCZOS)
            top = y + (rh - h) // 2
            # 1px rim lifts the portrait off the dark backdrop without drawing attention
            draw.rectangle([x - 1, top - 1, x + w, top + h], outline=(48, 46, 58))
            canvas.paste(resized, (x, top))
            x += w + GAP_X
        y += rh + GAP_Y
    return canvas


def key_for(filenames):
    """Cache key: the SET of portraits, order-independent."""
    names = sorted(set(filenames))
    digest = hashlib.sha1("|".join(names).encode("utf-8")).hexdigest()[:16]
    return digest, names


def frame_path(filenames):
    digest, _ = key_for(filenames)
    return FRAMES / f"{digest}.png"


def ensure(filenames):
    """Render (once) and return the cached frame path."""
    out = frame_path(filenames)
    if not out.exists():
        FRAMES.mkdir(exist_ok=True)
        compose(sorted(set(filenames))).save(out, optimize=True)
    return out


def block_sets():
    """Every distinct portrait set used by the block-1 timeline."""
    data = json.loads(BLOCK_JSON.read_text(encoding="utf-8"))
    sets = {}
    for c in data["chapters_detail"]:
        for s in c["scenes"]:
            imgs = [i for i in s["images"] if not i.startswith("(")]
            if imgs:
                d, names = key_for(imgs)
                sets[d] = names
    return sets


def contact_sheet(sets, out):
    """One PNG showing every distinct frame, for a quick human check."""
    cols = 4
    tw, th = 480, 270
    rows = (len(sets) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
    for i, names in enumerate(sets.values()):
        thumb = compose(names).resize((tw, th), Image.LANCZOS)
        sheet.paste(thumb, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", action="store_true", help="render every frame used by block 1")
    ap.add_argument("--contact-sheet", metavar="PATH", nargs="?", const=str(HERE / "frames" / "_contact_sheet.png"))
    a = ap.parse_args()

    sets = block_sets()
    print(f"distinct portrait sets in block 1: {len(sets)}")
    by_size = {}
    for names in sets.values():
        by_size[len(names)] = by_size.get(len(names), 0) + 1
    print("  by cast size: " + ", ".join(f"{k}->{v}" for k, v in sorted(by_size.items())))

    if a.block:
        FRAMES.mkdir(exist_ok=True)
        for names in sets.values():
            ensure(names)
        print(f"frames written to {FRAMES}")
    if a.contact_sheet:
        FRAMES.mkdir(exist_ok=True)
        print("contact sheet ->", contact_sheet(sets, a.contact_sheet))


if __name__ == "__main__":
    main()
