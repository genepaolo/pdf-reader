#!/usr/bin/env python3
"""Composite one frame per distinct set of on-screen portraits.

Frames are cached by the sorted set of portrait filenames, so the ~10 000 scenes in a full book
collapse to a few hundred renders. Layout follows DESIGN.md section 6: normalise every portrait to a
common height, space them evenly on a 1920x1080 canvas, no name captions.

    py -3.12 character_scene_video/compose_frames.py --block            # all frames used by built blocks
    py -3.12 character_scene_video/compose_frames.py --contact-sheet     # one PNG to eyeball
    (add --project NAME for a non-default project)
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import charvid_project  # noqa: E402

W, H = 1920, 1080
MARGIN_X, MARGIN_Y = 70, 55
GAP_X, GAP_Y = 44, 36
MAX_PORTRAIT_H = 950
MAX_PER_FRAME = 9          # DESIGN section 6: cap huge Tarot gatherings

# Bump whenever the LAYOUT changes (rows_for/_fit_row/margins/rim sizes). It is part of the cache
# key, so old frames are orphaned rather than silently reused -- without this, a layout change
# leaves every cached PNG stale and re-rendering the videos changes nothing (the same silent-skip
# trap as render_chapter/build_block_video, which cost us a full sweep on 2026-08-29).
#   v2 (2026-09-03): rows_for() became aspect-aware and maximises the smallest row.
#   v3 (2026-09-03): fewest-rows tie-break, so one added portrait cannot reflow a scene.
LAYOUT_VERSION = 3

# how much smaller the fewest-row layout may be and still win (0.90 = accept up to 10% smaller)
ROW_TOLERANCE = 0.90

BG_TOP = (18, 17, 24)
BG_BOTTOM = (9, 9, 13)
RIM = (48, 46, 58)             # 1px rim: lifts a portrait off the backdrop, draws no attention
MENTION_RIM = (198, 158, 74)   # warm gold: this person is being TALKED ABOUT, not in the room
MENTION_RIM_W = 4


def background():
    """Dark vertical gradient -- portraits are the content, the backdrop must not compete."""
    bg = Image.new("RGB", (1, H))
    px = bg.load()
    for y in range(H):
        t = y / (H - 1)
        px[0, y] = tuple(round(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM))
    return bg.resize((W, H))


_BG = None


def _row_height(aspects, avail_h):
    """Height _fit_row() will settle on for one row of these aspects."""
    return min(MAX_PORTRAIT_H, avail_h,
               (W - 2 * MARGIN_X - GAP_X * (len(aspects) - 1)) / sum(aspects))


def rows_for(aspects):
    """Pick the row split that makes the SMALLEST portrait as large as possible.

    Supersedes the fixed DESIGN section 6 table (1 / 2-4 one row / 5-8 two rows / 9+ grid), which
    was blind to two things: it sized rows by their share of the canvas HEIGHT while leaving a
    third of the WIDTH empty (5 portraits rendered at 467px when one row fits them at 709px), and
    it ignored aspect ratio entirely -- a cast mixing tall character cards with near-square anime
    stills needs more rows than one of all-tall cards. So score real splits on real aspects and
    maximise the worst row. `aspects` may be an int for a rough count-only estimate.
    """
    if isinstance(aspects, int):
        aspects = [0.45] * aspects
    n = len(aspects)
    cands = []
    for r in range(1, min(3, n) + 1):
        base, extra = divmod(n, r)
        rows, i, worst = [], 0, float('inf')
        avail_h = (H - 2 * MARGIN_Y - GAP_Y * (r - 1)) / r
        for k in range(r):
            count = base + (1 if k < extra else 0)
            worst = min(worst, _row_height(aspects[i:i + count], avail_h))
            rows.append(count)
            i += count
        cands.append((rows, worst))
    # Prefer the FEWEST rows unless extra rows are materially bigger. Without this a single added
    # portrait can reflow a whole scene: ch347's 5 fit one row at 533px, but ch348 adds Steve and
    # one row drops to 443px -- just under the 467px of two rows -- so the frame split mid-fight
    # for a 5% gain. (user, 2026-09-03)
    best_h = max(h for _, h in cands)
    for rows, h in cands:                      # cands is ordered fewest-rows first
        if h >= best_h * ROW_TOLERANCE:
            return rows
    return cands[0][0]


def _fit_row(imgs, avail_w, avail_h):
    """Scale a row of portraits to a shared height that fits the space. -> [(img, w, h)]"""
    aspects = [im.width / im.height for im in imgs]
    gaps = GAP_X * (len(imgs) - 1)
    h = min(MAX_PORTRAIT_H, avail_h, (avail_w - gaps) / sum(aspects))
    return [(im, max(1, round(h * a)), max(1, round(h))) for im, a in zip(imgs, aspects)]


def compose(filenames, P, mentioned=()):
    """-> PIL image for this exact ORDERED list of portraits. A missing portrait file is a hard
    error -- silently dropping a character from the frame is exactly the wrong-art failure mode.

    Order is meaningful (build_block sets it): protagonist first, then Tarot Club members, then
    everyone else, then the mentioned-only names. Portraits in `mentioned` get a gold rim so a
    viewer can tell at a glance who is present and who is only being discussed."""
    mentioned = set(mentioned)
    global _BG
    if _BG is None:
        _BG = background()
    canvas = _BG.copy()

    names = list(filenames)[:MAX_PER_FRAME]
    imgs, flags = [], []
    for fn in names:
        p = P.portraits / fn
        if not p.exists():
            raise FileNotFoundError(
                f"portrait missing: {p} -- fix character_map.json/_manifest.json or re-fetch portraits")
        imgs.append(Image.open(p).convert("RGB"))
        flags.append(fn in mentioned)
    if not imgs:
        return canvas

    layout = rows_for([im.width / im.height for im in imgs])
    avail_w = W - 2 * MARGIN_X
    avail_h = H - 2 * MARGIN_Y - GAP_Y * (len(layout) - 1)
    row_h = avail_h / len(layout)

    placed, i = [], 0
    for count in layout:
        row = _fit_row(imgs[i:i + count], avail_w, row_h)
        placed.append([(im, w, h, flags[i + k]) for k, (im, w, h) in enumerate(row)])
        i += count

    # vertically centre the whole stack, horizontally centre each row
    total_h = sum(max(h for _, _, h, _ in row) for row in placed) + GAP_Y * (len(placed) - 1)
    y = (H - total_h) // 2
    draw = ImageDraw.Draw(canvas)
    for row in placed:
        rh = max(h for _, _, h, _ in row)
        x = (W - (sum(w for _, w, _, _ in row) + GAP_X * (len(row) - 1))) // 2
        for im, w, h, is_mention in row:
            resized = im.resize((w, h), Image.LANCZOS)
            top = y + (rh - h) // 2
            canvas.paste(resized, (x, top))
            if is_mention:
                for k in range(MENTION_RIM_W):
                    draw.rectangle([x - 1 - k, top - 1 - k, x + w + k, top + h + k],
                                   outline=MENTION_RIM)
            else:
                draw.rectangle([x - 1, top - 1, x + w, top + h], outline=RIM)
            x += w + GAP_X
        y += rh + GAP_Y
    return canvas


def key_for(filenames, mentioned=()):
    """Cache key: the ORDERED list of portraits plus which of them are mentioned-only.
    Order is part of the key because it is part of the picture (protagonist first, members next)."""
    names, seen = [], set()
    for fn in filenames:                       # dedupe, keep order
        if fn not in seen:
            seen.add(fn); names.append(fn)
    ment = [fn for fn in names if fn in set(mentioned)]
    raw = "|".join(names) + "#" + "|".join(ment) + "#L%d" % LAYOUT_VERSION
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16], names


def frame_path(filenames, P, mentioned=()):
    digest, _ = key_for(filenames, mentioned)
    return P.frames / f"{digest}.png"


def ensure(filenames, P, mentioned=()):
    """Render (once) and return the cached frame path."""
    out = frame_path(filenames, P, mentioned)
    if not out.exists():
        _, names = key_for(filenames, mentioned)
        P.frames.mkdir(exist_ok=True)
        compose(names, P, mentioned).save(out, optimize=True)
    return out


def block_sets(P):
    """Every distinct portrait set used by any built block timeline of this project."""
    sets = {}
    for bj in P.block_jsons():
        data = json.loads(bj.read_text(encoding="utf-8"))
        for c in data["chapters_detail"]:
            for s in c["scenes"]:
                imgs = [i for i in s["images"] if not i.startswith("(")]
                if imgs:
                    ment = s.get("mentioned_images", [])
                    d, names = key_for(imgs, ment)
                    sets[d] = (names, ment)
    return sets


def contact_sheet(sets, out, P):
    """One PNG showing every distinct frame, for a quick human check."""
    cols = 4
    tw, th = 480, 270
    rows = (len(sets) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
    for i, (names, ment) in enumerate(sets.values()):
        thumb = compose(names, P, ment).resize((tw, th), Image.LANCZOS)
        sheet.paste(thumb, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=None)
    ap.add_argument("--block", action="store_true", help="render every frame used by built blocks")
    ap.add_argument("--contact-sheet", metavar="PATH", nargs="?", const="")
    a = ap.parse_args()
    P = charvid_project.load(a.project)

    sets = block_sets(P)
    print(f"distinct portrait sets across built blocks: {len(sets)}")
    by_size = {}
    for names, _ in sets.values():
        by_size[len(names)] = by_size.get(len(names), 0) + 1
    print("  by cast size: " + ", ".join(f"{k}->{v}" for k, v in sorted(by_size.items())))

    if a.block:
        P.frames.mkdir(exist_ok=True)
        for names, ment in sets.values():
            ensure(names, P, ment)
        print(f"frames written to {P.frames}")
    if a.contact_sheet is not None:
        P.frames.mkdir(exist_ok=True)
        out = a.contact_sheet or str(P.frames / "_contact_sheet.png")
        print("contact sheet ->", contact_sheet(sets, out, P))


if __name__ == "__main__":
    main()
