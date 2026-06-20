#!/usr/bin/env python3
"""
Fetch SPECIFIC named portraits that aren't `<Name> Official.<ext>` files.

The main scraper (scrape_official_images.py) only keeps clean `File:<Name> Official.<ext>`
images via the wiki-wide allimages enumeration. Some characters have no Official portrait, so
a human picks a specific gallery/file image instead (e.g. a Donghua still). Those choices are
recorded here so the (gitignored) binaries stay regenerable.

Each entry maps a canonical character name -> the exact `File:` title on the wiki. We resolve the
direct image URL via the imageinfo API and download to "<Canonical Name>.<ext>" in the asset dir,
matching character_map.json's `image` field. Idempotent: skips existing files unless --force.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://lordofthemysteries.fandom.com/api.php"
UA = "LOTM-fan-project/1.0 (character-scene-video asset scraper)"
DEST = Path(__file__).resolve().parent.parent / "tts_pipeline" / "assets" / "characters" / "lotm"

# Canonical character name -> exact wiki File: title (human-chosen; no Official.jpg exists).
PORTRAITS: dict[str, str] = {
    "Melissa Moretti": "File:Melissa Moretti Donghua.jpg",
    "Benson Moretti": "File:EP 2 - Benson (cropped).jpg",
    "Rozanne": "File:EP 2 - Rozanne Adelaide (cropped).png",
    "Old Neil": "File:Old Neil Character File.jpg",
    "Angelica Barrehart": "File:EP 4 - Angelica (cropped).jpg",
    "Frye": "File:EP 3 - Frye (cropped).jpg",
    "Glacis": "File:EP 4 - Glacis (cropped).jpg",
    "Annie": "File:Annie2.png",
    "Earl Hall": "File:Earl Hall Manhua 2020.png",
    "Quentin Cohen": "File:Manhua 2025 Ch 20 - Quentin Cohen.jpg",
    "Wendy Smyrin": "File:Wendy Smyrin Manhua 2020.jpg",
    "Aguesid Negan": "File:Aguesid-manhua.jpeg",
    "Hanass Vincent": "File:EP 4 - Hanass (cropped).jpg",
    "Susie": "File:EP 4 - Susie (cropped).jpg",
    "Royale Reideen": "File:EP 2 - Royale Reideen (cropped).png",
    "Elliott Vickroy": "File:EP 2 - Elliott (cropped).jpg",
}


def _get(params: dict) -> dict:
    params = {**params, "format": "json"}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def resolve(title: str) -> dict:
    data = _get({"action": "query", "titles": title, "prop": "imageinfo",
                 "iiprop": "url|size|mime"})
    pages = data["query"]["pages"]
    page = next(iter(pages.values()))
    if "imageinfo" not in page:
        raise RuntimeError(f"no imageinfo for {title!r} (missing/renamed?)")
    return page["imageinfo"][0]


def safe_filename(name: str, mime: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", name)
    ext = "png" if mime == "image/png" else "jpg"
    return f"{safe}.{ext}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="Re-download even if the file exists")
    args = ap.parse_args()

    DEST.mkdir(parents=True, exist_ok=True)
    downloaded = skipped = failed = 0
    for name, title in PORTRAITS.items():
        try:
            info = resolve(title)
            out_path = DEST / safe_filename(name, info["mime"])
            if out_path.exists() and not args.force:
                print(f"  skip (exists): {out_path.name}")
                skipped += 1
                continue
            req = urllib.request.Request(info["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                out_path.write_bytes(resp.read())
            print(f"  saved: {out_path.name}  ({info.get('width')}x{info.get('height')}, {info['mime']})")
            downloaded += 1
            time.sleep(0.2)  # be polite to the wiki
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED {name} <- {title}: {exc}", file=sys.stderr)
            failed += 1

    print(f"Downloaded: {downloaded}  Skipped(existing): {skipped}  Failed: {failed}")


if __name__ == "__main__":
    main()
