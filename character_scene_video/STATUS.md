# Character-Scene Videos — STATUS / Session Handoff

**Read this first to resume.** Last updated end of the session that built Block 1.

## Where the work lives (IMPORTANT)
- **All of this is on `master` in the main repo** (`C:\Users\paolo\Work\Projects\LOTM\pdf-reader`).
  Work directly there. The `feature/book1-character-scene-videos` branch and the
  `pdf-reader-charvid` worktree were merged and deleted 2026-06-23 — ignore any older instruction
  to "stay in the worktree".
- Gitignored (not committed, regenerable): `formatted_text/`, the EPUB, the character image
  binaries under `tts_pipeline/assets/characters/lotm/`, and the composited frame cache
  `character_scene_video/frames/`.
- **Run scripts with `py -3.12`, not `python`** — `python` on this machine is 3.11 and lacks deps.

## What's done (Block 1 = chapters 1–50)
- **Audited clean:** 50/50 chapters tagged, 156 scenes, total ≈ **10:52:09**, verifier **168/168, 0 to fix**.
- Pipeline proven end to end: scrape → registry → scene-tag → image-resolve → **align → timeline →
  composite → render** → verify → reports. **A real chapter video has been produced and checked.**

### Timing is REAL now (M3 done, 2026-08-01)
Durations are no longer char-share estimates. `align_chapter.py` forced-aligns each chapter's text
against its own MP3 and writes `align/ch_<N>.json` (start/end seconds for every spoken line).
- **Not aeneas/WhisperX.** The audio is Azure TTS of text we already have, so no acoustic model is
  needed — and aeneas needs espeak + a C build that is painful on Windows. Instead we detect
  silences with ffmpeg and monotonically match the text's sentence sequence to the audio's pause
  sequence with a DP. Zero new dependencies; a chapter aligns in a couple of seconds.
- **Result over ch1–50:** 100% of sentence boundaries matched to real pauses, **0 structural
  errors**, 31/3560 lines (0.87%) with an odd implied speaking rate, median **14.07 chars/sec**
  (per-chapter 13.20–14.79). `verify_alignment.py` is the gate and currently reports **PASS**.
- Versus the old estimates, scene starts moved a median of **1.1s** (p90 6.8s, max 13.8s) — so the
  estimates were decent, but alignment removes the tail.
- **Gotcha it uncovered:** book-1's MP3s were synthesised *before* `epub_to_text` learned to drop the
  leading body echo of the chapter title, so **47 of 50** chapters read the title twice while the
  current text has it once. `has_title_echo()` detects this per chapter; without it the first body
  line of those chapters was mistimed.

### Compositor + renderer (M4 done)
- `compose_frames.py` — row/grid frames on a 1920×1080 dark backdrop, portraits normalised to a
  common height, no captions, cached by the *set* of portrait filenames. Block 1's 156 scenes need
  only **37 distinct frames** (cast sizes: 8×1, 15×2, 13×3, 1×5).
- `render_chapter.py` — cuts the frames on the aligned timestamps and muxes the existing MP3
  (stream copy). Matches the existing book-1 format: 1920×1080, **1 fps** (the picture only changes
  at scene boundaries), h264. Auto-detects NVENC and **falls back to libx264** — NVENC is listed by
  ffmpeg on this machine but `nvcuda.dll` fails to load, so it currently encodes on CPU.
- **Rendered and visually verified:** `Chapter_1.mp4` (621.0s, 12.8 MB, 2 cuts) and `Chapter_5.mp4`
  (890.2s, 19.2 MB, 5 cuts) in `D:/PDFReader/lotm_book1_output/character_video/`. Ch5 is the
  gray-fog test and steps correctly Klein → The Fool → Audrey → Alger → all three together.
  Encoding runs ~200× realtime, so the full 10.9-hour block is only a few minutes of CPU.

## The 4 things to review (your ask)
| What | File | Notes |
|---|---|---|
| **Character mapping** | `tts_pipeline/assets/characters/lotm/character_map.json` | 26 characters + Klein persona cluster (Zhou Mingrui → Klein (Beginning) → Klein Moretti → The Fool / Sherlock / Gehrman …). Open roster — add images anytime (`_adding_images`). |
| **Continuity** | `continuity.json` | All 49 ch1–50 boundaries: **42 continue, 7 hard breaks** (7,8,29,33,36,47,49). Carries cast across cuts. |
| **Scene timeline** | `timelines/block_01_ch001-050.md` | Chapter-by-chapter, scene-by-scene: start · duration · present cast · images · missing. `↳` marks continuations. |
| **Scene character participation** | `timelines/character_report_block01.md` | **The "who needs a portrait" view** — every character, portrait status, scene count, chapters, and grounded context. |

**Portrait decisions for Block 1 are DONE** (recorded in `portrait_decisions.json`). Current report:
`have:23  need:0  declined:2  minor:9  unnamed:34`.
- **23 have portraits** — the original 6 (Klein, Dunn Smith, Leonard Mitchell, Audrey Hall, Alger Wilson, Daly Simone),
  the 4 added earlier (Old Neil, Melissa, Rozanne, Benson), plus the **13 just decided yes**: Angelica Barrehart,
  Frye, Glacis, Annie, Earl Hall, Azik Eggers, Quentin Cohen, Wendy Smyrin, Aguesid Negan, Hanass Vincent, Susie,
  Royale Reideen, Elliott Vickroy.
- **2 declined** (🚫 no portrait, by decision): Bredt, Mr. Franky.
- 9 minor (no wiki page); 34 unnamed extras — left as-is.

Sourcing: 12 of the 13 yeses are wiki picks fetched via `fetch_named_portraits.py` (File: titles all validated,
0 failed). **Azik Eggers** is a manual crop of `Azik_Eggers_Official_Full.webp` (1000x5950 → top 1000x2224); source +
crop box noted in its `character_map.json` entry. Portrait binaries stay gitignored/regenerable.

## Key decisions locked
- Timing = **per-chapter forced alignment** (aeneas), combine by cumulative offset. (Not yet run — durations are
  char-share ESTIMATES.)
- Display = **scene-presence**; multiple characters → normalized row/grid; **fallback = hold previous frame**.
- Klein persona base flips **Klein (Beginning) → Klein Moretti at ch17** (Nighthawks contract). Tarot scenes → The Fool.
- **Anti-hallucination:** readers use text-literal names (`TAGGING_GUIDE.md`); `verify_tags.py` grounds every tag
  against the source; `name_aliases.json` holds canonical merges / `exclude` / `verified_present`.
- Assets = wiki-wide `<Name> Official.jpg` (35 char portraits + 11 place images); Susie is a real character (kept).

## How to resume (run from the repo root)
```
py -3.12 character_scene_video/align_chapter.py 1 50        # forced alignment -> align/ch_N.json
py -3.12 character_scene_video/verify_alignment.py 1 50     # timing gate, must say PASS
py -3.12 character_scene_video/build_block.py 1 50          # rebuild block-1 timeline (uses align/)
py -3.12 character_scene_video/verify_tags.py 1 50          # must be 0 to fix
py -3.12 character_scene_video/build_character_report.py 1 50
py -3.12 character_scene_video/compose_frames.py --block --contact-sheet   # frames + review sheet
py -3.12 character_scene_video/render_chapter.py 5 --preview              # cut plan, renders nothing
py -3.12 character_scene_video/render_chapter.py 1 5                      # actually render
```
To correct a scene: edit `timelines/scenes/ch_<N>.json`; to merge/rename a character: `name_aliases.json`;
to mark a confirmed presence the verifier flags: `verified_present` in `name_aliases.json`.

## Open threads / next steps
1. ✅ **Portrait decisions done** (`portrait_decisions.json`): 13 yes (sourced), 2 declined; need:0.
2. ✅ **Timing** — forced alignment built and passing (see above). No aeneas needed.
3. ✅ **Compositor + renderer** — built; ch1 and ch5 rendered and visually verified.
4. ⛔ **BLOCKED ON YOU — portrait source quality.** The compositor is correct, but the contact sheet
   (`frames/_contact_sheet.png`) shows the *inputs* are inconsistent, and this is the one thing that
   will be obvious to a viewer. Decide before rendering the block:
   - **Old Neil** is a promotional poster: it has a **腾讯视频 (Tencent Video) watermark** and the
     words "Old Neil" printed across it. It is not a portrait.
   - **Susie** resolves to a photo of a **golden retriever**. Correct per the "Susie is a real
     character" decision, but worth a conscious yes/no for on-screen use.
   - Several picks (Frye, Rozanne, Benson, Melissa…) are **anime screenshots** — wide busts with
     their own backgrounds — sitting beside the tall official character cards. Mixed styles and
     mixed apparent head sizes.
   - The official cards have the **诡秘之主 / Lord of the Mysteries logo and a copyright line**
     baked in, which is fine but does show on screen.
   Fixing means re-picking images in `portrait_decisions.json` / `character_map.json` and re-running
   `fetch_named_portraits.py`; the frame cache regenerates automatically.
5. **Then** render the block: chapters 1–50 → one ~10.9 hr video (`render_chapter.py` per chapter,
   then an ffmpeg concat + `0:00 Chapter N` description). **Not started — deliberately.**
6. **Tag Block 2 (ch51–100)** — text-literal guide + auto-verify + continuity from the start.

## Known limits (honest)
- ~0.9% of lines still land on a slightly wrong timestamp (a boundary slips by a few seconds
  between two adjacent lines). 7 of 156 scenes sit near one. Effect on screen is a portrait
  changing a few seconds early or late inside a 3-minute scene.
- Alignment assumes the text matches the audio. It does *not* for the title echo (handled), and it
  would not if any chapter's MP3 were regenerated from different text — re-run alignment if audio
  is ever re-synthesised.
- Shortest scene in block 1 is **3.1s** (ch3), so one portrait flashes briefly. No minimum-duration
  merging is applied; say the word if you want short scenes absorbed into their neighbour.
- The copyright posture from DESIGN.md §8 is still undecided and still applies.

## File map (character_scene_video/)
- `DESIGN.md` — full design + decisions + milestones (+ §10 timeline schema, continuity, alignment).
- `TAGGING_GUIDE.md` — anti-hallucination tagging rules.
- `scrape_official_images.py` — wiki-wide portrait scraper (→ `_manifest.json`, binaries gitignored).
- `build_character_registry.py` → `character_registry.json` (384 Book-1 chars + portrait coverage).
- `build_block.py` → `timelines/block_01_*.md/.json` (the timeline; applies personas, aliases, continuity).
- `build_character_report.py` → `timelines/character_report_block01.md` (participation/decision view).
- `verify_tags.py` — source-grounding gate.
- `fetch_named_portraits.py` — downloads human-chosen non-Official wiki portraits (File: title → `<Canonical>.<ext>`).
- `portrait_decisions.json` — yes/no portrait ledger; build scripts read it (yes→sourced, no→🚫 declined bucket).
- `timelines/scenes/ch_*.json` — raw per-chapter scene tags (source of truth for content).
- `align_chapter.py` → `align/ch_<N>.json` — forced alignment; per-line start/end seconds.
- `verify_alignment.py` — timing gate (structural checks + implied speaking-rate sanity).
- `compose_frames.py` → `frames/<hash>.png` — portrait row/grid frames, cached by cast set
  (gitignored; `--contact-sheet` writes one PNG of every distinct frame for review).
- `render_chapter.py` → `D:/PDFReader/lotm_book1_output/character_video/Chapter_<N>.mp4`.
