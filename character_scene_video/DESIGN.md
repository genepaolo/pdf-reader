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

- **Open roster.** 35 characters currently have portraits (wiki-wide scrape). The roster is *open* — drop in
  a portrait for any character/name and add one `character_map.json` entry (see `_adding_images` there). The
  per-batch character index (§10) lists who still lacks an image so you know what to find.
- **Row viability.** Portraits vary in aspect/resolution. The compositor normalizes each to a common height
  (e.g. 980 px) and even horizontal spacing on the 1920×1080 canvas, so mixed sources sit together cleanly.
  Images flagged `row_viable=false` in `_manifest.json` (landscape banners / very low-res, e.g. the
  670×360 `Klein` banner) are **excluded from group scenes**; ideally portraits are tall, full-body/bust, on a
  clean or transparent background.
- **Layout by count:** 1 → centered; 2–4 → single row; 5–8 → two rows; 9+ (big Tarot gatherings) → grid,
  cap at a max (e.g. 9) and/or shrink.
- **No name captions** (confirmed) — portraits only.
- **Cache key = sorted set of portrait filenames** → identical groups reuse one rendered PNG (huge speedup
  across 281 hrs).
- **Fallback = HOLD PREVIOUS FRAME (CONFIRMED).** When a scene has no portrait-bearing character present
  (e.g. a POV cutaway to a character who has no portrait, or pure narration), **keep the previous frame on
  screen** rather than forcing Klein in. Only if there is no previous frame (very start) default to Klein's
  current persona. This prevents falsely implying Klein is in a scene he's absent from. (Note: with Audrey
  Hall and Alger Wilson now in the roster, several former "cutaway → Klein" cases resolve to the actual
  character instead.)

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
5. **Asset gaps** — 35 characters have art; many minor characters have none. Mitigated by the open roster
   (add images anytime) + full-cast tracking (§10 lists who's missing) + hold-previous-frame fallback.

---

## 9. Decisions — RESOLVED

- **Timing:** forced alignment (aeneas) on existing audio. ✔
- **Display:** scene-presence. ✔
- **Assets:** `<Name> Official.jpg|png` only (no Crop/Cropped/Full), discovered **wiki-wide** (the category
  was incomplete) → **35 character portraits**. Roster is open; user supplies more over time. ✔
- **Klein personas:** rules in §3 confirmed; Amon & True Creator are separate; Merlin Hermes = Klein. ✔
- **`Sharron Cropped`:** keep the key as-is (it is not actually cropped). ✔
- **Fallback frame:** **hold previous frame** when no portrait-bearing character is present (not Klein). ✔
- **Multi-character rows:** normalize to common height; exclude `row_viable=false` images (e.g. Klein banner). ✔
- **Full-cast tracking:** every scene logs all present characters + a per-batch "needs image" list. ✔
- **Name captions:** none. ✔
- **EPUB integrity:** verified — 1,432 chapters (1–1432), no gaps/dupes/empties, clean prose. ✔

**Still to pin (during the Scene Timeline, M1):** the five event-anchor chapters from §3 (join Nighthawks,
become Sherlock, Tarot Club founding, The World intro, Gehrman Sparrow creation).

---

## 10. Scene Timeline artifact (per batch) — the review deliverable

**Requirement:** for each batch of chapters we produce one timeline that lists, scene by scene, **how long
each scene runs** and **which characters/images are shown**. This is the artifact you verify before any
video is rendered.

**Granularity.** One timeline per **video batch** (50 chapters ≈ 10 hr; book1 = 29 batches). A **scene** is a
contiguous span over which the on-screen cast is stable — a new scene begins when the present character set
changes (someone enters/leaves) or at a clear location/POV shift. Scene *boundaries* come from Claude's text
tagging; each scene's *length* comes from forced-aligning that span's text against the audio.

**Two paired files per batch:**
- `character_scene_video/timelines/block_NN_chAAA-BBB.json` — machine format that drives rendering.
- `character_scene_video/timelines/block_NN_chAAA-BBB.md` — human-readable table for your review.

**Track the FULL cast, not just who has a portrait.** Every scene records *all* named characters/titles
physically present — including ones with no image yet — so each batch yields a complete character inventory
and a "needs an image" list. You can then supply missing images over time (per `character_map.json
_adding_images`), and re-rendering picks them up.

**JSON schema (per scene):**
```jsonc
{
  "batch": 1,
  "chapters": "1-50",
  "video_duration": "10:52:18",          // sum of all scene durations in the batch
  "scenes": [
    {
      "id": "ch1.s1",
      "chapter": 1,
      "start": "00:00:00.0",             // batch-relative (maps onto the concatenated video)
      "end":   "00:01:48.3",
      "duration": "00:01:48.3",          // <-- the scene length
      "present_cast": ["Klein (as Zhou Mingrui)"],  // EVERY named character present this scene
      "images": ["Zhou Mingrui.jpg"],    // resolved portraits (subset of present_cast that has art)
      "missing_images": [],              // present_cast members with NO portrait yet (you can supply later)
      "layout": "single",                // single | row(N) | grid(N) | hold-previous
      "text_anchor": "Painful! How painful! My head hurts so badly!"  // first words, so you can locate it
    }
  ],
  "characters_index": {                  // batch rollup, auto-generated from present_cast
    "Klein": { "has_image": true,  "scenes": 14 },
    "Melissa": { "has_image": false, "scenes": 1 }   // <-- shows up on the "needs an image" list
  }
}
```

**Human-readable `.md` row per scene:** `start | duration | ch | present cast | images | missing`. Plus a
**character index** table at the bottom: every name seen in the batch, scene count, and ✅/❌ for portrait
availability — that ❌ list is your shopping list of images to find. A reviewer reads top to bottom,
spot-checks image choices against the text_anchor, and edits any wrong cast/persona. Corrections feed back
into `character_map.json` (add image / aliases / anchors) or a per-scene override before rendering.

> Until forced alignment is wired up (M3), scene *durations* are placeholders; scene *content* (cast + images)
> can be reviewed first from the text alone.

## 11. Milestones

**The per-batch Scene Timeline (§10) is built and human-verified BEFORE any video is rendered.**

1. **M0 (done):** scrape + filter assets (30 portraits), verify EPUB integrity, write this doc.
2. **M1 — Source + map:**
   - ✅ `formatted_text/lotm_book1` extracted — **1,432 chapters**, 9 volumes (Clown…Side Stories), global
     numbering, UTF-8. Required a `volume_map.json` (book1's TOC has "Book" in 3 chapter titles that the
     no-map path mis-ate as volume headers) and a converter fix: added `--series-title` so book1 files say
     "Lord of Mysteries" not the hardcoded book2 title.
   - ✅ Drafted `character_map.json` (30 chars + images; Klein persona cluster; conservative empty aliases).
   - 🔶 Event anchors — **3 of 5 pinned with citations:** Zhou→Klein(Beginning) ch 1 line 93 · Sherlock
     ch 215 line 79 · Gehrman created ch 483 line 47. **Still open:** Nighthawks induction (ch 16 is only
     *contemplation*; real join ~ch 13–20) and The World introduction (mid-Vol 2, context read). Tarot Club
     first gathering ~ch 7 (Fool override) to confirm.
3. **M2 — Scene Timeline per batch (REVIEW GATE):** produce the §10 artifact for a batch — every scene with
   its **duration** and **character images**, as a human-readable table you verify/correct. Validate the
   character/persona logic first on a small sample (ch 1–5 + a Tarot Club chapter + a Gehrman/Sherlock
   chapter) before generating all 29 batches.
4. **M3 — Timing:** forced-align the verified-timeline chapters → attach timestamps to each scene.
5. **M4 — PoC video:** render Chapter 1 end-to-end (composite → switching frames → mux audio); you review.
6. **M5 — Block #1:** scale to chapters 1–50 → one ~10.9 hr video + `0:00 Chapter N` description.
7. **M6 — Rollout:** remaining 28 blocks; integrate with existing upload pipeline (mind multi-GB files +
   the copyright posture from §8).
