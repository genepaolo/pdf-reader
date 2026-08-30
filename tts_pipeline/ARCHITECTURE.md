# TTS Pipeline Architecture

*(Rewritten 2026-08-10 to match the code as it actually is. For commands see
[SCRIPTS_GUIDE.md](SCRIPTS_GUIDE.md); for operational state see the root
[CLAUDE.md](../CLAUDE.md).)*

## Overview

Project-based pipeline that turns `formatted_text/<project>/` chapter files
into audio (Azure **Batch Synthesis**), still-image videos (ffmpeg/NVENC),
and YouTube uploads. Each book is a **project**: its config lives in
`config/projects/<project>/`, its art in `assets/projects/<project>/`, its
outputs in `D:/PDFReader/<project>_output/`.

## Data flow

```
formatted_text/<project>/Volume_N_Name/Chapter_N_Title.txt
        │  ChapterFileOrganizer (utils/file_organizer.py)
        │    - walks volume dirs matching processing_config volume_pattern
        │    - yields chapter dicts {filename, volume_name, chapter_number, chapter_title, ...}
        │    - chapter_title read from line 2 of the file ("Chapter N: Title")
        ▼
AzureTTSClient (api/azure_tts_client.py, via api/azure_tts_factory.py)
        │    - Batch Synthesis jobs (BatchJobManager), up to batch_size inputs/job
        │    - creds from env: AZURE_TTS_SUBSCRIPTION_KEY / AZURE_TTS_REGION
        │    - output mirrors the INPUT volume folder name; a legacy fallback maps
        │      bare chapter numbers to book1's old N___VOLUME_N___ folders
        ▼
D:/PDFReader/<project>_output/Volume_N_Name/*.mp3
        │  VideoProcessor (api/video_processor.py)
        │    - background per chapter: config/projects/<project>/portrait_mapping.json
        │      (chapter-range → image in assets/projects/<project>/backgrounds/resized/)
        │    - project_name is injected into processing_config by Project loading;
        │      without it the processor refuses to guess another project's mapping
        │    - ffmpeg still-image, -r 1; H.264 encoder probed at runtime with a real
        │      test encode (nvenc → amf → qsv → libx264 — listing isn't trusted
        │      because nvenc can be listed yet fail without an NVIDIA driver)
        ▼
D:/PDFReader/<project>_output/video/Volume_N_Name/*.mp4
        │  upload_queue.py → api/youtube_uploader.py (repo root)
        │    - YouTube Data API; titles from chapter text line 2
        │    - playlist routing via youtube_config.json (pinned playlist IDs)
        │    - tracker: D:/PDFReader/<project>_output/youtube_progress.json
        ▼
YouTube  (+ youtube_endscreen.py: Studio-UI automation for end screens)
```

## Components (live code)

| Module | Role |
|---|---|
| `utils/project_manager.py` | `ProjectManager` / `Project`; loads the 4 config files, injects `project_name` into processing config |
| `utils/file_organizer.py` | Chapter discovery + ordering (Project-based ctor) |
| `utils/file_based_progress_tracker.py` | Progress = counting actual mp3/mp4 files on disk (self-healing, no DB) |
| `utils/chapter_title.py` | Reads real chapter title from the text header |
| `api/azure_tts_factory.py` | Creates the batch client |
| `api/azure_tts_client.py` | `BatchJobManager` (REST) + `AzureTTSClient` (batching, download, placement) |
| `api/video_processor.py` | Portrait-mapping resolution + ffmpeg rendering |
| `api/youtube_uploader.py` | Upload, metadata, playlist management |
| `scripts/*` | Entry points (see SCRIPTS_GUIDE.md) |

**Removed 2026-08-10:** legacy `utils/progress_tracker.py` (superseded by the
file-based tracker) and its test suites; stale tests targeting pre-batch
client constructors.

## Configuration files per project

```
config/projects/<project>/
├── project.json            # input_directory, output_directory, metadata
├── processing_config.json  # patterns (chapter_pattern / volume_pattern),
│                           # batch settings, and the "video" block the
│                           # VideoProcessor actually reads
├── portrait_mapping.json   # chapter-range → background image (null = art missing,
│                           # render fails loudly instead of using wrong art)
├── youtube_config.json     # channel, playlist pinning, templates
├── azure_config.json       # voice settings (gitignored — copy the .example)
└── batch_config.json       # (book1 only, historical)
```

Note: a separate `video_config.json` exists in project dirs but the renderer
reads the `video` block of **processing_config.json** — keep those in sync or
treat video_config.json as vestigial.

## Import convention

Modules inside `tts_pipeline` import each other as `utils.X` / `api.X` /
`scripts.X`; every entry point (pipeline scripts, root-level upload scripts,
tests via conftest) puts `tts_pipeline/` on `sys.path`. Never use
`from tts_pipeline. ...` inside the package — that form only resolves for
repo-root entry points and once silently broke both pipeline scripts
(2026-08 audit; guarded by entry-point smoke tests).

## Known legacy seams

- Book1 audio on disk uses the old `N___VOLUME_N___TITLE` folder names while
  `formatted_text/lotm_book1` uses `Volume_N_Name`; the azure client keeps a
  chapter-number→legacy-folder fallback for it. Book1 is complete, so this
  only matters if it's ever re-rendered.
- `formatted_text/lom_book2_coi/Volume_2_Light_Chaser` vs. audio/video output
  `Volume_2_Lightseeker`: the volume_map was renamed after V2 was generated.
  Outputs keep the old name; do not rename either side mid-project.
