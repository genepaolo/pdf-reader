# Character-Scene Videos — STATUS / Session Handoff

**Read this first to resume.** Last updated end of the session that built Block 1.

## Where the work lives (IMPORTANT)
- **Branch:** `feature/book1-character-scene-videos`
- **Worktree:** `C:\Users\paolo\Work\Projects\LOTM\pdf-reader-charvid` ← do feature work here.
- Your other branch `feature/youtube-endscreens` is checked out in the MAIN repo
  (`...\pdf-reader`). The IDE kept switching between them mid-session; the worktree exists so the two
  never collide. **Stay in the worktree for this feature.**
- Last commit at handoff: see `git log` on the branch (Block-1 continuity + reports).
- Gitignored (not committed, regenerable): `formatted_text/`, the EPUB, the character image binaries.
  The worktree has a local copy of `formatted_text/lotm_book1` so the scripts run.

## What's done (Block 1 = chapters 1–50)
- **Audited clean:** 50/50 chapters tagged, 156 scenes, total ≈ **10:52:09**, verifier **168/168, 0 to fix**.
- Pipeline proven end to end: scrape → registry → scene-tag → image-resolve → timeline → verify → reports.

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

## How to resume (run from the worktree)
```
python character_scene_video/build_block.py 1 50            # rebuild block-1 timeline
python character_scene_video/verify_tags.py 1 50            # must be 0 to fix
python character_scene_video/build_character_report.py 1 50 # who-needs-a-portrait report
```
To correct a scene: edit `timelines/scenes/ch_<N>.json`; to merge/rename a character: `name_aliases.json`;
to mark a confirmed presence the verifier flags: `verified_present` in `name_aliases.json`.

## Open threads / next steps
1. ✅ **Portrait decisions done** (`portrait_decisions.json`): 13 yes (sourced), 2 declined. Report shows need:0.
   Remaining content review is optional (scene fixes / any new portraits later — roster stays open).
2. **Stand up aeneas** → replace estimated durations with real per-chapter timestamps.
3. **Build the compositor** (row/grid frames; gray-fog Fool+Audrey+Alger is the first real multi-portrait test).
4. **Tag Block 2 (ch51–100)** — will use the text-literal guide + auto-verify + continuity from the start.

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
