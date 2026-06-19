#!/usr/bin/env python3
"""
Build character_registry.json — the canonical list of Book 1 characters important enough to
have their own wiki article (Category:Book One Characters), cross-referenced with which ones
have an official portrait in our asset set.

This is the reference the per-batch Scene Timeline checks against: every named character in a
scene is recorded, and ones lacking a portrait become the "needs an image" list (DESIGN.md §10).
Run anytime to refresh; images are matched from _manifest.json.
"""
from __future__ import annotations
import json
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://lordofthemysteries.fandom.com/api.php"
UA = "LOTM-fan-project/1.0 (character registry)"
HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / "tts_pipeline" / "assets" / "characters" / "lotm" / "_manifest.json"
OUT = HERE / "character_registry.json"

# All these portraits depict the protagonist; attribute them to his category entries.
PROTAGONIST_PERSONAS = {
    "Klein", "Klein Moretti", "Klein Moretti (Beginning of the Series)", "Zhou Mingrui",
    "The Fool", "Gehrman Sparrow", "Sherlock Moriarty", "Dwayne Dantès", "Merlin Hermes",
}
PROTAGONIST_CATEGORY_NAMES = {"Klein Moretti", "Zhou Mingrui"}

# category name -> image basename, where the wiki article title differs from the image filename.
CATEGORY_IMAGE_OVERRIDE = {
    "Will Auceptin": "Wil Auceptin",
    "Danitz Dubois": "Danitz",
    "Sharron": "Sharron Cropped",
}


def _get(params: dict) -> dict:
    url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json'})}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def book_one_characters() -> list[str]:
    names, cont = [], None
    while True:
        p = {"action": "query", "list": "categorymembers",
             "cmtitle": "Category:Book_One_Characters", "cmtype": "page", "cmlimit": "500"}
        if cont:
            p["cmcontinue"] = cont
        d = _get(p)
        names += [m["title"] for m in d["query"]["categorymembers"] if m["ns"] == 0]
        cont = d.get("continue", {}).get("cmcontinue")
        if not cont:
            break
    return sorted(names)


def main() -> None:
    names = book_one_characters()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    images = {m["name"]: m for m in manifest if m["kind"] == "character"}
    used_images: set[str] = set()

    registry: dict[str, dict] = {}
    for name in names:
        entry: dict = {"wiki": True, "has_image": False, "image": None}
        if name in PROTAGONIST_CATEGORY_NAMES:
            entry["has_image"] = True
            entry["protagonist"] = True
            entry["image"] = "(persona system — see character_map.json)"
            used_images |= {f"{p}" for p in PROTAGONIST_PERSONAS if p in images}
        else:
            img_name = CATEGORY_IMAGE_OVERRIDE.get(name, name)
            if img_name in images and img_name not in PROTAGONIST_PERSONAS:
                m = images[img_name]
                entry["has_image"] = True
                entry["image"] = f"{img_name}.{ 'png' if m['mime']=='image/png' else 'jpg'}"
                entry["row_viable"] = m["row_viable"]
                used_images.add(img_name)
        registry[name] = entry

    with_image = sum(1 for e in registry.values() if e["has_image"])
    # Images we have that didn't map to any category entry (spelling drift / extras to reconcile).
    unused = sorted(set(images) - used_images - PROTAGONIST_PERSONAS)

    out = {
        "_source": "Category:Book One Characters (fandom) — characters with their own wiki article",
        "_note": "has_image cross-references _manifest.json. Names without images are tracked so they "
                 "can be matched to user-supplied images later (DESIGN.md §10 full-cast tracking).",
        "total_characters": len(names),
        "with_image": with_image,
        "without_image": len(names) - with_image,
        "characters": registry,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Book One Characters: {len(names)}")
    print(f"  with portrait:    {with_image}")
    print(f"  without portrait: {len(names) - with_image}")
    if unused:
        print(f"  ⚠️ image files NOT matched to a category name (reconcile): {unused}")
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
