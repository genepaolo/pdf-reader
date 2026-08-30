# YouTube Upload Plan — LOTM Volume 2: Faceless (ch214–482, in FIVE PARTS)

Built and packed **2026-08-29**. Same procedure as Volume 1 — read
`YOUTUBE_UPLOAD_PLAN_VOL1.md` sections 6 and 7 for the step-by-step upload/verify/end-screen flow
(it is volume-generic); this file records only what is specific to Volume 2.

| Part | File | Chapters | Duration | Size |
|---|---|---|---|---|
| 1 | `Block_05_ch214-266.mp4` | 214–266 | 10:49:10 | 806 MB |
| 2 | `Block_06_ch267-320.mp4` | 267–320 | 10:53:01 | 805 MB |
| 3 | `Block_07_ch321-374.mp4` | 321–374 | 10:50:06 | 804 MB |
| 4 | `Block_08_ch375-428.mp4` | 375–428 | 10:46:40 | 799 MB |
| 5 | `Block_09_ch429-482.mp4` | 429–482 (finale) | 10:51:58 | 808 MB |

All five sit **~1 h 10 m under YouTube's 12 h cap** (enforced on us 2026-08-28). Total 54:11.

**Why these boundaries.** Volume 2 has no round 50-chapter seams that fit the cap, so the split was
computed as a balanced 5-way min-max over the aligned per-chapter audio durations (max part
10.88 h), then the cut points were nudged onto story beats:

- Part 1 ends **ch266 "The World's Commission"**
- Part 2 ends **ch320 "Action"**
- Part 3 ends **ch374 "Artificial Sleepwalking"** — immediately before Capim's dinner
- Part 4 ends **ch428 "The Scapegoat"** — the Duke Negan aftermath
- Part 5 runs to **ch482**, the end of the volume

Part 4 is the set piece: Capim's dinner, the black armour and black crown, and the papers naming
the **Hero Bandit Dark Emperor**. That persona has its own portrait as of 2026-08-29, so Klein
visibly changes form for those chapters.

**Files** (all next to the MP4s in
`D:/PDFReader/lotm_book1_output/character_video/Volume_2_Faceless/`):

- `Block_NN_chAAA-BBB_description_YOUTUBE.txt` — 3,478–3,623 / 5,000 ✅ (full per-chapter marker
  list fits, so every chapter is a real in-player chapter)
- `Block_NN_chAAA-BBB_pinned_comment.txt` — 2,367–2,521 / 10,000 ✅ (part links + full chapter list;
  fill the `[link]` placeholders once all five are up)
- `Block_NN_chAAA-BBB_tags.txt` — 380 / 500 ✅
- `thumbnails/thumb_vol02_pN.jpg` — series template, ~229 KB each ✅
- `playlist_vol02.txt` — playlist title + description

Titles (89 / 100 chars each):

> **Lord of the Mysteries Audiobook — Volume 2: Faceless | Part N of 5 (Ch A–B, 11 Hours)**

Regenerate anything: `py -3.12 character_scene_video/make_upload_pack.py --volume 2` (add
`--part N` for one) and `py -3.12 character_scene_video/make_thumbnail.py 2 --name "Faceless"
--part N --of 5 --range "214-266" --hours 11`. Part ranges and hooks live in
`projects/lotm_book1/upload_meta.json` under `volumes.2`.

## Volume-2-specific notes

- **Playlist:** create "Lord of the Mysteries Audiobook — Volume 2: Faceless" at Part 1, order
  1→5. Keep it distinct from the per-chapter playlists.
- **End screens:** Part N → Part N+1; Part 5 → Volume 1 Part 1 (or subscribe only until Volume 3
  exists). Manual — `youtube_endscreen.py` targets the COI project, not this one.
- **Publish order:** all five unlisted and verified first, then flip Public together.
- **Volume 1 is still unuploaded** as of 2026-08-29 — upload it first, or Part 5's "start with
  Volume 1" pitch points at nothing.
- **Portrait coverage caveat:** 38 Volume-2 wiki characters have no art (recorded `no for now` in
  `portrait_decisions.json`), so scenes where only portrait-less characters are present collapse
  into long single-portrait stretches — most visibly ch377–380, where Capim, Harras, Katy and
  Parker are all portrait-less and the raid renders as two cuts across 824 s. Installing art for
  any of them and rerunning `build_block.py` → `compose_frames.py` → `render_chapter.py` →
  `build_block_video.py` for the affected part fixes it; the wiki's physical descriptions are
  collected in `projects/lotm_book1/timelines/portrait_wanted_descriptions.md`.
