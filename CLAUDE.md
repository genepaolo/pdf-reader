# CLAUDE.md

## Active Project Scope
- Current active project is `lom_book2_coi`.
- Unless explicitly stated otherwise, all commands and status updates for audio generation,
  video generation, and YouTube uploads refer only to `lom_book2_coi`.
- **Second workstream:** `character_scene_video` (Book 1 per-scene portrait videos) — see its
  section below. **Next session there: manual Studio upload of Volume 2's 5 parts (proof of readiness = `verify_render.py 214 482` CLEAN; thumbnail picks in `THUMBNAIL_TEST_ANALYSIS.md`), then Vol 3 block 11 portrait decisions -> render (STATUS.md top block).**

- **Third workstream (planned, not started): replace Azure TTS with local VoiceStudio** —
  plan in `VOICESTUDIO_TTS_SWAP_PLAN.md` (written on the Mac 2026-10-02). Starts at Phase 0, a GPU
  go/no-go benchmark on the RX 9070 XT; voice-clone of Steffan first, presets as fallback. Azure stays
  the default (`tts_engine: azure`) until Phase 2d passes. Never commit clone weights or reference WAVs.

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
  `<Volume_dir>/parts/Part_1_ch001-050/thumbnails/thumb_vol01_p1_var{A_row,B_faces,C_strip}.jpg` + paste-ready
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
- **Output is BY VOLUME, then BY PART (layout adopted 2026-09-06):** under `<video_out_dir>/<Volume_dir>/`
  (e.g. `.../character_video/Volume_2_Faceless/`; the volume folder is derived from the text layout by
  `charvid_project` helpers):
  `chapters/Chapter_N.mp4` (per-chapter masters) · `parts/Part_K_chAAA-BBB/` (one upload part:
  `Part_K_chAAA-BBB.mp4` + `_description.txt` + `_description_YOUTUBE.txt` + `_pinned_comment.txt` +
  `_tags.txt` + `thumbnails/` with that part's thumbnail and A/B variants) · `thumbnails/` (volume-level)
  · `playlist_volNN.txt`. **K is the part's list position under its volume in `upload_meta.json`** —
  `build_block_video.py` looks the range up there (or takes `--part K` for an ad-hoc range) and refuses
  ranges that cross a volume boundary. Vol 1's abandoned 43 h single upload lives in
  `Volume_1_Clown/_legacy/`. Helpers: `P.chapter_video(ch)`, `P.part_dir(K,a,b)`, `P.part_stem(K,a,b)`,
  `P.thumbnails_dir(vol, part)`.
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
   ⚠ **Frames are cached by cast+order+rims and `LAYOUT_VERSION` (compose_frames.py). If you
   change LAYOUT (rows_for/_fit_row/margins/rims) you MUST bump LAYOUT_VERSION, else every
   cached PNG is reused and the re-render changes nothing.**
   ⚠ **re-renders MUST pass `--force`** — without it the script SKIPS existing MP4s while still
   printing a normal-looking per-chapter summary (timeline cuts, not the file). Bit us 2026-08-29:
   six portrait installs looked rendered but weren't until a `--force` sweep. Verify with an
   ffmpeg frame grab, not the log — or better, **`py -3.12 character_scene_video/verify_render.py A B`**
   (added 2026-09-18): pixel-compares every scene of every chapter MP4 against the frame the current
   block data resolves to, checks the frame cache against a fresh recompose (in-place portrait swaps),
   and flags parts older than their chapters. Exit 0 = CLEAN; otherwise it prints the exact
   `chapters_to_rerender` / stale PNGs / stale parts (`--json PATH` for a machine-readable list;
   `--frames` = cache-only, seconds). **This is the only accepted proof that a range is rendered.**
9. `py -3.12 character_scene_video/build_block_video.py A B --plan` then without `--plan`
   → `<Volume_dir>/parts/Part_K_chAAA-BBB/Part_K_chAAA-BBB.mp4` + `_description.txt` (K from
   `upload_meta.json`, so add the part range there FIRST; keep each upload part < 12 h;
   warns past 11.9 h; must not cross a volume boundary)
   ⚠ **re-concats MUST pass `--force` too** — same silent skip as step 8 (bit us 2026-09-02:
   packs regenerated while all 9 part MP4s stayed stale). Verify with file mtimes.
10. Upload prep: add the volume's parts + hooks to `projects/<name>/upload_meta.json`, then
    `py -3.12 character_scene_video/make_upload_pack.py --volume V` and
    `py -3.12 character_scene_video/make_thumbnail.py V --name "<Vol Name>" --part K --of N --range "A-B" --hours H`
    (both write into `parts/Part_K_chA-B/`)

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
- Old one-off issue: ch215 title may need a manual fix.
- ✅ **PLAYLIST ROUTING IS RESOLVED — audited via API 2026-09-05, nothing to move.** The old warning about
  `PLV2gvMHy77hrh1HeiBECpJ61Smbgg5_S6` ("30 early uploads incl. 236–240 need manual moving") was STALE:
  that playlist **no longer exists** (404 `playlistNotFound`) and every chapter now sits in the right one.
  Verified membership of all 390 uploaded chapters:
  Vol 1 Nightmare `PLV2gvMHy77hpWltp0KalQNL8JPkqBKWQu` = ch1–109 · Vol 2 Lightseeker = ch110–263 ·
  Vol 3 Conspirer = ch264–390. **Zero chapters outside a playlist.**
  Root cause of the original mess (fixed by commit `c852902`, 2026-06-14): `get_or_create_playlist`
  resolved playlists **by NAME** from `name_template`, which then read `LOTM 2 - Volume {n}` and did not
  match the hand-made `LOM2 COI - Volume 2: Lightseeker`, so the uploader **auto-created its own**
  playlist and filled it. The fix pins `playlists.playlist_ids` and short-circuits before the by-name
  lookup. ⚠️ Volume **1** has no `playlist_ids` entry — harmless today (vol 1 is fully uploaded, and the
  renamed template now matches by name), but pin it if vol-1 uploads ever resume.
- ✅ **TRACKER REPAIRED 2026-09-05.** ch122 and ch230 had held **deleted** video IDs (`MKqJQyOKqJE`,
  `7Ur5oGt7lt4`) — residue of the ch230–232 duplicate cleanup. Repointed to the live re-uploads
  (ch122 = `M7f0V00TlYo`, ch230 = `sfmJd-_p69w`) with their real publish times + Lightseeker playlist id.
  Backup: `youtube_progress.json.bak-2026-09-05`. Re-audited: **390/390 ids alive, 0 dead, no gaps.**
  Worth re-running that audit occasionally (videos.list over every tracker id) — nothing else does it.
- ✅ **END-SCREEN CHAIN VERIFIED INTACT around the repair (2026-09-05).** An earlier worry that ch121/ch229
  pointed at the deleted videos was **WRONG** — checked and disproved: ch121 → live ch122, ch229 → live
  ch230, and ch122 → 123, ch230 → 231 all present and correct (watch-page check: dead ids appear 0×, live
  ids 56×). **Why it self-healed: `youtube_endscreen.py` picks the TARGET by searching Studio for the
  chapter TITLE (`#search-yours`, `youtube_endscreen.py:262`), NOT by tracker video_id.** Only the SOURCE
  video is addressed by tracker id. So a stale tracker id can break the source lookup for that chapter,
  but can never mis-aim a target.
- ⚠️ Vol 3 Conspirer playlist holds **2 `Deleted video` rows** (`OKRcFKOhBTE`, `IFa7FCbQ4Bs`) — dead
  entries to remove in Studio (why its itemCount is 129 vs 127 real chapters).
## Current Progress Log

### lom_book2_coi (uploads updated 2026-09-30)
| Stage | Done | Highest | Next action |
|---|---|---|---|
| Audio (`.mp3`) | 603 | 603 | generate ch. **604+** |
| Video (`.mp4`) | 601 files (through 600, contiguous 1–600) | 600 | create ch. **601–603**, then wait for audio |
| Upload | 472 (1–472, no gaps) | 472 | upload ch. **473+** (128 pending). ⚠️ background jobs now get killed (see below) |

- Most recent upload: 2026-09-30, **ch471–472 only** (batch of 20 abandoned, see below). Before that: 451–470
  (09-27), 431–450 (09-20), 411–430 (09-16) — all clean.
  ⚠️ **2026-09-30: BACKGROUND JOBS ARE NOW KILLED AT A TIME LIMIT (~30 min, even with timeout=600000).** Two
  `upload_queue.py` runs died after ~1 upload each (earlier sessions ran 3.5 h unattended). Second kill hit
  AFTER ch472 finished uploading but BEFORE the uploader's playlist-add + tracker write, leaving a complete,
  untracked video (`vaJim7ioOXY`, size identical to local MP4). Reconciled by hand: added to Conspirer
  playlist + tracker entry (backup `youtube_progress.json.bak-2026-09-30`). **After ANY killed run: query the
  channel's newest uploads for an UNTRACKED video before restarting, or you create a duplicate.**
  473–490 NOT uploaded; needs a way to run >30 min (foreground/other host) or small `--limit` chunks.
  ⚠️ `upload_queue.py` stdout is BLOCK-BUFFERED when redirected to a file — a background run's log can sit
  at 0 bytes for an hour while uploads succeed. Judge progress by `youtube_progress.json` (mtime + entry
  count) or the process being alive, never by an empty log.
- End screens: **DONE through 469→470 (2026-09-27); 470→471 and 471→472 NOT yet done.** Sources 450–469: 20/20 confirmed + saved, 0 WARN/ERROR/
  SKIP (Chrome 153, still logged in). Before that: 430–449 (09-20), 410–429 (09-16), 390–409 (09-10,
  independently re-verified in Studio). ⏭ **Dangling: ch470** — run sources **470–(M-1)** after the next
  batch lands. Pattern that now works every time: relaunch Chrome on 9222 → `--plan-only` →
  run with `-u` and `--allow-public-chapters $(seq -s, N M)`.
  ⚠️ **THE UNLISTED-ONLY GUARD IS NOW PERMANENTLY IN THE WAY — always pass `--allow-public-chapters`.**
  Uploads still go up unlisted (`upload_settings.privacy`) but flip public in **under a day**
  (381–390 uploaded 2026-09-04 were public by 2026-09-05), so 'run end screens promptly while unlisted'
  is dead. Without the override a run is a SILENT NO-OP: `--plan-only 360-389` said
  `Eligible (unlisted): 0 / 30` and a normal run would print a plausible plan and edit nothing.
  The flag takes an explicit comma list, so generate it: `seq -s, N M`. Working invocation:
  `py -3.12 youtube_endscreen.py --project lom_book2_coi --chapters N-M --connect-port 9222 --yes \n   --allow-public-chapters $(seq -s, N M)`
  Read-only presence audit (no edits): open `studio.youtube.com/video/<id>/editor` over CDP and count
  `#add-endscreen-icon-button` — 1 = missing, 0 = present (same check the tool uses at
  `youtube_endscreen.py:220`). Visual tell: End screen row shows `Edit` + a Subscribe/Video timeline
  track when present, `+` and no track when missing.
  ⚠️ Run the tool with `py -3.12 -u` — like the uploader, its stdout block-buffers when redirected.
- Volume boundaries: ch264+ → vol 3 (Conspirer). Ch885+ needs background art before video creation.
- Disk: ~1.17 TB free on D:; ~672 MB/video average.
- EPUB source: 1180 formatted chapters in 8 volume folders under `formatted_text/lom_book2_coi`.
- Per-batch video IDs and dated batch history: `youtube_progress.json` + git history of this file.

### character_scene_video (2026-08-29)
- Volume 1 (ch1–213): rendered complete; **all 4 parts UPLOADED + PUBLIC 2026-08-28** (IDs and
  day-1 analytics in the "Current state" section above). Obsolete 43 h `Block_01_ch001-213.mp4`
  still on disk, parked in `Volume_1_Clown/_legacy/` (delete only with user approval).
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
- **2026-09-01/02 — FULL RE-RENDER + RE-PACK (both volumes) with the new frame system.**
  Portrait ordering (Klein first, Tarot members next, mentioned-only last), gold mentioned-rims,
  7 deity cards, `frame_focus` (ch461 s2 six-god mural ONLY — reserved for over-cap crowding),
  delayed-entrance splits (ch447 Amon reveal, ch264 Lanevus painting), missing-tag sweep
  (22 scenes gained mentions; ch460 s3 Derrick presence fix; ch447 s1 Amon deliberately untagged
  for the reveal). **Sharon ≠ Sharron (user, ×2): Madam Sharon = Backlund madam, Demoness pathway,
  own portrait `Sharon.png` — never alias to the ch244+ bodyguard.** frame-cap warning now built
  into `build_block.py` (both volumes clean; max 8 portraits, ch461 s3). All 482 chapters
  re-rendered `--force` + frame-grab verified; **all 9 parts re-concatenated (`--force`!) 
  2026-09-02 15:25–15:30, packs regenerated**; verify_tags 0-to-fix on all 11 blocks. Standing
  rules added to `TAGGING_GUIDE.md`; session details in `STATUS.md`.
- **Vol 1 P1 thumbnail A/B (checked 2026-09-02 via Studio/CDP):** running, ~10 days left, no
  per-variant data yet; P1 7-day CTR 2.4% (up from 1.7% day-1, ~3–3.5% post-test-start estimate)
  while control parts P2/P3/P4 stayed 1.4%/0.7%/1.1% — new thumbnail concepts are winning; which
  variant unknown until ~Sep 11. Plan: hold P2–P4 + P1 title; **Vol 2 P1 variants BUILT 2026-09-02** —
  `thumb_vol02_p1_var{A_bigface,B_faces,C_row}.jpg` (A = S2-poster Sherlock face, the
  recommended default; art sources + test setup in `YOUTUBE_UPLOAD_PLAN_VOL2.md`): set varA at
  upload, then Test & Compare with B + C. **2026-09-02: variant trios (A bigface / B faces /
  C row) BUILT for every remaining part** — Vol1 p2-4 + Vol2 p2-5, part-specific casts, in
  each part's `thumbnails/` folder (generator: session scratchpad `make_all_variants.py`). Vol-2 upload
  readiness AUDITED (5 MP4s fresh, durations match descriptions, packs/tags/pinned/playlist
  present); human spot-check list: `character_scene_video/VOL2_REVIEW_CHECKLIST.md`.
- **2026-09-03 ch215 PERSONA FLIP FIXED** (user spotted it): Klein was rendering as Sherlock
  Moriarty from line 3, but he invents the name at **L79** ("Sherlock Moriarty. You can call
  me Sherlock."). `base_flips` is CHAPTER-granular, so it overrode the scene tags. Flip moved
  to **at_chapter 216**; ch215 is now tagged scene by scene (Klein Moretti s1-s5, Sherlock
  s6-s9, split at L79). Lesson: for a mid-chapter identity change, set the scene personas AND
  push the base_flip to the NEXT chapter, or the flip silently wins.
- **2026-09-03 THREE-TIER MENTION RULE** (user): character / subject-of-conversation / passing
  note — a simple mention warrants NO portrait. Recorded in `TAGGING_GUIDE.md`. Swept all 56
  Vol-2 mention tags: removed 5 tier-3 tags (ch245 TC, ch265 EBS, ch292 Qilangos+Cattleya,
  ch440 Evernight). Same sweep caught a STRUCTURAL bug: **ch406 had a duplicate scene**
  (57-89 alongside its own split halves 57-71 + 73-89) and the halves had lost Fors Wall —
  fixed; a 482-chapter overlap scan found no others. Chapters 245/265/292/406/440 re-rendered,
  parts 1/2/4/5 re-concatenated, Vol-2 pack regenerated; all durations unchanged.
- **2026-09-03 (late) PORTRAIT ROUND + REVIEW.** User reviewed all 5 Vol-2 parts; outstanding
  re-check list (chapters that changed AFTER each part was signed off) is in
  **`character_scene_video/VOL2_OUTSTANDING_REVIEW.md`** — read that first to resume.
  New portraits: **Eye of Wisdom** (own art; NEVER Isengard Stanton.png, ch415 reveal),
  **Mr. Door**, **Daisy** (`*` reference), **God of Combat** (Badheil), **Colin Iliad** (16
  chapters!), **Lovia**, and **Zaratul** replaced. **`Apothecary` not `Darkwill` in Vol 2**
  (the name Darkwill first appears Vol 3 ch585). ch461 merged to ONE 7-god focus frame.
  ⚠ **85 Vol-2 characters are tagged-but-artless** (Kaslana 86 min, Stuart 53, Escalante 48,
  Horamick Haydn 38…) — `build_character_report.py` ranks by SCENE COUNT so they never
  surface; switching it to SCREEN TIME is the fix.
  ⚠ **After installing ANY portrait, rebuild ALL 11 blocks** — a partial rebuild left ch216/217
  rendering a stale cast with Mr. Door still missing, and the render log looked normal.
- **2026-09-03 MR. WORLD IS A SEATED MEMBER, NOT A PERSONA** (user): `[The World]` (bracketed
  background) -> **`The World`** with its own portrait across all 35 gathering chapters ch264-464.
  Art = the official Gehrman Sparrow card as a pure SILHOUETTE (user-supplied; `The World.png`),
  because members see 'a hooded black robe... illusory and hazy' and Gehrman Sparrow is not
  created until **ch483** (Vol 3 ch1). Seated in `portrait_priority.members` by joining order
  (after Derrick). Registered in `character_registry.json` so verify_tags accepts him.
  ⏭ **Vol 3+: swap to the FULL `Gehrman Sparrow.jpg`** and keep him a separate row ONLY inside
  gatherings (rule in `TAGGING_GUIDE.md`). All 35 chapters re-rendered + all 5 parts
  re-concatenated 2026-09-03 (durations unchanged); ch461 s3 now sits AT the 9-portrait cap.
- **2026-09-05 SOEST INSTALLED (`*` reference, user-supplied).** Leonard Mitchell's team leader
  (ch408 L61 "The middle-aged man named Soest"); 22:38 of screen time across ch408, 409, 421,
  424, 426, 429 -- another casualty of the scene-count ranking in `build_character_report.py`.
  Non-official art, so `mark_depiction.py` stamped the white `*`; his `character_map.json` note
  records that the text says middle-aged while the reference reads much younger. All 11 blocks
  rebuilt, the 6 chapters re-rendered `--force`, parts 4 + 5 re-concatenated `--force`, Vol-2
  pack regenerated. Verified 2026-09-05: frame grabs of ch424 s2 + ch429 s3 show the `*` portrait;
  staleness check clean on all 5 parts; durations unchanged (10:49:10 / 10:53:01 / 10:50:06 /
  10:46:40 / 10:51:58). **Nine portraits added over 2026-09-03/05** (The World, Eye of Wisdom,
  Mr. Door, Zaratul replaced, Daisy, God of Combat, Colin Iliad, Lovia, Soest); the user's
  outstanding re-check list is now **41 chapters** in `VOL2_OUTSTANDING_REVIEW.md`.
- **2026-09-05 LEONARD MITCHELL PINNED TO `portrait_priority.members`** (user ruling: he is the POV
  lead of his own chapters and a future Tarot seat). Appended LAST in `members`, which is also his
  joining order, so nothing has to move when he is actually seated. He shares **no** Vol-2 frame
  with a seated member, so in Volume 2 this only reorders him against Soest/Daly/Ikanser: exactly
  **3 scenes** changed -- ch408 s2, ch409 s2, ch429 s3 (Soest had been leading). Re-rendered
  `--force`, parts 4 + 5 re-concatenated `--force`, pack regenerated.
  ⚠ **The same rule reorders 25 VOLUME-1 chapters** (17, 45, 46, 71-77, 97, 105, 106, 109, 122-125,
  165, 204, 205, 207-209, 211) because Leonard now outranks **Dunn Smith** -- his own captain -- plus
  Megose, Trissy and the Moretti siblings. Those chapter MP4s were re-rendered so the masters stay
  truthful to the data, but **the four Volume-1 part files were deliberately NOT re-concatenated**:
  Volume 1 ships as-is and is not being re-uploaded, so a Vol-1 staleness check is EXPECTED to
  report those parts as older than their chapters. If Volume 1 is ever revisited, decide first
  whether Dunn Smith should outrank Leonard in the Book-1 Nighthawks scenes.
- **2026-09-05 VOLUME 2 PIXEL-AUDITED END TO END — 838/838 scenes correct, 0 mismatches.**
  For every scene of ch214-482 the real frame was decoded out of `Chapter_N.mp4` and pixel-compared
  against the frame the current block data resolves to (chapter-number overlay masked; worst
  matching deviation 1.37/255 = encoder noise). All five concatenated parts spot-checked the same
  way at a chapter marker deep inside each. **Volume 2 needs no further rendering.**
  ⚠ **DO NOT trust frame-PNG mtimes as a staleness signal.** `compose_frames.ensure()` writes only
  `if not out.exists()`, so a PNG's mtime is its CREATION time. After the 2026-09-03 cache clear the
  frames were rebuilt at 14:38-14:41 from identical inputs, which makes a naive
  "frame newer than MP4" check flag **209 of 269 Vol-2 chapters as stale when none of them are**.
  The pixel comparison above is the real check; chapter-mtime-vs-part-mtime is still valid for
  catching un-re-concatenated parts.
- **2026-09-06 THUMBNAIL TESTS READ + VOL-2 PACKS ADJUSTED + OUTPUT RE-LAID-OUT.** Full write-up in
  `character_scene_video/THUMBNAIL_TEST_ANALYSIS.md`. Daily Studio numbers (Aug 27-Sep 5) for the 4 Vol-1
  parts: launch-day CTR is noise (1000+ Browse impressions at 0.8-1.7%); post-launch the new concepts run
  ~2x the template (P1 3.6% vs P2/P3/P4 1.5/0.3/2.0% in the same window); **P2 jumped 1.5% -> 5.3% when its
  bigface test started while P3's dark bigface got 0 clicks on 180 impressions** -- face-panel brightness
  (121 vs 49 /255) is the tell. All 4 tests are running (user started P2-P4 ~Sep 2/3) but the channel is
  impression-starved (~60-100/day/part) so YouTube will likely end them "no clear winner" -- **pick the
  winner manually when each ends, or Studio reverts P1 to the OLD template.** Applied to Vol 2: P4 (48) and
  P5 (64) bigfaces are as dark as the failing Vol-1 P3, P2 mid (90) -> built `varD_bright` for P2/P4/P5
  (lifted panel, tighter face, warm glow); upload P1/P3 with varA, P2/P4/P5 with varD, test the rest.
  Packs regenerated (both volumes): `make_upload_pack.py` now writes the rewritten line 1 that Vol 1 has
  used live since 08-29; Vol 2 overrides the bridge line ("Season 2 adapts THIS volume") and its pinned
  comment cross-links the Vol-1 playlist (`upload_meta.json` -> `volumes.2.bridge_line` /
  `pinned_extra_lines`). Titles/tags unchanged. **Output layout is now by part** (see Engine layout):
  571 files moved by a scratchpad script, nothing deleted; 43 h Vol-1 single upload parked in `_legacy/`.
  All four path-aware scripts verified on the new tree (`--plan`, pack, thumbnail, ad-hoc-range refusal).
- **2026-09-12 TESTS RE-READ (through Sep 10): still NO per-variant data on any of the 4; P1 ends ~Sep 13,
  P2-P4 ~Sep 17, all will end "no clear winner".** Whole-test-window CTR vs template: P2 1.3% -> 3.4%
  (real), P3 0.4% -> 3.3% but every click is Sep 7-10 with Playlists now 52.6% of its traffic (P2's
  viewers binge-continuing, not thumbnail clicks), P4 too few impressions, P1 drifting 3.7% -> 2.2%.
  Recommendation recorded in `THUMBNAIL_TEST_ANALYSIS.md` s6: stop waiting, set thumbnails by hand when
  each test ends (P2-P4 varA bigface, P1 varB faces), let Vol 2's launch run the only resolvable test
  (varD_bright vs varA on P2/P4/P5). **Volume 3 (ch483-732, `Volume_3_Traveler`) is staged upstream:**
  250 chapters of text + 250 MP3s exist, nothing aligned or tagged — ready to start at recipe step 3.
- **2026-09-18 CAITLYN HALL INSTALLED (`*` fan art, user-supplied: Audrey with her mother on the ballroom
  floor; uncropped per standing preference, so Audrey appears in the card too).** Alias `Caitlyn`/`Lady
  Caitlyn`/`Countess Hall`. All 12 blocks rebuilt: 4 chapters changed -- ch343 s5, ch472 s1, ch482 s3 (Vol 2)
  + ch513 (Vol 3, not rendered yet). The three Vol-2 chapters re-rendered `--force`, parts 3 + 5
  re-concatenated `--force` (durations unchanged 10:50:06 / 10:51:58), pack regenerated, ch482 frame-grab
  verified, staleness 0 on all 5 parts. Review list now 44 chapters.
- **2026-09-18 KASLANA + ESCALANTE INSTALLED (`*` references, user-supplied; Kaslana's 2026-08-28
  hard-decline reversed by the user).** Kaslana: 11 chapters (299,301,305,337,413-416,418-420), parts 2-4
  re-concatenated. Escalante: 11 chapters (339,356,368,388,405,417,418,444,449,450,471), parts 3-5
  re-concatenated. Both `--force`, durations unchanged, packs regenerated, frame-grabs verified (ch414 s1,
  ch339 s3), staleness 0 on all 5 parts. Note Escalante's reference reads adult; the text calls her
  baby-faced. Review list now 66 chapters (`VOL2_OUTSTANDING_REVIEW.md`).
- **2026-09-18 CAPIM INSTALLED (`*` reference).** ch377-380 (the Hero Bandit raid) re-rendered, part 4
  re-concatenated, pack regenerated, ch378 frame-grab verified, staleness 0. Harras/Katy/Parker still blank.
- **2026-09-18 STUART INSTALLED (`*` reference, transparent PNG composited onto the frame backdrop).**
  10 chapters (299,300,301,305,337,338,370,371,413,414) re-rendered, parts 2-4 re-concatenated, pack
  regenerated, ch299 s1 frame-grab verified, staleness 0. Alias `Ian` -> `Ian Wright` added (page-literal
  tag vs registry name). Six `*` references installed today: Caitlyn Hall, Kaslana, Escalante, Capim, Stuart.
  ⚠ Kaslana's art is SQUARE (1200x1200): in a row with tall cards the aspect-aware layout gives her ~2.5x
  their width. Crop to portrait aspect if that reads wrong.
- **2026-09-18 HORAMICK HAYDN INSTALLED (`*` reference).** ch324,446,447,448 re-rendered, parts 3 + 5
  re-concatenated (part 5 now 10:52:01, +3 s from cut rounding; markers regenerated), ch447 s2 frame-grab
  verified (the Amon reveal now shows Horamick turning the frame), staleness 0. Vol 3 ch491/493 pick him up.
- **2026-09-18 HANDOFF (pre-compaction).** `verify_render.py` added and run on Vol 2: **`214 482` -> 183 frames 0 stale, 838/838 scenes match,
  0 stale parts, CLEAN** (report `projects/lotm_book1/verify_vol2_2026-09-18.json`) -- see STATUS.md
  top block and for Vol 3 block 11 state (tagged, verified, NOT rendered; needs
  `upload_meta.json` volume 3 entry + portrait decisions first). Six `*` references installed today.
  ⏭ **NEXT ACTION: manual Studio upload of Volume 2's 5 parts** (files in
  `Volume_2_Faceless/parts/Part_K_chAAA-BBB/`; thumbnail choice per part in the analysis doc). **Volume 1 will NOT be
  re-uploaded (user decision 2026-09-03)** — it stays live with its original frames; its local
  masters carry the new layout but that is not shipping. All future changes are Vol 2+ only.
- **2026-10-02 PRE-UPLOAD PACK REVIEW (Vol 2).** Part 2's hook described ch264-266 (which are in Part 1)
  -> rewritten in `upload_meta.json` + Part 2 pack regenerated. `playlist_vol02.txt` claimed the Fool's
  identity is no secret to the gathering by vol end (false) -> fixed. Everything else checked OK: titles
  89/100, descriptions 3.7k/5k, no `<>`, markers 0:00-first, tags 380/500. API snapshot: Vol-1 parts
  433/107/63/186 views in 35 days; per-chapter Vol-2 playlist (`PLV2gvMHy77hrwY_XlTOU8dvcEM92uigRM`)
  holds 43.3k views; Vol-1 parts sit at the BOTTOM (pos 214-217) of the per-chapter Vol-1 playlist.
