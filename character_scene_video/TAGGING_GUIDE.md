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

**Three tiers, sharpened 2026-09-03 (user ruling, after the ch245 miss):**
1. **Characters in the scene** -> `other_characters`, plain portrait.
2. **Subjects of the conversation** -> `mentioned_characters`, gold rim. The talk is ABOUT them:
   who they are, what they did, what they look like, what to do about them.
3. **Passing notes about a subject** -> NO tag at all. The name appears while discussing something
   else -- pathway/organization lore, a comparison, an oath, background flavor. A simple mention of
   a character or deity does not warrant a portrait.
The failure mode tier 3 guards against: ch245 s2 profiles Mr. A, and the Aurora Order's pathway
"is the direct route to the True Creator" -- one minute of pathway lore, but a scene-level tag
would have kept the deity's portrait on screen for the whole 8-minute divination. When unsure,
ask: if a viewer glanced at the frame mid-scene, would the rimmed portrait explain what is being
talked about (tag) or make them wonder why that face is there (don't)?

Worked examples from Vol 2: ch264 s4 Klein lays a picture of **Lanevus** on the table and commissions
the investigation; ch358 s4 Derrick asks "have any of you heard of a person named **Amon**?" and
ch359 s1 Alger unpacks the family taboo; ch461 s1 Derrick projects the tomb mural and the table
identifies the **Evernight Goddess** and the **True Creator** among the six distorted gods; ch404 s2
Klein divines whether **Will Auceptin** is dead; ch463 s2 The Fool names **Edessak Augustus**.
Rejected: ch467 s1 Amon (comparison), ch440 s2 Amon (family list), ch351 s3 Tyre (a vision -- the
dream/vision rule still wins).

The applied set for Vol 2 is 34 scenes / 40 additions. These names always appear literally in the
scene's own lines, so `verify_tags.py` grounds them with no `verified_present` entry needed.

## Frame focus and delayed entrances (standing rules, 2026-09-01)

**`frame_focus: "mentioned"`** on a scene makes the frame show ONLY the mentioned_characters --
the room is dropped from the picture (everyone stays in the cast for verification and screen-time
accounting; no gold rims, since the whole frame is discussed-only). This is reserved for
**over-cap crowding**: use it only when the cast plus mentions cannot fit MAX_PER_FRAME and the
beat is everyone staring at one image. The only instance in Book 1 is **ch461 s2** (Klein + four
members + six gods of the mural = the room steps aside for the pantheon). Do NOT use it as a
cinematic device elsewhere -- the user's rule (2026-09-01) is that the room stays in the frame.

**Delayed entrances**: when a portrait would spoil or pre-empt a reveal, split the scene so the
character ARRIVES in the frame at the story beat instead of sitting in it from the top. Nobody is
dropped; an entrance is just delayed. Worked examples: **ch447** (Amon's portrait enters only when
Horamick turns the Specter Portrait Frame around -- for the preceding 11:44 of tomb exploration
the Amon FAMILY is discussed but his face is deliberately untagged); **ch264** (Lanevus enters
when Klein lays the painting on the table, not during Mr. World's introduction). When a sweep
flags a name as substantially-discussed-but-untagged, check whether the omission is one of these
deliberate spoiler holds before "fixing" it.

## Mr. World is a separate seat, not a persona (standing rule, 2026-09-03)

`The World` is Klein's FAKE second Tarot Club seat, introduced ch264. He is tagged in
`other_characters` like any other member -- NOT in `persona.map` -- so a gathering frame shows
Mr. Fool AND Mr. World side by side. That is correct: the club genuinely believes he is a
different person. The text backs it -- Audrey wonders "where he's from. Loen? Intis?", Derrick
thanks "Miss Justice, Miss Magician, and Mr. World" as three people, and Audrey rates "Mr. World's
sources" as trustworthy. He is seated in `portrait_priority.members` in joining order
(after Derrick, before Fors).

**Volume 2 art = the official Gehrman Sparrow card as a pure SILHOUETTE.** The members see "a
stranger wearing a hooded black robe... illusory and hazy", so no face may show. Gehrman Sparrow
is not created until **ch483** (Vol 3 ch1, via Sharron), so the silhouette spoils nothing and
foreshadows correctly.

**Volume 3 onward (user ruling 2026-09-03):** once Vol 3 starts, The World uses the FULL
`Gehrman Sparrow.jpg` portrait -- from mid-Vol-3 the club views Mr. World as Gehrman Sparrow.
He stays a separate row from The Fool, but ONLY inside Tarot Club gatherings; anywhere Klein is
walking around as Gehrman Sparrow in the real world, that is the protagonist persona
(`protagonist_persona: "Gehrman Sparrow"`), not a second seat. Never both in one scene.

## Code names vs. real names (standing rule, 2026-08-29)
When a character operates under a code name, tag **what the scene itself uses** — do NOT alias the
code name onto the real identity even when they are the same person:

- **`Eye of Wisdom`** is Isengard Stanton (wiki alias; revealed ch415). At a **Beyonder gathering**
  the text says "Mr. Eye of Wisdom", so tag `Eye of Wisdom`; anywhere he appears as the detective,
  tag `Isengard Stanton`. **He has his OWN portrait since 2026-09-03** (`Eye of Wisdom.png`,
  user-supplied: elderly, top hat, monocle, cane) -- before that he was tagged but had no art, so he
  was silently invisible at every gathering he hosts. Never point this name at
  `Isengard Stanton.png`; that would show his face 142 chapters early. The gathering name is the more explicit of the two in that context, and
  keeping them apart avoids showing his face 175 chapters before the reveal. Same reasoning as
  Klein's own personas being separate rows.
- Same treatment for other gathering code names (`Black Snake`, `Stray Dog`, `Mr. A`).

**`Apothecary` is Darkwill (Vol 2 rule, user 2026-09-03).** The name *Darkwill* appears NOWHERE in
Volume 2 -- its first use is Vol 3 ch585. Volume 2 tags him **`Apothecary`** (the text's own word
from ch240; ch239 calls him only "a fat-faced man" and carries a `verified_present` line). Same art
either way. Vol 3+ may switch to `Darkwill`. This is the same principle as Eye of Wisdom: tag the
name the STORY has revealed, never the wiki's.

**Unidentified is not the same as present.** At the Rice Circus (ch326 s2, ch327 s1) he is
physically in the row but Klein never places him -- "kind of familiar", then "Could it be that
Apothecary? That shouldn't be the case." Tagged `[chubby heckler]`, bracketed, no portrait. Giving
him his card there would assert an identification the text withholds. The ch327 gathering imagery
is a DREAM-recall and is not presence either.

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
