# Character-Scene Videos — STATUS / Session Handoff

> **Output layout changed 2026-09-06:** chapter masters live in `<Volume_dir>/chapters/`, each upload part in its own `<Volume_dir>/parts/Part_K_chAAA-BBB/` folder (MP4 + pack files + `thumbnails/`), volume-level thumbnails in `<Volume_dir>/thumbnails/`. The old `Block_NN_` file stems are now `Part_K_`; the abandoned 43 h Vol-1 single upload sits in `Volume_1_Clown/_legacy/`. Older path mentions below were rewritten to match; anything still saying `Block_` is history.


**Read this first to resume.** Last updated 2026-09-18 (see the block right below; the 09-02
paragraph after it is older context).

## Session 2026-09-18 — six `*` references, Vol 3 block 11 tagged, verify_render.py added

**Volume 2 state: every chapter proven correct against the CURRENT frame cache, packs fresh.**
The proof is `py -3.12 character_scene_video/verify_render.py 214 482` (exit 0 = CLEAN). It runs two
pixel checks — cached PNG vs fresh recompose (catches in-place portrait swaps), and decoded video
frame vs cached PNG per scene (catches un-re-rendered chapters) — plus part-vs-chapter mtimes.
**Run it BEFORE any claim that a range is rendered, and again AFTER re-rendering.** Findings are
also written as JSON with `--json`; `chapters_to_rerender` and `stale_parts` are the work list.
Frame-PNG mtimes are not a signal (see CLAUDE.md 09-05 note).
**Last full run 2026-09-18 (after the six installs): 183 distinct frames 0 stale / 0 missing, 838/838 scenes match, 0 stale parts — CLEAN (188 s).** Report kept at `projects/lotm_book1/verify_vol2_2026-09-18.json`. Anything that changes Vol 2 after this invalidates that verdict — re-run, don't reuse it.

Installed today (all user-supplied, all marked `*`, decisions flipped to yes): **Caitlyn Hall**
(fan art of Audrey + mother, uncropped), **Kaslana** (hard-decline reversed; SQUARE art — ~2.5x the
width of a card in a row, crop to portrait if it reads wrong), **Escalante** (reads older than the
text's "baby-faced"), **Capim**, **Stuart** (transparent PNG composited on the backdrop), **Horamick
Haydn** (low-res anime still). Chapters touched: 343,472,482 / 299,301,305,337,413-416,418-420 /
339,356,368,388,405,417,418,444,449,450,471 / 377-380 / 299,300,301,305,337,338,370,371,413,414 /
324,446-448. Every part was re-concatenated at least once; part 5 is now 10:52:01 (+3 s, cut
rounding). Alias `Ian` -> `Ian Wright`. User's review list: `VOL2_OUTSTANDING_REVIEW.md` (71 ch).

**Volume 3 block 11 (ch483-532): TAGGED + VERIFIED, NOT RENDERED.** Aligned 483-732 (all 250 at
100%), verify_alignment PASS, 186 scenes, verify_tags 471/471. Ten parallel readers, brief in the
session scratchpad `vol3_notes/READER_BRIEF.md` (worth copying into the repo before block 12).
Engine changes: `base_flips` Sherlock -> **Gehrman Sparrow at ch484** (ch483 tagged by scene);
`character_map.json` gained `image_from_chapter` — The World shows the FULL Gehrman Sparrow card
from ch483 (`build_block.image_for()`); Vol 2 blocks rebuilt byte-identical afterwards.
Judgment calls made during consolidation: throwaway Faceless guises (ch531 "Wendt") render as
Gehrman Sparrow; ch523 s7 keeps The World for the staged prayer answer (ch336 precedent); the
ch525-526 "beheaded Danitz" is tagged as Danitz for the reveal (ch447 precedent); `Cordoba Roye`
is aliased DOWN to the page's `Cordoba` (not a wiki character). Boundary 503 took the fuller
dining-room cast. Vol 3 durations: 50.12 h -> five parts (~483-531 / 532-581 / 582-632 / 633-683 /
684-732), cut points not yet nudged to story beats; `upload_meta.json` has NO volume 3 entry yet
(build_block_video refuses ranges not listed there).
**Before rendering block 11:** portrait decisions — `build_character_report.py 483 532` says
need:16 (Donna, Denton, Elland Kag, Urdi Branch, Maveti, Squall, Hendry, Hamilton, Logan, Hermes,
Medici, Millet, Berg, Caitlyn Hall[now has art], Davy Raymond, Waymandy) plus non-registry names
with heavy screen time (Cleves 2:22, Cecile 2:11, Teague 1:05, Harris, Timothy). The Branch-family
voyage ch499-512 renders as Klein + Danitz alone until those get art.

 (**BOTH VOLUMES FULLY RE-RENDERED,
RE-CONCATENATED AND RE-PACKED** with the 2026-08-31→09-02 upgrades: member-first portrait
ordering, gold mentioned-rims, 7 deity cards, frame_focus, delayed-entrance splits, and the
missing-tag sweep. Volume 1 is live on YouTube (old frames — re-upload optional); **Volume 2's 5
parts await manual Studio upload**. P1 thumbnail A/B test runs until ~Sep 11).

## Full re-render + re-pack 2026-09-02 (the deferred "render sweep")
- All 482 chapters re-rendered with `--force` (log-verified 482/482, 0 failures) AND frame-grab
  verified (ch196 Sharon, ch447 Amon reveal at 11:55 vs clean 5:00, ch461 six-god mural).
- All 9 upload parts re-concatenated fresh (each 10:07–11:10, under the 12 h cap) + packs regenerated.
  ⚠ `build_block_video.py` SKIPS existing part MP4s without `--force` — same trap as
  `render_chapter.py`; the first concat run silently kept 9 stale files while the packs regenerated.
- `render_chapter.py` bug fixed: my mentioned-images patch referenced `sc`/undefined vars and had
  never run; steps now carry the mentioned list end to end.
- ch447's +3 s "DURATION MISMATCH" is benign: the MP3 has ~3 s trailing silence beyond the
  alignment total; `-shortest` extends the last frame to cover it.

## frame_focus + delayed entrances + missing-tag sweep 2026-09-01→02 (user decisions)
- **`frame_focus: "mentioned"`** (build_block): frame shows ONLY the mentioned names — reserved for
  over-cap crowding; the sole instance is **ch461 s2** (six-god mural incl. True Creator; user kept
  Him despite the style break). Cast/report/verify unaffected; no gold rims in a focus frame.
- **Delayed entrances** (splits, nobody dropped): ch447 s1→s1+s2 (Amon's portrait lands only when
  Horamick turns the frame — his face no longer spoils 11:44 of tomb crawl); ch264 s4→s4+s5
  (Lanevus arrives with the painting; +1 verified_present for seated Derrick).
- **Missing-tag sweep** (names substantially discussed in Fool scenes but untagged; 103 raw hits
  judged): 22 scenes gained mentioned tags (Qilangos ×6 incl. his in-scene portrait ch146, Azik,
  Trissy, Susie, Mr. A, Ince Zangwill+Selena, Dunn Smith, Hanass Vincent+Ray Bieber, True Creator
  ×4, Amon ch393 both halves, EBS ch140, Lilith ch468). **ch460 s3: Derrick was MISSING from the
  cast while speaking — presence fix.** ch447 s1's Amon ×8 stays deliberately untagged (spoiler).
- **Sharon ≠ Sharron (user correction ×2):** Madam Sharon (Backlund madam, Demoness pathway,
  ch174/195-199, own user-supplied donghua portrait `Sharon.png`) is NOT Sharron (Wraith bodyguard,
  ch244+). A briefly-added alias wrongly overrode her portrait with Sharron's card — unwound, the
  6 affected chapters re-rendered. Do NOT re-merge them.
- Frame cap: `build_block.py` now imports MAX_PER_FRAME and prints over/at-cap warnings per build;
  both volumes scan clean (largest frame: 8 portraits, ch461 s3).
- All 11 blocks verify_tags: **0 to fix** (172/258/254/243/72/216/238/201/247/258/109).
- New standing rules recorded in `TAGGING_GUIDE.md` (frame focus + delayed entrances).

## Volume 2 — BUILT 2026-08-29
- Frames: `compose_frames.py --block --contact-sheet` composed the 83 new portrait sets (212
  distinct sets across Book 1, 218 PNGs + `_contact_sheet.png`); all 1,529 scenes in every block
  resolve to a frame on disk, 0 missing.
- Render: `render_chapter.py 214 482` — **269/269 chapters**, 0 missing, 0 undersized, exit 0.
  Output `D:/PDFReader/lotm_book1_output/character_video/Volume_2_Faceless/`.
- Concat: **5 parts**, each ~1 h 10 m under the 12 h cap — `Block_05_ch214-266` (10:49:10),
  `Block_06_ch267-320` (10:53:01), `Block_07_ch321-374` (10:50:06), `Block_08_ch375-428`
  (10:46:40), `Block_09_ch429-482` (10:51:58). ~805 MB each, 54:11 total, 1920x1080 @ 1 fps,
  MP3 stream-copied. Split = balanced 5-way min-max over aligned audio durations, cut points
  nudged onto story beats.
- Packs: `make_upload_pack.py --volume 2` (descriptions 3.5k/5k, pinned 2.4k/10k, tags 380/500)
  + `make_thumbnail.py` → `thumbnails/thumb_vol02_p1..5.jpg`, plus `playlist_vol02.txt`.
  Plan: `character_scene_video/YOUTUBE_UPLOAD_PLAN_VOL2.md`.
- ⚠ Portrait-coverage caveat: with 38 characters portrait-less, scenes containing only
  portrait-less cast collapse into long single-portrait stretches — most visibly ch377-380 (the
  Capim raid renders as 2 cuts across 824 s). Fixable later per part by installing art and rerunning
  build → frames → render → concat for that part.

## Visualized-in-the-fog tagging pass 2026-08-29
- New standing rule (see `TAGGING_GUIDE.md`): substantially-discussed absent figures ARE tagged in
  Tarot gatherings and solo above-the-fog scenes. Scanned all 154 Fool-persona scenes in Vol 2 →
  155 candidate (scene, name) pairs → **34 scenes / 40 additions** kept after reading each span.
- Added: Amon x9 scenes, True Creator x10, Lanevus x5, Mr. A x3, Will Auceptin x2, Evernight
  Goddess x2, Edessak Augustus x2, plus Cattleya, Qilangos, Sharron, Zaratul, Ince Zangwill,
  Talim Dumont. Biggest wins: ch461 s1 (the six-gods mural), ch358-359 + ch392 (the Amon taboo),
  ch446-448 (the Amon tomb replay), ch404 (divining Will Auceptin's death).
- **Ouroboros has NO eligible scene in Vol 2** — the ch389 hit is "that Ouroboros-like snake"
  (the shape, not the being); Colin only names him at ch466, which is not a fog scene.
- All six blocks verify clean after the pass (214/213/193/230/226/104, 0 to fix — counts rose
  because the new tags are real named cast). 31 chapters re-rendered with `--force`, all five
  parts re-concatenated (durations unchanged), packs regenerated.

## ⚠ Render-skip gotcha found + fixed 2026-08-29
- `render_chapter.py` **skips existing MP4s unless `--force`**, printing a normal-looking summary
  anyway. All post-bulk re-renders (Edessak, Old Kohler, Darkwill, Steve, Jason, Tyre — 38
  chapters) had silently skipped; caught via an ffmpeg frame grab of ch348. Fixed with a
  `--force` sweep of all 38 + re-concat of all five parts (durations unchanged). Rule: re-renders
  always `--force`, verify with a frame grab.

## Volume 2 — portrait round, 2026-08-28
- **10 installed** from user-supplied art (clipboard flow, each visually verified before install):
  Aaron Ceres, Jurgen Cooper, Stelyn Sammer, Maric, Talim Dumont, Utravsky, Mike Joseph,
  Ikanser Bernard, Lanevus + the `Will Auceptin` rekey (wiki spells it `Wil`). Cover scans were
  hand-cropped to head/shoulders so title/volume/publisher typography stays out of the row.
  Aaron Ceres was re-supplied at 1210x1730; the first cover crop is superseded (old file parked in
  the session scratchpad, not deleted). Jurgen Cooper is low-res 190x267 — replace if a better
  source appears.
- **Kaslana + Kaspars Kalinin: hard no.**
- **Depiction convention + Steve/Jason/Tyre installed 2026-08-29:** non-official art is allowed,
  stamped with a white * top-right (`mark_depiction.py`, now in the repo) and disclosed in the
  series credit line. Steve = user-supplied resemblance art; Jason = cartoon-zombie joke stand-in;
  Tyre = werewolf joke stand-in (the ch347-350 Rose School fight -- 48+35 min -- now renders with
  faces). Block 7 verify 186/186, 0 to fix; ch347-350 re-rendered; part 3 re-concatenated
  (10:50:06 unchanged); packs regenerated with the * disclosure.
- **Darkwill installed 2026-08-29** (user identified the `[fat-faced man]` Apothecary/Beast Tamer
  from Eye of Wisdom's gatherings as Darkwill): 13 scenes retagged ch239-335 + 13
  `verified_present` entries (he is never named on-page in Vol 2 -- ch304 only reveals the Beast
  Tamer Sequence). Blocks 5-7 rebuilt (**213/202/186**, 0 to fix -- counts grew because bracketed
  tags became named), frames recomposed, 13 chapters re-rendered, **parts 1-3 re-concatenated**
  (10:49:10 / 10:53:01 / 10:50:06, unchanged) + packs regenerated.
- **Old Kohler installed 2026-08-29** (user art, cropped 515x1030 -> 439x783 to drop an
  'INTERVIEW' banner): found via the new `Kohler` -> `Old Kohler` alias — the report had him
  mis-filed as minor for 20 scenes / 89 min across ch282-476. Blocks 6-10 rebuilt (all 0 to fix),
  frames recomposed, his 15 chapters re-rendered, **parts 2-5 re-concatenated** (durations
  unchanged: 10:53:01 / 10:50:06 / 10:46:40 / 10:51:58) + packs regenerated. Code-name rule
  (Eye of Wisdom vs Isengard Stanton kept separate) documented in `TAGGING_GUIDE.md`.
- **Edessak Augustus installed 2026-08-29** (page-photo art, used as-is 888x1527): blocks 9+10
  rebuilt (217/217, 102/102), frames recomposed, ch438/439/444/470/474/479 re-rendered and upload
  **Part 5 re-concatenated with `--force`** (10:51:58, 808 MB) + pack regenerated. 37 names left.
- **38 others: 'no for now'** — no art found, but they are NOT unwanted. Tracked in
  `portrait_decisions.json` → `_no_for_now` (names + scene weight + blocks) with the wiki's own
  physical descriptions in `timelines/portrait_wanted_descriptions.md`, so lookalike art can be
  slotted in later: install the file, add a `character_map.json` entry, flip the name to `yes`,
  rerun `build_block.py` then `compose_frames.py`.
- All six blocks rebuilt + verified after the round: **need:0**, verify_tags
  208/198/182/220/217/102, 0 to fix.

## Volume 2 — `Hero Bandit` persona added 2026-08-29
- New persona in `project.json` → `persona.map`: `"Hero Bandit": ["Klein (as the Hero Bandit)",
  "Hero Bandit.png"]`, plus `Hero Bandit` in `image_names` so it never counts as a character
  portrait. Art is user-supplied (clipboard, verified), scaled 4258x4785 -> 979x1100, **uncropped**.
- Retagged the 12 scenes where Klein is actually in the black armour + black crown (was
  `Sherlock Moriarty`): **ch377 s3** (the transformation + flight to Capim's), **ch378 s1-s2**,
  **ch379 s1**, **ch380 s1-s5** (the whole Capim raid through the rooftop vanish), and
  **ch426 s3-s4 + ch427 s1** (the Sequence 5 Devil in the sewer). Blocks 8 + 9 rebuilt: the form
  resolves on all 12, verify_tags still 220/220 and 217/217, 0 to fix.
- Context: in Book 1 "Hero Bandit Dark Emperor" is what the newspapers christen the unknown killer
  in ch382 — Klein never adopts it as an identity here. It becomes a real alias later
  (Vol 3 ch717 "The World and Hero Bandit"; Dwayne Dantès in Vol 4). `image_names` reserves
  `Dwayne Dantès` and `Merlin Hermes` for that, but neither has a `map` entry — adding one without
  an image file would KeyError in `build_block.py`.
- Frames, render, concat and packs for these 12 scenes are DONE — they sit inside upload Part 4
  (ch375-428) and Part 5 (ch429-482). See the "Volume 2 — BUILT 2026-08-29" section at the top.

## Volume 2 — Block 10 (ch464-482) — TAGGED + VERIFIED 2026-08-28 — **VOLUME 2 CONTENT DONE**
- Final 19 chapters scene-tagged (**68 scenes, 3:50:52**; short block — Volume 2 ends at ch482).
  Gates: verify_tags **102/102, 0 to fix** (2 verified_present); verify_alignment **PASS**
  (0 structural, 1.21%). Continuity boundaries 463-481 written.
- Story beats: Emlyn joins the Tarot Club as **The Moon** (ch468), Derrick breaks the Ouroboros time
  loop, Trissy revealed as "Trissy Cheek" (the Primordial Demoness's name), the **Great Haze of
  Backlund** (~21k dead + ~40k plague — Old Kohler, Liv and Freja die), Klein wrecks the Aurora
  Order's ritual with the Master Key, 0-17 erases Lady Despair/Mr. A/Funkel, Prince Edessak's
  suicide, and the volume closes with Benson and Melissa arriving in Backlund.
- Portrait decisions PENDING: report = 46 chars, **have:15 need:6** →
  `timelines/character_report_block10.md` (Edessak Augustus, Funkel, Nibbs Odora, Daisy, Utravsky,
  Hibbert Hall).
- ⏭ **Volume 2 tagging is finished.** Remaining Volume 2 work is the deferred pipeline:
  portrait decisions for blocks 5-10 → `build_block.py` rerun → `compose_frames.py` →
  `render_chapter.py` → `build_block_video.py` (respecting the 12 h upload-part cap).
  Next new tagging would be Volume 3 (ch483+).

## Volume 2 — Block 9 (ch414-463) — TAGGED + VERIFIED 2026-08-28 (portraits + render PENDING)
- All 50 chapters scene-tagged (**143 scenes, 10:01:45**). Gates: verify_tags **217/217, 0 to fix**
  (6 verified_present — Susie at Audrey's initiation, Leonard inside 1-42's armor, gathering seats).
  verify_alignment **PASS** (0 structural, 0.82%). Continuity boundaries 413-462 written.
- Story beats: the Desire Apostle hunt and Duke Negan's assassination (Twilight Hermit Order named),
  Arrodes reporting the Amon-tomb expedition to "the mighty existence above the spirit world",
  **Klein advances to Sequence 6 Faceless (ch451)**, the sealed evil spirit's Red Priest card offer,
  Prince Edessak's commission and the ring-wearing woman whose meetings keep being deflected (0-08),
  Derrick's looping expedition, and Nibbs Odora ordering Emlyn to pray to The Fool.
- **Roselle diary interludes** (standing rule): ch440 s2, ch462 s2 (both cast Roselle + persons named
  in the pages: Mr. Door/Zaratul/Bernadette/Floren, then Zaratul/Karen). ch439's single trailing
  diary line was folded into the gathering scene rather than split out.
- Portrait decisions PENDING: report = 84 chars, **have:21 need:18** →
  `timelines/character_report_block09.md` (Ikanser Bernard, Kaslana, Aaron Ceres, Soest, Utravsky,
  Edessak Augustus, Horamick Haydn, Rafter Pound, Cosmi Odora, Hilbert Alucard, Mike Joseph,
  Nibbs Odora, Stephen Hampres, Talim Dumont, Daisy, Jurgen Cooper, Lockhart Siakam, Stelyn Sammer).
- ⏭ Next tagging block: **ch464-482** (19 chapters — completes Volume 2).

## Volume 2 — Block 8 (ch364-413) — TAGGED + VERIFIED 2026-08-28 (portraits + render PENDING)
- All 50 chapters scene-tagged (**159 scenes, 9:58:11**). Gates: verify_tags **220/220, 0 to fix**
  (6 verified_present — Count Hall still at the ch382/383 breakfast; The Sun / Justice / Magician
  seated through the ch391+ch395 gathering scenes). verify_alignment **PASS** (0 structural, 0.90%).
  Continuity boundaries 363-412 written.
- Story beats: the Capim rescue ("Hero Bandit Dark Emperor"), the Magician's Rules concluded,
  Will Auceptin's corpse, Derrick's staged exposure of the corrupted expedition, the Aurora Order
  hunting believers of The Fool, Stanton's disappearance and the Devil-dog master's blood letters.
- **Roselle diary interlude:** ch391 s2 (L59-121) split out per the standing rule — cast
  [Roselle Gustav, Edwards, Grimm] only; gathering resumes at ch391 s3.
- Portrait decisions PENDING: report = 82 chars, **have:16 need:23** →
  `timelines/character_report_block08.md` (Aaron Ceres, Capim, Harras, Jurgen Cooper, Katy, Parker,
  Daisy, Lawrence Nord, Mike Joseph, Talim Dumont, Utravsky, Darc Regence, Framis Cage,
  Pacheco Dwayne, Soest, Aiflor, Belize, Hibbert Hall, Kaslana, Leppard, Stelyn Sammer,
  Stephen Hampres, Will Auceptin).
- ⏭ Next tagging block: **ch414-463** (Volume 2 ends at ch482).

## Volume 2 — Block 7 (ch314-363) — TAGGED + VERIFIED 2026-08-28 (portraits + render PENDING)
- All 50 chapters scene-tagged (**125 scenes, 10:02:53**). Gates: verify_tags **182/182, 0 to fix**
  (8 verified_present — gathering epithets, Sharron's bodiless voice, Amon-by-phantom in ch363).
  verify_alignment **PASS** (0 structural, 0.59%). Continuity boundaries 313-362 written.
- Named reveals folded back: the basement vampire = **Emlyn White** (ch315-316 retagged),
  the recurring homeless man = **Kohler** (ch282+352 retagged w/ verified_present). Diary
  interludes: ch359 s3 + ch360 s1 (Roselle's FIRST entries — Huang Tao reveal; boundary 359
  carries Roselle Gustav).
- ⚠️ Lesson repeated: "Mary Gale" is NOT a registry char — tag her text-literally as "Mary"
  (ch259/340/357/358 use "Mary"; ch242/244 have the full name in-text so "Mary Gale" is fine there).
- Portrait decisions PENDING: report = 84 chars, **have:17 need:17** →
  `timelines/character_report_block07.md` (Maric, Mike Joseph, Talim Dumont, Aaron Ceres,
  Stelyn Sammer, Tyre, Jurgen Cooper, Steve, Jason, Luke Sammer, Utravsky, Hibbert Hall,
  Hilbert Alucard, Horamick Haydn, Ikanser Bernard, Kaslana, Leppard).
- ⏭ Next tagging block: **ch364-413**.

## Volume 2 — Block 6 (ch264-313) — TAGGED + VERIFIED 2026-08-28 (portraits + render PENDING)
- All 50 chapters scene-tagged (**145 scenes, 10:03:24**). Gates: verify_tags **197/197, 0 to
  fix** (8 verified_present — epithet presences: 'Justice' praying, 'The Sun' at gatherings,
  'her father' Count Hall, the golden retriever = Susie). verify_alignment **PASS**
  (0 structural, 0.76% outliers). Continuity boundaries 263-312 written.
- **Sharron revealed (ch278)**: Miss Bodyguard = "Sharron" (wiki char, official card
  `Sharron Cropped.jpg` already on disk). Added character_map entry "Sharron" → that image and
  retroactively retagged all 24 "[pale woman in black regal dress]" scenes (ch246-263) to
  "Sharron" with verified_present citations + updated 5 continuity boundaries. NOTE: she is
  DISTINCT from "Sharon" the Backlund madam (ch174/196-199, Sharon.png).
- Diary interludes: ch264 s5 + ch265 + ch266 s1 (Bornova/Bernadette/Ciel/Zaratul/Floren pages,
  carried across both cuts via Roselle Gustav); ch290 s2 (single page, no named figures).
- Mr. World (Klein's puppet at gatherings) is tagged as bracketed "[The World]" everywhere.
- Portrait decisions PENDING: report = 91 chars, **have:17 need:16** →
  `timelines/character_report_block06.md`. The 16: Lanevus, Utravsky, Luke Sammer, Mike Joseph,
  Stelyn Sammer, Talim Dumont, Kapusky Reid, Kaslana, Kaspars Kalinin, Jurgen Cooper, Leppard,
  Millet Carter, Rafter Pound, Williams, Hibbert Hall, Tracy. (Isengard Stanton + Sharron
  already have art from Vol-1 installs/wiki.)
- ⏭ Next tagging block: **ch314-363**.

## Volume 2 — Block 5 (ch214-263) — TAGGED + VERIFIED 2026-08-28 (portraits + render PENDING)
- All 50 chapters scene-tagged by careful reading (**176 scenes, 10:13:58**), Volume-1 conventions
  + the ch215 base flip Klein Moretti → **Sherlock Moriarty** (wired in project.json; scenes from
  ch215 on tag "Sherlock Moriarty"; "The Fool" for gray-fog/Tarot as before, persona null for
  member-only scenes). ch214-218 were tagged in an earlier session; ch219-263 this session.
- **Gates:** verify_tags 214-263 = **184/184, 0 to fix** (9 verified_present w/ citations — e.g.
  Mr. A as the Shepherd assassin in ch249 s1; 'the two of them' + Susie the retriever courier in
  ch244 s3). verify_alignment 214-263 = **PASS** (0 structural, 0.60% outliers, median
  14.18 c/s; ch250 is the one no-title-echo MP3). Continuity boundaries 213-262 written
  (39 continue / 11 breaks; 213 carries the Vol1→Vol2 volume break note).
- **Roselle diary interludes applied:** ch216 s7→ch217→ch218 s1 (Mr. Door pages; carried across
  BOTH cuts, boundaries 216/217 carry Roselle Gustav) and **ch237 s1** (Zaratul/Matilda/Fan Esti/
  Savigny+Nast Solomon pages; boundary 236 marked continues=false with note — the reading starts
  exactly at the ch237 cut, so the interlude cast swap lands on the chapter boundary).
- Alias notes: added Bakerland→Bakerland Jean Madan, Kance→Kance Leerhsen. Do NOT alias names
  that lack a registry entry ('Fan Esti', 'Mary') — the verifier then checks the unknown canonical
  and flags INVENTED; leave them text-literal (learned this session, 2 rounds of fixes).
- Recurring unnamed figure: Klein's 1000-pound ghost bodyguard = "[pale woman in black regal
  dress]" (ch246-263, 15 scenes) — kept bracketed (never named in text).
- **Portrait decisions PENDING (user):** report = 89 chars, **have:15 need:17** declined:2
  minor:15 unnamed:40 → `timelines/character_report_block05.md`. The 17: Kaspars Kalinin,
  Stelyn Sammer, Maric, Millet Carter, Bakerland Jean Madan, Doragu Gale, Jurgen Cooper,
  Aaron Ceres, Black Snake, Leppard, Luke Sammer, Meursault, Hibbert Hall, Nast Solomon, Rosago,
  Savigny Solomon, Talim Dumont. (Nast/Savigny Solomon appear ONLY in the ch237 diary interlude.)
- ⏭ After portraits: `compose_frames.py --block --contact-sheet` → `render_chapter.py 214 263`
  → `build_block_video.py` (per BLOCK RECIPE steps 7-9). **Next tagging block: ch264-313.**

## Block 4 (ch151-200) + tail (ch201-213) — TAGGED + VERIFIED + RENDERED 2026-08-27
- Block 4: 181 scenes, 9:51:51; verify_tags 237/237 (5 verified_present w/ citations — e.g. 'the
  three Nighthawks' returning from Morse Town); alignment PASS (0 structural, 0.61% outliers).
- Tail: 54 scenes, 2:39:30; verify_tags 67/67; alignment PASS (0.89%). Continuity 150-212 done.
- Roselle diary interlude at ch158→159 (carried across the cut). Ince Zangwill has wiki art
  already; the ch210 notebook chapter renders as Zangwill solo.
- **Portrait decisions DONE 2026-08-27 — all 7 yes**, user-supplied via the clipboard-grab flow
  (grab verified against the paste every time): Isengard Stanton, Sharon, Ace Snake, Qilangos,
  Pallas Negan, Hood Eugen, Crestet Cesimir. Report: **have:32 need:0 declined:2**.
  Framing notes worth reusing: Sharon/Qilangos/Hood Eugen were wide stills → cropped to the
  subject then PADDED to ~1:1.3 with backdrop-dark; Ace Snake and Pallas Negan needed bystanders
  trimmed out; Crestet Cesimir was already portrait-framed and went in untouched; **Isengard's
  first crop cut him at the waist to dodge the cover title — redone to show the whole figure with
  the publisher logos + "17" badge inpainted out** (feathered-blur heal, 3 passes; see his
  `_note`). Cover title text across his coat is unavoidable and matches the Klein Moretti card.
- Frames: **128 distinct sets** composed + contact sheet, eyeballed.
- **RENDERED: all 63 mp4s (151-213), 0 errors.** Also re-rendered **ch117, 142, 145, 146** —
  Hood Eugen is in 117/142 and Qilangos in 145/146, block-3 chapters already rendered before their
  art existed. ⚠️ Standing lesson: after installing a portrait, grep the scene tags for that name
  across ALL blocks, not just the current one, and re-render any already-rendered chapter that
  gains a portrait.
- ✅ **Volume 1 complete: ch1-213 rendered, verified on disk, no gaps.**
- **Volume concat BUILT 2026-08-27:** `Block_01_ch001-213.mp4` (43:18:36, 3.40 GB, stream-copy,
  duration verified) + `_description.txt` (213 markers) in
  `D:/PDFReader/lotm_book1_output/character_video/`.
  ⚠️ Windows Explorer shows its Length as **19:18:36** — that's a 24-hour display wraparound
  (43:18:36 − 24 h), NOT a short file; ffprobe confirms both streams at 155,916 s and a frame
  decodes at 43:10:00 inside ch213.
- **USER SPOT-CHECK PASSED 2026-08-27** ("everything looks good") — checked the individual chapter
  mp4s: finale ch213 (plays to the end, family closing frame), all new-art chapters (190-192
  Qilangos/Pallas/Ace Snake, 196+199+174 Sharon, 166 Crestet, 157 Isengard re-crop), the four
  block-3 re-renders (117, 142, 145, 146), diary interludes (145, 159), ch185 Lanevus vision rule,
  ch201 tail start, ch210 single-cut. **The volume video is APPROVED for upload.**
- **Upload package READY 2026-08-27 — see `YOUTUBE_UPLOAD_PLAN_VOL1.md`** (title, description,
  tags, pinned comment, thumbnail drafts, trend analysis, Studio upload procedure + 12-hour-limit
  fallback). Key gotcha solved there: the full titled timestamp list (7,960 chars) exceeds the
  5,000-char description limit → description carries **every-10-chapter markers** (22 titled
  entries, `_description_YOUTUBE.txt`, 1,976 chars — user decision 2026-08-27) and the pinned
  comment carries **every chapter** with titles (`_pinned_comment.txt`, 7,957 chars).
- **Series thumbnail template ESTABLISHED 2026-08-27** (user decision): every volume block video
  uses the same background — the Fool-above-his-personas puppet-stage promo art (user-supplied
  via clipboard, verified, installed at `tts_pipeline/assets/channel/thumbnail_bg_fool_stage.png`)
  — with only the text changing per volume. Generator: `character_scene_video/make_thumbnail.py N
  --name "..." --chapters N --hours H` → `thumbnails/thumb_volNN.jpg`. Vol 1 generated (227 KB).

## Block 3 (ch101-150) — TAGGED + VERIFIED 2026-08-27, awaiting portrait decisions
- All 50 chapters scene-tagged by careful reading (175 scenes, 9:47:12), block-1/2 conventions:
  text-literal names, base persona "Klein (Beginning)" (build flips), "The Fool" for gray-fog/Tarot,
  [brackets] for unnamed, **vision rule applied** (dream/vision/memory figures only in `setting` as
  "(visions only: …)" — e.g. ch105 spirit channeling, ch126 Trissy-on-train future vision, ch133
  Elizabeth's dream knight, ch140 the Eternal Blazing Sun).
- **Gates:** verify_tags 101-150 = **241/241, 0 to fix** (4 new verified_present entries with
  citations; one is a source TYPO — ch141 L89 "Fyre sat behind the typewriter" = Frye).
  verify_alignment 101-150 = **PASS** (0 structural, 1.18% outliers, median 14.20 c/s; 50/50
  chapters ≥99.5% boundary match). Continuity boundaries 100-149 written (38 continue, 12 breaks).
- **Quirk:** ch129's text file ends with a ~40-line translator's/author's note (it IS in the audio).
  Tagged as a final cast-less scene → renders the default throne cover; its rate outliers explain
  the 1.18% figure (still well under the 2% budget).
- New aliases: Cohen Quentin→Quentin Cohen (text reverses his name), Derrick→Derrick Berg.
  Derrick Berg (The Sun, 12 scenes) already has a portrait.
- **Portrait decisions COMPLETE (2026-08-27): all 6 yes** with user-supplied art via clipboard-grab
  (every capture visually verified against the paste before install — Selena-lesson honored):
  Glaint (7 scenes), Swain (6), Daxter Guderian (3), Mr. A (2), Sirius Arapis (2), Megose (1).
  All flagged manual/do-not-re-fetch in `character_map.json`; decisions recorded; report shows
  **need:0** (Gawain stays declined). ⚠️ Gotcha hit + fixed: the block timeline had been built
  BEFORE the installs, so `compose_frames --block` silently skipped the new casts (still cached as
  missing_images). Re-ran `build_block.py 101 150` → all 6 resolve in exactly their expected scene
  counts, 0 missing wiki chars; `compose_frames --block --contact-sheet` → 89 distinct sets (+6),
  new multi-cast frames (salon trio, 5-person secret gathering) eyeballed and clean.
  **Next: `render_chapter.py 101 150` (spot-check a few), then optional Block_03 concat.**

## Roselle diary-reading interludes (user ruling 2026-08-27) — NEW STANDING CONVENTION
- Rule now in TAGGING_GUIDE.md: when The Fool reads Roselle's diary pages **during a Tarot
  Gathering**, a break scene [The Fool + Roselle Gustav + anyone named in the pages] replaces the
  gathering cast for exactly the reading's lines; members resume after. Only gathering readings —
  the diary-collection commissioning (ch34-35), solo fog readings (ch95/100), the Antigonus diary
  (ch61), and casual Roselle quotes stay untouched.
- **Applied everywhere:** block 3 ch113 s4→ch114 s1 and ch144 s2→ch145 s1 (readings span the
  chapter cuts; boundary 113/144 now carry Roselle Gustav; 2 verified_present entries since the
  short spans don't literally say 'Roselle'); block 2 ch59 s2 (Roselle+Grimm+Edwards+Matilda+
  Zaratul) and ch93 s2 (Roselle+Zaratul). Block 1 has NO gathering readings (checked ch1-50).
- Roselle Gustav's official card was already fetched; the new Fool+Roselle frame composed and
  eyeballed (90 distinct sets). All gates re-run: blocks 1/2/3 = 168/168, 255/255, 248/248, 0 to fix.
- ✅ **ch59 + ch93 re-rendered 2026-08-27** with the interludes, and **all of block 3 (101-150)
  rendered** in the same run (52/52, 0 errors; ch131's +1.7s flag = benign 1fps rounding past the
  audio end). Chapter mp4s now contiguous **ch1-150**. User is spot-checking the Tarot scenes.
- ✅ **Extension (same day, user follow-up): ch20-21 — Roselle's FIRST introduction** (Old Neil
  hands Klein the three pages; reading spans the ch20→21 cut). Interlude added with persona Klein
  (not The Fool — he's physically in the archive): ch20 s5 (16:24-16:47) + ch21 s1 (0:00-3:58,
  + Florena/Ithaca named in the pages). Boundary 20 now carries Roselle Gustav (was Old Neil);
  ch21's old Leonard verified_present renumbered s3→s4 (⚠️ splits shift scene indexes — check the
  whitelist). Block 1 = 158 scenes, 172/172 tags; Klein+Roselle frame composed (91 sets);
  **ch20 + ch21 re-rendered**.
- ✅ **Diary-figure decisions CLOSED 2026-08-27: Zaratul YES** (user-supplied Thai vol-33 cover,
  clipboard-grabbed + verified, cropped (0,85)-(428,445) to drop logos/title — crop box in
  character_map.json; ch59 + ch93 re-rendered with him); **Grimm + Edwards NO** (recorded in
  portrait_decisions.json). Block 2 report = need:0. Zaratul's first crop was near-square and
  rendered him double-wide (compositor scales to COMMON HEIGHT, width follows aspect) — re-cropped
  narrower (105,85)-(345,445), stale cached frame deleted (cache only regenerates missing files),
  recomposed, ch59+ch93 re-rendered again. ⚠️ **PORTRAIT INTAKE RULE (user ruling 2026-08-27):
  the compositor never crops (it scales to common height, aspect preserved, rows centered) — so
  never hand-crop through a subject to force a narrow aspect. Instead take the FULL figure and
  PAD vertically with backdrop-dark (14,13,19) to ~1:1.5, subject centered; the bands melt into
  the frame background.** (Zaratul redone this way — third and final version.) Changed art under
  the same filename needs its stale cached frame deleted before compose_frames. The no-wiki diary names (Florena, Ithaca, Matilda,
  Florais, Fan Estin) stay portrait-less by the same user ruling.

## Session handoff (2026-08-27 end)
- **Blocks 1 AND 2 fully rendered** (ch1-100, badge + #N labels, default-image fallback live).
  `Block_01_ch001-050.mp4` (10:52:07) built; block-2 chapter mp4s ready for concat when wanted.
- **Late fixes this session:** Selena.jpg was accidentally Elizabeth's image (clipboard-grab timing;
  re-grabbed + verified, ch84-87 re-rendered, Selena confirmed only in ch84-87). Vision-figure tags
  removed from ch90 s3 / ch100 s1 → NEW TAGGING RULE in TAGGING_GUIDE.md: dream/vision/memory
  figures never go in other_characters (setting note "(visions only: …)" instead).
- **Portrait intake technique:** user pastes images in chat -> they do NOT hit disk; grab via
  PowerShell STA clipboard script (scratchpad grab_clip.ps1 pattern) and ALWAYS verify the capture
  visually against the paste before installing (that skipped check caused the Selena mixup).
- **Next:** (1) tag Block 3 (ch101-150) per CLAUDE.md BLOCK RECIPE + the new vision rule;
  (2) user still owes the upload-size decision (Block_01 as unlisted test vs volume-scale ch1-213).

## Generalized per-project (2026-08-26)
- The pipeline is now a **shared engine + per-project config**, same pattern as tts_pipeline.
  All book-specific data lives in `projects/<name>/` (config `project.json`, scene tags,
  alignment, aliases, continuity, portrait decisions, built timelines, frame cache).
  Every script takes `--project NAME` (default `lotm_book1`, or env `CHARVID_PROJECT`).
  New-book checklist: `charvid_project.py` docstring + `projects/_TEMPLATE/project.json`.
- Book-specific persona logic moved into config: `persona.map`, `persona.base_flips`
  (ch17 Nighthawks flip AND the ch215 Sherlock flip are now wired; Gehrman/The Fool stay
  scene-tagged), `persona.image_names`.
- **New: `build_block_video.py` (stage 6)** — concats a block's chapter MP4s (stream copy,
  uniformity-checked) into one upload file + writes the `0:00 Chapter N: Title` description
  for YouTube chapter markers. `--plan` first.
- Robustness fixes from the 2026-08-26 audit: block naming/lookup no longer hardcodes block 1
  (auto by range / by chapter); volume folders no longer hardcode `Volume_1_Clown` (block 5+
  crosses volumes); hold-previous now seeds across blocks (`seed_prev_images`) and the renderer
  bills leading hold time to the first real frame instead of silently dropping it; a missing
  portrait file is now a HARD ERROR in the compositor (was: silently dropped from the frame);
  `verify_tags` gained `--recall` (triage sweep for portrait characters named in a scene's text
  but not tagged — presence-vs-mention stays a human call; 75 candidates in block 1, mostly
  Evernight Goddess prayer mentions) and a real exit code.
- **Everything re-verified after the refactor:** alignment gate PASS (0 structural, 0.87%
  outliers), tags 168/168, block rebuild + ch1 realign byte-identical, render previews and
  stage-6 plan correct.

## Where the work lives (IMPORTANT)
- **All of this is on `master` in the main repo** (`C:\Users\paolo\Work\Projects\LOTM\pdf-reader`).
  Work directly there. The `feature/book1-character-scene-videos` branch and the
  `pdf-reader-charvid` worktree were merged and deleted 2026-06-23 — ignore any older instruction
  to "stay in the worktree".
- Gitignored (not committed, regenerable): `formatted_text/`, the EPUB, the character image
  binaries under `tts_pipeline/assets/characters/lotm/`, and the composited frame cache
  `character_scene_video/projects/*/frames/`.
- **Run scripts with `py -3.12`, not `python`** — `python` on this machine is 3.11 and lacks deps.

## Block 2 (ch51-100) — TAGGED + VERIFIED 2026-08-27, render pending portrait decisions
- All 50 chapters scene-tagged by careful reading (137 scenes, 10:07:58 total), following the
  block-1 conventions exactly: text-literal names, base persona "Klein (Beginning)" (build flips),
  "The Fool" for gray-fog/Tarot scenes, [brackets] for unnamed figures.
- **Gates:** verify_tags 51-100 = 251/251, 0 to fix (11 new verified_present entries, each with a
  why-citation — e.g. Borgia driving the carriage he boarded one line before the scene break).
  verify_alignment 51-100 = PASS (0 structural, 0.80% outliers, median 14.15 c/s; 50/50 chapters
  100% boundary match). Continuity boundaries 50-99 written (43/50 continue).
- **Aligner fix found by the gate:** ch66's final short line was squeezed to zero by a boundary
  matched to the file's trailing silence; `_find_squeezed` now also repairs any unit under 0.05s
  (block-1 outputs verified byte-identical after the fix).
- New aliases: Angelica->Angelica Barrehart, Benson/Melissa->full names, Kenley->Kenley White,
  Azik/Mr. Azik->Azik Eggers.
- **Portrait decisions COMPLETE (2026-08-27):** 9 yes with user-supplied art (Lorotta, Aiur Harson,
  Borgia, Selena, Elizabeth, Kenley White, Ademisaul, Seeka Tron, Ray Bieber — donghua stills/manhua
  panels captured via the clipboard-grab flow, all flagged manual in character_map.json), 3 declined
  for now (Gawain, Jack, Naya — reversible). **NEW: default-image fallback** — `default_image` in
  project.json (`_default_scene.jpg`, the official throne cover): when a scene's cast has NO
  portraits, the cover is shown instead of holding the previous frame (user decision — holding
  falsely implied the prior cast, e.g. Alger over the ch53 Jack scene). Supersedes DESIGN §6's
  hold-previous for this project; template documents the knob. Affects 7 block-2 chapters
  (53,55,56,66,81,82,83); block 1 has zero such scenes, its renders untouched.
- (was) BLOCKED ON USER — 12 portrait decisions (see timelines/character_report_block02.md):
  Aiur Harson, Borgia, Lorotta (the Backlund escort trio, ch71-78 battle arc — most screen time),
  Elizabeth, Selena (banquet/mirror arc), Kenley White, Ademisaul, Gawain, Jack, Naya, Ray Bieber,
  Seeka Tron. After decisions: source portraits, then render 51-100 per chapter (badge label
  auto-applies), then Block_02 concat or hold for the Volume-1 (ch1-213) concat.
- Recall sweep: 63 triage candidates (mostly mentions: Glacis being discussed, the Goddess
  invoked in prayers) — spot-check during timeline review, none block rendering.

## What's done (Block 1 = chapters 1–50)
- **Audited clean:** 50/50 chapters tagged, 156 scenes, total ≈ **10:52:09**, verifier **168/168, 0 to fix**.
- Pipeline proven end to end: scrape → registry → scene-tag → image-resolve → **align → timeline →
  composite → render** → verify → reports. **A real chapter video has been produced and checked.**

### Timing is REAL now (M3 done, 2026-08-01)
Durations are no longer char-share estimates. `align_chapter.py` forced-aligns each chapter's text
against its own MP3 and writes `align/ch_<N>.json` (start/end seconds for every spoken line).
- **Not aeneas/WhisperX.** The audio is Azure TTS of text we already have, so no acoustic model is
  needed — and aeneas needs espeak + a C build that is painful on Windows. Instead we detect
  silences with ffmpeg and monotonically match the text's sentence sequence to the audio's pause
  sequence with a DP. Zero new dependencies; a chapter aligns in a couple of seconds.
- **Result over ch1–50:** 100% of sentence boundaries matched to real pauses, **0 structural
  errors**, 31/3560 lines (0.87%) with an odd implied speaking rate, median **14.07 chars/sec**
  (per-chapter 13.20–14.79). `verify_alignment.py` is the gate and currently reports **PASS**.
- Versus the old estimates, scene starts moved a median of **1.1s** (p90 6.8s, max 13.8s) — so the
  estimates were decent, but alignment removes the tail.
- **Gotcha it uncovered:** book-1's MP3s were synthesised *before* `epub_to_text` learned to drop the
  leading body echo of the chapter title, so **47 of 50** chapters read the title twice while the
  current text has it once. `has_title_echo()` detects this per chapter; without it the first body
  line of those chapters was mistimed.

### Compositor + renderer (M4 done)
- `compose_frames.py` — row/grid frames on a 1920×1080 dark backdrop, portraits normalised to a
  common height, no captions, cached by the *set* of portrait filenames. Block 1's 156 scenes need
  only **37 distinct frames** (cast sizes: 8×1, 15×2, 13×3, 1×5).
- `render_chapter.py` — cuts the frames on the aligned timestamps and muxes the existing MP3
  (stream copy). Matches the existing book-1 format: 1920×1080, **1 fps** (the picture only changes
  at scene boundaries), h264. Auto-detects NVENC and **falls back to libx264** — NVENC is listed by
  ffmpeg on this machine but `nvcuda.dll` fails to load, so it currently encodes on CPU.
- **Rendered and visually verified:** `Chapter_1.mp4` (621.0s, 12.8 MB, 2 cuts) and `Chapter_5.mp4`
  (890.2s, 19.2 MB, 5 cuts) in `D:/PDFReader/lotm_book1_output/character_video/`. Ch5 is the
  gray-fog test and steps correctly Klein → The Fool → Audrey → Alger → all three together.
  Encoding runs ~200× realtime, so the full 10.9-hour block is only a few minutes of CPU.

## The 4 things to review (your ask)
| What | File | Notes |
|---|---|---|
| **Character mapping** | `tts_pipeline/assets/characters/lotm/character_map.json` | 26 characters + Klein persona cluster (Zhou Mingrui → Klein (Beginning) → Klein Moretti → The Fool / Sherlock / Gehrman …). Open roster — add images anytime (`_adding_images`). |
| **Continuity** | `continuity.json` | All 49 ch1–50 boundaries: **42 continue, 7 hard breaks** (7,8,29,33,36,47,49). Carries cast across cuts. |
| **Scene timeline** | `timelines/block_01_ch001-050.md` | Chapter-by-chapter, scene-by-scene: start · duration · present cast · images · missing. `↳` marks continuations. |
| **Scene character participation** | `timelines/character_report_block01.md` | **The "who needs a portrait" view** — every character, portrait status, scene count, chapters, and grounded context. |

**Portrait decisions for Block 1 are DONE** (recorded in `portrait_decisions.json`). Current report:
`have:23  need:0  declined:2  minor:9  unnamed:34`.
- **23 have portraits** — the original 6 (Klein, Dunn Smith, Leonard Mitchell, Audrey Hall, Alger Wilson, Daly Simone),
  the 4 added earlier (Old Neil, Melissa, Rozanne, Benson), plus the **13 just decided yes**: Angelica Barrehart,
  Frye, Glacis, Annie, Earl Hall, Azik Eggers, Quentin Cohen, Wendy Smyrin, Aguesid Negan, Hanass Vincent, Susie,
  Royale Reideen, Elliott Vickroy.
- **2 declined** (🚫 no portrait, by decision): Bredt, Mr. Franky.
- 9 minor (no wiki page); 34 unnamed extras — left as-is.

Sourcing: 12 of the 13 yeses are wiki picks fetched via `fetch_named_portraits.py` (File: titles all validated,
0 failed). **Azik Eggers** is a manual crop of `Azik_Eggers_Official_Full.webp` (1000x5950 → top 1000x2224); source +
crop box noted in its `character_map.json` entry. Portrait binaries stay gitignored/regenerable.

## Key decisions locked
- Timing = **per-chapter forced alignment** (aeneas), combine by cumulative offset. (Not yet run — durations are
  char-share ESTIMATES.)
- Display = **scene-presence**; multiple characters → normalized row/grid; **fallback = hold previous frame**.
- Klein persona base flips **Klein (Beginning) → Klein Moretti at ch17** (Nighthawks contract). Tarot scenes → The Fool.
- **Anti-hallucination:** readers use text-literal names (`TAGGING_GUIDE.md`); `verify_tags.py` grounds every tag
  against the source; `name_aliases.json` holds canonical merges / `exclude` / `verified_present`.
- Assets = wiki-wide `<Name> Official.jpg` (35 char portraits + 11 place images); Susie is a real character (kept).

## How to resume (run from the repo root)
```
py -3.12 character_scene_video/align_chapter.py 1 50        # forced alignment -> projects/<p>/align/ch_N.json
py -3.12 character_scene_video/verify_alignment.py 1 50     # timing gate, must say PASS
py -3.12 character_scene_video/build_block.py 1 50          # rebuild block timeline (uses align/)
py -3.12 character_scene_video/verify_tags.py 1 50          # must be 0 to fix (add --recall for triage sweep)
py -3.12 character_scene_video/build_character_report.py 1 50
py -3.12 character_scene_video/compose_frames.py --block --contact-sheet   # frames + review sheet
py -3.12 character_scene_video/render_chapter.py 5 --preview              # cut plan, renders nothing
py -3.12 character_scene_video/render_chapter.py 1 5                      # actually render
py -3.12 character_scene_video/build_block_video.py 1 50 --plan           # stage 6 readiness
py -3.12 character_scene_video/build_block_video.py 1 50                  # block MP4 + description
```
All take `--project NAME` (default `lotm_book1`).
To correct a scene: edit `projects/lotm_book1/timelines/scenes/ch_<N>.json`; to merge/rename a character: `projects/lotm_book1/name_aliases.json`;
to mark a confirmed presence the verifier flags: `verified_present` in `name_aliases.json`.

## Open threads / next steps
1. ✅ **Portrait decisions done** (`portrait_decisions.json`): 13 yes (sourced), 2 declined; need:0.
2. ✅ **Timing** — forced alignment built and passing (see above). No aeneas needed.
3. ✅ **Compositor + renderer** — built; ch1 and ch5 rendered and visually verified.
4. ✅→🔶 **Portrait source quality — the two hard problems are FIXED (2026-08-26).** User supplied
   replacement art, installed at the same canonical filenames (map/decisions/timelines untouched),
   frame cache regenerated, and verified inside real rendered frames (ch20 + ch41):
   - **Old Neil**: user-supplied donghua still replaces the Tencent-watermarked poster.
   - **Susie**: user-supplied fan art (chess scene, Audrey in background — fine: her only block-1
     scene has Audrey in the cast) replaces the golden-retriever photo.
   - Both entries are now flagged manual in `character_map.json` and **disabled in
     `fetch_named_portraits.py`** so a wiki re-fetch can't clobber them.
   - Remaining (accepted for now): anime screenshots (Frye, Rozanne, Benson, Melissa…) sit beside
     the tall official cards — mixed styles/head sizes; official cards carry the baked-in logo.
   Original note kept below for history:
   ⛔ *(was)* **portrait source quality.** The compositor is correct, but the contact sheet
   (`frames/_contact_sheet.png`) shows the *inputs* are inconsistent, and this is the one thing that
   will be obvious to a viewer. Decide before rendering the block:
   - **Old Neil** is a promotional poster: it has a **腾讯视频 (Tencent Video) watermark** and the
     words "Old Neil" printed across it. It is not a portrait.
   - **Susie** resolves to a photo of a **golden retriever**. Correct per the "Susie is a real
     character" decision, but worth a conscious yes/no for on-screen use.
   - Several picks (Frye, Rozanne, Benson, Melissa…) are **anime screenshots** — wide busts with
     their own backgrounds — sitting beside the tall official character cards. Mixed styles and
     mixed apparent head sizes.
   - The official cards have the **诡秘之主 / Lord of the Mysteries logo and a copyright line**
     baked in, which is fine but does show on screen.
   Fixing means re-picking images in `portrait_decisions.json` / `character_map.json` and re-running
   `fetch_named_portraits.py`; the frame cache regenerates automatically.
5. **Per-chapter verification loop (user-chosen workflow, 2026-08-26): render → human-check →
   fix → concat only at the end.** **BLOCK 1 PRODUCED 2026-08-26:** user approved test renders, then
   the folder was cleared and all 50 chapters re-rendered with the final label style — **top-left
   circular Bread Moretti badge + bold white `#N`** (render-time ffmpeg overlay; config
   `chapter_label` in project.json {enabled/template/fontsize/badge/badge_size}; badge assets in
   `tts_pipeline/assets/channel/`; frame cache untouched). 50/50 rendered, 0 errors →
   `Block_01_ch001-050.mp4` **10:52:07, 0.85 GB** + `_description.txt` (50 YouTube chapter markers),
   in `D:/PDFReader/lotm_book1_output/character_video/`. Upload size still TBD (user decision).
   The repeatable per-block recipe is in CLAUDE.md → "BLOCK RECIPE". Loop per chapter:
   watch the mp4 with `timelines/block_01_ch001-050.md` open (each scene: time · cast · anchor);
   to fix, edit `timelines/scenes/ch_N.json` (or `name_aliases.json`), then
   `build_block.py 1 50` + `render_chapter.py N --force`. When all 50 are approved:
   `build_block_video.py 1 50` (concat + YouTube-chapter description).
   **Upload viability (researched 2026-08-26):** our 50-ch blocks are 9.9–10.9 h — under YouTube's
   documented 12 h/256 GB cap, so fine. AudioVerse's 38–137 h videos are **ordinary uploads, not
   livestreams** (checked via API: 0/15 of their >12 h videos have liveStreamingDetails) — the
   documented 12 h limit is evidently not enforced against large files under 256 GB. If we ever
   want AudioVerse-scale multi-block videos, test once with a >12 h concat (ours are tiny:
   ~1 GB/10.9 h, so even 100 h ≈ 9 GB); fall back to ≤12 h blocks if rejected.
6. **Tag Block 2 (ch51–100)** — text-literal guide + auto-verify + continuity from the start.

## Known limits (honest)
- ~0.9% of lines still land on a slightly wrong timestamp (a boundary slips by a few seconds
  between two adjacent lines). 7 of 156 scenes sit near one. Effect on screen is a portrait
  changing a few seconds early or late inside a 3-minute scene.
- Alignment assumes the text matches the audio. It does *not* for the title echo (handled), and it
  would not if any chapter's MP3 were regenerated from different text — re-run alignment if audio
  is ever re-synthesised.
- Shortest scene in block 1 is **3.1s** (ch3), so one portrait flashes briefly. No minimum-duration
  merging is applied; say the word if you want short scenes absorbed into their neighbour.
- The copyright posture from DESIGN.md §8 is still undecided and still applies.

## File map (character_scene_video/)
- `DESIGN.md` — full design + decisions + milestones (+ §10 timeline schema, continuity, alignment).
- `TAGGING_GUIDE.md` — anti-hallucination tagging rules.
- `scrape_official_images.py` — wiki-wide portrait scraper (→ `_manifest.json`, binaries gitignored).
- `build_character_registry.py` → `character_registry.json` (384 Book-1 chars + portrait coverage).
- `build_block.py` → `timelines/block_01_*.md/.json` (the timeline; applies personas, aliases, continuity).
- `build_character_report.py` → `timelines/character_report_block01.md` (participation/decision view).
- `verify_tags.py` — source-grounding gate.
- `fetch_named_portraits.py` — downloads human-chosen non-Official wiki portraits (File: title → `<Canonical>.<ext>`).
- `portrait_decisions.json` — yes/no portrait ledger; build scripts read it (yes→sourced, no→🚫 declined bucket).
- `timelines/scenes/ch_*.json` — raw per-chapter scene tags (source of truth for content).
- `align_chapter.py` → `align/ch_<N>.json` — forced alignment; per-line start/end seconds.
- `verify_alignment.py` — timing gate (structural checks + implied speaking-rate sanity).
- `compose_frames.py` → `frames/<hash>.png` — portrait row/grid frames, cached by cast set
  (gitignored; `--contact-sheet` writes one PNG of every distinct frame for review).
- `render_chapter.py` → `<video_out>/<Volume_dir>/Chapter_<N>.mp4` (e.g.
  `D:/PDFReader/lotm_book1_output/character_video/Volume_1_Clown/Chapter_5.mp4`). Output is
  organized BY VOLUME since 2026-08-28: `charvid_project.Project` derives each chapter's volume
  folder from the text layout (`volume_dir_of` / `video_dir` / `chapter_video` helpers), all
  existing Volume-1 files were migrated into `Volume_1_Clown/`, and `build_block_video.py`
  refuses ranges that cross a volume boundary. Upload packs are stage 7
  (`make_upload_pack.py --volume N`, config in `projects/<name>/upload_meta.json`); thumbnails
  land in `<Volume_dir>/thumbnails/`.

---

# History — moved out of CLAUDE.md on 2026-10-07 (verbatim)

Original line numbers refer to CLAUDE.md @ 13dd43f.

## [CLAUDE.md lines 37-119] Current state (2026-08-28) + running ledger

### Current state (2026-08-28)
- ✅ **VOLUME 1 CONTENT COMPLETE:** ch1–213 tagged, verified, rendered (0 gaps, verified on disk).
- **12 h cap is ENFORCED by YouTube** (43 h single upload rejected 2026-08-28). Volume 1 uploads as
  **4 parts**, all built + packed in `D:/PDFReader/lotm_book1_output/character_video/Volume_1_Clown/`:
  ch1–50 (10:52:07) / 51–100 (10:07:56) / 101–157 (11:08:29) / 158–213 (11:10:03).
- ✅ **VOLUME 1 UPLOADED 2026-08-28, all 4 parts public** (verified via API + Studio 2026-08-29):
  P1 `sQ94crQVoAQ` / P2 `AfBLteZ9nfU` / P3 `Qi3hZkRr_j0` / P4 `8lha69vkmCE`; all in playlist
  `PLQD_MWrZYC-I` ("…Large Audiobook — Volume 1: The Clown") AND the per-chapter
  "LOTM - Volume 1: CLOWN" playlist. Day-1 analytics (impressions/CTR/views/uniques):
  P1 1.4K/1.7%/101/24 · P2 849/1.3%/33/12 · P3 207/1.0%/9/3 · P4 1.7K/0.9%/59/21; traffic
  ~50–89% Browse. **CTR test assets ready 2026-08-29 — see
  `character_scene_video/CTR_TEST_PLAN_VOL1.md`**: 3 thumbnail variants in
  `<Volume_dir>/parts/Part_1_ch001-050/thumbnails/thumb_vol01_p1_var{A_row,B_faces,C_strip}.jpg` + paste-ready
  description line-1s + title options. Sequencing: thumbnail Test & Compare on P1 first,
  description line 1 on all parts now, title change only after the thumbnail test. **Done
  2026-08-29:** thumbnail Test & Compare started + line-1 rewrites applied by user (verified via
  API); cross-link line prepended via API to the top-25-viewed Vol-1 per-chapter videos
  (casual wording, links `watch?v=sQ94crQVoAQ&list=PLQD_MWrZYC-I` so autoplay chains parts;
  script idempotent in session scratchpad `crosslink_batch.py`). **End screens verified via
  Studio 2026-08-29: P1→P2→P3 chained ✅, P4 has NONE ❌** — add manually (Vol-1 playlist +
  subscribe now; swap to Vol-2 P1 when live). **First vertical Short built 2026-08-29:**
  `<Volume_dir>/shorts/short_accidental_god_v1.mp4` (69 s, ch1+6+7 "accidental god" comedy
  compilation; commentary captions carry the humor over the monotone TTS; beats timed via
  `align/ch_N.json` lines; build script + upload notes + next-Short candidates in the same
  folder — upload manually, set Related Video → P1). **Community post PUBLISHED 2026-08-29**
  (posted by Claude via CDP/Studio; text matched the channel's casual voice — see the existing
  posts before drafting another — with the P1 video card attached; reusable CDP driver:
  scratchpad `cdp.py`, "Create post" opens the composer on www.youtube.com, not Studio).
  Still TODO: upload the Short, P4 end screen, manual pinned comments on the top ~5 chapter videos.
- **Volume 2 (ch214–482, `Volume_2_Faceless`) TAGGING COMPLETE (2026-08-28):** Blocks 5–10
  (ch214–482) tagged + verified (176+145+125+159+143+68 scenes, ~54:11 total; tags 208/208,
  197/197, 182/182, 220/220, 217/217, 102/102; alignment PASS all). Sharron (Miss Bodyguard,
  ch244+) mapped to her existing wiki card. **Portrait decisions COMPLETE 2026-08-28 — need:0 in
  all six blocks** (10 installed, everyone else answered 'no for now'; see the ledger below).
  ⏭ **Next for Vol 2: frames → render → pack** (new tagging would be Vol 3, ch483+).
- **`Hero Bandit` persona added 2026-08-29** (`project.json` → `persona.map`, image
  `Hero Bandit.png`, label "Klein (as the Hero Bandit)"): Klein's black-armour/black-crown Dark
  Emperor form, which the papers name in ch382. Tagged on the 12 scenes where he is actually in it —
  ch377 s3, ch378 s1–2, ch379 s1, ch380 s1–5 (the Capim raid) and ch426 s3–4 + ch427 s1 (the Devil
  in the sewer). NOT a disguise-identity like Sherlock: it becomes a real alias only later
  (Vol 3 ch717, Dwayne Dantès in Vol 4). `image_names` also reserves Dwayne Dantès + Merlin Hermes,
  but neither has a `map` entry yet — adding one without an image would KeyError in `build_block`.
  The ch215 persona flip
  (Klein → Sherlock Moriarty) is configured in `project.json` `base_flips`; ~ch214+ MP3s
  post-date the title-echo fix (alignment's `has_title_echo()` handles either case).
- Portrait ledger: Vol 1 have:32 need:0. Vol 2 in progress — 2026-08-28: `Will Auceptin` rekeyed in
  `character_map.json` (wiki spells it `Wil`, one L) + **9 installs from user-supplied art**
  (Aaron Ceres, Jurgen Cooper, Stelyn Sammer, Maric, Talim Dumont, Utravsky, Mike Joseph,
  Ikanser Bernard, Lanevus) + **Edessak Augustus and Old Kohler 2026-08-29** (37 names left in
  `_no_for_now`; their chapters were re-rendered and the affected upload parts re-concatenated).
  **Depiction/stand-in convention adopted 2026-08-29** (user decision): resemblance art and joke
  stand-ins are allowed for characters with no official art, marked with a small white * in the
  image's top-right corner (`character_scene_video/mark_depiction.py <image>` stamps it at install)
  and disclosed once in the series `credit_line` in `upload_meta.json` ("Portraits marked with a
  small * are artist depictions or playful stand-ins"). First three: **Steve** (resemblance,
  black coat + red cloak lining), **Jason** (cartoon zombie -- wiki literally says he looks like a
  zombie), **Tyre** (werewolf under the moon). Susie + Mr. A's older fan art stays unmarked
  ("obviously for fun", grandfathered). ch347-350 re-rendered, part 3 re-concatenated, packs
  regenerated for both volumes.
  **`Darkwill` identified 2026-08-29** (user): the plump 'Apothecary'/Beast Tamer from Eye of
  Wisdom's gatherings, previously the bracketed `[fat-faced man]` — retagged to `Darkwill` in his
  13 scenes (ch239-335) with `verified_present` entries (name never on-page there), portrait
  installed (art with his owl, used as-is 648x900), blocks 5-7 rebuilt (213/202/186, 0 to fix),
  chapters re-rendered, parts 1-3 re-concatenated (durations unchanged).
  **`Kohler` -> `Old Kohler` alias added 2026-08-29** — the text says plain "Kohler", so the report
  had been mis-filing a 20-scene / 89-min recurring character as ➖ minor and never asked about him;
  standing rule + the Eye-of-Wisdom code-name rule (gathering scenes tag `Eye of Wisdom`, detective
  scenes tag `Isengard Stanton`, NEVER aliased together) are documented in `TAGGING_GUIDE.md`. Sources are Chinese/Thai cover scans, page photos and donghua stills;
  covers are hand-cropped to head/shoulders so the title, volume number and publisher logos stay out
  of frame. Aaron Ceres was re-supplied at 1210x1730 and the first cover crop superseded (old file
  parked in the session scratchpad, not deleted). Jurgen Cooper is low-res 190x267 — replace if a
  bigger source appears.
  **The other 38 Vol-2 wiki characters are recorded 'no' (2026-08-28) for lack of art, NOT because
  they're unwanted** — tracked in `portrait_decisions.json` → `_no_for_now` (names + scene weight)
  with the wiki's physical descriptions in
  `projects/lotm_book1/timelines/portrait_wanted_descriptions.md`, so lookalike art can be slotted
  in later (install → flip to `yes` → rerun `build_block.py` + `compose_frames.py`).
  Hard-declined: Kaslana/Kaspars Kalinin (2026-08-28) +
  Gawain/Jack/Naya/Mr. Franky/Bredt/Grimm/Edwards
  (+ minor never-asked bucket). New-art installs use the clipboard-grab flow (visually verify each
  capture before install); manual portraits are flagged in `character_map.json` so wiki re-fetches
  can't clobber them.


## [CLAUDE.md lines 342-526] Progress Log: character_scene_video

### character_scene_video (2026-08-29)
- Volume 1 (ch1–213): rendered complete; **all 4 parts UPLOADED + PUBLIC 2026-08-28** (IDs and
  day-1 analytics in the "Current state" section above). Obsolete 43 h `Block_01_ch001-213.mp4`
  still on disk, parked in `Volume_1_Clown/_legacy/` (delete only with user approval).
- Optional leftover: user spot-check of the 29 block-3 Tarot-gathering scenes (list generated 2026-08-27).
- **VOLUME 2 TAGGING COMPLETE 2026-08-28: Blocks 5–10 (ch214–482) TAGGED + VERIFIED**
  (176/145/125/159/143/68 scenes, ~54:11 total; verify_tags 208/208, 197/197, 182/182, 220/220,
  217/217, 102/102; alignment PASS all). Frames + render deferred per user.
- **Vol 2 portrait round started 2026-08-28:** Will Auceptin spelling fix + **Aaron Ceres, Jurgen
  Cooper, Stelyn Sammer, Maric, Talim Dumont, Utravsky, Mike Joseph, Ikanser Bernard, Lanevus** installed
  (user-supplied cover/illustration art via clipboard; Aaron Ceres re-supplied at higher res, cover
  crop superseded); **Kaslana + Kaspars Kalinin hard-declined**. The remaining **38 got 'no for
  now'** (no art found) — recorded in `portrait_decisions.json` → `_no_for_now` with scene weight,
  and their wiki physical descriptions collected in
  `timelines/portrait_wanted_descriptions.md` so the user can hunt lookalike art; flipping one to
  `yes` after installing art + rerunning `build_block.py`/`compose_frames.py` is all it takes.
- **PORTRAIT DECISIONS DONE — all six Vol-2 blocks rebuilt + verified 2026-08-28: need:0 everywhere,
  verify_tags 208/198/182/220/217/102, 0 to fix.**
- **2026-08-29 — FRAMES DONE:** `compose_frames.py --block --contact-sheet` composed the 83 new
  portrait sets (212 distinct sets across Book 1; 218 PNGs + `_contact_sheet.png` in
  `projects/lotm_book1/frames/`); all 1,529 scenes across every block resolve to a frame on disk
  (0 missing).
- **2026-08-29 — VOLUME 2 IS BUILT AND PACKED.** `render_chapter.py 214 482` rendered all 269
  chapters (0 missing, 0 undersized), then `build_block_video.py` concatenated **five upload
  parts** into `character_video/Volume_2_Faceless/`, all ~1 h 10 m under the 12 h cap:
  ch214–266 (10:49:10) / 267–320 (10:53:01) / 321–374 (10:50:06) / 375–428 (10:46:40) /
  429–482 (10:51:58), ~805 MB each, 54:11 total. Split computed as a balanced 5-way min-max over
  the aligned audio durations, cut points nudged onto story beats (The World's Commission / Action /
  Artificial Sleepwalking just before Capim's dinner / The Scapegoat). `make_upload_pack.py
  --volume 2` + `make_thumbnail.py` wrote per-part description/pinned/tags files and
  `thumbnails/thumb_vol02_p1..5.jpg`; `playlist_vol02.txt` and
  `character_scene_video/YOUTUBE_UPLOAD_PLAN_VOL2.md` are written too.
- **2026-09-01/02 — FULL RE-RENDER + RE-PACK (both volumes) with the new frame system.**
  Portrait ordering (Klein first, Tarot members next, mentioned-only last), gold mentioned-rims,
  7 deity cards, `frame_focus` (ch461 s2 six-god mural ONLY — reserved for over-cap crowding),
  delayed-entrance splits (ch447 Amon reveal, ch264 Lanevus painting), missing-tag sweep
  (22 scenes gained mentions; ch460 s3 Derrick presence fix; ch447 s1 Amon deliberately untagged
  for the reveal). **Sharon ≠ Sharron (user, ×2): Madam Sharon = Backlund madam, Demoness pathway,
  own portrait `Sharon.png` — never alias to the ch244+ bodyguard.** frame-cap warning now built
  into `build_block.py` (both volumes clean; max 8 portraits, ch461 s3). All 482 chapters
  re-rendered `--force` + frame-grab verified; **all 9 parts re-concatenated (`--force`!) 
  2026-09-02 15:25–15:30, packs regenerated**; verify_tags 0-to-fix on all 11 blocks. Standing
  rules added to `TAGGING_GUIDE.md`; session details in `STATUS.md`.
- **Vol 1 P1 thumbnail A/B (checked 2026-09-02 via Studio/CDP):** running, ~10 days left, no
  per-variant data yet; P1 7-day CTR 2.4% (up from 1.7% day-1, ~3–3.5% post-test-start estimate)
  while control parts P2/P3/P4 stayed 1.4%/0.7%/1.1% — new thumbnail concepts are winning; which
  variant unknown until ~Sep 11. Plan: hold P2–P4 + P1 title; **Vol 2 P1 variants BUILT 2026-09-02** —
  `thumb_vol02_p1_var{A_bigface,B_faces,C_row}.jpg` (A = S2-poster Sherlock face, the
  recommended default; art sources + test setup in `YOUTUBE_UPLOAD_PLAN_VOL2.md`): set varA at
  upload, then Test & Compare with B + C. **2026-09-02: variant trios (A bigface / B faces /
  C row) BUILT for every remaining part** — Vol1 p2-4 + Vol2 p2-5, part-specific casts, in
  each part's `thumbnails/` folder (generator: session scratchpad `make_all_variants.py`). Vol-2 upload
  readiness AUDITED (5 MP4s fresh, durations match descriptions, packs/tags/pinned/playlist
  present); human spot-check list: `character_scene_video/VOL2_REVIEW_CHECKLIST.md`.
- **2026-09-03 ch215 PERSONA FLIP FIXED** (user spotted it): Klein was rendering as Sherlock
  Moriarty from line 3, but he invents the name at **L79** ("Sherlock Moriarty. You can call
  me Sherlock."). `base_flips` is CHAPTER-granular, so it overrode the scene tags. Flip moved
  to **at_chapter 216**; ch215 is now tagged scene by scene (Klein Moretti s1-s5, Sherlock
  s6-s9, split at L79). Lesson: for a mid-chapter identity change, set the scene personas AND
  push the base_flip to the NEXT chapter, or the flip silently wins.
- **2026-09-03 THREE-TIER MENTION RULE** (user): character / subject-of-conversation / passing
  note — a simple mention warrants NO portrait. Recorded in `TAGGING_GUIDE.md`. Swept all 56
  Vol-2 mention tags: removed 5 tier-3 tags (ch245 TC, ch265 EBS, ch292 Qilangos+Cattleya,
  ch440 Evernight). Same sweep caught a STRUCTURAL bug: **ch406 had a duplicate scene**
  (57-89 alongside its own split halves 57-71 + 73-89) and the halves had lost Fors Wall —
  fixed; a 482-chapter overlap scan found no others. Chapters 245/265/292/406/440 re-rendered,
  parts 1/2/4/5 re-concatenated, Vol-2 pack regenerated; all durations unchanged.
- **2026-09-03 (late) PORTRAIT ROUND + REVIEW.** User reviewed all 5 Vol-2 parts; outstanding
  re-check list (chapters that changed AFTER each part was signed off) is in
  **`character_scene_video/VOL2_OUTSTANDING_REVIEW.md`** — read that first to resume.
  New portraits: **Eye of Wisdom** (own art; NEVER Isengard Stanton.png, ch415 reveal),
  **Mr. Door**, **Daisy** (`*` reference), **God of Combat** (Badheil), **Colin Iliad** (16
  chapters!), **Lovia**, and **Zaratul** replaced. **`Apothecary` not `Darkwill` in Vol 2**
  (the name Darkwill first appears Vol 3 ch585). ch461 merged to ONE 7-god focus frame.
  ⚠ **85 Vol-2 characters are tagged-but-artless** (Kaslana 86 min, Stuart 53, Escalante 48,
  Horamick Haydn 38…) — `build_character_report.py` ranks by SCENE COUNT so they never
  surface; switching it to SCREEN TIME is the fix.
  ⚠ **After installing ANY portrait, rebuild ALL 11 blocks** — a partial rebuild left ch216/217
  rendering a stale cast with Mr. Door still missing, and the render log looked normal.
- **2026-09-03 MR. WORLD IS A SEATED MEMBER, NOT A PERSONA** (user): `[The World]` (bracketed
  background) -> **`The World`** with its own portrait across all 35 gathering chapters ch264-464.
  Art = the official Gehrman Sparrow card as a pure SILHOUETTE (user-supplied; `The World.png`),
  because members see 'a hooded black robe... illusory and hazy' and Gehrman Sparrow is not
  created until **ch483** (Vol 3 ch1). Seated in `portrait_priority.members` by joining order
  (after Derrick). Registered in `character_registry.json` so verify_tags accepts him.
  ⏭ **Vol 3+: swap to the FULL `Gehrman Sparrow.jpg`** and keep him a separate row ONLY inside
  gatherings (rule in `TAGGING_GUIDE.md`). All 35 chapters re-rendered + all 5 parts
  re-concatenated 2026-09-03 (durations unchanged); ch461 s3 now sits AT the 9-portrait cap.
- **2026-09-05 SOEST INSTALLED (`*` reference, user-supplied).** Leonard Mitchell's team leader
  (ch408 L61 "The middle-aged man named Soest"); 22:38 of screen time across ch408, 409, 421,
  424, 426, 429 -- another casualty of the scene-count ranking in `build_character_report.py`.
  Non-official art, so `mark_depiction.py` stamped the white `*`; his `character_map.json` note
  records that the text says middle-aged while the reference reads much younger. All 11 blocks
  rebuilt, the 6 chapters re-rendered `--force`, parts 4 + 5 re-concatenated `--force`, Vol-2
  pack regenerated. Verified 2026-09-05: frame grabs of ch424 s2 + ch429 s3 show the `*` portrait;
  staleness check clean on all 5 parts; durations unchanged (10:49:10 / 10:53:01 / 10:50:06 /
  10:46:40 / 10:51:58). **Nine portraits added over 2026-09-03/05** (The World, Eye of Wisdom,
  Mr. Door, Zaratul replaced, Daisy, God of Combat, Colin Iliad, Lovia, Soest); the user's
  outstanding re-check list is now **41 chapters** in `VOL2_OUTSTANDING_REVIEW.md`.
- **2026-09-05 LEONARD MITCHELL PINNED TO `portrait_priority.members`** (user ruling: he is the POV
  lead of his own chapters and a future Tarot seat). Appended LAST in `members`, which is also his
  joining order, so nothing has to move when he is actually seated. He shares **no** Vol-2 frame
  with a seated member, so in Volume 2 this only reorders him against Soest/Daly/Ikanser: exactly
  **3 scenes** changed -- ch408 s2, ch409 s2, ch429 s3 (Soest had been leading). Re-rendered
  `--force`, parts 4 + 5 re-concatenated `--force`, pack regenerated.
  ⚠ **The same rule reorders 25 VOLUME-1 chapters** (17, 45, 46, 71-77, 97, 105, 106, 109, 122-125,
  165, 204, 205, 207-209, 211) because Leonard now outranks **Dunn Smith** -- his own captain -- plus
  Megose, Trissy and the Moretti siblings. Those chapter MP4s were re-rendered so the masters stay
  truthful to the data, but **the four Volume-1 part files were deliberately NOT re-concatenated**:
  Volume 1 ships as-is and is not being re-uploaded, so a Vol-1 staleness check is EXPECTED to
  report those parts as older than their chapters. If Volume 1 is ever revisited, decide first
  whether Dunn Smith should outrank Leonard in the Book-1 Nighthawks scenes.
- **2026-09-05 VOLUME 2 PIXEL-AUDITED END TO END — 838/838 scenes correct, 0 mismatches.**
  For every scene of ch214-482 the real frame was decoded out of `Chapter_N.mp4` and pixel-compared
  against the frame the current block data resolves to (chapter-number overlay masked; worst
  matching deviation 1.37/255 = encoder noise). All five concatenated parts spot-checked the same
  way at a chapter marker deep inside each. **Volume 2 needs no further rendering.**
  ⚠ **DO NOT trust frame-PNG mtimes as a staleness signal.** `compose_frames.ensure()` writes only
  `if not out.exists()`, so a PNG's mtime is its CREATION time. After the 2026-09-03 cache clear the
  frames were rebuilt at 14:38-14:41 from identical inputs, which makes a naive
  "frame newer than MP4" check flag **209 of 269 Vol-2 chapters as stale when none of them are**.
  The pixel comparison above is the real check; chapter-mtime-vs-part-mtime is still valid for
  catching un-re-concatenated parts.
- **2026-09-06 THUMBNAIL TESTS READ + VOL-2 PACKS ADJUSTED + OUTPUT RE-LAID-OUT.** Full write-up in
  `character_scene_video/THUMBNAIL_TEST_ANALYSIS.md`. Daily Studio numbers (Aug 27-Sep 5) for the 4 Vol-1
  parts: launch-day CTR is noise (1000+ Browse impressions at 0.8-1.7%); post-launch the new concepts run
  ~2x the template (P1 3.6% vs P2/P3/P4 1.5/0.3/2.0% in the same window); **P2 jumped 1.5% -> 5.3% when its
  bigface test started while P3's dark bigface got 0 clicks on 180 impressions** -- face-panel brightness
  (121 vs 49 /255) is the tell. All 4 tests are running (user started P2-P4 ~Sep 2/3) but the channel is
  impression-starved (~60-100/day/part) so YouTube will likely end them "no clear winner" -- **pick the
  winner manually when each ends, or Studio reverts P1 to the OLD template.** Applied to Vol 2: P4 (48) and
  P5 (64) bigfaces are as dark as the failing Vol-1 P3, P2 mid (90) -> built `varD_bright` for P2/P4/P5
  (lifted panel, tighter face, warm glow); upload P1/P3 with varA, P2/P4/P5 with varD, test the rest.
  Packs regenerated (both volumes): `make_upload_pack.py` now writes the rewritten line 1 that Vol 1 has
  used live since 08-29; Vol 2 overrides the bridge line ("Season 2 adapts THIS volume") and its pinned
  comment cross-links the Vol-1 playlist (`upload_meta.json` -> `volumes.2.bridge_line` /
  `pinned_extra_lines`). Titles/tags unchanged. **Output layout is now by part** (see Engine layout):
  571 files moved by a scratchpad script, nothing deleted; 43 h Vol-1 single upload parked in `_legacy/`.
  All four path-aware scripts verified on the new tree (`--plan`, pack, thumbnail, ad-hoc-range refusal).
- **2026-09-12 TESTS RE-READ (through Sep 10): still NO per-variant data on any of the 4; P1 ends ~Sep 13,
  P2-P4 ~Sep 17, all will end "no clear winner".** Whole-test-window CTR vs template: P2 1.3% -> 3.4%
  (real), P3 0.4% -> 3.3% but every click is Sep 7-10 with Playlists now 52.6% of its traffic (P2's
  viewers binge-continuing, not thumbnail clicks), P4 too few impressions, P1 drifting 3.7% -> 2.2%.
  Recommendation recorded in `THUMBNAIL_TEST_ANALYSIS.md` s6: stop waiting, set thumbnails by hand when
  each test ends (P2-P4 varA bigface, P1 varB faces), let Vol 2's launch run the only resolvable test
  (varD_bright vs varA on P2/P4/P5). **Volume 3 (ch483-732, `Volume_3_Traveler`) is staged upstream:**
  250 chapters of text + 250 MP3s exist, nothing aligned or tagged — ready to start at recipe step 3.
- **2026-09-18 CAITLYN HALL INSTALLED (`*` fan art, user-supplied: Audrey with her mother on the ballroom
  floor; uncropped per standing preference, so Audrey appears in the card too).** Alias `Caitlyn`/`Lady
  Caitlyn`/`Countess Hall`. All 12 blocks rebuilt: 4 chapters changed -- ch343 s5, ch472 s1, ch482 s3 (Vol 2)
  + ch513 (Vol 3, not rendered yet). The three Vol-2 chapters re-rendered `--force`, parts 3 + 5
  re-concatenated `--force` (durations unchanged 10:50:06 / 10:51:58), pack regenerated, ch482 frame-grab
  verified, staleness 0 on all 5 parts. Review list now 44 chapters.
- **2026-09-18 KASLANA + ESCALANTE INSTALLED (`*` references, user-supplied; Kaslana's 2026-08-28
  hard-decline reversed by the user).** Kaslana: 11 chapters (299,301,305,337,413-416,418-420), parts 2-4
  re-concatenated. Escalante: 11 chapters (339,356,368,388,405,417,418,444,449,450,471), parts 3-5
  re-concatenated. Both `--force`, durations unchanged, packs regenerated, frame-grabs verified (ch414 s1,
  ch339 s3), staleness 0 on all 5 parts. Note Escalante's reference reads adult; the text calls her
  baby-faced. Review list now 66 chapters (`VOL2_OUTSTANDING_REVIEW.md`).
- **2026-09-18 CAPIM INSTALLED (`*` reference).** ch377-380 (the Hero Bandit raid) re-rendered, part 4
  re-concatenated, pack regenerated, ch378 frame-grab verified, staleness 0. Harras/Katy/Parker still blank.
- **2026-09-18 STUART INSTALLED (`*` reference, transparent PNG composited onto the frame backdrop).**
  10 chapters (299,300,301,305,337,338,370,371,413,414) re-rendered, parts 2-4 re-concatenated, pack
  regenerated, ch299 s1 frame-grab verified, staleness 0. Alias `Ian` -> `Ian Wright` added (page-literal
  tag vs registry name). Six `*` references installed today: Caitlyn Hall, Kaslana, Escalante, Capim, Stuart.
  ⚠ Kaslana's art is SQUARE (1200x1200): in a row with tall cards the aspect-aware layout gives her ~2.5x
  their width. Crop to portrait aspect if that reads wrong.
- **2026-09-18 HORAMICK HAYDN INSTALLED (`*` reference).** ch324,446,447,448 re-rendered, parts 3 + 5
  re-concatenated (part 5 now 10:52:01, +3 s from cut rounding; markers regenerated), ch447 s2 frame-grab
  verified (the Amon reveal now shows Horamick turning the frame), staleness 0. Vol 3 ch491/493 pick him up.
- **2026-09-18 HANDOFF (pre-compaction).** `verify_render.py` added and run on Vol 2: **`214 482` -> 183 frames 0 stale, 838/838 scenes match,
  0 stale parts, CLEAN** (report `projects/lotm_book1/verify_vol2_2026-09-18.json`) -- see STATUS.md
  top block and for Vol 3 block 11 state (tagged, verified, NOT rendered; needs
  `upload_meta.json` volume 3 entry + portrait decisions first). Six `*` references installed today.
  ⏭ **NEXT ACTION: manual Studio upload of Volume 2's 5 parts** (files in
  `Volume_2_Faceless/parts/Part_K_chAAA-BBB/`; thumbnail choice per part in the analysis doc). **Volume 1 will NOT be
  re-uploaded (user decision 2026-09-03)** — it stays live with its original frames; its local
  masters carry the new layout but that is not shipping. All future changes are Vol 2+ only.
- **2026-10-02 PRE-UPLOAD PACK REVIEW (Vol 2).** Part 2's hook described ch264-266 (which are in Part 1)
  -> rewritten in `upload_meta.json` + Part 2 pack regenerated. `playlist_vol02.txt` claimed the Fool's
  identity is no secret to the gathering by vol end (false) -> fixed. Everything else checked OK: titles
  89/100, descriptions 3.7k/5k, no `<>`, markers 0:00-first, tags 380/500. API snapshot: Vol-1 parts
  433/107/63/186 views in 35 days; per-chapter Vol-2 playlist (`PLV2gvMHy77hrwY_XlTOU8dvcEM92uigRM`)
  holds 43.3k views; Vol-1 parts sit at the BOTTOM (pos 214-217) of the per-chapter Vol-1 playlist.

