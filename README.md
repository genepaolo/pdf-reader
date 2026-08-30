# LOTM Audiobook Pipeline (EPUB → TTS → Video → YouTube)

Turns a book EPUB into per-chapter audio, per-chapter YouTube videos, and
managed uploads — organized **per project** (one project = one book).

> **Operational state, progress log, and the exact commands for the active
> project live in [CLAUDE.md](CLAUDE.md).** This README describes the system;
> CLAUDE.md describes what's currently running. Run everything from the repo
> root with `py -3.12` (plain `python` resolves to 3.11 on this machine and
> is missing deps).

## The pipeline

```
EPUB ──[epub_to_text]──► formatted_text/<project>/Volume_N_Name/Chapter_N_Title.txt
                                        │
                        [tts_pipeline process_project.py]  (Azure Batch Synthesis)
                                        ▼
                        D:/PDFReader/<project>_output/Volume_N_Name/Chapter_N_Title.mp3
                                        │
                        [tts_pipeline create_videos.py]  (ffmpeg still-image, art from portrait_mapping.json)
                                        ▼
                        D:/PDFReader/<project>_output/video/Volume_N_Name/Chapter_N_Title.mp4
                                        │
                        [upload_queue.py]  (YouTube Data API, playlist routing)
                                        ▼
                        YouTube channel + [youtube_endscreen.py] next-chapter end screens
```

### Stage 1 — EPUB → formatted text (`epub_to_text/`)

```bash
py -3.12 epub_to_text/main.py "epub_to_text/<project>/epub/<Book>.epub" -p <project> -o formatted_text
```

- Volume boundaries come from `epub_to_text/<project>/volume_map.json`
  (chapter ranges per volume). Inspect first with `--inspect-only`.
- Line 1 of every chapter file = series title (from the EPUB's `dc:title`
  metadata unless `--series-title` is passed); line 2 = `Chapter N: Title`.
  Both lines give the TTS natural pauses; title echoes in the body are dropped.

### Stage 2 — Audio (`tts_pipeline/scripts/process_project.py`)

```bash
py -3.12 tts_pipeline/scripts/process_project.py --project <project> --chapters N-M
py -3.12 tts_pipeline/scripts/process_project.py --list-projects
```

- Azure **Batch Synthesis** API (up to 10k inputs/job). Credentials via env:
  `AZURE_TTS_SUBSCRIPTION_KEY`, `AZURE_TTS_REGION` (see `.env`).
- Progress is **file-based** (`FileBasedProgressTracker` counts actual
  `.mp3`/`.mp4` files) — no database to drift out of sync.
- `--dry-run` validates without billing; `--create-videos` chains Stage 3.

### Stage 3 — Video (`tts_pipeline/scripts/create_videos.py`)

```bash
py -3.12 tts_pipeline/scripts/create_videos.py --project <project> --chapters N-M
```

- Still-image videos (ffmpeg; H.264 encoder auto-probed — hardware if present, libx264 otherwise): one background per chapter,
  chosen by chapter range from
  `tts_pipeline/config/projects/<project>/portrait_mapping.json`.
- Art lives in `tts_pipeline/assets/projects/<project>/backgrounds/`
  (`resized/*_1920x1080.*` copies are what actually get rendered).
- **Adding art:** drop images in `assets/projects/<project>/dropoff/`, run
  `py -3.12 tts_pipeline/scripts/prepare_backgrounds.py --project <project>`,
  then edit the project's `portrait_mapping.json`. Check with `--status`.
  See `tts_pipeline/assets/projects/README.md`.

### Stage 4 — Upload (`upload_queue.py`) and end screens (`youtube_endscreen.py`)

```bash
py -3.12 upload_queue.py --project <project> --yes --limit=10   # next 10 pending
py -3.12 youtube_endscreen.py --project <project> --chapters (N-1)-(M-1) --connect-port 9222 --yes
```

- **One upload job at a time.** Quota-safe pace ≈ 6 uploads/hour.
- Titles come from the `Chapter N: <title>` line of the source text.
- Playlist routing, OAuth notes, end-screen rules and the batch bookkeeping
  are all in [CLAUDE.md](CLAUDE.md) — follow it, it's the operational source
  of truth.

## Per-project layout

```
epub_to_text/<project>/            epub/ + volume_map.json
formatted_text/<project>/          Volume_N_Name/Chapter_N_Title.txt
tts_pipeline/config/projects/<project>/
    project.json                   input/output dirs, metadata
    processing_config.json         patterns, batch settings, video block
    portrait_mapping.json          chapter-range → background image
    youtube_config.json            channel, playlists, templates
    azure_config.json              voice (gitignored; copy the .example)
tts_pipeline/assets/projects/<project>/
    dropoff/                       ← drop new art here
    backgrounds/ (+ resized/)      background images used by videos
D:/PDFReader/<project>_output/     mp3 + video/ mp4 + youtube_progress.json
```

Active projects: `lotm_book1` (complete, 1432 chapters) and `lom_book2_coi`
(in progress — see CLAUDE.md).

## Tests

```bash
cd tts_pipeline && py -3.12 -m pytest tests/ -q
```

Unit + regression + integration (integration skips politely without Azure
credentials). The regression suite pins lotm_book1 discovery at 1432
chapters / 9 volumes and smoke-runs every documented entry point.

## Legacy corners

- `pdf_to_txt/` — the original PDF extraction stage; replaced by
  `epub_to_text` (kept for reference, not part of the flow).
- `character_scene_video/` — separate Book-1 workstream (per-scene character
  portraits); see its own `DESIGN.md`/`STATUS.md`.
- `generate_upload_csv.py` — manual-upload fallback from the pre-API days.
- Historical design docs in `tts_pipeline/` (`*_PLAN.md`) are marked as such.
