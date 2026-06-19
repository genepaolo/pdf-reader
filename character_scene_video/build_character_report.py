#!/usr/bin/env python3
"""
Character participation report for a block — the "who's important, do they need a portrait?" view.

For every character across the block it lists: portrait status, how many scenes, which chapters, and
grounded CONTEXT (the scene settings they appear in) so you can judge importance and decide whether to
source a portrait — WITHOUT re-reading the chapters. Uses the same canonicalization as build_block
(aliases, exclude, continuity carry).

Output: timelines/character_report_block01.md
Usage: python build_character_report.py [first last]   (default 1 50)
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
SCENES = HERE / "timelines" / "scenes"
MAN = json.loads((ROOT / "tts_pipeline" / "assets" / "characters" / "lotm" / "_manifest.json").read_text(encoding="utf-8"))
REGISTRY = set(json.loads((HERE / "character_registry.json").read_text(encoding="utf-8"))["characters"])
_AL = json.loads((HERE / "name_aliases.json").read_text(encoding="utf-8"))
ALIASES, EXCLUDE = _AL["aliases"], set(_AL.get("exclude", []))
CONT = json.loads((HERE / "continuity.json").read_text(encoding="utf-8"))["boundaries"]

PERSONA_IMG = {"Zhou Mingrui", "Klein Moretti", "Klein Moretti (Beginning of the Series)", "The Fool",
               "Sherlock Moriarty", "Gehrman Sparrow", "Dwayne Dantès", "Merlin Hermes"}
AVAIL = {m["name"] for m in MAN if m["kind"] == "character" and m["name"] not in PERSONA_IMG and m["row_viable"]}


def status(name):
    if name == "Klein (protagonist)":
        return "have"
    if name in AVAIL:
        return "have"
    if name.startswith("["):
        return "unnamed"
    return "need" if name in REGISTRY else "minor"


def main():
    first, last = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, 50)
    chars = {}  # name -> {chapters:set, settings:list, scenes:int}

    def add(name, ch, setting):
        e = chars.setdefault(name, {"chapters": set(), "settings": [], "scenes": 0})
        e["chapters"].add(ch); e["scenes"] += 1
        if setting and setting not in e["settings"]:
            e["settings"].append(setting)

    for ch in range(first, last + 1):
        sf = SCENES / f"ch_{ch}.json"
        if not sf.exists():
            continue
        specs = json.loads(sf.read_text(encoding="utf-8"))["scenes"]
        cont = CONT.get(str(ch - 1), {})
        carried = cont.get("carried_others", []) if cont.get("continues") else []
        for idx, s in enumerate(specs):
            setting = s.get("setting", "")
            if s.get("protagonist_present"):
                add("Klein (protagonist)", ch, setting)
            others = list(s.get("other_characters", [])) + (carried if idx == 0 else [])
            seen = set()
            for raw in others:
                nm = ALIASES.get(raw, raw)
                if nm in EXCLUDE or nm in seen:
                    continue
                seen.add(nm)
                add(nm, ch, setting)

    # group by status
    order = {"have": 0, "need": 1, "minor": 2, "unnamed": 3}
    rows = sorted(chars.items(), key=lambda kv: (order[status(kv[0])], -kv[1]["scenes"], kv[0]))
    MARK = {"have": "✅ portrait", "need": "❌ NEEDS decision (wiki char)",
            "minor": "➖ minor (no wiki page)", "unnamed": "· unnamed extra"}

    def ctx(settings):
        out = " / ".join(s[:55] for s in settings[:2])
        return (out[:110] + "…") if len(out) > 110 else (out or "—")

    L = [f"# Character Participation — Block 1 (chapters {first}-{last})", "",
         "_Every character that appears, with portrait status + grounded context (the scene settings they're "
         "in) so you can decide who needs art. ✅ = has a portrait now · ❌ = wiki character, no portrait "
         "(your call) · ➖ = minor, no wiki page · · = unnamed extra. Counts include cross-chapter carry._", ""]
    for st in ("have", "need", "minor", "unnamed"):
        group = [(n, d) for n, d in rows if status(n) == st]
        if not group:
            continue
        L += [f"## {MARK[st]} ({len(group)})", "",
              "| Character | Scenes | Chapters | Context (where they appear) |", "|---|---|---|---|"]
        for n, d in group:
            chs = sorted(d["chapters"])
            chs_str = (f"{chs[0]}–{chs[-1]} ({len(chs)})" if len(chs) > 4 else ",".join(map(str, chs)))
            L.append(f"| {n} | {d['scenes']} | {chs_str} | {ctx(d['settings'])} |")
        L.append("")

    need = [n for n, d in rows if status(n) == "need"]
    (HERE / "timelines" / "character_report_block01.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Characters: {len(chars)}  |  have:{sum(1 for n in chars if status(n)=='have')} "
          f"need:{len(need)} minor:{sum(1 for n in chars if status(n)=='minor')} "
          f"unnamed:{sum(1 for n in chars if status(n)=='unnamed')}")
    print("NEEDS a portrait decision:", ", ".join(need))


if __name__ == "__main__":
    main()
