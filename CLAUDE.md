# CLAUDE.md

## Active Project Scope
- Current active project is `lom_book2_coi`.
- Unless explicitly stated otherwise, all commands and status updates for:
  - audio generation
  - video generation
  - YouTube uploads
  refer only to `lom_book2_coi`.

## Agent context (how this file is loaded)
- **Cursor:** `.cursor/rules/claude-context.mdc` has `alwaysApply: true` and requires every assistant turn to read `CLAUDE.md` from the repo root before tools or substantive changes. Do not rely on memory from earlier turns—re-read each message.
- **To set up on another machine or repo:** (1) add `CLAUDE.md` at the repository root with project scope, commands, and progress log; (2) add `.cursor/rules/claude-context.mdc` (or equivalent) with `alwaysApply: true` pointing at that file; (3) keep the progress log updated after pipeline runs.
- **Claude Code / other tools:** If they do not auto-load this file, paste or `@`-reference `CLAUDE.md` at session start and after large progress changes.

## Instructions
- Read this file at the start of **each user message** (see **Agent context** above), not only the first message in a session.
- Do not read `.env` or secret credential files.
- Keep changes scoped to the requested task.
- Prefer dry-run before full processing when touching pipeline behavior.
- If deleting files/folders, ask for permission first.
- After every run command that affects outputs/uploads, update "Current Progress Log" in this file immediately.
- Use the YouTube API to read most recent uploads when upload status needs verification or refresh.

## The 3-Step Workflow (audio → video → upload)
> Always run from the repository root (`pdf-reader`). Default project is `lom_book2_coi`, so the examples omit it where the script defaults to it. Replace `N-M` with the chapter range you want.

### Step 1 — Create AUDIO (Azure TTS)  → `D:/PDFReader/lom_book2_coi_output/Volume_*/*.mp3`
- `python tts_pipeline/scripts/process_project.py --project lom_book2_coi --dry-run --max-chapters 5`
  - **Safe validation pass** (no Azure billing). Run this first when unsure.
- `python tts_pipeline/scripts/process_project.py --project lom_book2_coi --chapters N-M`
  - Generate audio for a chapter range. Single chapter = `--chapters 604`.
- `python tts_pipeline/scripts/process_project.py --project lom_book2_coi --continue 10`
  - Generate audio for the **next 10 chapters** from where you left off (file-based tracking).
- `python tts_pipeline/scripts/process_project.py --project lom_book2_coi`
  - Resume/continue normal processing.

### Step 2 — Create VIDEO (from existing audio)  → `D:/PDFReader/lom_book2_coi_output/video/Volume_*/*.mp4`
- `python tts_pipeline/scripts/create_videos.py --project lom_book2_coi --chapters N-M`
  - **Standalone video creation** from already-generated `.mp3` files. Use this to clear the video backlog (audio is ahead of video).
- `python tts_pipeline/scripts/create_videos.py --project lom_book2_coi --chapters N --preview`
  - Preview settings for one chapter without writing files.
- `python tts_pipeline/scripts/create_videos.py --project lom_book2_coi --resume`
  - Resume an interrupted video batch.
- **One-shot audio+video:** add `--create-videos` to the Step 1 command to make the video right after each chapter's audio:
  - `python tts_pipeline/scripts/process_project.py --project lom_book2_coi --chapters N-M --create-videos`

### Step 3 — UPLOAD to YouTube  → tracker `D:/PDFReader/lom_book2_coi_output/youtube_progress.json`
> **Run only ONE upload job at a time** (two = duplicate uploads). Quota-safe pace ≈ 6 uploads/hour (~10 min apart).
- `python upload_queue.py --project lom_book2_coi --limit=0`
  - Auth + tracker check only (no uploads). Use to confirm OAuth and see the next pending chapter.
- `python upload_queue.py --project lom_book2_coi --yes --limit=1`
  - Upload the **next single** pending chapter (use when fixing a gap).
- `python upload_queue.py --project lom_book2_coi --yes --limit=10`
  - Upload the **next 10** pending chapters in order.
- **OAuth:** if prompted, complete Google sign-in in the browser (creates/refreshes `token.json` in repo root). Nothing appears in YouTube Studio until auth finishes.
- YouTube titles come from the **`Chapter N: <title>`** line in the formatted source text (`input_directory`), not the video filename.
- Config: `tts_pipeline/config/projects/lom_book2_coi/youtube_config.json`

### Step 4 — END SCREENS (next-chapter links)  → run AFTER a fully successful upload
> Standing rule: **whenever the user asks to upload videos, once the whole batch has uploaded successfully (Step 3 reports `Failed: 0`), proceed to add end screens.** If ANY video in the batch failed to upload, do NOT run this step — fix the upload first. Tool: `youtube_endscreen.py` (drives YouTube Studio UI via Playwright; end screens are not in the Data API).
- **Range rule (include the previous boundary chapter):** for an uploaded batch of chapters **N–M**, run end screens on **sources `(N-1)` through `(M-1)`**. This makes the previous last chapter `(N-1)` link to the first new chapter `N`, and each new chapter link to the next. The newest chapter `M` is intentionally **left until the next batch** (its target `M+1` isn't uploaded yet).
  - **Example:** user uploads the next 10 = **261–270** → run end screens on **260–269** (`260→261`, `261→262`, … `269→270`). Chapter **270** waits for the following batch.
- **Command:** `python youtube_endscreen.py --project lom_book2_coi --chapters (N-1)-(M-1) --connect-port 9222 --yes`
  - e.g. after uploading 261–270: `python youtube_endscreen.py --project lom_book2_coi --chapters 260-269 --connect-port 9222 --yes`
  - Pre-check offline first (no browser): add `--plan-only`. Verify one before a big batch: `--chapters (N-1)-(N-1)` then `--dry-run`.
- **Style (matches the manual videos ch.249 and below):** Subscribe element left-middle + next-chapter Video element right-middle. Implemented by importing the layout from `--style-from 249` (default) and retargeting the video element. Don't change unless the user asks.
- **Login / browser prereq (Google blocks automated sign-in):** the tool ATTACHES to a real Chrome on `--connect-port 9222`. Start it first; the logged-in profile persists at `%USERPROFILE%\yt-studio-login` (account = **breadmoretti@gmail.com**, which manages the channel — NOT paolo.gene).
  - Launch: `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\yt-studio-login" "https://studio.youtube.com/"`
  - If that profile is ever logged out / missing: sign in FIRST in a normal Chrome with a custom `--user-data-dir` and **no** debug port (Google allows it), then relaunch the same dir WITH the port. (App-Bound Encryption blocks copying a logged-in profile; a Playwright-launched browser is blocked at sign-in.)
- **Safety guard:** unlisted-only — the tool reads `privacyStatus` via the Data API and skips public/private videos. If the boundary chapter `(N-1)` is already **public**, include it explicitly with `--allow-public-chapters (N-1)`.
- **Idempotent:** videos that already have an end screen are skipped (no duplicates); rebuilding one requires clearing it manually first.
- Tool lives on branch `feature/youtube-endscreens` (merge to master to use it from the main branch).

### (Setup only) — Extract EPUB → formatted text
- `python epub_to_text/main.py "<path>.epub" -p "lom_book2_coi" -o "formatted_text"`
  - Extracts EPUB to `formatted_text/<project>/Volume_#/…/Chapter_#_….txt` for TTS. Each file begins with two header lines for TTS pauses: `Lord of Mysteries 2: Circle of Inevitability` then `Chapter N: <title>`. Leading body echoes of the title (including nav-style `N Title` / `N: Title` lines) are dropped so they are not read twice by TTS.

### Utility
- `python tts_pipeline/scripts/process_project.py --list-projects` — list available TTS projects.

## Tracking (Audio, Video, Uploads)
- Do not use `tracking/*.json` for progress status updates.
- Keep progress status directly in this file under "Current Progress Log".
- Use local output folder as source of truth for created audio/video counts:
  - `D:/PDFReader/lom_book2_coi_output`
- Use YouTube API (or `youtube_progress.json` when reconciling) for most recent uploaded video.

## TTS project `lom_book2_coi`
- Run `process_project.py` with **current working directory = repository root** (`pdf-reader`). `project.json` uses `input_directory` `formatted_text/lom_book2_coi` so paths resolve under the repo (not `../formatted_text`, which points outside the repo when cwd is the root).
- Config directory: `tts_pipeline/config/projects/lom_book2_coi/` (`project.json`, `processing_config.json`, `video_config.json`).
- `processing_config.json` uses `volume_pattern` `Volume_(\\d+)_` so chapter discovery matches `formatted_text/lom_book2_coi/Volume_N_Name/Chapter_N_*.txt` (not the book1 `N___VOLUME_N___` layout).
- Azure voice file: copy `azure_config.json.example` to `azure_config.json` in that folder (real `azure_config.json` is gitignored under `tts_pipeline/`). Set `AZURE_TTS_SUBSCRIPTION_KEY` and `AZURE_TTS_REGION` in the environment (do not commit secrets).

## YouTube uploads (`lom_book2_coi`)

- **Cwd:** repository root (`pdf-reader`).
- **One job at a time** — never run two `upload_queue.py` processes (causes duplicate uploads).
- **Volume 2 playlist (canonical):** [LOM2 COI - Volume 2: Lightseeker](https://www.youtube.com/playlist?list=PLV2gvMHy77hrYzC8lxYXCtEp4NArMkh7s) — playlist ID `PLV2gvMHy77hrYzC8lxYXCtEp4NArMkh7s` (set in `youtube_config.json` → `playlists.playlist_ids["2"]`).
- **Video folder for vol. 2:** `D:/PDFReader/lom_book2_coi_output/video/Volume_2_Lightseeker/` (`volume_name` = `Lightseeker` for playlist title formatting).
- **Do not use** wrong auto-created playlist `PLV2gvMHy77hrh1HeiBECpJ61Smbgg5_S6` (from old `LOTM 2 - Volume …` name template).
  - ✅ **Fixed:** `get_playlist_id()` now returns the configured `playlists.playlist_ids["2"]` when `create_per_volume` is true, so new Volume-2 uploads (ch. 241+) go to the correct Lightseeker playlist. (Commit the working-copy changes to `youtube_uploader.py` + `youtube_config.json`.)
  - ⚠️ **Cleanup left:** the 30 chapters already uploaded to the wrong playlist (incl. 236–240) must be **moved manually** in YouTube Studio — code change does not relocate existing videos.
- **Tracker:** `D:/PDFReader/lom_book2_coi_output/youtube_progress.json`

## Path and Environment Conventions
- Active local output root base is `D:/PDFReader/`.
- Optional local convention for portability:
  - `.env` key name: `LOCAL_OUTPUT_ROOT`
  - Example value: `D:/PDFReader/`
- Per-project outputs should append project-specific folders (example: `D:/PDFReader/lom_book2_coi_output`).
- Note: current runtime uses project config files for output paths; keep `.env` and config aligned unless code is updated to consume `LOCAL_OUTPUT_ROOT`.

## Repo Audit (done 2026-06-14)
- **Deleted** (dead/orphan, recover from git if ever needed): `tts_pipeline/api/azure_tts_client_old.py`, `upload_test.py`, `tts_pipeline/scripts/fix_progress_tracking_v2.py`, `tts_pipeline/scripts/check_project_status_v2.py`.
- **Kept:** `tts_pipeline/scripts/check_project_status.py` (the referenced status check) and `generate_upload_csv.py` (manual-upload fallback).
- Stale docs still to reconcile with this file: `tts_pipeline/TTS_PROGRESS.md`, `tts_pipeline/SCRIPTS_GUIDE.md`, root `README.md`.

## Upload Readiness (next session) — checked 2026-06-15
**You can upload immediately — just run Step 3.** Prereqs verified:
- ✅ No upload process running (safe to start one).
- ✅ `token.json` present & fresh (used 2026-06-14) — OAuth should not re-prompt; if it does, finish the browser sign-in.
- ✅ Videos for ch. **251–350 all exist** (100 ready). Next pending = **251**.
- **Command:** `python upload_queue.py --project lom_book2_coi --yes --limit=10` (uploads 251–260). Optional pre-check: `--limit=0`.
- ⚠️ **Volume boundary at ch. 264:** ch. 251–263 → Volume 2 (Lightseeker, pinned). Ch. **264+ → Volume 3 (Conspirer)**, which is NOT pinned, so the first ch.264 upload will **auto-create** a `"LOM2 COI - Volume 3: Conspirer"` playlist (intended). **After that upload, capture the new playlist ID into** `youtube_config.json → playlists.playlist_ids["3"]` so later vol-3 uploads reuse it instead of re-searching by name.
- After any batch, update the progress table below (and "next to upload").

## Current Progress Log
Update this section during/after processing runs.

### lom_book2_coi — verified against disk + tracker on 2026-06-14
- Output folder: `D:/PDFReader/lom_book2_coi_output`
- **Pipeline position (each stage feeds the next):**
  | Stage | Files done | Highest chapter | Next action |
  |---|---|---|---|
  | Audio (`.mp3`) | 603 | 603 | generate ch. **604+** |
  | Video (`.mp4`) | 351 | 350 | create ch. **351+** (audio is ~253 ch. ahead) |
  | Upload | 260 | 260 (no gaps) | upload ch. **261** |
- **Audio:** 603 files (V1=109, V2=154, V3=231, V4=109). Last run `2026-05-12` — ch. `603` (`Volume_4_Sinner/Chapter_603_Organs_Again.mp3`).
- **Video:** 351 files through ch. 350 (V1=110, V2=154, V3=87, V4=**0**). Big backlog: ch. 351–603 have audio but no video; `Volume_4_Sinner` has none yet.
- **Uploads:** 260 entries, chapters **1–260 fully uploaded with NO gaps**.
- **Next to upload:** chapter `261` (then 262, 263 …). Videos exist through ch. 350, so ~90 chapters (261–350) are ready to upload right now. ⚠️ Volume boundary at ch. 264: ch. 261–263 → Volume 2 (Lightseeker); ch. **264+ → Volume 3 (Conspirer)** which auto-creates a new playlist — capture that ID into `youtube_config.json → playlists.playlist_ids["3"]` after the first ch.264 upload.
- Most recent upload: `2026-06-18` — batch of ch. **251–260** uploaded (10/10 success, 0 failed), all routed to the canonical Lightseeker playlist `PLV2gvMHy77hrYzC8lxYXCtEp4NArMkh7s`. Video IDs: 251 `NAcRnOcfezM`, 252 `7aAfZhRt5kU`, 253 `Qn_If9Ocw9U`, 254 `N92STG7KL5k`, 255 `OtMSCWY4Ro8`, 256 `NIgL_FPrWsU`, 257 `FsHhzue1ZBo`, 258 `slJubVTzF3I`, 259 `emfmO9UGyWo`, 260 `XVJw7wvQiXE`. (Each logged a benign "Video may not be in playlist" warning — verify playlist membership in YouTube Studio if needed.)
- **Playlist note:** the older uploads **236–240** (and 25 earlier ones) are still on the WRONG playlist `PLV2gvMHy77hrh1HeiBECpJ61Smbgg5_S6` — move them manually in YouTube Studio. Everything from 241 on is correct.
- Notes: ch. **230–232** may have duplicate uploads on channel from overlapping runs. Ch. 215 title may still need a manual fix on YouTube.
- EPUB formatted chapters (repo): `1180` `.txt` files under `formatted_text/lom_book2_coi` in **8** volume folders (from `epub_to_text/lom_book2_coi/epub/Circle of Inevitability.epub` + `epub_to_text/lom_book2_coi/volume_map.json`)
