#!/usr/bin/env python3
"""
Build a full per-batch Scene Timeline from per-chapter scene JSONs (timelines/scenes/ch_<N>.json).

- Persona resolution: scene's protagonist_persona, with the base "Klein (Beginning)" flipped to
  "Klein Moretti" from the Nighthawks-induction anchor onward (NIGHTHAWKS_ANCHOR).
- Images resolved from _manifest.json; non-portrait characters cross-referenced against the
  384-character registry -> "get image" (wiki char) vs minor vs unnamed background.
- Durations are char-share ESTIMATES x each chapter's audio duration (placeholder until alignment).

Output: timelines/block_01_ch001-050.md (chapter-by-chapter, reviewable) + .json
Usage: python build_block.py [first_chapter last_chapter]   (default 1 50)
"""
from __future__ import annotations
import csv, glob, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
FT = ROOT / "formatted_text" / "lotm_book1" / "Volume_1_Clown"
SCENES_DIR = HERE / "timelines" / "scenes"
MANIFEST = ROOT / "tts_pipeline" / "assets" / "characters" / "lotm" / "_manifest.json"
DUR_CSV = Path("D:/PDFReader/lotm_book1_output/_durations.csv")
OUT = HERE / "timelines"

NIGHTHAWKS_ANCHOR = 17  # ch17: Klein signs the Nighthawks contract ("from now on, you are one of us")

PERSONA = {
    "Zhou Mingrui": ("Klein (as Zhou Mingrui)", "Zhou Mingrui.jpg"),
    "Klein (Beginning)": ("Klein (Beginning)", "Klein Moretti (Beginning of the Series).jpg"),
    "Klein Moretti": ("Klein Moretti", "Klein Moretti.jpg"),
    "The Fool": ("Klein (as The Fool)", "The Fool.jpg"),
    "Sherlock Moriarty": ("Klein (as Sherlock Moriarty)", "Sherlock Moriarty.jpg"),
    "Gehrman Sparrow": ("Klein (as Gehrman Sparrow)", "Gehrman Sparrow.jpg"),
}
PERSONA_IMG_NAMES = {"Zhou Mingrui", "Klein Moretti", "Klein Moretti (Beginning of the Series)",
                     "The Fool", "Sherlock Moriarty", "Gehrman Sparrow", "Dwayne Dantès", "Merlin Hermes"}


def load_images():
    avail = {}
    for m in json.loads(MANIFEST.read_text(encoding="utf-8")):
        if m["kind"] != "character" or m["name"] in PERSONA_IMG_NAMES or not m["row_viable"]:
            continue
        avail[m["name"]] = f"{m['name']}.{'png' if m['mime']=='image/png' else 'jpg'}"
    return avail


def load_durations():
    d = {}
    with open(DUR_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d[int(row["Ch"])] = float(row["Sec"])
    return d


AVAIL = load_images()
REGISTRY = set(json.loads((HERE / "character_registry.json").read_text(encoding="utf-8"))["characters"])
_AL = json.loads((HERE / "name_aliases.json").read_text(encoding="utf-8"))
ALIASES = _AL["aliases"]
EXCLUDE = set(_AL.get("exclude", []))
CONT = json.loads((HERE / "continuity.json").read_text(encoding="utf-8"))["boundaries"]
DUR = load_durations()


def chapter_file(n):
    hits = sorted(FT.glob(f"Chapter_{n}_*.txt"))
    return hits[0] if hits else None


def title_of(n):
    f = chapter_file(n)
    return f.stem.split("_", 2)[2].replace("_", " ") if f else f"Chapter {n}"


def body_chars(n, ls, le):
    f = chapter_file(n)
    lines = f.read_text(encoding="utf-8").splitlines()
    return sum(len(lines[i-1].strip()) for i in range(ls, min(le, len(lines))+1) if 1 <= i <= len(lines))


def hms(sec):
    sec = int(round(sec))
    return f"{sec//3600:d}:{(sec%3600)//60:02d}:{sec%60:02d}"


def resolve(scene, chapter, carried=()):
    persona = scene.get("protagonist_persona")
    if persona == "Klein (Beginning)" and chapter >= NIGHTHAWKS_ANCHOR:
        persona = "Klein Moretti"
    cast, images, missing = [], [], []
    if scene.get("protagonist_present") and persona:
        label, img = PERSONA[persona]
        cast.append(label); images.append(img)
    others = list(scene.get("other_characters", []))
    for nm in carried:                           # carry cast across a continuing chapter boundary
        if nm not in others:
            others.append(nm)
    seen = set()
    for name in others:
        name = ALIASES.get(name, name)          # canonicalize (merge invented surnames/title prefixes)
        if name in EXCLUDE or name in seen:      # drop non-people (e.g. dog Susie) / dedupe
            continue
        seen.add(name)
        cast.append(name)
        (images.append(AVAIL[name]) if name in AVAIL else missing.append(name))
    if not images:
        return cast, ["(hold previous frame)"], missing, "hold-previous"
    n = len(images)
    return cast, images, missing, ("single" if n == 1 else (f"row({n})" if n <= 4 else f"grid({n})"))


def classify(label):
    if label.startswith("Klein") or label in AVAIL:
        return "have"
    if label.startswith("["):
        return "background"
    return "need" if label in REGISTRY else "minor"


def main():
    first, last = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, 50)
    offset, index, chapters_out, prev_images = 0.0, {}, [], []
    for ch in range(first, last + 1):
        sf = SCENES_DIR / f"ch_{ch}.json"
        if not sf.exists():
            continue
        specs = json.loads(sf.read_text(encoding="utf-8"))["scenes"]
        counts = [max(1, body_chars(ch, s["line_start"], s["line_end"])) for s in specs]
        tot = sum(counts)
        cont = CONT.get(str(ch - 1), {})
        continues = cont.get("continues", False)
        carried = cont.get("carried_others", []) if continues else []
        rows = []
        for idx, (s, cc) in enumerate(zip(specs, counts)):
            cast, images, missing, layout = resolve(s, ch, carried if idx == 0 else ())
            if layout == "hold-previous" and prev_images:   # carry the actual previous frame
                images = list(prev_images)
            cont_prev = idx == 0 and continues
            dur = DUR[ch] * cc / tot
            rows.append({"start": hms(offset), "duration": hms(dur), "present_cast": cast,
                         "images": images, "missing_images": missing, "layout": layout,
                         "continues_prev": cont_prev, "text_anchor": s.get("text_anchor", "")})
            prev_images = images
            for label in cast:
                key = "Klein Moretti (protagonist)" if label.startswith("Klein") else label
                e = index.setdefault(key, {"status": classify(label), "scenes": 0})
                e["scenes"] += 1
            offset += dur
        chapters_out.append({"chapter": ch, "title": title_of(ch), "scenes": rows})

    # ---- write markdown ----
    STATUS = {"have": "✅", "need": "❌ get image (wiki char)", "minor": "➖ minor (no wiki page)",
              "background": "· unnamed"}
    L = [f"# Scene Timeline — Block 1 (chapters {first}-{last})", "",
         f"_Content pass, full-cast tracking. Durations are char-share ESTIMATES (placeholder until forced "
         f"alignment). Base persona flips Klein (Beginning) -> Klein Moretti at ch{NIGHTHAWKS_ANCHOR} "
         f"(Nighthawks contract). Review chapter-by-chapter; correct any cast/persona; missing wiki "
         f"characters are listed at the bottom._", "",
         f"**Total:** {hms(offset)}  ·  **scenes:** {sum(len(c['scenes']) for c in chapters_out)}  ·  "
         f"**chapters:** {len(chapters_out)}", ""]
    for c in chapters_out:
        L.append(f"## Chapter {c['chapter']}: {c['title']}")
        if c["scenes"] and c["scenes"][0]["continues_prev"]:
            L.append(f"_↳ continues the scene from Chapter {c['chapter']-1} (cast carries over)_")
        L += ["", "| Start | Dur | Present cast | Image(s) | Missing |", "|---|---|---|---|---|"]
        for r in c["scenes"]:
            miss = ", ".join(r["missing_images"]) or "—"
            anchor = "↳ " if r["continues_prev"] else ""
            L.append(f"| {r['start']} | {r['duration']} | {anchor}{', '.join(r['present_cast'])} | "
                     f"{', '.join(r['images'])} | {miss} |")
        L.append("")
    # ---- consolidated character index ----
    L += ["## Character index (whole batch)", "", "| Character | Status | Scenes |", "|---|---|---|"]
    for name in sorted(index, key=lambda n: (-index[n]["scenes"], n)):
        L.append(f"| {name} | {STATUS[index[name]['status']]} | {index[name]['scenes']} |")
    need = sorted(n for n in index if index[n]["status"] == "need")
    minor = sorted(n for n in index if index[n]["status"] == "minor")
    bg = sum(1 for n in index if index[n]["status"] == "background")
    L += ["", f"**🎯 Get an image — wiki characters with no portrait ({len(need)}):** " + (", ".join(need) or "none"),
          f"**Minor named (no wiki page) ({len(minor)}):** " + (", ".join(minor) or "none"),
          f"**Unnamed background figures:** {bg}"]
    (OUT / f"block_01_ch{first:03d}-{last:03d}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (OUT / f"block_01_ch{first:03d}-{last:03d}.json").write_text(
        json.dumps({"batch": 1, "chapters": f"{first}-{last}", "total": hms(offset),
                    "chapters_detail": chapters_out, "characters_index": index}, indent=2, ensure_ascii=False),
        encoding="utf-8")

    print(f"Block ch{first}-{last}: {len(chapters_out)} chapters, "
          f"{sum(len(c['scenes']) for c in chapters_out)} scenes, {hms(offset)}")
    print(f"  wiki chars needing images: {len(need)}")
    print(f"  -> {', '.join(need)}")


if __name__ == "__main__":
    main()
