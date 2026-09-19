# Scene-reader brief — Lord of the Mysteries, Volume 3 "Traveler" (ch483–732)

> Used 2026-09-18 for block 11 (ch483–532): ten parallel readers, 5 chapters each, then one
> consolidation pass merged their notes sidecars into `continuity.json` / `name_aliases.json`.
> Reuse for blocks 12–15; adjust the chapter range and the notes folder path per reader.

You are tagging WHO IS PHYSICALLY PRESENT in every scene of a chapter range, for a video that shows
character portraits on screen as the audiobook plays. Repo root: `C:\Users\paolo\Work\Projects\LOTM\pdf-reader`.
Run any script with `py -3.12` (never `python`).

## Read these FIRST, in full
1. `character_scene_video/TAGGING_GUIDE.md` — every standing rule. Non-negotiable.
2. Worked examples of the output: `character_scene_video/projects/lotm_book1/timelines/scenes/ch_482.json`
   (ordinary chapter), `ch_264.json` (a Tarot gathering with `mentioned_characters`, a delayed entrance and a
   Roselle diary-reading break scene), `ch_483.json` (Vol 3 opener: mid-chapter identity change tagged BY SCENE).
3. `character_scene_video/projects/lotm_book1/name_aliases.json` — existing aliases / whitelist format.

## Input
Chapter text: `formatted_text/lotm_book1/Volume_3_Traveler/Chapter_<N>_*.txt` (glob it — titles contain
curly quotes). Line 1 = series, line 2 = "Chapter N: Title", story starts at line 3. Line numbers you cite are
1-based file lines; blank lines count. Read the WHOLE chapter before splitting it.

## Output — one file per chapter, strict JSON
`character_scene_video/projects/lotm_book1/timelines/scenes/ch_<N>.json`:
```
{"chapter": N, "scenes": [
  {"line_start": int, "line_end": int,            # inclusive, first/last line of the scene's text
   "protagonist_present": bool,                    # is Klein physically in this scene (any persona)?
   "protagonist_persona": "Gehrman Sparrow" | "The Fool" | "Klein Moretti" | null,
   "other_characters": ["literal names", "[unnamed figure]"],
   "setting": "one or two sentences: place, moment, what happens (this is what a human reviewer reads)",
   "text_anchor": "a SHORT verbatim quote from inside the scene's lines",
   "mentioned_characters": ["..."]                 # OPTIONAL, gatherings / above-the-fog scenes only
  }, ...]}
```
Scenes are contiguous, non-overlapping, in order; leave the blank separator line between scenes out of both
(e.g. 3–49, 51–105). Split on a change of place, time, or cast. Typical chapter = 2–5 scenes; a chapter that
is one continuous conversation is ONE scene. Never produce a duplicate/overlapping scene.

## Volume 3 specifics
- **Persona.** In the real world Klein now travels as the bounty hunter **`Gehrman Sparrow`** (identity bought
  ch483; from ch484 that is the default). Above the gray fog / at Tarot gatherings he is **`The Fool`**. Use
  `Klein Moretti` only if the text has him plainly as himself with no adopted identity (rare now). If he
  adopts some OTHER guise in a scene, tag the persona as the text names it and flag it in your notes.
- **`The World`** is Klein's fake SECOND seat at gatherings — a separate character in `other_characters`,
  never a persona. Members address him as "Mr. World"; he only exists inside gatherings. Never put The World
  in a real-world scene.
- Tarot Club members, tag with these names when the text names them by seat or name: `Audrey Hall`
  (Justice), `Alger Wilson` (Hanged Man), `Derrick Berg` (Sun), `Fors Wall` (Magician), `Emlyn White` (Moon),
  `The World`. A member seated for the whole gathering but not re-named inside a later sub-scene is still
  present — tag them and list a `verified_present` suggestion in your notes (see ch483 s3 precedent).
- **Sharron ≠ Sharon.** Sharron = the Beyonder who got Klein his identity (Vol 2 bodyguard); Sharon = a
  Backlund madam. Copy the spelling on the page.
- **Roselle's diary** pages are still read at gatherings — the diary-reading break-scene rule in the guide
  applies (cast = `Roselle Gustav` + people named in the pages; everyone else dropped for those lines).
- **Visions, dreams, divination images, memories = NOT present** (put them in `setting` as "(visions only: …)").
  A spirit/soul Klein talks WITH above the fog IS a conversation partner → bracketed tag like
  `[Faceless spirit]`.
- **Names are literal.** What the page says. "Danitz" not "Blazing Danitz" unless the page says so; a person
  the text only calls "the first mate" is `[first mate]`. No surnames, titles or pathway names from memory.
  Animals, ships, artifacts, gods that are only invoked → not characters (exclude list in name_aliases.json).
- **Mentions** (`mentioned_characters`): ONLY in gatherings / above-the-fog scenes, ONLY for a figure the
  table is substantially talking ABOUT (a report, a deduction, a divination, something shown). Passing
  references, comparisons, organization/pathway lore → nothing. When in doubt, leave it out. Never use
  `frame_focus`.

## Continuity + notes sidecar
For EVERY boundary N→N+1 inside your range AND the boundary from your last chapter to the next one (read the
first ~40 lines of that next chapter), decide `continues` (does N+1 open by directly continuing the scene that
ended N — same place, moment, cast?) and `carried_others` (non-protagonist characters present at the cut,
canonical names). Do NOT edit `continuity.json` or `name_aliases.json` yourself — write everything to
`<notes folder>/notes_<A>-<B>.json`:
```
{"boundaries": {"N": {"continues": bool, "carried_others": [...], "_note": "..."}, ...},
 "verified_present": [{"chapter": N, "scene": k, "name": "...", "why": "..."}],
 "alias_suggestions": {"short form seen on page": "full registry name (only if certain)"},
 "new_characters": [{"name": "...", "first_chapter": N, "who": "one line", "physical": "one line if the text describes them"}],
 "questions": ["anything you were unsure about, with chapter+line"]}
```

## Self-check before you finish
Run `py -3.12 character_scene_video/verify_tags.py <A> <B>` from the repo root. Fix any **INVENTED** name
(you used a name that is not on the page and not a known character) and any **WRONG SCENE** tag that is a real
mistake. A WRONG SCENE that is genuinely presence-by-description (named in an adjacent scene/chapter) is fine —
put it in `verified_present` in your notes instead. Do not touch any other project file. Report, in your
final message: chapters done, scene counts, the verify_tags tally, and your open questions.
