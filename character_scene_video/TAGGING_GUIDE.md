# Scene-Tagging Guide (anti-hallucination)

Rules for the per-chapter scene readers. The goal: tags that are **provable against the source**.
After every batch, run `python verify_tags.py <first> <last>` — it must report **0 INVENTED, 0 WRONG SCENE**
(beyond the human-reviewed `verified_present` whitelist) before the timeline is trusted.

## The one rule that prevents invented names
**Use names exactly as they appear in the text. Never add a surname, title, or pathway prefix from outside
knowledge.** If the page says "Rozanne," tag `Rozanne` — not "Rozanne Bengun." If it says "the butler,"
tag `[butler]` until the text names him.

Canonicalization to full/registry names is a **separate, deterministic step** (the alias map + registry),
never the model's memory. Extraction stays literal; the build step canonicalizes.

## Presence, not mention
Tag a character only if they are **physically in the scene** (acting/speaking/clearly there). Do **not** tag
someone who is only **mentioned, remembered, or named in narration** (e.g. ch8: "Susie was a gift to her
father, Count Hall" — both are *mentioned*, neither is present).

A character can be present while named only in an adjacent scene (ch17: "the brown-haired girl" is Rozanne,
named a few paragraphs later). That's fine — tag them; the verifier flags it and a human confirms via
`verified_present` in `name_aliases.json`.

## Not people
Don't tag animals/objects as characters (ch41: "Susie" is Audrey's dog). Add such names to `exclude` in
`name_aliases.json`.

## Output per scene (strict JSON)
`{line_start, line_end, protagonist_present, protagonist_persona|null, other_characters[], setting, text_anchor}`
- `protagonist_persona`: text-driven — `Zhou Mingrui` (ch1 pre-name), `The Fool` (Tarot/gray-fog), else the
  base persona; the build flips `Klein (Beginning)`→`Klein Moretti` at the Nighthawks anchor (ch17).
- `other_characters`: literal names from the page; `[bracketed]` for unnamed figures.

## The two-layer guard
1. **verify_tags.py** — every named tag must appear in its scene's lines, OR be a short form of a real
   registry character, OR be on the `verified_present` whitelist. INVENTED names (not any known character)
   and un-whitelisted WRONG-SCENE tags are hard failures.
2. **name_aliases.json** — `aliases` (canonical merges), `exclude` (non-people), `verified_present`
   (human-cleared presence-by-description).
