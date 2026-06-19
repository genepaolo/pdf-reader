# Character-Scene Videos — Design Doc

**Branch:** `feature/book1-character-scene-videos`
**Project:** `lotm_book1` (Book 1 — *Lord of Mysteries*). Note this is a deliberate exception to the
default active project (`lom_book2_coi`); all paths/commands here are book1-specific.
**Status:** DESIGN — no production code yet. Assets scraped. Awaiting decisions on open questions (§9).

---

## 1. Goal

Replace the static Klein Arcana Card backgrounds with **official character art that changes over the
course of each chapter to match who is present in the current scene**. When multiple characters share a
scene (e.g. a Tarot Club gathering), show all of them together in a row/grid at good resolution.

Final output is the same "giant batch" format already agreed: **~50 chapters ≈ 10 hr per video, 29 videos
for all 1,432 chapters** (see chapter-block table from prior analysis; durations in
`D:/PDFReader/lotm_book1_output/_durations.csv`).

**Locked decisions (from kickoff):**
- **Timing = forced alignment** of existing audio against the known EPUB text (no TTS re-cost). Tool:
  `aeneas` or WhisperX. Claude never touches the audio — it reads text.
- **Display = scene-presence.** Show everyone present in the scene together; we do NOT try to track the
  literal current speaker word-by-word.

---

## 2. Asset rules (RESOLVED) — what we scrape and what we ignore

Source: <https://lordofthemysteries.fandom.com/wiki/Category:Official_Character_Images> (108 files total).

**Rule:** keep **only** `File:<Name> Official.jpg|png`. **Never** use the `Official Crop`,
`Official Cropped`, or `Official Full` variants, and never the bare/unofficial files (e.g.
`File:Dwayne Dantès.jpg`).

Applying that filter → **30 portraits**, downloaded to
[`tts_pipeline/assets/characters/lotm/`](../tts_pipeline/assets/characters/lotm/) (manifest in
`_manifest.json`). All are tall full-body art (~1:2.2 aspect, mostly 689–1080 px wide).

The 30 canonical files:

```
Amon, Bernadette Gustav, Cattleya, Colin Iliad, Cynthia, Danitz, Derrick Berg, Dunn Smith,
Dwayne Dantès, Edwina Edwards, Emlyn White, Evernight Goddess, Fors Wall, Frank Lee,
Gehrman Sparrow, Ince Zangwill, Klein Moretti, Klein Moretti (Beginning of the Series),
Leonard Mitchell, Merlin Hermes, Ouroboros, Reinette Tinekerr, Sharron Cropped, Sherlock Moriarty,
The Fool, Trissy, True Creator, Wil Auceptin, Xio Derecha, Zhou Mingrui
```

**Edge case flagged:** `Sharron Cropped Official.jpg` passed the filter because the *character name itself*
contains the word "Cropped" (it is the only official image for Sharron, not a cropped variant of another).
Confirm whether to keep as-is or rename the canonical key to just `Sharron`.

**Scope rule (RESOLVED):** we only care about characters that HAVE an official image. The 30 above are the
entire roster the videos can depict. Any character mentioned in text without an official portrait is simply
not shown (scene falls back to whoever else is present, or a default — see §6).

---

## 3. Klein persona depiction (RULES CONFIRMED — chapters to be pinned in the Scene Timeline)

The protagonist is depicted by **different portraits depending on story progression and scene context**.
Because this is intricate and event-driven, we build a **Scene Timeline first for manual verification**
(§10): these rules drive the timeline, and you review/correct it before any video is rendered.

**A. Base persona by story progression** (the "default Klein" when no special context applies):

| Order | Trigger event | Portrait | Anchor chapter |
|---|---|---|---|
| 0 | Very beginning, until the name "Klein" is first mentioned | `Zhou Mingrui` | ch 1 start |
| 1 | First mention of the name "Klein" | `Klein Moretti (Beginning of the Series)` | within ch 1 |
| 2 | Joins the Nighthawks | `Klein Moretti` | TO PIN |
| 3 | Moves city, becomes Sherlock Moriarty | `Sherlock Moriarty` (all default Klein portraits from here) | TO PIN |

**B. Context override:** any **Tarot Club** scene → `The Fool`, regardless of the base persona above.

**C. "The World"** — an alternate identity of Klein introduced **~middle of Volume 2**:
- Depicted with **`Sherlock Moriarty`** from introduction until Gehrman Sparrow is created.
- After **Gehrman Sparrow** is created → The World is depicted with **`Gehrman Sparrow`** until the end.

**D. Alias-driven disguises** — use that exact portrait whenever the text uses the name:
`Gehrman Sparrow`, `Sherlock Moriarty`, `Dwayne Dantès`, `Merlin Hermes` — **all are Klein.**

**E. Default-default fallback:** whatever persona Klein currently is per A–C; if genuinely ambiguous,
`Klein Moretti`.

**Separate characters (NOT Klein, CONFIRMED):** `Amon`, `True Creator` — standalone portraits, never folded
into the Klein cluster.

> Note: `Zhou Mingrui` is used at the very opening — from the first line until the name **"Klein"** is first
> mentioned in the text — then it switches to `Klein Moretti (Beginning of the Series)`. This is a
> within-chapter-1 switch, so the Scene Timeline must support a persona change mid-chapter (not just at
> chapter boundaries).

**Event anchors to pin during the Scene Timeline (M1):** join-Nighthawks chapter, move-to-Backlund /
become-Sherlock chapter, Tarot Club founding, The World introduction (mid-Vol 2), Gehrman Sparrow creation.
Claude proposes each with a chapter citation; **you verify.**

---

## 4. Character & alias map

We build one curated JSON: `tts_pipeline/assets/characters/lotm/character_map.json`.

```jsonc
{
  "characters": {
    "Audrey Hall": {                  // canonical key
      "image": "Audrey Hall.jpg",     // file in this folder, or null if no official image
      "aliases": ["Miss Hall", "Justice"]   // Tarot Club title etc.
    }
    // ... only the 30 with images need an image; aliases help Claude resolve mentions
  },
  "persona_clusters": {
    "Klein": {
      "alias_to_image": {
        "The Fool": "The Fool.jpg",
        "Gehrman Sparrow": "Gehrman Sparrow.jpg",
        "Sherlock Moriarty": "Sherlock Moriarty.jpg",
        "Dwayne Dantès": "Dwayne Dantès.jpg"
      },
      "timeline_fallback": [
        { "max_chapter": 0,    "image": "Zhou Mingrui.jpg" },
        { "max_chapter": 999,  "image": "Klein Moretti (Beginning of the Series).jpg" },
        { "max_chapter": 9999, "image": "Klein Moretti.jpg" }
      ]
    }
  }
}
```

Aliases for the non-protagonist Tarot Club members (Audrey=Justice, Alger=Hanged Man, etc.) only matter for
the few who **have** an official image (Audrey Hall, Fors Wall, Emlyn White, Cattleya, etc.). Claude can draft
this map from the wiki for review; **we do not ship it unverified.**

---

## 5. Pipeline (each stage independent, cacheable, resumable)

| Stage | What | Tool | Output |
|---|---|---|---|
| 0a | EPUB → formatted text for book1 | existing `epub_to_text/main.py` | `formatted_text/lotm_book1/...` |
| 0b | Scrape official portraits | MediaWiki API (DONE) | `assets/characters/lotm/*.jpg` |
| 0c | Curate character/alias/persona map | Claude draft + human verify | `character_map.json` |
| 1 | Forced-align each chapter text↔MP3 | aeneas/WhisperX | `align/Chapter_N.json` (paragraph timestamps) |
| 2 | Claude scene-tagging | Claude API | `scenes/Chapter_N.json` (`[{para_range, characters[]}]`) |
| 3 | Join 1+2 → timed timeline | Python | `timeline/Chapter_N.json` (`[{start,end,characters[]}]`) |
| 4 | Composite frames (row/grid of portraits), cached by character-set | Pillow | `frames/<set-hash>.png` |
| 5 | Per-chapter video: image track switches at timestamps + mux audio | ffmpeg + NVENC | `video/.../Chapter_N.mp4` |
| 6 | Concat 50 chapters → batch video + `0:00 Chapter N` description | ffmpeg concat | block `.mp4` + description |

Stages 1–5 are per-chapter and idempotent: re-running only reprocesses missing/changed chapters.

---

## 6. Frame composition rules (scene-presence)

- Portraits are tall (~1:2.2). Scale each to a common height (e.g. 980 px) on a 1920×1080 canvas.
- Layout by count: 1 → centered; 2–4 → single row; 5–8 → two rows; 9+ (rare, big Tarot gatherings) → grid,
  cap at a max (e.g. 9) and/or shrink. Optional name caption under each.
- **Cache key = sorted set of portrait filenames** → identical groups reuse one rendered PNG (huge speedup
  across 281 hrs).
- **No name captions** (confirmed) — portraits only.
- **Fallback (CONFIRMED):** scene with no portrait-bearing character / narration-only → show **Klein's
  current persona portrait** (per §3 A–C), i.e. the default-default is whatever guise Klein is in at that
  point in the story (`Klein Moretti` if ambiguous). We do NOT fall back to a neutral background.

---

## 7. Video assembly

Per chapter: build an ffmpeg `concat` demuxer list of composite PNGs each with its `duration` (from the
timeline), produce the silent visual track, then mux the chapter's MP3. Reuse existing NVENC settings from
[`video_processor.py`](../tts_pipeline/api/video_processor.py) (`h264_nvenc`, `-cq 18`, faststart). Then Stage
6 concatenates 50 finished chapter MP4s (stream copy, no re-encode) into the batch and emits the timestamped
description so YouTube auto-generates chapter markers.

---

## 8. Risks / honest unknowns

1. **Copyright.** Official art is IP-holder copyrighted; using it in public/monetized YouTube videos invites
   Content-ID / manual claims. Decide risk posture before publishing.
2. **Character-ID accuracy** is the quality ceiling — aliases, pronoun-only passages, the Klein cluster.
   Scene-presence (chosen) is the robust option; still needs spot-checking.
3. **Alignment drift** on long chapters — mitigated by chunking and aligning to *known* text.
4. **Compute** — aligning + rendering 281 hrs is heavy but local, GPU-accelerated, and incremental.
5. **Asset gaps** — only 30 characters have art; many minor characters will never appear. Confirm the default
   fallback visual.

---

## 9. Decisions — RESOLVED

- **Timing:** forced alignment (aeneas) on existing audio. ✔
- **Display:** scene-presence. ✔
- **Assets:** only `<Name> Official.jpg|png` (30 portraits); no Crop/Cropped/Full. ✔
- **Klein personas:** rules in §3 confirmed; Amon & True Creator are separate; Merlin Hermes = Klein. ✔
- **`Sharron Cropped`:** keep the key as-is (it is not actually cropped). ✔
- **Fallback frame:** Klein's current persona portrait (default `Klein Moretti`). ✔
- **Name captions:** none. ✔
- **EPUB integrity:** verified — 1,432 chapters (1–1432), no gaps/dupes/empties, clean prose. ✔

**Still to pin (during the Scene Timeline, M1):** the five event-anchor chapters from §3 (join Nighthawks,
become Sherlock, Tarot Club founding, The World intro, Gehrman Sparrow creation).

---

## 10. Milestones

**The Scene Timeline is built and human-verified BEFORE any video is rendered.**

1. **M0 (done):** scrape + filter assets (30 portraits), verify EPUB integrity, write this doc.
2. **M1 — Source + map:**
   - ✅ `formatted_text/lotm_book1` extracted — **1,432 chapters**, 9 volumes (Clown…Side Stories), global
     numbering, UTF-8. Required a `volume_map.json` (book1's TOC has "Book" in 3 chapter titles that the
     no-map path mis-ate as volume headers) and a converter fix: added `--series-title` so book1 files say
     "Lord of Mysteries" not the hardcoded book2 title.
   - ⬜ Curate `character_map.json` (aliases + Klein persona cluster).
   - ⬜ Verify the five event-anchor chapters (§3). **Keyword first-occurrences (candidates, need context
     read to pin the actual event):** `Tarot Club` ch 7 · `Nighthawk` ch 6 (org named; membership later) ·
     `Sherlock Moriarty` ch 215 (Vol 2 start / move to Backlund) · `Gehrman Sparrow` ch 483 (Vol 3 start) ·
     `Dwayne Dantès` ch 732 · `Merlin Hermes` ch 1290. "The World" identity is not keyword-findable (generic
     phrase) — needs a context read mid-Vol 2.
3. **M2 — Scene Timeline (REVIEW GATE):** generate the per-chapter Scene Timeline — for each scene, the
   characters present and Klein's resolved persona portrait — as a **human-readable artifact you manually
   verify/correct.** No audio/video work yet; this validates the character logic first. Start with a small
   sample (e.g. ch 1–5 + a Tarot Club chapter + a known Gehrman/Sherlock chapter) so you can sanity-check the
   persona rules before generating all 1,432.
4. **M3 — Timing:** forced-align the verified-timeline chapters → attach timestamps to each scene.
5. **M4 — PoC video:** render Chapter 1 end-to-end (composite → switching frames → mux audio); you review.
6. **M5 — Block #1:** scale to chapters 1–50 → one ~10.9 hr video + `0:00 Chapter N` description.
7. **M6 — Rollout:** remaining 28 blocks; integrate with existing upload pipeline (mind multi-GB files +
   the copyright posture from §8).
