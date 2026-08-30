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

## Visions and dreams are NOT presence (user ruling 2026-08-27)
Characters seen in **dream divinations, visions, memories, or remote viewings** are NOT physically
in the scene — never put them in `other_characters`, even when named. Record them in the `setting`
text as "(visions only: …)" so reviewers still see what the dream shows. Precedent: ch100 s1 put
Hanass Vincent's portrait next to The Fool above the fog (wrong — he was a dream image); ch90 s3
had the lead-poisoned girls (also visions). Both corrected. Live conversation partners (e.g. the
Tarot Gathering members) ARE present; a one-way vision of someone is not.

## Roselle diary-reading interludes (user ruling 2026-08-27 — deliberate EXCEPTION to presence)
Whenever the protagonist **reads pages of Roselle's diary** — at a Tarot Gathering OR in person
(ch20-21 first reading at Old Neil's archive) — split out a separate "break scene" spanning
exactly the reading: cast = `Roselle Gustav` + anyone **named in the diary pages** (ch21:
Florena, Ithaca; ch144: Matilda, Florais, Fan Estin), persona unchanged (The Fool at gatherings,
Klein otherwise), and everyone else physically present is **dropped** for those lines. Resume the
normal scene (original cast, no Roselle) when the reading ends. If the reading spans a chapter
break (ch20→21, ch113→114, ch144→145), carry `Roselle Gustav` in `continuity.json`. If "Roselle"
isn't literally inside the reading's line span, whitelist via `verified_present` citing where the
pages were introduced — and remember a split renumbers later scenes (update existing
verified_present indexes). Applies ONLY to actual readings — commissioning/discussion (ch34-35),
the Antigonus diary (ch61, ch95), recollections (ch94, ch100), and casual quotes stay untouched.

## Visualized-in-the-fog exception (standing rule, 2026-08-29)
The "presence, not mention" rule has ONE exception: **in Tarot Club gatherings and Klein's solo
above-the-fog scenes, a figure who is SUBSTANTIALLY DISCUSSED gets tagged**, even though nobody in
the room has met them. The portraits are there to let the audience see who is being talked about
while the table talks about them (user decision 2026-08-29).

Substantially discussed = the figure is the SUBJECT of a report, an explanation, a deduction, a
divination, or something shown to the table (a projected memory, a portrait laid on the bronze
table, a mural). NOT: a possessive or organizational reference ("the Evernight Goddess's Sleepless",
"the Church of the Evernight Goddess"), a name in a list of families or admirals, or a passing
comparison ("scary like Blasphemer Amon").

Worked examples from Vol 2: ch264 s4 Klein lays a picture of **Lanevus** on the table and commissions
the investigation; ch358 s4 Derrick asks "have any of you heard of a person named **Amon**?" and
ch359 s1 Alger unpacks the family taboo; ch461 s1 Derrick projects the tomb mural and the table
identifies the **Evernight Goddess** and the **True Creator** among the six distorted gods; ch404 s2
Klein divines whether **Will Auceptin** is dead; ch463 s2 The Fool names **Edessak Augustus**.
Rejected: ch467 s1 Amon (comparison), ch440 s2 Amon (family list), ch351 s3 Tyre (a vision -- the
dream/vision rule still wins).

The applied set for Vol 2 is 34 scenes / 40 additions. These names always appear literally in the
scene's own lines, so `verify_tags.py` grounds them with no `verified_present` entry needed.

## Code names vs. real names (standing rule, 2026-08-29)
When a character operates under a code name, tag **what the scene itself uses** — do NOT alias the
code name onto the real identity even when they are the same person:

- **`Eye of Wisdom`** is Isengard Stanton (wiki alias; revealed ch415). At a **Beyonder gathering**
  the text says "Mr. Eye of Wisdom", so tag `Eye of Wisdom`; anywhere he appears as the detective,
  tag `Isengard Stanton`. The gathering name is the more explicit of the two in that context, and
  keeping them apart avoids showing his face 175 chapters before the reveal. Same reasoning as
  Klein's own personas being separate rows.
- Same treatment for other gathering code names (`Black Snake`, `Stray Dog`, `Mr. A`).

The opposite case is a **spelling/prefix mismatch**, which must ALWAYS be aliased, because the
report silently drops the character into the ➖ minor bucket and nobody is ever asked about a
portrait: `Kohler` -> `Old Kohler` (20 scenes, found 2026-08-29), `Wil`/`Will Auceptin` (fixed in
`character_map.json`). When a recurring character never shows up in a ❌ NEEDS-decision list, check
for this first.

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
