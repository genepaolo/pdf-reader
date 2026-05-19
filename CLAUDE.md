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

## Commands and What They Do
- `python tts_pipeline/scripts/process_project.py --list-projects`
  - Lists available TTS projects.
- `python tts_pipeline/scripts/process_project.py --project lom_book2_coi --dry-run --max-chapters 5`
  - Runs a safe validation pass without Azure billing.
- `python tts_pipeline/scripts/process_project.py --project lom_book2_coi --chapters 1-10`
  - Processes a chapter range for the selected project.
- `python tts_pipeline/scripts/process_project.py --project lom_book2_coi --chapters 601`
  - Processes a single chapter (same as `601-601`).
- `python tts_pipeline/scripts/process_project.py --project lom_book2_coi`
  - Resumes/continues normal project processing.
- `python generate_upload_csv.py --project lom_book2_coi`
  - Generates manual YouTube upload metadata text file for a project.
- `python upload_queue.py --project lom_book2_coi --yes --limit=5`
  - Attempts quota-safe automated YouTube uploads for a project. YouTube titles use the **`Chapter N: <title>`** line from each project’s formatted source text (`input_directory` in `project.json`), not the video filename—so apostrophes and long titles stay correct for any project.
- `python epub_to_text/main.py "<path>.epub" -p "lom_book2_coi" -o "formatted_text"`
  - Extracts EPUB to `formatted_text/<project>/Volume_#/…/Chapter_#_….txt` for TTS. Each file begins with two header lines for TTS pauses: `Lord of Mysteries 2: Circle of Inevitability` then `Chapter N: <title>`. Leading body echoes of the title (including nav-style `N Title` / `N: Title` lines) are dropped so they are not read twice by TTS.

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

## Path and Environment Conventions
- Active local output root base is `D:/PDFReader/`.
- Optional local convention for portability:
  - `.env` key name: `LOCAL_OUTPUT_ROOT`
  - Example value: `D:/PDFReader/`
- Per-project outputs should append project-specific folders (example: `D:/PDFReader/lom_book2_coi_output`).
- Note: current runtime uses project config files for output paths; keep `.env` and config aligned unless code is updated to consume `LOCAL_OUTPUT_ROOT`.

## Current Progress Log
Update this section during/after processing runs.

### lom_book2_coi
- Output folder: `D:/PDFReader/lom_book2_coi_output`
- Audio files created: `603`
- Last TTS run: `2026-05-12` — chapter `603` (`Volume_4_Sinner/Chapter_603_Organs_Again.mp3`, batch synthesis ~34s)
- Video files created: `351`
- Uploaded videos: `212` (chapters 1–212 per `youtube_progress.json`)
- Most recent upload timestamp: `2026-05-13T03:44:45.244074`
- Most recent uploaded file: `Chapter_212_Actor.mp4` (`https://youtube.com/watch?v=whM3ONkAW80`)
- EPUB formatted chapters (repo): `1180` `.txt` files under `formatted_text/lom_book2_coi` in **8** volume folders (from `epub_to_text/lom_book2_coi/epub/Circle of Inevitability.epub` + `epub_to_text/lom_book2_coi/volume_map.json`)
