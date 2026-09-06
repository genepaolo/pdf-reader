#!/usr/bin/env python3
"""
Source-grounding verifier for scene tags — an anti-hallucination guard.

For every tagged character in every scene, confirm the name actually appears in that scene's
source lines. Flags:
  EMBELLISHED — a token of the name appears but the full string does not (e.g. text says
                "Rozanne" but the tag says "Rozanne Bengun" -> invented surname).
  NOT FOUND   — no part of the name appears in the scene's lines (wrong scene / invented).
Bracketed descriptive tags like "[carriage driver]" are skipped (they are not literal names).

This gate proves PRECISION (every tag is real). It cannot prove RECALL (someone present but
never tagged passes silently) — `--recall` adds a triage sweep for that: portrait-bearing
characters whose name appears in a scene's text but was not tagged. Mentions land on that list
too (by design — "presence vs mention" needs a human), so recall hits are candidates to review,
never auto-failures, and they do not affect the exit code.

Run: py -3.12 verify_tags.py [first last] [--project NAME] [--recall]
Exit code: 0 when nothing to fix, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from charvid_project import pop_project_arg  # noqa: E402


def scene_text(lines, ls, le):
    return " ".join(lines[i-1] for i in range(ls, min(le, len(lines))+1) if 1 <= i <= len(lines)).lower()


def portrait_names(P):
    """Characters that have art (manifest + manual map picks), minus the protagonist cluster."""
    persona_imgs = set(P.persona.get("image_names", []))
    names = set()
    man = P.portraits / "_manifest.json"
    if man.exists():
        for m in json.loads(man.read_text(encoding="utf-8")):
            if m.get("kind") == "character" and m.get("row_viable"):
                names.add(m["name"])
    cm = P.portraits / "character_map.json"
    if cm.exists():
        for n, e in json.loads(cm.read_text(encoding="utf-8")).get("characters", {}).items():
            if e.get("image"):
                names.add(n)
    return names - persona_imgs


def main():
    P, rest = pop_project_arg(sys.argv[1:])
    recall = "--recall" in rest
    nums = [a for a in rest if not a.startswith("-")]
    first, last = (int(nums[0]), int(nums[1])) if len(nums) > 1 else (1, 50)

    REGISTRY = set(json.loads(P.registry_file.read_text(encoding="utf-8"))["characters"])
    _AL = json.loads(P.aliases_file.read_text(encoding="utf-8"))
    ALIASES = _AL["aliases"]
    EXCLUDE = set(_AL.get("exclude", []))
    VERIFIED = {(v["chapter"], v["scene"], v["name"]) for v in _AL.get("verified_present", [])}
    SWEEP = portrait_names(P) if recall else set()

    grounded = canon = invented = notfound = skipped = verified = 0
    problems, recall_hits = [], []
    for n in range(first, last + 1):
        sf = P.scenes_dir / f"ch_{n}.json"
        if not sf.exists():
            continue
        cf = P.chapter_text(n)
        lines = cf.read_text(encoding="utf-8").splitlines() if cf else []
        for si, s in enumerate(json.loads(sf.read_text(encoding="utf-8"))["scenes"], 1):
            txt = scene_text(lines, s["line_start"], s["line_end"])
            tagged = set()
            for raw in list(s.get("other_characters", [])) + list(s.get("mentioned_characters", [])):
                if raw.startswith("["):
                    skipped += 1
                    continue
                name = ALIASES.get(raw, raw)            # apply canonical alias map
                tagged.add(name)
                if name in EXCLUDE:                     # non-people by decision
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
            if recall:
                for nm in SWEEP:
                    if nm in tagged or nm in EXCLUDE:
                        continue
                    if re.search(rf"\b{re.escape(nm.lower())}\b", txt):
                        recall_hits.append((n, si, nm))
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
    if recall:
        print(f"\nRECALL SWEEP (portrait characters named in scene text but NOT tagged): {len(recall_hits)}")
        print("  These are triage candidates — each is either an untagged PRESENCE (fix the scene"
              " tags) or a mere MENTION (correct to leave untagged). Human call per line.")
        for n, si, nm in recall_hits:
            print(f"  ch{n} s{si}: {nm}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
