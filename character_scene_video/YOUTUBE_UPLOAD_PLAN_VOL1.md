# YouTube Upload Plan — LOTM Volume 1 (ch1–213, in FOUR PARTS)

> **Output layout changed 2026-09-06:** chapter masters live in `<Volume_dir>/chapters/`, each upload part in its own `<Volume_dir>/parts/Part_K_chAAA-BBB/` folder (MP4 + pack files + `thumbnails/`), volume-level thumbnails in `<Volume_dir>/thumbnails/`. The old `Block_NN_` file stems are now `Part_K_`; the abandoned 43 h Vol-1 single upload sits in `Volume_1_Clown/_legacy/`. Older path mentions below were rewritten to match; anything still saying `Block_` is history.


**2026-08-28: the single 43 h upload was REJECTED — YouTube enforces its documented 12 h / 256 GB
cap** ("The maximum file size you can upload is 256 GB or 12 hours, whichever is less"). The
AudioVerse-style >12 h videos are grandfathered older uploads, not a live loophole. Volume 1
therefore uploads as **four parts**, all built and packed 2026-08-28:

| Part | File | Chapters | Duration | Size |
|---|---|---|---|---|
| 1 | `parts/Part_1_ch001-050/Part_1_ch001-050.mp4` | 1–50 | 10:52:07 | 0.85 GB |
| 2 | `parts/Part_2_ch051-100/Part_2_ch051-100.mp4` | 51–100 | 10:07:56 | 0.79 GB |
| 3 | `parts/Part_3_ch101-157/Part_3_ch101-157.mp4` | 101–157 | 11:08:29 | 0.88 GB |
| 4 | `parts/Part_4_ch158-213/Part_4_ch158-213.mp4` | 158–213 (finale) | 11:10:03 | 0.88 GB |

Why these boundaries: parts 1–2 keep the round 50-chapter blocks; the old fallback split
(101–150 / 151–213) does NOT work — 151–213 runs **12:31:20**, over the cap — so the back half is
rebalanced at ch157/158, giving two ~11:09 parts. All four sit ≥50 min under the limit.
Part 1 was re-concatenated 2026-08-28 from the current chapter files so the ch20–21 diary-interlude
re-renders are included. The 43 h `Block_01_ch001-213.mp4` + its pack files are obsolete for
upload (parked in `Volume_1_Clown/_legacy/`).

**Per-part pack files** (all regenerable with `make_upload_pack.py`; live next to the MP4s in
`D:/PDFReader/lotm_book1_output/character_video/Volume_1_Clown/parts/Part_K_chAAA-BBB/` — output
reorganized BY VOLUME 2026-08-28 and BY PART 2026-09-06):

- `Part_K_chAAA-BBB_description_YOUTUBE.txt` — paste into the description (~3.1–3.5k / 5,000 ✅)
- `Part_K_chAAA-BBB_pinned_comment.txt` — part-navigation links; post + pin (283 / 10,000 ✅)
- `Part_K_chAAA-BBB_tags.txt` — Tags field (363 / 500 ✅)
- `parts/Part_N_.../thumbnails/thumb_vol01_pN.jpg` — series-template thumbnail with part number (~227 KB ✅)

Regenerate packs: `py -3.12 character_scene_video/make_upload_pack.py --volume 1` (all parts;
add `--part 3` for one). Part ranges, story hooks, tags, and pitch lines live in
`projects/lotm_book1/upload_meta.json` — the script is engine-generic (template in
`projects/_TEMPLATE/upload_meta.json`). Thumbnails: `py -3.12
character_scene_video/make_thumbnail.py 1 --name "The Clown" --part 3 --range "101-157"
--hours 11`.

---

## 1. Titles (printed by `make_upload_pack.py`; 87–90 / 100 chars)

> **Lord of the Mysteries Audiobook — Volume 1: The Clown | Part 1 of 4 (Ch 1–50, 11 Hours)**
> **Lord of the Mysteries Audiobook — Volume 1: The Clown | Part 2 of 4 (Ch 51–100, 10 Hours)**
> **Lord of the Mysteries Audiobook — Volume 1: The Clown | Part 3 of 4 (Ch 101–157, 11 Hours)**
> **Lord of the Mysteries Audiobook — Volume 1: The Clown | Part 4 of 4 (Ch 158–213, 11 Hours)**

Same shape as the single-video title (search phrase front-loaded, numbers set expectations), with
the part position made explicit so binge-listeners see the sequence at a glance.

## 2. Descriptions (paste each part's `_description_YOUTUBE.txt`)

Improvement over the 43 h plan: with ~50 chapters per part, the **full per-chapter timestamp list
fits the 5,000-char description**, so EVERY chapter is a real in-player chapter segment (the
every-10 compromise + pinned-comment-for-granularity workaround is gone). Each description has:

- The ~150-char hook naming series, volume, **part N of 4**, chapter range, hours.
- A part-specific story hook (non-spoiler, drawn from that part's arcs).
- The portraits USP + donghua bridge lines (unchanged from the original plan).
- A **part map** ("THIS IS PART 3 OF 4 …" with all four ranges and ◀ YOU ARE HERE).
- The full `H:MM:SS Chapter N: Title` list — timestamps are part-local, from ffprobe of the
  actual files, so markers land exactly on the cuts.
- Outro: narration credit, next-part/Volume-2 subscribe line, 5 hashtags.

Pasting the description IS the chapter setup — after processing, confirm the ticks appear;
re-save the description if not (known Studio quirk).

## 3. Pinned comments (paste `_pinned_comment.txt`, then Pin)

**Part-navigation links + the full per-chapter timestamp list** (user request 2026-08-28 — not
everyone reads descriptions, so the chapter list lives in BOTH places). The `[link]` placeholders
get the real URLs once all four parts are up, then edit the comments; the current part's line
says "you are here". ~2.0–2.4k / 10,000 chars per part.

## 4. Thumbnails

Same series template as before (`make_thumbnail.py`, Fool puppet-stage art, consistent branding),
with the red line now **"PART N — FULL AUDIOBOOK"** and the info line carrying the chapter range:
`thumb_vol01_p1.jpg` … `thumb_vol01_p4.jpg` (generated 2026-08-28, all ~227 KB). The whole-volume
`thumb_vol01.jpg` and card-art drafts remain as alternates for A/B testing.

## 5. Why now — the trend window

(Unchanged.) The donghua's 3-episode special hit Crunchyroll June 20, 2026; S2 (30 eps) lands
2027 with a 10-year/7-season plan behind it. Adaptation-gap searches ("where does the anime end
in the novel?") convert straight to "full audiobook" queries — have all of Volume 1 up, and
Volume 2 before S2 airs. Multi-part is arguably BETTER for the algorithm: four videos → four
impressions surfaces, and a completed Part 1 feeds Part 2 directly via end screens.

## 6. Upload procedure (per part, in order 1 → 4)

Manual upload through YouTube Studio in Chrome as **breadmoretti@gmail.com** (NOT paolo.gene) —
`upload_queue.py` stays untouched (COI per-chapter flow only).

1. Upload the part's MP4, visibility **Unlisted**.
2. While processing: paste the part's title, description file, tags file; thumbnail
   `thumb_vol01_pN.jpg`; Audience **Not made for kids**; Category Entertainment; License Standard.
3. Add to the **"Lord of the Mysteries Audiobook — Volume 1: The Clown"** playlist (create at
   Part 1; title + description ready in `playlist_vol01.txt` next to the MP4s; ORDER MATTERS —
   playlist order 1→4 is the binge path). Distinct from the existing per-chapter playlist
   "LOTM - Volume 1: CLOWN" — consider renaming that one to "LOTM Volume 1 — Individual
   Chapters" so viewers don't pick the wrong one. Later, a master "Lord of the Mysteries —
   Complete Audiobook (All Volumes)" playlist can hold every part across volumes.
4. Wait for full processing (an ~11 h video still takes hours for HD; chapters/seeking look broken
   until it finishes). Verify: plays at 0:00, chapter ticks present, seek to the last chapter and
   confirm it plays to the end.
5. Post + pin the part's navigation comment (fill `[link]`s once all four are up).
6. Repeat for the next part. **After all four are unlisted-verified:** add end screens
   (Part N → Part N+1, subscribe element; manual — `youtube_endscreen.py` targets the COI
   project), fill all pinned-comment links, then flip all four **Public** together
   (best window: Friday 14:00–17:00 UTC). Publishing together keeps early viewers from hitting a
   dead "Part 2" search. Don't Premiere.

## 7. Post-upload checklist (per part)

- [ ] Chapters render in the player bar (re-save description if not)
- [ ] Pinned comment posted + pinned (links filled after all four exist)
- [ ] Playlist position correct (1→4)
- [ ] End screen → next part (Part 4: → Volume 2 when it exists / subscribe only)
- [ ] Record the video ID + URL in CLAUDE.md progress log
- [ ] After 48 h: check CTR + retention; A/B thumbnails after ~2 weeks

## Sources

- [Crunchyroll LOTM special / S2 timing](https://screenrant.com/lord-mysteries-crunchyroll-season-2-release-date/) · [10-year donghua plan](https://www.sportskeeda.com/anime/news-lord-mysteries-donghua-announces-10-year-production-plan-7-seasons-3-specials-movie)
- [Thumbnail best practices 2026 (vidIQ)](https://vidiq.com/blog/post/youtube-thumbnail-design-tips/) · [Title best practices](https://humbleandbrag.com/blog/youtube-title-best-practices) · [Title length guide](https://ytzolo.com/blog/youtube-video-title-length-best-practices-2026/)
- [Video chapters rules (YouTube Help)](https://support.google.com/youtube/answer/9884579?hl=en) · [Chapters format + pinned-comment distinction](https://tubealfred.com/blog/youtube-chapters-format/) · [Description/comment char limits](https://typecount.com/blog/youtube-description-character-limit)
- [12 h / 256 GB upload limit (YouTube Help)](https://support.google.com/youtube/answer/71673?hl=en&co=GENIE.Platform%3DDesktop) — **enforced on us 2026-08-28**
