# CLAUDE.md

## Active Project Scope
- Active project is `lom_book2_coi`; unless stated otherwise, audio/video/YouTube commands and status mean it.
- **Second workstream:** `character_scene_video` (Book 1 per-scene portrait videos) — current state in
  the section below; full history in `character_scene_video/STATUS.md`.
- **Third (planned, not started):** replace Azure TTS with local VoiceStudio — `VOICESTUDIO_TTS_SWAP_PLAN.md`.
  Azure stays default (`tts_engine: azure`). Never commit clone weights or reference WAVs.
- Older narrative (progress logs, 2026-09 repair notes, moved from this file 2026-10-07): `docs/history.md`.

## Instructions
- Do not read `.env` or secret credential files.
- Keep changes scoped to the requested task; prefer dry-run before full processing.
- If deleting files/folders, ask for permission first.
- After every run that affects outputs/uploads, update the progress table below immediately.
- Use the YouTube API to verify recent uploads when status needs confirmation.
- ⚠️ Run all scripts with `py -3.12`, not `python` (PATH `python` = 3.11, missing `dotenv`/`google-api-python-client`).

---

## character_scene_video (Book 1 — separate workstream)
> Per-scene character-portrait videos for **Book 1 (LOTM)**. Design: `character_scene_video/DESIGN.md`.
> Session handoff + full history: `character_scene_video/STATUS.md`. Tagging rules: `TAGGING_GUIDE.md`.

### Current state (2026-10-07)
- **Vol 1 (ch1–213): uploaded, 4 parts public** (`sQ94crQVoAQ` / `AfBLteZ9nfU` / `Qi3hZkRr_j0` / `8lha69vkmCE`);
  YouTube caps uploads at 12 h. Not being re-uploaded.
- **Vol 2 (ch214–482): rendered, packed, `verify_render.py 214 482` CLEAN.** 5 parts in `Volume_2_Faceless/parts/`.
  ⏭ **Next: manual Studio upload** (thumbnail picks in `THUMBNAIL_TEST_ANALYSIS.md`).
- **Vol 3 (ch483+): block 11 tagged + verified, NOT rendered**; needs `upload_meta.json` volume-3 entry + portrait decisions (STATUS.md top block).
- After ANY portrait install rebuild ALL blocks, then `compose_frames.py`. `*` = artist depiction. Sharon ≠ Sharron.

### Engine layout (run everything with `py -3.12` from repo root)
- Engine + per-project config: `character_scene_video/projects/<name>/project.json` (template `_TEMPLATE/`);
  all scripts take `--project` (default `lotm_book1`); data (tags, align, timelines, decisions) in `projects/<name>/`.
- **Output is BY VOLUME, then BY PART:** `<video_out_dir>/<Volume_dir>/chapters/Chapter_N.mp4` (masters) ·
  `parts/Part_K_chAAA-BBB/` (upload part: mp4 + descriptions + pinned comment + tags + `thumbnails/`).
  **K = the part's list position under its volume in `upload_meta.json`** (add the range there first);
  ranges may not cross a volume boundary. Full layout/helpers: `docs/history.md`.
- Alignment is NOT aeneas/WhisperX: Azure-TTS audio of known text matched to ffmpeg pauses with a DP.

### BLOCK RECIPE (replace A B with the chapter range, e.g. 214 263)
Steps 1–2 are content work (new blocks only); 3–10 are mechanical.
1. **Tag scenes**: read each chapter, write `projects/lotm_book1/timelines/scenes/ch_N.json` per
   `TAGGING_GUIDE.md` (text-literal names); add boundary entries to `continuity.json` (incl.
   boundary A-1); new aliases → `name_aliases.json`.
   ⚠️ Dream/vision/memory figures are NOT present, and Roselle diary-reading scenes are split around the
   reading — both rules in `TAGGING_GUIDE.md` (read it before tagging).
2. **Portrait decisions**: after step 5, `build_character_report.py A B` → record yes/no in
   `portrait_decisions.json`; source images (`fetch_named_portraits.py` or user-supplied). After
   ANY portrait change: rerun `build_block.py`, THEN `compose_frames.py`.
3-7. (all `py -3.12 character_scene_video/<script> A B`) `align_chapter.py` → `verify_alignment.py` (must PASS) →
   `build_block.py` → `verify_tags.py` (must be 0 to fix) → `compose_frames.py --block --contact-sheet` (eyeball)
8. `py -3.12 character_scene_video/render_chapter.py A B`       # `--preview` first; spot-check
   ⚠ **Frames are cached by cast+order+rims and `LAYOUT_VERSION` (compose_frames.py). If you
   change LAYOUT (rows_for/_fit_row/margins/rims) you MUST bump LAYOUT_VERSION, else every
   cached PNG is reused and the re-render changes nothing.**
   ⚠ **re-renders MUST pass `--force`** — otherwise existing MP4s are SKIPPED while the log still looks
   normal (bit us 2026-08-29). Verify with a frame grab, not the log — or better, **`py -3.12 character_scene_video/verify_render.py A B`**
   (2026-09-18) pixel-compares every scene of every chapter MP4 against the frame the block data
   resolves to, checks the frame cache and flags stale parts. Exit 0 = CLEAN, else it prints
   `chapters_to_rerender` / stale PNGs / stale parts (`--json PATH`, `--frames` = cache-only).
   **This is the only accepted proof that a range is rendered.**
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
> Run from repo root. Replace `N-M` with the chapter range. Full prior detail: `docs/history.md`.

### Step 1 — AUDIO (Azure TTS) → `D:/PDFReader/lom_book2_coi_output/Volume_*/*.mp3`
- `py -3.12 tts_pipeline/scripts/process_project.py --project lom_book2_coi --chapters N-M` (safe check: `--dry-run --max-chapters 5`;
  next 10: `--continue 10`; resume: no flag; audio+video in one go: `--create-videos`).

### Step 2 — VIDEO → `D:/PDFReader/lom_book2_coi_output/video/Volume_*/*.mp4`
- `py -3.12 tts_pipeline/scripts/create_videos.py --project lom_book2_coi --chapters N-M` (`--resume`; encoder `h264_amf`).
  `--preview` does NOT validate audio/art (simulated success).

### Step 3 — UPLOAD → tracker `D:/PDFReader/lom_book2_coi_output/youtube_progress.json`
> **ONE upload job at a time** (two = duplicates). Pace ≈ 6/hour (the script paces itself).
- Tracker check: `py -3.12 upload_queue.py --project lom_book2_coi --limit=0` · upload: `... --yes --limit=1|10`
- OAuth sign-in as **breadmoretti@gmail.com** if prompted (`token.json` in repo root). Titles come from the
  `Chapter N: <title>` line in the source text. Config: `tts_pipeline/config/projects/lom_book2_coi/youtube_config.json`.
- ⚠️ NO retry: a failed chapter leaves a hole; fix in order before the next batch (delete out-of-order uploads only with approval).
  `Video may not be in playlist` warnings are an API-listing quirk, not data loss.
- ⚠️ **After ANY killed/aborted upload run, check the channel's newest uploads for an UNTRACKED video before
  restarting, or you create a duplicate.** Background jobs are killed at ~30 min (2026-09-30): use small `--limit`
  chunks or a foreground shell. Stdout is block-buffered when redirected: judge progress by `youtube_progress.json`.

### Step 4 — END SCREENS (run AFTER a fully successful upload batch; skip if ANY upload failed)
> Tool: `youtube_endscreen.py` (Playwright over Studio; idempotent; `--replace` not implemented).
- **Range rule:** for uploaded batch N–M run sources **(N-1)–(M-1)**; newest chapter M waits for the next batch.
- **Chrome prereq:** assume down; `curl http://127.0.0.1:9222/json/version`, if silent relaunch:
  `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\yt-studio-login" "https://studio.youtube.com/"`
  (logged out: sign in first in normal Chrome with that profile, no debug port, then relaunch).
- **Recipe (canonical):** plan first, then run, always with `-u` and the public-chapter override:
  `py -3.12 -u youtube_endscreen.py --project lom_book2_coi --chapters X-Y --connect-port 9222 --plan-only`
  `py -3.12 -u youtube_endscreen.py --project lom_book2_coi --chapters X-Y --connect-port 9222 --yes --allow-public-chapters $(seq -s, X Y)`
- ⚠️ **`--allow-public-chapters` is mandatory:** uploads go up unlisted but flip public in under a day, and
  without the flag a run is a SILENT NO-OP (`Eligible (unlisted): 0 / N`). Check the plan output's eligible count.
- Re-running is the safe verify; don't pipe through `tail`. Style comes from ch249 (`--style-from`), don't change.

### Chapter background art (per-project)
> `tts_pipeline/config/projects/<project>/portrait_mapping.json` maps chapter-range → filename;
- `lom_book2_coi` art: parts `coi_v1..coi_v11` mapped through ch884 (boundary list in `docs/history.md`);
  ✅ **ch885+ has NO art yet.** `lotm_book1` mapping complete.

### Setup / utility
- EPUB → text: `py -3.12 epub_to_text/main.py "<path>.epub" -p "<project>" -o "formatted_text"`
  (two header lines per file for TTS pauses; drops body title echoes).
- List projects: `py -3.12 tts_pipeline/scripts/process_project.py --list-projects`
- Tests: `cd tts_pipeline && py -3.12 -m pytest tests/ -q`.

## Config & path conventions
- Output root `D:/PDFReader/<project>_output`; `process_project.py` must run with cwd = repo root.
- COI config: `tts_pipeline/config/projects/lom_book2_coi/` (`volume_pattern` = `Volume_(\\d+)_`).
- Azure: `azure_config.json` (gitignored, from `.example`); `AZURE_TTS_SUBSCRIPTION_KEY` / `AZURE_TTS_REGION` in env; never commit secrets.
- Naming quirks (don't "fix"): book1 audio keeps legacy `N___VOLUME_N___` folders; COI text says `Volume_2_Light_Chaser`, outputs `Volume_2_Lightseeker`.

## YouTube (`lom_book2_coi`)
- Channel account: **breadmoretti@gmail.com** (NOT paolo.gene). Playlists pinned in `youtube_config.json → playlists.playlist_ids`:
  V1 Nightmare `PLV2gvMHy77hpWltp0KalQNL8JPkqBKWQu` (ch1–109) · V2 Lightseeker `PLV2gvMHy77hrYzC8lxYXCtEp4NArMkh7s`
  (110–263) · V3 Conspirer `PLV2gvMHy77hpe3q8VvnIeXK1s-y8sNSpM` (264+). Vol 1 has no `playlist_ids` pin.
- Vol 3 Conspirer holds 2 `Deleted video` rows (`OKRcFKOhBTE`, `IFa7FCbQ4Bs`) — remove in Studio.
- Playlist/tracker/end-screen audit narrative (2026-09-05): `docs/history.md`.

## Current Progress Log

### lom_book2_coi (updated 2026-10-07; last upload 2026-09-30)
| Stage | Done | Highest | Next action |
|---|---|---|---|
| Audio (`.mp3`) | 603 | 603 | generate ch. **604+** |
| Video (`.mp4`) | 601 files (1–600 contiguous) | 600 | create ch. **601–603** |
| Upload | 472 (1–472, no gaps) | 472 | upload ch. **473+** |
- End screens done through 469→470; **470→471 and 471→472 NOT done** — run sources **470–(M-1)** after the next batch.
- Volume boundaries: ch264+ → vol 3 (Conspirer). Ch885+ needs background art before video creation.
- Disk: ~1.17 TB free on D:; ~672 MB/video. Per-batch history: `docs/history.md`, `youtube_progress.json`, git log.

### character_scene_video
See "Current state" above; dated log lives in `character_scene_video/STATUS.md` (History section).
