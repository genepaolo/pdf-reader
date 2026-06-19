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

**Portrait decision is YOURS.** The report sorts by frequency + flags wiki-vs-minor so you can judge importance
fast. Current: **6 have portraits** (Klein, Dunn Smith, Leonard Mitchell, Audrey Hall, Alger Wilson, Daly Simone);
**19 wiki characters need a decision** (top: Old Neil 16 scenes, Melissa Moretti 15, Rozanne 13, Benson Moretti 10);
9 minor (no wiki page); 34 unnamed extras.

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
1. **You review** `character_report_block01.md` + the timeline; tell me portrait decisions + any scene fixes.
2. **Source portraits** for the chosen characters (drop file in `assets/characters/lotm/` + one `character_map.json` entry).
3. **Stand up aeneas** → replace estimated durations with real per-chapter timestamps.
4. **Build the compositor** (row/grid frames; gray-fog Fool+Audrey+Alger is the first real multi-portrait test).
5. **Tag Block 2 (ch51–100)** — will use the text-literal guide + auto-verify + continuity from the start.

## File map (character_scene_video/)
- `DESIGN.md` — full design + decisions + milestones (+ §10 timeline schema, continuity, alignment).
- `TAGGING_GUIDE.md` — anti-hallucination tagging rules.
- `scrape_official_images.py` — wiki-wide portrait scraper (→ `_manifest.json`, binaries gitignored).
- `build_character_registry.py` → `character_registry.json` (384 Book-1 chars + portrait coverage).
- `build_block.py` → `timelines/block_01_*.md/.json` (the timeline; applies personas, aliases, continuity).
- `build_character_report.py` → `timelines/character_report_block01.md` (participation/decision view).
- `verify_tags.py` — source-grounding gate.
- `timelines/scenes/ch_*.json` — raw per-chapter scene tags (source of truth for content).
