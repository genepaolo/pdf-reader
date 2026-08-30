#!/usr/bin/env python3
"""
Build a full per-batch Scene Timeline from per-chapter scene JSONs
(projects/<name>/timelines/scenes/ch_<N>.json).

- Persona resolution: scene's protagonist_persona run through the project's chapter-anchored
  base_flips (book1: "Klein (Beginning)" -> "Klein Moretti" at ch17, -> "Sherlock Moriarty" at
  ch215; Gehrman/The Fool stay scene-tagged per DESIGN section 3).
- Images resolved from the portraits dir (_manifest.json + character_map.json overrides);
  non-portrait characters cross-referenced against the registry -> "get image" vs minor vs unnamed.
- Durations come from forced alignment (align/ch_<N>.json) when present, so scene boundaries sit on
  real audio timestamps; chapters with no alignment fall back to char-share estimates and say so.

Output: projects/<name>/timelines/block_NN_chAAA-BBB.md (chapter-by-chapter, reviewable) + .json
Usage: py -3.12 build_block.py [first last] [--project NAME]   (default 1 50, lotm_book1)
"""
from __future__ import annotations
import csv, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from align_chapter import load as align_load, scene_span  # noqa: E402
from charvid_project import pop_project_arg               # noqa: E402


def load_images(P):
    avail = {}
    manifest = P.portraits / "_manifest.json"
    persona_imgs = set(P.persona.get("image_names", []))
    if manifest.exists():
        for m in json.loads(manifest.read_text(encoding="utf-8")):
            if m["kind"] != "character" or m["name"] in persona_imgs or not m["row_viable"]:
                continue
            avail[m["name"]] = f"{m['name']}.{'png' if m['mime']=='image/png' else 'jpg'}"
    # character_map.json is the committed source of truth for manual portrait picks (characters
    # with no `<Name> Official.<ext>` file, so absent from the regenerable manifest). It overrides
    # the manifest. Skip entries explicitly flagged row_viable=false (e.g. landscape banners).
    char_map = P.portraits / "character_map.json"
    if char_map.exists():
        for name, entry in json.loads(char_map.read_text(encoding="utf-8")).get("characters", {}).items():
            if entry.get("image") and entry.get("row_viable", True):
                avail[name] = entry["image"]
    return avail


def load_durations(P):
    d = {}
    if P.durations_csv and P.durations_csv.exists():
        with open(P.durations_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                d[int(row["Ch"])] = float(row["Sec"])
    return d


# project-scoped state, set by init()
P = None
AVAIL = REGISTRY = ALIASES = EXCLUDE = CONT = DECISIONS = DUR = None
PERSONA = FLIPS = None
PROTAG_PREFIX = INDEX_LABEL = None
DEFAULT_IMG = None


def init(project):
    global P, AVAIL, REGISTRY, ALIASES, EXCLUDE, CONT, DECISIONS, DUR
    global PERSONA, FLIPS, PROTAG_PREFIX, INDEX_LABEL, DEFAULT_IMG
    P = project
    AVAIL = load_images(P)
    REGISTRY = set(json.loads(P.registry_file.read_text(encoding="utf-8"))["characters"])
    _al = json.loads(P.aliases_file.read_text(encoding="utf-8"))
    ALIASES = _al["aliases"]
    EXCLUDE = set(_al.get("exclude", []))
    CONT = json.loads(P.continuity_file.read_text(encoding="utf-8"))["boundaries"]
    DECISIONS = (json.loads(P.decisions_file.read_text(encoding="utf-8"))["decisions"]
                 if P.decisions_file.exists() else {})
    DUR = load_durations(P)
    PERSONA = {k: tuple(v) for k, v in P.persona.get("map", {}).items()}
    FLIPS = P.persona.get("base_flips", [])
    PROTAG_PREFIX = P.persona.get("protagonist_prefix") or "\x00no-protagonist"
    INDEX_LABEL = P.persona.get("index_label", "(protagonist)")
    DEFAULT_IMG = P.cfg.get("default_image")


def body_chars(n, ls, le):
    f = P.chapter_text(n)
    lines = f.read_text(encoding="utf-8").splitlines()
    return sum(len(lines[i-1].strip()) for i in range(ls, min(le, len(lines))+1) if 1 <= i <= len(lines))


def hms(sec):
    sec = int(round(sec))
    return f"{sec//3600:d}:{(sec%3600)//60:02d}:{sec%60:02d}"


def resolve(scene, chapter, carried=()):
    persona = scene.get("protagonist_persona")
    for f in FLIPS:                              # chapter-anchored base-persona progression
        if persona == f["from"] and chapter >= f["at_chapter"]:
            persona = f["to"]
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
        if name in EXCLUDE or name in seen:      # drop non-people / dedupe
            continue
        seen.add(name)
        cast.append(name)
        (images.append(AVAIL[name]) if name in AVAIL else missing.append(name))
    if not images:
        # USER DECISION 2026-08-27: when nobody on screen has a portrait, show the project's
        # default image (book cover) instead of holding the previous frame -- holding falsely
        # implied the previous scene's cast (e.g. Alger lingering over the Jack scene in ch53).
        if DEFAULT_IMG:
            return cast, [DEFAULT_IMG], missing, "default"
        return cast, ["(hold previous frame)"], missing, "hold-previous"
    n = len(images)
    return cast, images, missing, ("single" if n == 1 else (f"row({n})" if n <= 4 else f"grid({n})"))


def classify(label):
    if label.startswith(PROTAG_PREFIX) or label in AVAIL:
        return "have"
    if label.startswith("["):
        return "background"
    if label not in REGISTRY:
        return "minor"
    return "declined" if DECISIONS.get(label) == "no" else "need"


def seed_prev_images(first):
    """Last on-screen frame of the previous block, so a leading hold-previous scene in this
    block holds a real image instead of the literal placeholder (which the renderer drops)."""
    if first <= 1:
        return []
    for f in P.block_jsons():
        m = re.search(r"ch(\d+)-(\d+)\.json$", f.name)
        if m and int(m.group(2)) == first - 1:
            data = json.loads(f.read_text(encoding="utf-8"))
            for c in reversed(data["chapters_detail"]):
                for s in reversed(c["scenes"]):
                    imgs = [i for i in s["images"] if not i.startswith("(")]
                    if imgs:
                        return imgs
    return []


def main():
    project, rest = pop_project_arg(sys.argv[1:])
    init(project)
    first, last = (int(rest[0]), int(rest[1])) if len(rest) > 1 else (1, 50)
    block_no = P.block_no(first)
    offset, index, chapters_out = 0.0, {}, []
    prev_images = seed_prev_images(first)
    for ch in range(first, last + 1):
        sf = P.scenes_dir / f"ch_{ch}.json"
        if not sf.exists():
            continue
        specs = json.loads(sf.read_text(encoding="utf-8"))["scenes"]
        counts = [max(1, body_chars(ch, s["line_start"], s["line_end"])) for s in specs]
        tot = sum(counts)
        # real timings from forced alignment when we have them, else char-share estimates
        arec = align_load(ch, P)
        ch_dur = arec["duration"] if arec else DUR.get(ch)
        if ch_dur is None:
            print(f"ch{ch}: no alignment and no durations_csv entry -> skipped")
            continue
        starts = None
        if arec:
            spans = [scene_span(arec, s["line_start"], s["line_end"]) for s in specs]
            if all(spans):
                # tile the chapter: a scene runs until the next one starts, so the first scene
                # also covers the title read-in and no frame is ever undefined
                starts = [0.0] + [sp[0] for sp in spans[1:]]
                ends = starts[1:] + [ch_dur]
                if any(e <= s for s, e in zip(starts, ends)):
                    starts = None            # non-monotonic tags; fall back rather than emit junk
        timing = "aligned" if starts else "estimated"
        ch_offset = 0.0
        cont = CONT.get(str(ch - 1), {})
        continues = cont.get("continues", False)
        carried = cont.get("carried_others", []) if continues else []
        rows = []
        for idx, (s, cc) in enumerate(zip(specs, counts)):
            cast, images, missing, layout = resolve(s, ch, carried if idx == 0 else ())
            if layout == "hold-previous" and prev_images:   # carry the actual previous frame
                images = list(prev_images)
            cont_prev = idx == 0 and continues
            if starts:
                ch_start, ch_end = starts[idx], ends[idx]
            else:
                ch_start = ch_offset
                ch_end = ch_offset + ch_dur * cc / tot
            dur = ch_end - ch_start
            ch_offset = ch_end
            rows.append({"start": hms(offset), "end": hms(offset + dur), "duration": hms(dur),
                         "present_cast": cast, "images": images, "missing_images": missing,
                         "layout": layout, "continues_prev": cont_prev,
                         "line_start": s["line_start"], "line_end": s["line_end"],
                         "setting": s.get("setting", ""),
                         "text_anchor": s.get("text_anchor", ""),
                         "timing": timing,
                         "chapter_start": round(ch_start, 3), "chapter_end": round(ch_end, 3),
                         "batch_start": round(offset, 3), "batch_end": round(offset + dur, 3)})
            prev_images = images
            for label in cast:
                key = INDEX_LABEL if label.startswith(PROTAG_PREFIX) else label
                e = index.setdefault(key, {"status": classify(label), "scenes": 0})
                e["scenes"] += 1
            offset += dur
        chapters_out.append({"chapter": ch, "title": P.title_of(ch), "scenes": rows,
                             "timing": timing, "audio_duration": round(ch_dur, 3)})

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

    n_aligned = sum(1 for c in chapters_out if c["timing"] == "aligned")
    L = [f"# Scene Timeline — Block {block_no} (chapters {first}-{last})", "",
         f"**Total** {hms(offset)} · **{sum(len(c['scenes']) for c in chapters_out)} scenes** · "
         f"{len(chapters_out)} chapters &nbsp;|&nbsp; {n_aligned}/{len(chapters_out)} chapters timed by "
         f"forced alignment{'' if n_aligned == len(chapters_out) else ' (rest are char-share estimates)'}"
         f" &nbsp;|&nbsp; `↳` = scene continues from the previous chapter.", "",
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
    (P.timelines / f"block_{block_no:02d}_ch{first:03d}-{last:03d}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (P.timelines / f"block_{block_no:02d}_ch{first:03d}-{last:03d}.json").write_text(
        json.dumps({"batch": block_no, "chapters": f"{first}-{last}", "total": hms(offset),
                    "chapters_detail": chapters_out, "characters_index": index}, indent=2, ensure_ascii=False),
        encoding="utf-8")

    print(f"Block ch{first}-{last}: {len(chapters_out)} chapters, "
          f"{sum(len(c['scenes']) for c in chapters_out)} scenes, {hms(offset)}")
    print(f"  wiki chars needing images: {len(need)}")
    print(f"  -> {', '.join(need)}")


if __name__ == "__main__":
    main()
