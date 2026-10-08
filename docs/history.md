# Moved out of CLAUDE.md on 2026-10-07 (verbatim)

Original line numbers refer to CLAUDE.md @ 13dd43f. Operational rules were re-stated in the slim CLAUDE.md.

## [CLAUDE.md lines 3-19] Active Project Scope + Agent context

## Active Project Scope
- Current active project is `lom_book2_coi`.
- Unless explicitly stated otherwise, all commands and status updates for audio generation,
  video generation, and YouTube uploads refer only to `lom_book2_coi`.
- **Second workstream:** `character_scene_video` (Book 1 per-scene portrait videos) — see its
  section below. **Next session there: manual Studio upload of Volume 2's 5 parts (proof of readiness = `verify_render.py 214 482` CLEAN; thumbnail picks in `THUMBNAIL_TEST_ANALYSIS.md`), then Vol 3 block 11 portrait decisions -> render (STATUS.md top block).**

- **Third workstream (planned, not started): replace Azure TTS with local VoiceStudio** —
  plan in `VOICESTUDIO_TTS_SWAP_PLAN.md` (written on the Mac 2026-10-02). Starts at Phase 0, a GPU
  go/no-go benchmark on the RX 9070 XT; voice-clone of Steffan first, presets as fallback. Azure stays
  the default (`tts_engine: azure`) until Phase 2d passes. Never commit clone weights or reference WAVs.

## Agent context (how this file is loaded)
- **Cursor:** `.cursor/rules/claude-context.mdc` (`alwaysApply: true`) requires reading `CLAUDE.md` before tools or substantive changes — re-read each message, don't rely on memory.
- **Claude Code / other tools:** if not auto-loaded, `@`-reference this file at session start.
- **Setup elsewhere:** repo-root `CLAUDE.md` + an always-apply rule pointing at it; keep the progress log updated after pipeline runs.


## [CLAUDE.md lines 146-154] Recipe step 1 tagging warnings (also in TAGGING_GUIDE.md)

   ⚠️ **Dream/vision/memory figures are NOT present** — never in `other_characters`; note them in
   `setting` as "(visions only: …)".
   ⚠️ **Roselle diary-reading interludes** (standing rule, all blocks): whenever Klein/The Fool
   READS diary pages, split the scene around the reading — break scene = protagonist + Roselle
   Gustav + anyone named in the pages (everyone else physically present dropped); resume scene
   after. Carry Roselle in `continuity.json` across chapter breaks; whitelist via
   `verified_present` if "Roselle" isn't in the line span; splitting renumbers scenes → update
   existing `verified_present` indexes. Does NOT apply to diary discussion without reading, the
   Antigonus diary, or recollections/quotes. Full rule in `TAGGING_GUIDE.md`.

## [CLAUDE.md lines 207-245] Step 3 UPLOAD + Step 4 END SCREENS + background art (old versions)

### Step 3 — UPLOAD → tracker `D:/PDFReader/lom_book2_coi_output/youtube_progress.json`
> **ONE upload job at a time** (two = duplicates). Quota-safe pace ≈ 6/hour (~10 min apart; the script paces itself).
- Auth/tracker check only: `py -3.12 upload_queue.py --project lom_book2_coi --limit=0`
- Next single: `... --yes --limit=1` · Next 10: `... --yes --limit=10`
- OAuth: complete browser sign-in as **breadmoretti@gmail.com** if prompted (`token.json` in repo root).
- Titles come from the `Chapter N: <title>` line in the formatted source text, not filenames.
- Config: `tts_pipeline/config/projects/lom_book2_coi/youtube_config.json`
- ⚠️ The script has NO retry — if a chapter fails mid-batch it continues and leaves a hole; fix the
  gap in order before the next batch (delete out-of-order later uploads only with user approval).
- ⚠️ A pre-check snapshot goes stale during a long batch — re-check discovery after the run.
- ⚠️ Per-upload `Video may not be in playlist` warnings are a known API-listing quirk, not data loss.

### Step 4 — END SCREENS (run AFTER a fully successful upload batch; skip if ANY upload failed)
> Standing rule: after Step 3 reports `Failed: 0`, add end screens. Tool: `youtube_endscreen.py`
> (Playwright driving Studio UI; idempotent — already-done videos are skipped; `--replace` not implemented).
- **Range rule:** for uploaded batch N–M, run sources **(N-1)–(M-1)** (boundary chapter links to the
  first new one; newest chapter M waits for the next batch).
- `py -3.12 youtube_endscreen.py --project lom_book2_coi --chapters (N-1)-(M-1) --connect-port 9222 --yes`
  (`--plan-only` = offline pre-check; style imported from ch249 via `--style-from`, don't change)
- **Chrome prereq:** attaches to real Chrome on port 9222; profile `%USERPROFILE%\yt-studio-login`
  (logged in as breadmoretti). **Assume Chrome is down between runs** — always
  `curl http://127.0.0.1:9222/json/version` first; if silent, relaunch:
  `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\yt-studio-login" "https://studio.youtube.com/"`
  (If logged out: sign in first in a normal Chrome with that user-data-dir and NO debug port, then relaunch with the port.)
- **Unlisted-only guard:** public videos are skipped; chapters go public within ~days of upload, so
  run end screens promptly, else include via `--allow-public-chapters 320` (comma-separated list).
- ⚠️ Don't pipe the tool's output through `tail` (truncates the log); re-running is the safe verify.

### Chapter background art (per-project)
> `tts_pipeline/config/projects/<project>/portrait_mapping.json` maps chapter-range → filename;
> images in `tts_pipeline/assets/projects/<project>/backgrounds/` (+ `resized/`).
- Add art: drop in `.../dropoff/` → `py -3.12 tts_pipeline/scripts/prepare_backgrounds.py --project <project>`
  → edit `portrait_mapping.json` → `... --status` to verify (exit 0 = all mapped).
- `null` ranges fail loudly at render; never use `--background-image` overrides for production.
- **`lom_book2_coi` mapping (physical-edition parts):** boundaries
  1-55 / 56-109 / 110-186 / 187-263 / 264-340 / 341-417 / 418-494 / 495-575 / 576-655 / 656-735 / 736-884
  (`coi_v1..coi_v11`; `coi_v10_sinner_3` is `.jpeg`). ✅ mapped through ch884 — **ch885+ has NO art yet.**
- `lotm_book1` mapping complete.


## [CLAUDE.md lines 263-298] Tracking + YouTube

## Tracking
- Progress status lives HERE (below), not in `tracking/*.json`.
- Source of truth for created audio/video: the output folder on D:. For uploads: YouTube API /
  `youtube_progress.json`.

## YouTube (`lom_book2_coi`)
- Channel account: **breadmoretti@gmail.com** (NOT paolo.gene).
- Playlists (reused by ID from `youtube_config.json → playlists.playlist_ids`):
  V2 Lightseeker `PLV2gvMHy77hrYzC8lxYXCtEp4NArMkh7s` · V3 Conspirer `PLV2gvMHy77hpe3q8VvnIeXK1s-y8sNSpM`.
- Old one-off issue: ch215 title may need a manual fix.
- ✅ **PLAYLIST ROUTING IS RESOLVED — audited via API 2026-09-05, nothing to move.** The old warning about
  `PLV2gvMHy77hrh1HeiBECpJ61Smbgg5_S6` ("30 early uploads incl. 236–240 need manual moving") was STALE:
  that playlist **no longer exists** (404 `playlistNotFound`) and every chapter now sits in the right one.
  Verified membership of all 390 uploaded chapters:
  Vol 1 Nightmare `PLV2gvMHy77hpWltp0KalQNL8JPkqBKWQu` = ch1–109 · Vol 2 Lightseeker = ch110–263 ·
  Vol 3 Conspirer = ch264–390. **Zero chapters outside a playlist.**
  Root cause of the original mess (fixed by commit `c852902`, 2026-06-14): `get_or_create_playlist`
  resolved playlists **by NAME** from `name_template`, which then read `LOTM 2 - Volume {n}` and did not
  match the hand-made `LOM2 COI - Volume 2: Lightseeker`, so the uploader **auto-created its own**
  playlist and filled it. The fix pins `playlists.playlist_ids` and short-circuits before the by-name
  lookup. ⚠️ Volume **1** has no `playlist_ids` entry — harmless today (vol 1 is fully uploaded, and the
  renamed template now matches by name), but pin it if vol-1 uploads ever resume.
- ✅ **TRACKER REPAIRED 2026-09-05.** ch122 and ch230 had held **deleted** video IDs (`MKqJQyOKqJE`,
  `7Ur5oGt7lt4`) — residue of the ch230–232 duplicate cleanup. Repointed to the live re-uploads
  (ch122 = `M7f0V00TlYo`, ch230 = `sfmJd-_p69w`) with their real publish times + Lightseeker playlist id.
  Backup: `youtube_progress.json.bak-2026-09-05`. Re-audited: **390/390 ids alive, 0 dead, no gaps.**
  Worth re-running that audit occasionally (videos.list over every tracker id) — nothing else does it.
- ✅ **END-SCREEN CHAIN VERIFIED INTACT around the repair (2026-09-05).** An earlier worry that ch121/ch229
  pointed at the deleted videos was **WRONG** — checked and disproved: ch121 → live ch122, ch229 → live
  ch230, and ch122 → 123, ch230 → 231 all present and correct (watch-page check: dead ids appear 0×, live
  ids 56×). **Why it self-healed: `youtube_endscreen.py` picks the TARGET by searching Studio for the
  chapter TITLE (`#search-yours`, `youtube_endscreen.py:262`), NOT by tracker video_id.** Only the SOURCE
  video is addressed by tracker id. So a stale tracker id can break the source lookup for that chapter,
  but can never mis-aim a target.
- ⚠️ Vol 3 Conspirer playlist holds **2 `Deleted video` rows** (`OKRcFKOhBTE`, `IFa7FCbQ4Bs`) — dead
  entries to remove in Studio (why its itemCount is 129 vs 127 real chapters).

## [CLAUDE.md lines 299-341] Progress Log: lom_book2_coi

## Current Progress Log

### lom_book2_coi (uploads updated 2026-09-30)
| Stage | Done | Highest | Next action |
|---|---|---|---|
| Audio (`.mp3`) | 603 | 603 | generate ch. **604+** |
| Video (`.mp4`) | 601 files (through 600, contiguous 1–600) | 600 | create ch. **601–603**, then wait for audio |
| Upload | 472 (1–472, no gaps) | 472 | upload ch. **473+** (128 pending). ⚠️ background jobs now get killed (see below) |

- Most recent upload: 2026-09-30, **ch471–472 only** (batch of 20 abandoned, see below). Before that: 451–470
  (09-27), 431–450 (09-20), 411–430 (09-16) — all clean.
  ⚠️ **2026-09-30: BACKGROUND JOBS ARE NOW KILLED AT A TIME LIMIT (~30 min, even with timeout=600000).** Two
  `upload_queue.py` runs died after ~1 upload each (earlier sessions ran 3.5 h unattended). Second kill hit
  AFTER ch472 finished uploading but BEFORE the uploader's playlist-add + tracker write, leaving a complete,
  untracked video (`vaJim7ioOXY`, size identical to local MP4). Reconciled by hand: added to Conspirer
  playlist + tracker entry (backup `youtube_progress.json.bak-2026-09-30`). **After ANY killed run: query the
  channel's newest uploads for an UNTRACKED video before restarting, or you create a duplicate.**
  473–490 NOT uploaded; needs a way to run >30 min (foreground/other host) or small `--limit` chunks.
  ⚠️ `upload_queue.py` stdout is BLOCK-BUFFERED when redirected to a file — a background run's log can sit
  at 0 bytes for an hour while uploads succeed. Judge progress by `youtube_progress.json` (mtime + entry
  count) or the process being alive, never by an empty log.
- End screens: **DONE through 469→470 (2026-09-27); 470→471 and 471→472 NOT yet done.** Sources 450–469: 20/20 confirmed + saved, 0 WARN/ERROR/
  SKIP (Chrome 153, still logged in). Before that: 430–449 (09-20), 410–429 (09-16), 390–409 (09-10,
  independently re-verified in Studio). ⏭ **Dangling: ch470** — run sources **470–(M-1)** after the next
  batch lands. Pattern that now works every time: relaunch Chrome on 9222 → `--plan-only` →
  run with `-u` and `--allow-public-chapters $(seq -s, N M)`.
  ⚠️ **THE UNLISTED-ONLY GUARD IS NOW PERMANENTLY IN THE WAY — always pass `--allow-public-chapters`.**
  Uploads still go up unlisted (`upload_settings.privacy`) but flip public in **under a day**
  (381–390 uploaded 2026-09-04 were public by 2026-09-05), so 'run end screens promptly while unlisted'
  is dead. Without the override a run is a SILENT NO-OP: `--plan-only 360-389` said
  `Eligible (unlisted): 0 / 30` and a normal run would print a plausible plan and edit nothing.
  The flag takes an explicit comma list, so generate it: `seq -s, N M`. Working invocation:
  `py -3.12 youtube_endscreen.py --project lom_book2_coi --chapters N-M --connect-port 9222 --yes \n   --allow-public-chapters $(seq -s, N M)`
  Read-only presence audit (no edits): open `studio.youtube.com/video/<id>/editor` over CDP and count
  `#add-endscreen-icon-button` — 1 = missing, 0 = present (same check the tool uses at
  `youtube_endscreen.py:220`). Visual tell: End screen row shows `Edit` + a Subscribe/Video timeline
  track when present, `+` and no track when missing.
  ⚠️ Run the tool with `py -3.12 -u` — like the uploader, its stdout block-buffers when redirected.
- Volume boundaries: ch264+ → vol 3 (Conspirer). Ch885+ needs background art before video creation.
- Disk: ~1.17 TB free on D:; ~672 MB/video average.
- EPUB source: 1180 formatted chapters in 8 volume folders under `formatted_text/lom_book2_coi`.
- Per-batch video IDs and dated batch history: `youtube_progress.json` + git history of this file.


## [CLAUDE.md lines 120-140] Engine layout (full original)

### Engine layout (generalized; run everything with `py -3.12` from repo root)
- Shared engine + per-project config: `character_scene_video/projects/<name>/project.json`
  (template in `projects/_TEMPLATE/`). All scripts take `--project` (default `lotm_book1`).
  Per-project data (scene tags, align, timelines, aliases, continuity, portrait decisions, frames)
  lives in `character_scene_video/projects/<name>/`.
- **Output is BY VOLUME, then BY PART (layout adopted 2026-09-06):** under `<video_out_dir>/<Volume_dir>/`
  (e.g. `.../character_video/Volume_2_Faceless/`; the volume folder is derived from the text layout by
  `charvid_project` helpers):
  `chapters/Chapter_N.mp4` (per-chapter masters) · `parts/Part_K_chAAA-BBB/` (one upload part:
  `Part_K_chAAA-BBB.mp4` + `_description.txt` + `_description_YOUTUBE.txt` + `_pinned_comment.txt` +
  `_tags.txt` + `thumbnails/` with that part's thumbnail and A/B variants) · `thumbnails/` (volume-level)
  · `playlist_volNN.txt`. **K is the part's list position under its volume in `upload_meta.json`** —
  `build_block_video.py` looks the range up there (or takes `--part K` for an ad-hoc range) and refuses
  ranges that cross a volume boundary. Vol 1's abandoned 43 h single upload lives in
  `Volume_1_Clown/_legacy/`. Helpers: `P.chapter_video(ch)`, `P.part_dir(K,a,b)`, `P.part_stem(K,a,b)`,
  `P.thumbnails_dir(vol, part)`.
- Upload-pack config (part ranges, story hooks, tags, pitch lines) lives per project in
  `projects/<name>/upload_meta.json` (template in `_TEMPLATE/`).
- Alignment is NOT aeneas/WhisperX: Azure-TTS audio of known text, matched sentence-sequence ↔
  ffmpeg-pause-sequence with a DP. No extra deps.


## [CLAUDE.md lines 158-186 excerpt] Step 8 verify_render paragraph + Step 2 encoder note (full originals)

   ⚠ **re-renders MUST pass `--force`** — without it the script SKIPS existing MP4s while still
   printing a normal-looking per-chapter summary (timeline cuts, not the file). Bit us 2026-08-29:
   six portrait installs looked rendered but weren't until a `--force` sweep. Verify with an
   ffmpeg frame grab, not the log — or better, **`py -3.12 character_scene_video/verify_render.py A B`**
   (added 2026-09-18): pixel-compares every scene of every chapter MP4 against the frame the current
   block data resolves to, checks the frame cache against a fresh recompose (in-place portrait swaps),
   and flags parts older than their chapters. Exit 0 = CLEAN; otherwise it prints the exact
   `chapters_to_rerender` / stale PNGs / stale parts (`--json PATH` for a machine-readable list;
   `--frames` = cache-only, seconds). **This is the only accepted proof that a range is rendered.**
9. `py -3.12 character_scene_video/build_block_video.py A B --plan` then without `--plan`

### Step 2 — VIDEO → `D:/PDFReader/lom_book2_coi_output/video/Volume_*/*.mp4`
- `py -3.12 tts_pipeline/scripts/create_videos.py --project lom_book2_coi --chapters N-M`
- Preview one: `... --chapters N --preview` (⚠️ preview does NOT validate audio/art — simulated success)
- Resume: `... --resume`
- Encoder auto-probes at first use (this machine: AMD RX 9070 XT → `h264_amf`).
- Audio filenames may drift from text filenames (old runs sanitized `'`/`,`/`!` and truncated);
  `create_videos.py` falls back to chapter-number matching — uploader titles come from text files,
  so drifted names are cosmetic.


## [CLAUDE.md lines 259-262] Repo audits note

  COI text says `Volume_2_Light_Chaser` but outputs use `Volume_2_Lightseeker`.
- Repo audits 2026-06-14 + 2026-08-10 (import fixes, asset reorg, doc sync, dead-file deletions)
  are recorded in git history and the synced docs (`README.md`, `ARCHITECTURE.md`, `SCRIPTS_GUIDE.md`).


## [CLAUDE.md lines 189-206 + 252-262] Steps 1-2 and Config (full originals)

## The 3-Step Workflow — `lom_book2_coi` (audio → video → upload)
> Run from repo root (`pdf-reader`). Replace `N-M` with the chapter range.

### Step 1 — AUDIO (Azure TTS) → `D:/PDFReader/lom_book2_coi_output/Volume_*/*.mp3`
- Safe validation: `py -3.12 tts_pipeline/scripts/process_project.py --project lom_book2_coi --dry-run --max-chapters 5`
- Range: `py -3.12 tts_pipeline/scripts/process_project.py --project lom_book2_coi --chapters N-M`
- Next 10 from where we left off: `... --continue 10` · Resume: no extra flag
- One-shot audio+video: add `--create-videos`

### Step 2 — VIDEO → `D:/PDFReader/lom_book2_coi_output/video/Volume_*/*.mp4`
- `py -3.12 tts_pipeline/scripts/create_videos.py --project lom_book2_coi --chapters N-M`
- Preview one: `... --chapters N --preview` (⚠️ preview does NOT validate audio/art — simulated success)
- Resume: `... --resume`
- Encoder auto-probes at first use (this machine: AMD RX 9070 XT → `h264_amf`).
- Audio filenames may drift from text filenames (old runs sanitized `'`/`,`/`!` and truncated);
  `create_videos.py` falls back to chapter-number matching — uploader titles come from text files,
  so drifted names are cosmetic.


## Config & path conventions
- Output root: `D:/PDFReader/` (per-project: `D:/PDFReader/<project>_output`).
- `process_project.py` must run with cwd = repo root (paths resolve under the repo).
- COI config dir: `tts_pipeline/config/projects/lom_book2_coi/` (`volume_pattern` = `Volume_(\\d+)_`).
- Azure: copy `azure_config.json.example` → `azure_config.json` (gitignored); set
  `AZURE_TTS_SUBSCRIPTION_KEY` / `AZURE_TTS_REGION` in env; never commit secrets.
- Naming quirks (don't "fix"): book1 audio on disk keeps legacy `N___VOLUME_N___` folders;
  COI text says `Volume_2_Light_Chaser` but outputs use `Volume_2_Lightseeker`.
- Repo audits 2026-06-14 + 2026-08-10 (import fixes, asset reorg, doc sync, dead-file deletions)
  are recorded in git history and the synced docs (`README.md`, `ARCHITECTURE.md`, `SCRIPTS_GUIDE.md`).


## [CLAUDE.md lines 155-165] Recipe steps 3-7 (full originals)

3. `py -3.12 character_scene_video/align_chapter.py A B`
4. `py -3.12 character_scene_video/verify_alignment.py A B`     # must PASS
5. `py -3.12 character_scene_video/build_block.py A B`
6. `py -3.12 character_scene_video/verify_tags.py A B`          # must be 0 to fix
7. `py -3.12 character_scene_video/compose_frames.py --block --contact-sheet`  # eyeball new frames
8. `py -3.12 character_scene_video/render_chapter.py A B`       # `--preview` first; spot-check
