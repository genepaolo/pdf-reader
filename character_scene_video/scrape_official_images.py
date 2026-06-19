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
UA = "LOTM-fan-project/1.0 (character-scene-video asset scraper)"

# allimages returns `name` with UNDERSCORES, e.g. "Audrey_Hall_Official.jpg".
# Keep exactly "<Name>_Official.<ext>"; drop the Crop/Cropped/Full variants. We enumerate
# wiki-wide (NOT just Category:Official_Character_Images) because that category is incomplete —
# some clean Official.jpg files live only on a character's gallery page (e.g. Audrey Hall, Alger Wilson).
OFFICIAL_RE = re.compile(r"^(?P<name>.+)_Official\.(?P<ext>jpg|jpeg|png)$", re.IGNORECASE)
VARIANT_RE = re.compile(r"_Official_(Crop|Cropped|Full)\.", re.IGNORECASE)

# Wiki-wide discovery also matches place/concept "Official" images (not characters). These are
# tagged kind="place" so the character roster can skip them (but they remain available, e.g. as
# location backdrops).
PLACES = {
    "Divination Club", "Forsaken Land of the Gods", "Giant King's Court", "Giant King’s Court",
    "Hornacis Mountain Range", "Inverted Mausoleum", "Liveseyd", "Mind World", "Sefirah Castle",
    "Spirit World", "Spirit World Appearance", "Tingen City",
}

# Images whose dimensions are unusable as a standing portrait in a multi-character row
# (e.g. landscape banners). Tagged not row-viable so the compositor skips them in group scenes.
NON_PORTRAIT = {"Klein"}  # "Klein Official.jpg" is a 670x360 banner, not a standing portrait

DEST = Path(__file__).resolve().parent.parent / "tts_pipeline" / "assets" / "characters" / "lotm"


def _get(params: dict) -> dict:
    params = {**params, "format": "json"}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def discover_official_portraits() -> list[dict]:
    """Enumerate ALL files wiki-wide and keep the clean `<Name> Official.<ext>` ones, tagging each
    character vs place and whether it is viable in a multi-character row (portrait-ish aspect)."""
    out: list[dict] = []
    cont: str | None = None
    while True:
        params = {"action": "query", "list": "allimages", "ailimit": "500",
                  "aiprop": "url|size|mime", "aisort": "name"}
        if cont:
            params["aicontinue"] = cont
        data = _get(params)
        for img in data["query"]["allimages"]:
            fname = img["name"]  # underscores
            if VARIANT_RE.search(fname):
                continue
            m = OFFICIAL_RE.match(fname)
            if not m:
                continue
            name = m.group("name").replace("_", " ")
            w, h = img.get("width") or 0, img.get("height") or 0
            row_viable = name not in NON_PORTRAIT and h >= w  # portrait-ish, tall enough for a row
            out.append({
                "title": f"File:{fname}",
                "name": name,
                "kind": "place" if name in PLACES else "character",
                "row_viable": bool(row_viable),
                "url": img["url"],
                "width": img.get("width"),
                "height": img.get("height"),
                "mime": img.get("mime"),
            })
        cont = data.get("continue", {}).get("aicontinue")
        if not cont:
            break
    return out


def safe_filename(name: str, mime: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", name)
    ext = "png" if mime == "image/png" else "jpg"
    return f"{safe}.{ext}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="Re-download even if the file exists")
    ap.add_argument("--list-only", action="store_true", help="Print the selected set; download nothing")
    ap.add_argument("--include-places", action="store_true",
                    help="Also download place/concept Official images (default: characters only)")
    args = ap.parse_args()

    found = sorted(discover_official_portraits(), key=lambda m: m["name"].lower())
    chars = [m for m in found if m["kind"] == "character"]
    places = [m for m in found if m["kind"] == "place"]
    print(f"Wiki-wide Official portraits: {len(found)}  "
          f"(characters: {len(chars)}, places: {len(places)})")

    to_download = found if args.include_places else chars

    if args.list_only:
        for m in to_download:
            flag = "" if m["row_viable"] else "  [NOT row-viable]"
            print(f"  {m['name']:34} {m['kind']:9} {m['width']}x{m['height']}{flag}")
        return

    DEST.mkdir(parents=True, exist_ok=True)
    # Manifest is the full source-of-truth record (characters + places); downloads are filtered.
    (DEST / "_manifest.json").write_text(json.dumps(found, indent=2, ensure_ascii=False), "utf-8")

    downloaded = skipped = failed = 0
    for m in to_download:
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
