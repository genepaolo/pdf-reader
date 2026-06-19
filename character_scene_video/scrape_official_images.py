#!/usr/bin/env python3
"""
Scrape official LOTM character portraits for the character-scene video feature.

Rule (per project decision): keep ONLY `File:<Name> Official.jpg|jpeg|png`.
Never the `Official Crop`, `Official Cropped`, or `Official Full` variants, and never the
bare/unofficial files. See character_scene_video/DESIGN.md §2.

Source category:
    https://lordofthemysteries.fandom.com/wiki/Category:Official_Character_Images

Downloads to tts_pipeline/assets/characters/lotm/ and writes _manifest.json. Idempotent:
re-running re-fetches the manifest and only downloads files that are missing (use --force to
re-download all). The image binaries are gitignored; this script + the manifest are the
source of truth.
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
CATEGORY = "Category:Official_Character_Images"
UA = "LOTM-fan-project/1.0 (character-scene-video asset scraper)"

# Exactly "<Name> Official.<ext>" — excludes "... Official Crop/Cropped/Full.<ext>" and bare names.
OFFICIAL_RE = re.compile(r"^File:(?P<name>.+) Official\.(?P<ext>jpg|jpeg|png)$", re.IGNORECASE)

DEST = Path(__file__).resolve().parent.parent / "tts_pipeline" / "assets" / "characters" / "lotm"


def _get(params: dict) -> dict:
    params = {**params, "format": "json"}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def list_category_files() -> list[str]:
    titles: list[str] = []
    cont: str | None = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": CATEGORY,
            "cmtype": "file",
            "cmlimit": "500",
        }
        if cont:
            params["cmcontinue"] = cont
        data = _get(params)
        titles += [m["title"] for m in data["query"]["categorymembers"]]
        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            break
    return titles


def resolve_image_urls(titles: list[str]) -> list[dict]:
    out: list[dict] = []
    # API caps titles per request; chunk to be safe.
    for i in range(0, len(titles), 50):
        chunk = titles[i : i + 50]
        data = _get(
            {
                "action": "query",
                "prop": "imageinfo",
                "iiprop": "url|size|mime",
                "titles": "|".join(chunk),
            }
        )
        for page in data["query"]["pages"].values():
            info = page.get("imageinfo")
            if not info:
                continue
            ii = info[0]
            m = OFFICIAL_RE.match(page["title"])
            out.append(
                {
                    "title": page["title"],
                    "name": m.group("name") if m else page["title"],
                    "url": ii["url"],
                    "width": ii.get("width"),
                    "height": ii.get("height"),
                    "mime": ii.get("mime"),
                }
            )
    return out


def safe_filename(name: str, mime: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", name)
    ext = "png" if mime == "image/png" else "jpg"
    return f"{safe}.{ext}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="Re-download even if the file exists")
    ap.add_argument("--list-only", action="store_true", help="Print the selected set; download nothing")
    args = ap.parse_args()

    all_titles = list_category_files()
    selected = [t for t in all_titles if OFFICIAL_RE.match(t)]
    print(f"Category files: {len(all_titles)}  ->  Official portraits selected: {len(selected)}")

    manifest = sorted(resolve_image_urls(selected), key=lambda m: m["name"].lower())

    if args.list_only:
        for m in manifest:
            print(f"  {m['name']:40} {m['width']}x{m['height']} {m['mime']}")
        return

    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), "utf-8")

    downloaded = skipped = failed = 0
    for m in manifest:
        out_path = DEST / safe_filename(m["name"], m["mime"])
        if out_path.exists() and not args.force:
            skipped += 1
            continue
        try:
            req = urllib.request.Request(m["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                out_path.write_bytes(resp.read())
            downloaded += 1
            time.sleep(0.2)  # be polite to the wiki
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED {m['name']}: {exc}", file=sys.stderr)
            failed += 1

    print(f"Downloaded: {downloaded}  Skipped(existing): {skipped}  Failed: {failed}")
    print(f"Manifest: {DEST / '_manifest.json'}")


if __name__ == "__main__":
    main()
