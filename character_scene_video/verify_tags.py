#!/usr/bin/env python3
"""
Source-grounding verifier for scene tags — an anti-hallucination guard.

For every tagged character in every scene, confirm the name actually appears in that scene's
source lines. Flags:
  EMBELLISHED — a token of the name appears but the full string does not (e.g. text says
                "Rozanne" but the tag says "Rozanne Bengun" -> invented surname).
  NOT FOUND   — no part of the name appears in the scene's lines (wrong scene / invented).
Bracketed descriptive tags like "[carriage driver]" are skipped (they are not literal names).

Run: python verify_tags.py [first last]   (default 1 50)
"""
from __future__ import annotations
import glob, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
FT = ROOT / "formatted_text" / "lotm_book1" / "Volume_1_Clown"
SCENES = HERE / "timelines" / "scenes"
REGISTRY = set(json.loads((HERE / "character_registry.json").read_text(encoding="utf-8"))["characters"])
_AL = json.loads((HERE / "name_aliases.json").read_text(encoding="utf-8"))
ALIASES = _AL["aliases"]
EXCLUDE = set(_AL.get("exclude", []))
VERIFIED = {(v["chapter"], v["scene"], v["name"]) for v in _AL.get("verified_present", [])}


def chapter_lines(n):
    hits = sorted(FT.glob(f"Chapter_{n}_*.txt"))
    return hits[0].read_text(encoding="utf-8").splitlines() if hits else []


def scene_text(lines, ls, le):
    return " ".join(lines[i-1] for i in range(ls, min(le, len(lines))+1) if 1 <= i <= len(lines)).lower()


def main():
    first, last = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, 50)
    grounded = canon = invented = notfound = skipped = verified = 0
    problems = []
    for n in range(first, last + 1):
        sf = SCENES / f"ch_{n}.json"
        if not sf.exists():
            continue
        lines = chapter_lines(n)
        for si, s in enumerate(json.loads(sf.read_text(encoding="utf-8"))["scenes"], 1):
            txt = scene_text(lines, s["line_start"], s["line_end"])
            for raw in s.get("other_characters", []):
                if raw.startswith("["):
                    skipped += 1
                    continue
                name = ALIASES.get(raw, raw)            # apply canonical alias map
                if name in EXCLUDE:                     # non-people (e.g. dog Susie)
                    skipped += 1
                    continue
                if name.lower() in txt:
                    grounded += 1
                    continue
                toks = [t for t in re.findall(r"[A-Za-z']+", name) if len(t) > 2]
                hit = [t for t in toks if t.lower() in txt]
                if not hit:
                    if (n, si, raw) in VERIFIED:
                        verified += 1            # human-confirmed present (named adjacently)
                        continue
                    notfound += 1
                    problems.append((n, si, raw, "WRONG SCENE", "name absent from these lines"))
                elif name in REGISTRY:
                    canon += 1                          # short form in text, expanded to a REAL char -> OK
                else:
                    invented += 1
                    problems.append((n, si, raw, "INVENTED NAME", f"only {hit} in text; '{name}' not a known character"))
    total = grounded + canon + verified + invented + notfound
    print(f"Named tags checked: {total}  (+{skipped} bracketed skipped)")
    print(f"  [OK] grounded (full name in source):              {grounded}")
    print(f"  [OK] canonicalized (short form -> registry char): {canon}")
    print(f"  [OK] verified-present (human-confirmed, named adjacent): {verified}")
    print(f"  [BAD] INVENTED name (not a known character):      {invented}")
    print(f"  [BAD] WRONG SCENE (name not in those lines):      {notfound}")
    print(f"  => {grounded + canon + verified}/{total} grounded/canonical/verified; {invented + notfound} to fix")
    if problems:
        print("\nPROBLEMS TO FIX:")
        for n, si, name, kind, why in problems:
            print(f"  ch{n} s{si}: {name!r} - {kind} ({why})")


if __name__ == "__main__":
    main()
