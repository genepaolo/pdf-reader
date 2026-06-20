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
import csv, glob, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
FT = ROOT / "formatted_text" / "lotm_book1" / "Volume_1_Clown"
SCENES_DIR = HERE / "timelines" / "scenes"
MANIFEST = ROOT / "tts_pipeline" / "assets" / "characters" / "lotm" / "_manifest.json"
CHAR_MAP = ROOT / "tts_pipeline" / "assets" / "characters" / "lotm" / "character_map.json"
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
    # character_map.json is the committed source of truth for manual portrait picks (characters
    # with no `<Name> Official.<ext>` file, so absent from the regenerable manifest). It overrides
    # the manifest. Skip entries explicitly flagged row_viable=false (e.g. landscape banners).
    for name, entry in json.loads(CHAR_MAP.read_text(encoding="utf-8")).get("characters", {}).items():
        if entry.get("image") and entry.get("row_viable", True):
            avail[name] = entry["image"]
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
_DEC = HERE / "portrait_decisions.json"
DECISIONS = json.loads(_DEC.read_text(encoding="utf-8"))["decisions"] if _DEC.exists() else {}
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
    if label not in REGISTRY:
        return "minor"
    return "declined" if DECISIONS.get(label) == "no" else "need"


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
            rows.append({"start": hms(offset), "end": hms(offset + dur), "duration": hms(dur),
                         "present_cast": cast, "images": images, "missing_images": missing,
                         "layout": layout, "continues_prev": cont_prev,
                         "line_start": s["line_start"], "line_end": s["line_end"],
                         "setting": s.get("setting", ""),
                         "text_anchor": s.get("text_anchor", "")})
            prev_images = images
            for label in cast:
                key = "Klein Moretti (protagonist)" if label.startswith("Klein") else label
                e = index.setdefault(key, {"status": classify(label), "scenes": 0})
                e["scenes"] += 1
            offset += dur
        chapters_out.append({"chapter": ch, "title": title_of(ch), "scenes": rows})

    # ---- write markdown (skim-friendly: per-scene blocks, inline portrait status) ----
    INLINE = {"have": "✅", "need": "❌", "declined": "🚫", "minor": "➖", "background": ""}

    def slug(s):
        return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", s.lower()).strip())

    def cast_line(r):
        parts = []
        for label in r["present_cast"]:
            m = INLINE[classify(label)]
            parts.append(f"{label} {m}".strip())
        return " · ".join(parts) if parts else "—"

    L = [f"# Scene Timeline — Block 1 (chapters {first}-{last})", "",
         f"**Total** {hms(offset)} · **{sum(len(c['scenes']) for c in chapters_out)} scenes** · "
         f"{len(chapters_out)} chapters &nbsp;|&nbsp; durations are char-share ESTIMATES (until forced "
         f"alignment) &nbsp;|&nbsp; `↳` = scene continues from the previous chapter.", "",
         "**Portrait status:**  ✅ has one · ❌ wiki character, none yet (your call) · ➖ minor (no wiki "
         "page) · unnamed extras shown plain.", "",
         "**Jump to chapter:** " + " · ".join(
             f"[{c['chapter']}](#chapter-{c['chapter']}-{slug(c['title'])})" for c in chapters_out), "",
         "---", ""]
    for c in chapters_out:
        cont = "  _↳ continues from Ch " + str(c["chapter"] - 1) + "_" if (
            c["scenes"] and c["scenes"][0]["continues_prev"]) else ""
        L += [f"## Chapter {c['chapter']}: {c['title']}{cont}", ""]
        for i, r in enumerate(c["scenes"], 1):
            tag = "↳ " if r["continues_prev"] else ""
            L.append(f"**S{i}** &nbsp; `{r['start']} → {r['end']}` &nbsp;·&nbsp; {r['duration']} &nbsp;·&nbsp; `L{r['line_start']}–{r['line_end']}` &nbsp; {tag}{cast_line(r)}  ")
            L.append(f"_{r['setting']}_  ")
            L.append(f"> {r['text_anchor']}")
            L.append("")
    # ---- consolidated character index ----
    STATUS = {"have": "✅", "need": "❌ get image (wiki char)", "declined": "🚫 no portrait (by decision)",
              "minor": "➖ minor (no wiki page)", "background": "· unnamed"}
    L += ["## Character index (whole batch)", "", "| Character | Status | Scenes |", "|---|---|---|"]
    for name in sorted(index, key=lambda n: (-index[n]["scenes"], n)):
        L.append(f"| {name} | {STATUS[index[name]['status']]} | {index[name]['scenes']} |")
    need = sorted(n for n in index if index[n]["status"] == "need")
    declined = sorted(n for n in index if index[n]["status"] == "declined")
    minor = sorted(n for n in index if index[n]["status"] == "minor")
    bg = sum(1 for n in index if index[n]["status"] == "background")
    L += ["", f"**🎯 Get an image — wiki characters with no portrait ({len(need)}):** " + (", ".join(need) or "none"),
          f"**🚫 Declined — no portrait by decision ({len(declined)}):** " + (", ".join(declined) or "none"),
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
