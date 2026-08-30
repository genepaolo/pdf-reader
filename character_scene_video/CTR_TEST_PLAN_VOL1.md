# Vol 1 CTR test plan — thumbnails + titles/descriptions (2026-08-29)

Day-1 analytics (see CLAUDE.md) showed CTR is the bottleneck: 0.9–1.7% on mostly-Browse
impressions, with the portrait-row USP invisible in the packaging. This file holds the test
assets and the paste-ready text. **Change one variable at a time** — thumbnail test first,
title only if thumbnails alone don't move CTR (else you can't tell which change did what).

## 1. Thumbnail Test & Compare (do this FIRST, on Part 1)

Three new 1280×720 variants generated 2026-08-29, in
`D:/PDFReader/lotm_book1_output/character_video/Volume_1_Clown/thumbnails/`
(regenerate: session scratchpad `make_variants2.py`; portraits from
`tts_pipeline/assets/characters/lotm/`, same fonts/colors as `make_thumbnail.py`):

| File | Concept | Why it might win |
|---|---|---|
| `thumb_vol01_p1_varB_faces.jpg` | **Big faces** — Audrey + Klein head-and-shoulders panels | Faces at feed size are the classic CTR lever; instantly reads as "the characters are the point" |
| `thumb_vol01_p1_varA_row.jpg` | **The portrait row** — Alger/Audrey/Fool trio as the video actually renders scenes | Truth-in-advertising: shows the actual product; Tarot Club trio is iconic |
| `thumb_vol01_p1_varC_strip.jpg` | **Current art + mini-strip** "PORTRAITS CHANGE EVERY SCENE" | Minimal delta from the proven series template; isolates the USP-label effect |

Studio → Part 1 (`sQ94crQVoAQ`) → Details → Test & compare accepts 3 slots. Recommended test:
**varB vs varA vs current** (varC is the fallback if you want a gentler test). Let YouTube run
it ~2 weeks / until it declares a winner on watch-time share. Roll the winning concept to
Parts 2–4 + future volumes (regenerate per part: only the red PART line + info line differ).

## 2. Description line 1 (safe — do on all 4 parts NOW)

Only the first ~150 chars show in search snippets/hover; the portraits line currently sits in
paragraph 3. Replace **only the first line** of each description (rest stays, incl. timestamps):

Part 1 (`sQ94crQVoAQ`):
> Lord of the Mysteries full audiobook with the cast on screen — character portraits change with every scene. Volume 1: The Clown, Part 1 of 4, Ch 1–50, 11 hours.

Part 2 (`AfBLteZ9nfU`):
> Lord of the Mysteries full audiobook with the cast on screen — character portraits change with every scene. Volume 1: The Clown, Part 2 of 4, Ch 51–100, 10 hours.

Part 3 (`Qi3hZkRr_j0`):
> Lord of the Mysteries full audiobook with the cast on screen — character portraits change with every scene. Volume 1: The Clown, Part 3 of 4, Ch 101–157, 11 hours.

Part 4 (`8lha69vkmCE`):
> Lord of the Mysteries full audiobook with the cast on screen — character portraits change with every scene. Volume 1: The Clown, Part 4 of 4, Ch 158–213, 11 hours — the volume finale.

(Bonus: line 1 now contains the exact query "lord of the mysteries full audiobook", which the
old "continuous audiobook" phrasing missed.)

## 3. Title change (HOLD until the thumbnail test concludes)

Current pattern (87–90/100): `Lord of the Mysteries Audiobook — Volume 1: The Clown | Part N of 4 (Ch A–B, H Hours)`

- **Option 1 — recommended:** insert one word: `Lord of the Mysteries Visual Audiobook — …`
  (+7 chars, fits all parts; keeps "audiobook" for search; small risk: breaks the exact phrase
  "Lord of the Mysteries Audiobook").
- **Option 2 — explicit USP, drop "of 4" + hours to fit 100:**
  `Lord of the Mysteries Audiobook — Volume 1: The Clown | Part N (Ch A–B) + Character Portraits`

## 4. Rest of the funnel (from the 2026-08-29 analytics review, unchanged)

Verify end-screen chain 1→2→3→4 · community post to subs · pinned-comment cross-links on the
top per-chapter LOTM videos · Shorts cut from iconic scenes. Playlists already verified good.
