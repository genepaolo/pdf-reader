#!/usr/bin/env python3
"""Stage 7: per-part YouTube upload pack (title + description + pinned comment + tags).

Volumes upload as PARTS (YouTube enforces its 12 h / 256 GB cap — the 43 h single file was
rejected 2026-08-28). All series/volume copy lives in projects/<name>/upload_meta.json (part
ranges + hooks per volume, tag/hashtag/pitch lines); this script is engine-generic. For each
part it emits, next to the part's MP4 in <video_out>/<Volume_dir>/:

    Block_NN_chAAA-BBB_description_YOUTUBE.txt   paste into the description (<= 5,000 chars)
    Block_NN_chAAA-BBB_pinned_comment.txt        post + pin after publishing (<= 10,000 chars)
    Block_NN_chAAA-BBB_tags.txt                  paste into the Tags field (<= 500 chars)

and prints the suggested title (<= 100 chars). Chapter timestamps come from the part's
_description.txt written by build_block_video.py, so run that first. A ~50-chapter part's FULL
per-chapter marker list fits the 5,000-char description, so every chapter gets a real in-player
chapter segment; the pinned comment repeats the list (not everyone reads descriptions) under the
part-to-part navigation links.

    py -3.12 character_scene_video/make_upload_pack.py --volume 1            # all parts
    py -3.12 character_scene_video/make_upload_pack.py --volume 1 --part 3   # one part
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import charvid_project  # noqa: E402

LIMITS = {"_description_YOUTUBE.txt": 5000, "_pinned_comment.txt": 10000, "_tags.txt": 500}


def parse_desc(path):
    """-> [(stamp, 'Chapter N: Title')] from a build_block_video _description.txt."""
    lines = []
    for l in path.read_text(encoding="utf-8").splitlines():
        if l[:1].isdigit() and " Chapter " in l:
            stamp, rest = l.split(" ", 1)
            lines.append((stamp, rest))
    return lines


def build_part(P, meta, vol_no, vol, part_no):
    parts = vol["parts"]
    total = len(parts)
    part = parts[part_no - 1]
    first, last = part["first"], part["last"]

    out_dir = P.video_dir(first)
    stem = f"Block_{P.block_no(first):02d}_ch{first:03d}-{last:03d}"
    src = out_dir / f"{stem}_description.txt"
    if not src.exists():
        sys.exit(f"{src} missing -- run build_block_video.py {first} {last} first")
    chapters = parse_desc(src)
    assert chapters[0][0] == "0:00" and len(chapters) == last - first + 1, "bad description file"

    # duration ~= last stamp; good enough for the rounded hours figure
    h, m = (chapters[-1][0].split(":") + ["0"])[:2]
    hours = round(int(h) + int(m) / 60)

    finale = " (finale)" if part_no == total else ""
    nav = [f"THIS IS PART {part_no} OF {total} — Volume {vol_no} is split for YouTube's "
           "12-hour upload limit:"]
    for n, p in enumerate(parts, 1):
        mark = "  ◀ YOU ARE HERE" if n == part_no else ""
        nav.append(f"Part {n} · Chapters {p['first']}–{p['last']}"
                   f"{' (finale)' if n == total else ''}{mark}")
    nav.append(f"▶ All parts are in the Volume {vol_no} playlist on this channel — links in the "
               "pinned comment.")

    next_up = (f"Part {part_no + 1} (Chapters {parts[part_no]['first']}–{parts[part_no]['last']})"
               if part_no < total else vol.get("next_teaser", "the next volume"))

    desc = "\n".join([
        f"{P.series_title} — Volume {vol_no}: {vol['name']}, PART {part_no} of {total}"
        f" (Chapters {first}–{last}){finale}. The hit web novel as a continuous audiobook"
        f" — {hours} hours, every chapter timestamped.",
        "",
        part.get("hook", ""),
        "",
        meta["usp_line"],
        "",
        meta["bridge_line"],
        "",
        *nav,
        "",
        "CHAPTERS (your watch position saves automatically)",
        *[f"{st} {rest}" for st, rest in chapters],
        "",
        meta["credit_line"],
        "",
        f"Next up: {next_up} — subscribe so you don't miss it. " + meta.get("also_line", ""),
        "",
        meta["hashtags"],
    ])

    pin = "\n".join([
        f"Volume {vol_no}: {vol['name']} — all {total} parts (tap to jump):",
        *[f"▶ Part {n} (Chapters {p['first']}–{p['last']}): "
          + ("you are here" if n == part_no else "[link]") for n, p in enumerate(parts, 1)],
        "",
        "Full chapter list (tap a timestamp to jump):",
        *[f"{st} {rest}" for st, rest in chapters],
    ])

    tags = ",".join(x for x in [meta["tags"], vol.get("extra_tags", ""),
                                f"lotm volume {vol_no} part {part_no}"] if x)

    title = (f"{meta['search_title']} — Volume {vol_no}: {vol['name']} | "
             f"Part {part_no} of {total} (Ch {first}–{last}, {hours} Hours)")

    print(f"TITLE ({len(title)}/100): {title}")
    for suffix, text in [("_description_YOUTUBE.txt", desc + "\n"),
                         ("_pinned_comment.txt", pin + "\n"),
                         ("_tags.txt", tags + "\n")]:
        path = out_dir / f"{stem}{suffix}"
        n, cap = len(text), LIMITS[suffix]
        if n > cap:
            sys.exit(f"  {path.name}: {n} chars OVER the {cap} limit -- trim upload_meta.json")
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.name}  ({n}/{cap} chars)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume", type=int, required=True)
    ap.add_argument("--part", type=int, help="one part only (default: all parts of the volume)")
    ap.add_argument("--project", default=None)
    a = ap.parse_args()
    P = charvid_project.load(a.project)

    meta_file = P.dir / "upload_meta.json"
    if not meta_file.exists():
        sys.exit(f"{meta_file} missing -- create it (see projects/lotm_book1/upload_meta.json)")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    vol = meta["volumes"].get(str(a.volume))
    if not vol:
        sys.exit(f"volume {a.volume} not in {meta_file.name} -- add its parts + hooks first")

    part_nos = [a.part] if a.part else range(1, len(vol["parts"]) + 1)
    for n in part_nos:
        build_part(P, meta, a.volume, vol, n)


if __name__ == "__main__":
    main()
