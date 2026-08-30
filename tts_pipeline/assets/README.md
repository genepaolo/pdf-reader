# tts_pipeline assets

```
assets/
├── projects/                  # PER-PROJECT video background art (see projects/README.md)
│   ├── lotm_book1/            #   book1 Sequence cards + cover (+ legacy animated bg)
│   └── lom_book2_coi/         #   COI volume art (v1–v3 recovered; v4–8 pending dropoff)
└── characters/                # Book-1 character portraits for the separate
                               # character_scene_video workstream (gitignored binaries)
```

- **Add / change chapter art:** drop images into
  `projects/<project>/dropoff/` and run
  `py -3.12 tts_pipeline/scripts/prepare_backgrounds.py --project <project>`.
  Full flow in [projects/README.md](projects/README.md).
- Which image a chapter gets is decided by
  `config/projects/<project>/portrait_mapping.json` — the renderer uses the
  `resized/*_1920x1080.*` copies.
- The old shared `assets/images/` + `assets/videos/` dirs were reorganized
  into `assets/projects/<project>/backgrounds/` on 2026-08-10 (the code still
  checks the old location as a legacy fallback).

## FFmpeg

Video creation needs ffmpeg on PATH (or a project-local `ffmpeg/` dir —
auto-detected by `scripts/setup_ffmpeg_path.py`). Windows install:
`choco install ffmpeg`.
