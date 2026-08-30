# CLAUDE.md

## Active Project Scope
- Current active project is `lom_book2_coi`.
- Unless explicitly stated otherwise, all commands and status updates for audio generation,
  video generation, and YouTube uploads refer only to `lom_book2_coi`.
- **Second workstream:** `character_scene_video` (Book 1 per-scene portrait videos) — see its
  section below. **Next session there: Volume 2 portrait decisions (tagging is done).**

## Agent context (how this file is loaded)
- **Cursor:** `.cursor/rules/claude-context.mdc` (`alwaysApply: true`) requires reading `CLAUDE.md` before tools or substantive changes — re-read each message, don't rely on memory.
- **Claude Code / other tools:** if not auto-loaded, `@`-reference this file at session start.
- **Setup elsewhere:** repo-root `CLAUDE.md` + an always-apply rule pointing at it; keep the progress log updated after pipeline runs.

## Instructions
- Read this file at the start of **each user message**.
- Do not read `.env` or secret credential files.
- Keep changes scoped to the requested task; prefer dry-run before full processing.
- If deleting files/folders, ask for permission first.
- After every run that affects outputs/uploads, update "Current Progress Log" here immediately.
- Use the YouTube API to verify recent uploads when status needs confirmation.
- ⚠️ **Run all scripts with `py -3.12`, not `python`** (PATH `python` = 3.11, missing `dotenv`/`google-api-python-client`).

---

## character_scene_video (Book 1 — separate workstream)
> NOT part of the `lom_book2_coi` pipeline. Per-scene character-portrait videos for **Book 1 (LOTM)**:
> tags every scene with who's present + setting, resolves portraits, renders per-chapter videos with
> scene-synced portrait rows. Design: `character_scene_video/DESIGN.md`. Session handoff + full block
> history: `character_scene_video/STATUS.md`. All on `master`.

### Current state (2026-08-28)
- ✅ **VOLUME 1 CONTENT COMPLETE:** ch1–213 tagged, verified, rendered (0 gaps, verified on disk).
- **12 h cap is ENFORCED by YouTube** (43 h single upload rejected 2026-08-28). Volume 1 uploads as
  **4 parts**, all built + packed in `D:/PDFReader/lotm_book1_output/character_video/Volume_1_Clown/`:
  ch1–50 (10:52:07) / 51–100 (10:07:56) / 101–157 (11:08:29) / 158–213 (11:10:03).
- ✅ **VOLUME 1 UPLOADED 2026-08-28, all 4 parts public** (verified via API + Studio 2026-08-29):
  P1 `sQ94crQVoAQ` / P2 `AfBLteZ9nfU` / P3 `Qi3hZkRr_j0` / P4 `8lha69vkmCE`; all in playlist
  `PLQD_MWrZYC-I` ("…Large Audiobook — Volume 1: The Clown") AND the per-chapter
  "LOTM - Volume 1: CLOWN" playlist. Day-1 analytics (impressions/CTR/views/uniques):
  P1 1.4K/1.7%/101/24 · P2 849/1.3%/33/12 · P3 207/1.0%/9/3 · P4 1.7K/0.9%/59/21; traffic
  ~50–89% Browse. **CTR test assets ready 2026-08-29 — see
  `character_scene_video/CTR_TEST_PLAN_VOL1.md`**: 3 thumbnail variants in
  `<Volume_dir>/thumbnails/thumb_vol01_p1_var{A_row,B_faces,C_strip}.jpg` + paste-ready
  description line-1s + title options. Sequencing: thumbnail Test & Compare on P1 first,
  description line 1 on all parts now, title change only after the thumbnail test. **Done
  2026-08-29:** thumbnail Test & Compare started + line-1 rewrites applied by user (verified via
  API); cross-link line prepended via API to the top-25-viewed Vol-1 per-chapter videos
  (casual wording, links `watch?v=sQ94crQVoAQ&list=PLQD_MWrZYC-I` so autoplay chains parts;
  script idempotent in session scratchpad `crosslink_batch.py`). **End screens verified via
  Studio 2026-08-29: P1→P2→P3 chained ✅, P4 has NONE ❌** — add manually (Vol-1 playlist +
  subscribe now; swap to Vol-2 P1 when live). **First vertical Short built 2026-08-29:**
  `<Volume_dir>/shorts/short_accidental_god_v1.mp4` (69 s, ch1+6+7 "accidental god" comedy
  compilation; commentary captions carry the humor over the monotone TTS; beats timed via
  `align/ch_N.json` lines; build script + upload notes + next-Short candidates in the same
  folder — upload manually, set Related Video → P1). **Community post PUBLISHED 2026-08-29**
  (posted by Claude via CDP/Studio; text matched the channel's casual voice — see the existing
  posts before drafting another — with the P1 video card attached; reusable CDP driver:
  scratchpad `cdp.py`, "Create post" opens the composer on www.youtube.com, not Studio).
  Still TODO: upload the Short, P4 end screen, manual pinned comments on the top ~5 chapter videos.
- **Volume 2 (ch214–482, `Volume_2_Faceless`) TAGGING COMPLETE (2026-08-28):** Blocks 5–10
  (ch214–482) tagged + verified (176+145+125+159+143+68 scenes, ~54:11 total; tags 208/208,
  197/197, 182/182, 220/220, 217/217, 102/102; alignment PASS all). Sharron (Miss Bodyguard,
  ch244+) mapped to her existing wiki card. **Portrait decisions COMPLETE 2026-08-28 — need:0 in
  all six blocks** (10 installed, everyone else answered 'no for now'; see the ledger below).
  ⏭ **Next for Vol 2: frames → render → pack** (new tagging would be Vol 3, ch483+).
- **`Hero Bandit` persona added 2026-08-29** (`project.json` → `persona.map`, image
  `Hero Bandit.png`, label "Klein (as the Hero Bandit)"): Klein's black-armour/black-crown Dark
  Emperor form, which the papers name in ch382. Tagged on the 12 scenes where he is actually in it —
  ch377 s3, ch378 s1–2, ch379 s1, ch380 s1–5 (the Capim raid) and ch426 s3–4 + ch427 s1 (the Devil
  in the sewer). NOT a disguise-identity like Sherlock: it becomes a real alias only later
  (Vol 3 ch717, Dwayne Dantès in Vol 4). `image_names` also reserves Dwayne Dantès + Merlin Hermes,
  but neither has a `map` entry yet — adding one without an image would KeyError in `build_block`.
  The ch215 persona flip
  (Klein → Sherlock Moriarty) is configured in `project.json` `base_flips`; ~ch214+ MP3s
  post-date the title-echo fix (alignment's `has_title_echo()` handles either case).
- Portrait ledger: Vol 1 have:32 need:0. Vol 2 in progress — 2026-08-28: `Will Auceptin` rekeyed in
  `character_map.json` (wiki spells it `Wil`, one L) + **9 installs from user-supplied art**
  (Aaron Ceres, Jurgen Cooper, Stelyn Sammer, Maric, Talim Dumont, Utravsky, Mike Joseph,
  Ikanser Bernard, Lanevus) + **Edessak Augustus and Old Kohler 2026-08-29** (37 names left in
  `_no_for_now`; their chapters were re-rendered and the affected upload parts re-concatenated).
  **Depiction/stand-in convention adopted 2026-08-29** (user decision): resemblance art and joke
  stand-ins are allowed for characters with no official art, marked with a small white * in the
  image's top-right corner (`character_scene_video/mark_depiction.py <image>` stamps it at install)
  and disclosed once in the series `credit_line` in `upload_meta.json` ("Portraits marked with a
  small * are artist depictions or playful stand-ins"). First three: **Steve** (resemblance,
  black coat + red cloak lining), **Jason** (cartoon zombie -- wiki literally says he looks like a
  zombie), **Tyre** (werewolf under the moon). Susie + Mr. A's older fan art stays unmarked
  ("obviously for fun", grandfathered). ch347-350 re-rendered, part 3 re-concatenated, packs
  regenerated for both volumes.
  **`Darkwill` identified 2026-08-29** (user): the plump 'Apothecary'/Beast Tamer from Eye of
  Wisdom's gatherings, previously the bracketed `[fat-faced man]` — retagged to `Darkwill` in his
  13 scenes (ch239-335) with `verified_present` entries (name never on-page there), portrait
  installed (art with his owl, used as-is 648x900), blocks 5-7 rebuilt (213/202/186, 0 to fix),
  chapters re-rendered, parts 1-3 re-concatenated (durations unchanged).
  **`Kohler` -> `Old Kohler` alias added 2026-08-29** — the text says plain "Kohler", so the report
  had been mis-filing a 20-scene / 89-min recurring character as ➖ minor and never asked about him;
  standing rule + the Eye-of-Wisdom code-name rule (gathering scenes tag `Eye of Wisdom`, detective
  scenes tag `Isengard Stanton`, NEVER aliased together) are documented in `TAGGING_GUIDE.md`. Sources are Chinese/Thai cover scans, page photos and donghua stills;
  covers are hand-cropped to head/shoulders so the title, volume number and publisher logos stay out
  of frame. Aaron Ceres was re-supplied at 1210x1730 and the first cover crop superseded (old file
  parked in the session scratchpad, not deleted). Jurgen Cooper is low-res 190x267 — replace if a
  bigger source appears.
  **The other 38 Vol-2 wiki characters are recorded 'no' (2026-08-28) for lack of art, NOT because
  they're unwanted** — tracked in `portrait_decisions.json` → `_no_for_now` (names + scene weight)
  with the wiki's physical descriptions in
  `projects/lotm_book1/timelines/portrait_wanted_descriptions.md`, so lookalike art can be slotted
  in later (install → flip to `yes` → rerun `build_block.py` + `compose_frames.py`).
  Hard-declined: Kaslana/Kaspars Kalinin (2026-08-28) +
  Gawain/Jack/Naya/Mr. Franky/Bredt/Grimm/Edwards
  (+ minor never-asked bucket). New-art installs use the clipboard-grab flow (visually verify each
  capture before install); manual portraits are flagged in `character_map.json` so wiki re-fetches
  can't clobber them.

### Engine layout (generalized; run everything with `py -3.12` from repo root)
- Shared engine + per-project config: `character_scene_video/projects/<name>/project.json`
  (template in `projects/_TEMPLATE/`). All scripts take `--project` (default `lotm_book1`).
  Per-project data (scene tags, align, timelines, aliases, continuity, portrait decisions, frames)
  lives in `character_scene_video/projects/<name>/`.
- **Output is BY VOLUME:** everything renders/concats into `<video_out_dir>/<Volume_dir>/`
  (e.g. `.../character_video/Volume_1_Clown/`); the volume folder is derived automatically from the
  text layout by `charvid_project` helpers. `build_block_video.py` refuses ranges that cross a
  volume boundary. Thumbnails go in `<Volume_dir>/thumbnails/`.
- Upload-pack config (part ranges, story hooks, tags, pitch lines) lives per project in
  `projects/<name>/upload_meta.json` (template in `_TEMPLATE/`).
- Alignment is NOT aeneas/WhisperX: Azure-TTS audio of known text, matched sentence-sequence ↔
  ffmpeg-pause-sequence with a DP. No extra deps.

### BLOCK RECIPE (replace A B with the chapter range, e.g. 214 263)
Steps 1–2 are content work (new blocks only); 3–10 are mechanical.
1. **Tag scenes**: read each chapter, write `projects/lotm_book1/timelines/scenes/ch_N.json` per
   `TAGGING_GUIDE.md` (text-literal names); add boundary entries to `continuity.json` (incl.
   boundary A-1); new aliases → `name_aliases.json`.
   ⚠️ **Dream/vision/memory figures are NOT present** — never in `other_characters`; note them in
   `setting` as "(visions only: …)".
   ⚠️ **Roselle diary-reading interludes** (standing rule, all blocks): whenever Klein/The Fool
   READS diary pages, split the scene around the reading — break scene = protagonist + Roselle
   Gustav + anyone named in the pages (everyone else physically present dropped); resume scene
   after. Carry Roselle in `continuity.json` across chapter breaks; whitelist via
   `verified_present` if "Roselle" isn't in the line span; splitting renumbers scenes → update
   existing `verified_present` indexes. Does NOT apply to diary discussion without reading, the
   Antigonus diary, or recollections/quotes. Full rule in `TAGGING_GUIDE.md`.
2. **Portrait decisions**: after step 5, `build_character_report.py A B` → record yes/no in
   `portrait_decisions.json`; source images (`fetch_named_portraits.py` or user-supplied). After
   ANY portrait change: rerun `build_block.py`, THEN `compose_frames.py`.
3. `py -3.12 character_scene_video/align_chapter.py A B`
4. `py -3.12 character_scene_video/verify_alignment.py A B`     # must PASS
5. `py -3.12 character_scene_video/build_block.py A B`
6. `py -3.12 character_scene_video/verify_tags.py A B`          # must be 0 to fix
7. `py -3.12 character_scene_video/compose_frames.py --block --contact-sheet`  # eyeball new frames
8. `py -3.12 character_scene_video/render_chapter.py A B`       # `--preview` first; spot-check
   ⚠ **re-renders MUST pass `--force`** — without it the script SKIPS existing MP4s while still
   printing a normal-looking per-chapter summary (timeline cuts, not the file). Bit us 2026-08-29:
   six portrait installs looked rendered but weren't until a `--force` sweep. Verify with an
   ffmpeg frame grab, not the log.
9. `py -3.12 character_scene_video/build_block_video.py A B --plan` then without `--plan`
   → `<Volume_dir>/Block_NN_chAAA-BBB.mp4` + `_description.txt` (keep each upload part < 12 h;
   warns past 11.9 h; must not cross a volume boundary)
10. Upload prep: add the volume's parts + hooks to `projects/<name>/upload_meta.json`, then
    `py -3.12 character_scene_video/make_upload_pack.py --volume V` and
    `py -3.12 character_scene_video/make_thumbnail.py V --name "<Vol Name>" --part K --range "A-B" --hours H`

---

## The 3-Step Workflow — `lom_book2_coi` (audio → video → upload)
> Run from repo root (`pdf-reader`). Replace `N-M` with the chapter range.

### Step 1 — AUDIO (Azure TTS) → `D:/PDFReader/lom_book2_coi_output/Volume_*/*.mp3`
- Safe validation: `py -3.12 tts_pipeline/scripts/process_project.py --project lom_book2_coi --dry-run --max-chapters 5`
- Range: `py -3.12 tts_pipeline/scripts/process_project.py --project lom_book2_coi --chapters N-M`
- Next 10 from where we left off: `... --continue 10` · Resume: no extra flag
- One-shot audio+video: add `--create-videos`

### Step 2 — VIDEO → `D:/PDFReader/lom_book2_coi_output/video/Volume_*/*.mp4`
- `py -3.12 tts_pipeline/scripts/create_videos.py --project lom_book2_coi --chapters N-M`
- Preview one: `... --chapters N --preview` (⚠️ preview does NOT validate audio/art — simulated success)
- Resume: `... --resume`
- Encoder auto-probes at first use (this machine: AMD RX 9070 XT → `h264_amf`).
- Audio filenames may drift from text filenames (old runs sanitized `'`/`,`/`!` and truncated);
  `create_videos.py` falls back to chapter-number matching — uploader titles come from text files,
  so drifted names are cosmetic.

### Step 3 — UPLOAD → tracker `D:/PDFReader/lom_book2_coi_output/youtube_progress.json`
> **ONE upload job at a time** (two = duplicates). Quota-safe pace ≈ 6/hour (~10 min apart; the script paces itself).
- Auth/tracker check only: `py -3.12 upload_queue.py --project lom_book2_coi --limit=0`
- Next single: `... --yes --limit=1` · Next 10: `... --yes --limit=10`
- OAuth: complete browser sign-in as **breadmoretti@gmail.com** if prompted (`token.json` in repo root).
- Titles come from the `Chapter N: <title>` line in the formatted source text, not filenames.
- Config: `tts_pipeline/config/projects/lom_book2_coi/youtube_config.json`
- ⚠️ The script has NO retry — if a chapter fails mid-batch it continues and leaves a hole; fix the
  gap in order before the next batch (delete out-of-order later uploads only with user approval).
- ⚠️ A pre-check snapshot goes stale during a long batch — re-check discovery after the run.
- ⚠️ Per-upload `Video may not be in playlist` warnings are a known API-listing quirk, not data loss.

### Step 4 — END SCREENS (run AFTER a fully successful upload batch; skip if ANY upload failed)
> Standing rule: after Step 3 reports `Failed: 0`, add end screens. Tool: `youtube_endscreen.py`
> (Playwright driving Studio UI; idempotent — already-done videos are skipped; `--replace` not implemented).
- **Range rule:** for uploaded batch N–M, run sources **(N-1)–(M-1)** (boundary chapter links to the
  first new one; newest chapter M waits for the next batch).
- `py -3.12 youtube_endscreen.py --project lom_book2_coi --chapters (N-1)-(M-1) --connect-port 9222 --yes`
  (`--plan-only` = offline pre-check; style imported from ch249 via `--style-from`, don't change)
- **Chrome prereq:** attaches to real Chrome on port 9222; profile `%USERPROFILE%\yt-studio-login`
  (logged in as breadmoretti). **Assume Chrome is down between runs** — always
  `curl http://127.0.0.1:9222/json/version` first; if silent, relaunch:
  `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\yt-studio-login" "https://studio.youtube.com/"`
  (If logged out: sign in first in a normal Chrome with that user-data-dir and NO debug port, then relaunch with the port.)
- **Unlisted-only guard:** public videos are skipped; chapters go public within ~days of upload, so
  run end screens promptly, else include via `--allow-public-chapters 320` (comma-separated list).
- ⚠️ Don't pipe the tool's output through `tail` (truncates the log); re-running is the safe verify.

### Chapter background art (per-project)
> `tts_pipeline/config/projects/<project>/portrait_mapping.json` maps chapter-range → filename;
> images in `tts_pipeline/assets/projects/<project>/backgrounds/` (+ `resized/`).
- Add art: drop in `.../dropoff/` → `py -3.12 tts_pipeline/scripts/prepare_backgrounds.py --project <project>`
  → edit `portrait_mapping.json` → `... --status` to verify (exit 0 = all mapped).
- `null` ranges fail loudly at render; never use `--background-image` overrides for production.
- **`lom_book2_coi` mapping (physical-edition parts):** boundaries
  1-55 / 56-109 / 110-186 / 187-263 / 264-340 / 341-417 / 418-494 / 495-575 / 576-655 / 656-735 / 736-884
  (`coi_v1..coi_v11`; `coi_v10_sinner_3` is `.jpeg`). ✅ mapped through ch884 — **ch885+ has NO art yet.**
- `lotm_book1` mapping complete.

### Setup / utility
- EPUB → text: `py -3.12 epub_to_text/main.py "<path>.epub" -p "<project>" -o "formatted_text"`
  (two header lines per file for TTS pauses; drops body title echoes).
- List projects: `py -3.12 tts_pipeline/scripts/process_project.py --list-projects`
- Tests: `cd tts_pipeline && py -3.12 -m pytest tests/ -q` (66 passed as of 2026-08-10).

## Config & path conventions
- Output root: `D:/PDFReader/` (per-project: `D:/PDFReader/<project>_output`).
- `process_project.py` must run with cwd = repo root (paths resolve under the repo).
- COI config dir: `tts_pipeline/config/projects/lom_book2_coi/` (`volume_pattern` = `Volume_(\\d+)_`).
- Azure: copy `azure_config.json.example` → `azure_config.json` (gitignored); set
  `AZURE_TTS_SUBSCRIPTION_KEY` / `AZURE_TTS_REGION` in env; never commit secrets.
- Naming quirks (don't "fix"): book1 audio on disk keeps legacy `N___VOLUME_N___` folders;
  COI text says `Volume_2_Light_Chaser` but outputs use `Volume_2_Lightseeker`.
- Repo audits 2026-06-14 + 2026-08-10 (import fixes, asset reorg, doc sync, dead-file deletions)
  are recorded in git history and the synced docs (`README.md`, `ARCHITECTURE.md`, `SCRIPTS_GUIDE.md`).

## Tracking
- Progress status lives HERE (below), not in `tracking/*.json`.
- Source of truth for created audio/video: the output folder on D:. For uploads: YouTube API /
  `youtube_progress.json`.

## YouTube (`lom_book2_coi`)
- Channel account: **breadmoretti@gmail.com** (NOT paolo.gene).
- Playlists (reused by ID from `youtube_config.json → playlists.playlist_ids`):
  V2 Lightseeker `PLV2gvMHy77hrYzC8lxYXCtEp4NArMkh7s` · V3 Conspirer `PLV2gvMHy77hpe3q8VvnIeXK1s-y8sNSpM`.
- ⚠️ Old wrong playlist `PLV2gvMHy77hrh1HeiBECpJ61Smbgg5_S6`: 30 early uploads (incl. 236–240) still
  need MANUAL moving in Studio; everything from 241 on is correct.
- Old one-off issues: ch230–232 may have duplicate uploads; ch215 title may need a manual fix.

## Current Progress Log

### lom_book2_coi (uploads updated 2026-08-21)
| Stage | Done | Highest | Next action |
|---|---|---|---|
| Audio (`.mp3`) | 603 | 603 | generate ch. **604+** |
| Video (`.mp4`) | 601 files (through 600, contiguous 1–600) | 600 | create ch. **601–603**, then wait for audio |
| Upload | 360 (1–360, no gaps) | 360 | upload ch. **361** (240 pending; all vol-3+ ranges routed by ID) |

- Most recent upload: 2026-08-21, ch. **351–360** (10/10, → Conspirer; drifted-filename ch357 worked end to end).
- End screens: done through **359→360** (2026-08-21). ⏭ **Dangling: ch360** — include as source in the
  next batch (sources 360–369 after uploading 361–370).
- Volume boundaries: ch264+ → vol 3 (Conspirer). Ch885+ needs background art before video creation.
- Disk: ~1.17 TB free on D:; ~672 MB/video average.
- EPUB source: 1180 formatted chapters in 8 volume folders under `formatted_text/lom_book2_coi`.
- Per-batch video IDs and dated batch history: `youtube_progress.json` + git history of this file.

### character_scene_video (2026-08-29)
- Volume 1 (ch1–213): rendered complete; **all 4 parts UPLOADED + PUBLIC 2026-08-28** (IDs and
  day-1 analytics in the "Current state" section above). Obsolete 43 h `Block_01_ch001-213.mp4`
  still on disk (delete only with user approval).
- Optional leftover: user spot-check of the 29 block-3 Tarot-gathering scenes (list generated 2026-08-27).
- **VOLUME 2 TAGGING COMPLETE 2026-08-28: Blocks 5–10 (ch214–482) TAGGED + VERIFIED**
  (176/145/125/159/143/68 scenes, ~54:11 total; verify_tags 208/208, 197/197, 182/182, 220/220,
  217/217, 102/102; alignment PASS all). Frames + render deferred per user.
- **Vol 2 portrait round started 2026-08-28:** Will Auceptin spelling fix + **Aaron Ceres, Jurgen
  Cooper, Stelyn Sammer, Maric, Talim Dumont, Utravsky, Mike Joseph, Ikanser Bernard, Lanevus** installed
  (user-supplied cover/illustration art via clipboard; Aaron Ceres re-supplied at higher res, cover
  crop superseded); **Kaslana + Kaspars Kalinin hard-declined**. The remaining **38 got 'no for
  now'** (no art found) — recorded in `portrait_decisions.json` → `_no_for_now` with scene weight,
  and their wiki physical descriptions collected in
  `timelines/portrait_wanted_descriptions.md` so the user can hunt lookalike art; flipping one to
  `yes` after installing art + rerunning `build_block.py`/`compose_frames.py` is all it takes.
- **PORTRAIT DECISIONS DONE — all six Vol-2 blocks rebuilt + verified 2026-08-28: need:0 everywhere,
  verify_tags 208/198/182/220/217/102, 0 to fix.**
- **2026-08-29 — FRAMES DONE:** `compose_frames.py --block --contact-sheet` composed the 83 new
  portrait sets (212 distinct sets across Book 1; 218 PNGs + `_contact_sheet.png` in
  `projects/lotm_book1/frames/`); all 1,529 scenes across every block resolve to a frame on disk
  (0 missing).
- **2026-08-29 — VOLUME 2 IS BUILT AND PACKED.** `render_chapter.py 214 482` rendered all 269
  chapters (0 missing, 0 undersized), then `build_block_video.py` concatenated **five upload
  parts** into `character_video/Volume_2_Faceless/`, all ~1 h 10 m under the 12 h cap:
  ch214–266 (10:49:10) / 267–320 (10:53:01) / 321–374 (10:50:06) / 375–428 (10:46:40) /
  429–482 (10:51:58), ~805 MB each, 54:11 total. Split computed as a balanced 5-way min-max over
  the aligned audio durations, cut points nudged onto story beats (The World's Commission / Action /
  Artificial Sleepwalking just before Capim's dinner / The Scapegoat). `make_upload_pack.py
  --volume 2` + `make_thumbnail.py` wrote per-part description/pinned/tags files and
  `thumbnails/thumb_vol02_p1..5.jpg`; `playlist_vol02.txt` and
  `character_scene_video/YOUTUBE_UPLOAD_PLAN_VOL2.md` are written too.
  ⏭ **NEXT ACTION: manual Studio upload of Volume 1's 4 parts, then Volume 2's 5 parts.**
