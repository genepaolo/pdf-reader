# Per-project video assets

Every project keeps its video background art here, under its own name:

```
assets/projects/<project_name>/
├── dropoff/                 # DROP NEW IMAGES HERE (any size, jpg/png/webp)
└── backgrounds/             # full-res originals (managed by prepare_backgrounds.py)
    └── resized/             # 1920x1080 letterboxed copies — what the renderer uses
```

## Adding / changing chapter art

1. Drop the image(s) into `assets/projects/<project>/dropoff/`.
2. Run `py -3.12 tts_pipeline/scripts/prepare_backgrounds.py --project <project>`
   — it moves each image to `backgrounds/` and writes the `_1920x1080` copy.
3. Map chapter ranges to the filenames in
   `tts_pipeline/config/projects/<project>/portrait_mapping.json`.
4. Check with `py -3.12 tts_pipeline/scripts/prepare_backgrounds.py --project <project> --status`.

`portrait_mapping.json` is the single source of truth for which image each
chapter gets (`"first-last": {"image": "file.jpg"}`). A `null` image means
"art not supplied yet" — rendering those chapters fails loudly instead of
silently using another book's art.

## Notes

- `lotm_book1/`: the nine Sequence-card portraits + cover (complete, book finished).
- `lom_book2_coi/`: volumes 1–3 art was **recovered from the rendered videos**
  on 2026-08-10 (the original source images were never saved). Volumes 4–8
  still need art — that's the current blocker for rendering ch. 495+.
- Resolution: images are letterboxed to 1920x1080, matching every video
  produced so far.
