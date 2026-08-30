# TTS Pipeline Scripts Guide

> Run everything from the **repo root** with **`py -3.12`** (plain `python`
> is 3.11 here and lacks deps). Active-project commands and the progress log
> are in the root [CLAUDE.md](../CLAUDE.md).

## Entry points (all support `--help`)

| Script | Purpose |
|---|---|
| `scripts/process_project.py` | Audio generation via Azure Batch Synthesis (optionally `--create-videos`) |
| `scripts/create_videos.py` | Standalone video creation from existing mp3s |
| `scripts/prepare_backgrounds.py` | Move dropped-off art into per-project background assets (+1920x1080 resize) |
| `scripts/check_project_status.py` | Report audio/video progress for a project |
| `scripts/format_text_for_tts.py` | (rarely needed) reformat raw text for TTS |
| `../upload_queue.py` | YouTube uploads (repo root) |
| `../youtube_endscreen.py` | End-screen automation (repo root) |

## process_project.py

```bash
py -3.12 tts_pipeline/scripts/process_project.py --list-projects
py -3.12 tts_pipeline/scripts/process_project.py --project <p> --dry-run --max-chapters 5   # safe validation
py -3.12 tts_pipeline/scripts/process_project.py --project <p> --chapters N-M
py -3.12 tts_pipeline/scripts/process_project.py --project <p> --continue 10               # next 10 pending
py -3.12 tts_pipeline/scripts/process_project.py --project <p> --chapters N-M --create-videos
```

Options: `--batch-size`, `--max-chapters`, `--force-mode single|batch`,
`--log-level`. Requires `AZURE_TTS_SUBSCRIPTION_KEY` / `AZURE_TTS_REGION` in
the environment (`.env` is loaded automatically).

## create_videos.py

```bash
py -3.12 tts_pipeline/scripts/create_videos.py --project <p> --chapters N-M
py -3.12 tts_pipeline/scripts/create_videos.py --project <p> --chapters N --preview   # plan only
py -3.12 tts_pipeline/scripts/create_videos.py --project <p> --resume
```

Background art per chapter comes from
`config/projects/<p>/portrait_mapping.json` → files in
`assets/projects/<p>/backgrounds/resized/`. A range mapped to `null` fails
loudly (no silent wrong-book art). `--background-image <path>` overrides the
mapping — **prefer the mapping**; override use is how the COI vol 1–3 source
art got lost.

## prepare_backgrounds.py

```bash
py -3.12 tts_pipeline/scripts/prepare_backgrounds.py --project <p>            # process dropoff/
py -3.12 tts_pipeline/scripts/prepare_backgrounds.py --project <p> --status   # mapping vs files report
```

Flow: drop art in `assets/projects/<p>/dropoff/` → run → edit
`portrait_mapping.json` ranges → `--status` to verify.

## Module layout / imports (matters if you add code)

- Modules inside `tts_pipeline` import each other as `utils.X` / `api.X`.
- Every entry point puts `tts_pipeline/` on `sys.path` (scripts do it
  themselves; root-level scripts insert it explicitly; tests via
  `tests/conftest.py`).
- Do **not** use `from tts_pipeline.utils...` inside the package — that only
  resolves for repo-root entry points and broke both pipeline scripts once
  (fixed 2026-08-10; guarded by `tests/unit/test_process_project.py`).

## Tests

```bash
cd tts_pipeline && py -3.12 -m pytest tests/ -q
```

- `tests/unit/` — component tests + entry-point smoke tests
- `tests/regression/` — lotm_book1 corpus discovery (1432 ch / 9 vols)
- `tests/integration/` — Azure batch flow (skips without credentials)
