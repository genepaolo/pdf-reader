#!/usr/bin/env python3
"""Per-project configuration for the character-scene-video pipeline.

Everything book-specific lives in projects/<name>/project.json plus that folder's data files
(scene tags, alignment, aliases, continuity, portrait decisions, built timelines, frame cache).
The scripts are a shared engine: every entry point takes --project NAME (default: lotm_book1,
or the CHARVID_PROJECT environment variable).

To start a NEW book:
  1. copy projects/_TEMPLATE/project.json -> projects/<name>/project.json and fill it in
  2. point text_root at the book's formatted_text and audio_root at its MP3 output
  3. create a portraits dir with a character_map.json (open roster -- add images over time)
  4. write projects/<name>/character_registry.json (known character names) and an empty
     name_aliases.json / continuity.json -- then tag scenes into timelines/scenes/
The engine (alignment, verification, timeline build, compositing, rendering, block concat)
needs no code changes per book.
"""
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT = "lotm_book1"


class Project:
    def __init__(self, name):
        self.name = name
        self.dir = HERE / "projects" / name
        if not (self.dir / "project.json").exists():
            raise SystemExit(f"no such charvid project: {name} (expected {self.dir}/project.json)")
        cfg = json.loads((self.dir / "project.json").read_text(encoding="utf-8"))
        self.cfg = cfg
        self.text_root = self._abs(cfg["text_root"])
        self.audio_root = self._abs(cfg["audio_root"])
        self.durations_csv = self._abs(cfg["durations_csv"]) if cfg.get("durations_csv") else None
        self.portraits = self._abs(cfg["portraits_dir"])
        self.video_out = self._abs(cfg["video_out_dir"])
        self.block_size = cfg.get("block_size", 50)
        self.series_title = cfg.get("series_title", name)
        self.persona = cfg.get("persona", {})
        # per-project data files/dirs (fixed layout inside the project folder)
        self.align_dir = self.dir / "align"
        self.timelines = self.dir / "timelines"
        self.scenes_dir = self.dir / "timelines" / "scenes"
        self.frames = self.dir / "frames"
        self.registry_file = self.dir / "character_registry.json"
        self.aliases_file = self.dir / "name_aliases.json"
        self.continuity_file = self.dir / "continuity.json"
        self.decisions_file = self.dir / "portrait_decisions.json"

    @staticmethod
    def _abs(v):
        p = Path(v)
        return p if p.is_absolute() else ROOT / p

    # ---- shared lookups (chapter files live under <root>/<Volume dir>/Chapter_N_*.ext) ----
    def chapter_text(self, ch):
        return next(iter(sorted(self.text_root.glob(f"*/Chapter_{ch}_*.txt"))), None)

    def chapter_audio(self, ch):
        return next(iter(sorted(self.audio_root.glob(f"*/Chapter_{ch}_*.mp3"))), None)

    def title_of(self, ch):
        f = self.chapter_text(ch)
        return f.stem.split("_", 2)[2].replace("_", " ") if f else f"Chapter {ch}"

    # ---- volume-aware output layout (standard: <video_out_dir>/<Volume_dir>/...) ----
    # The volume folder name comes from the text layout itself (Volume_1_Clown etc.), so any
    # project whose formatted_text follows <root>/<Volume dir>/Chapter_N_*.txt gets per-volume
    # video output with no extra config.
    def volume_dir_of(self, ch):
        """Volume folder NAME for a chapter, e.g. 'Volume_1_Clown'."""
        if not hasattr(self, "_voldir_cache"):
            self._voldir_cache = {}
        if ch not in self._voldir_cache:
            f = self.chapter_text(ch)
            if not f:
                raise SystemExit(f"ch{ch}: no chapter text under {self.text_root} -- "
                                 "cannot resolve its volume")
            self._voldir_cache[ch] = f.parent.name
        return self._voldir_cache[ch]

    def volume_dir_by_no(self, n):
        """Volume folder NAME by volume number, e.g. 1 -> 'Volume_1_Clown'."""
        hit = next(iter(sorted(self.text_root.glob(f"Volume_{n}_*"))), None)
        if not hit:
            raise SystemExit(f"no Volume_{n}_* folder under {self.text_root}")
        return hit.name

    def video_dir(self, ch):
        """Output directory for a chapter's volume (not created here)."""
        return self.video_out / self.volume_dir_of(ch)

    # ---- inside a volume folder (layout adopted 2026-09-06) ----
    #   <Volume_dir>/chapters/Chapter_N.mp4                       per-chapter masters
    #   <Volume_dir>/parts/Part_K_chAAA-BBB/Part_K_chAAA-BBB.mp4  one upload part + its pack
    #   <Volume_dir>/parts/Part_K_chAAA-BBB/*_description*.txt, *_pinned_comment.txt, *_tags.txt
    #   <Volume_dir>/parts/Part_K_chAAA-BBB/thumbnails/           that part's thumbnail + A/B variants
    #   <Volume_dir>/thumbnails/                                  volume-level thumbnails
    #   <Volume_dir>/playlist_volNN.txt
    # Part numbers K come from upload_meta.json (list order within the volume), so a part is
    # addressed by its chapter range and named Part_K, never by the 50-chapter tagging block.
    def chapters_dir(self, ch):
        return self.video_dir(ch) / "chapters"

    def chapter_video(self, ch):
        return self.chapters_dir(ch) / f"Chapter_{ch}.mp4"

    def volume_no_of(self, ch):
        """Volume NUMBER for a chapter (from the Volume_<n>_* folder name)."""
        m = re.match(r"Volume_(\d+)_", self.volume_dir_of(ch))
        if not m:
            raise SystemExit(f"ch{ch}: volume folder {self.volume_dir_of(ch)!r} is not Volume_<n>_*")
        return int(m.group(1))

    def upload_meta(self):
        f = self.dir / "upload_meta.json"
        if not f.exists():
            raise SystemExit(f"{f} missing -- create it (template in projects/_TEMPLATE/)")
        return json.loads(f.read_text(encoding="utf-8"))

    def part_for_range(self, first, last):
        """-> (part_no, total_parts) for a chapter range listed in upload_meta.json, else None."""
        vol = self.upload_meta().get("volumes", {}).get(str(self.volume_no_of(first)))
        if not vol:
            return None
        parts = vol.get("parts", [])
        for k, p in enumerate(parts, 1):
            if p["first"] == first and p["last"] == last:
                return k, len(parts)
        return None

    @staticmethod
    def part_stem(part_no, first, last):
        return f"Part_{part_no}_ch{first:03d}-{last:03d}"

    def part_dir(self, part_no, first, last):
        """Folder holding one upload part's MP4, pack files and thumbnails (not created here)."""
        return self.video_dir(first) / "parts" / self.part_stem(part_no, first, last)

    def thumbnails_dir(self, vol_no, part_no=None):
        """Volume-level thumbnails, or a part's own thumbnail folder when part_no is given."""
        root = self.video_out / self.volume_dir_by_no(vol_no)
        if part_no is None:
            return root / "thumbnails"
        vol = self.upload_meta().get("volumes", {}).get(str(vol_no))
        parts = (vol or {}).get("parts", [])
        if not 1 <= part_no <= len(parts):
            raise SystemExit(f"volume {vol_no} part {part_no}: not in upload_meta.json "
                             f"({len(parts)} parts listed) -- add its range first")
        p = parts[part_no - 1]
        return root / "parts" / self.part_stem(part_no, p["first"], p["last"]) / "thumbnails"

    def block_no(self, first):
        return (first - 1) // self.block_size + 1

    def block_jsons(self):
        return [f for f in sorted(self.timelines.glob("block_*_ch*.json")) if "_SAMPLE" not in f.name]

    def block_json_for(self, ch):
        for f in self.block_jsons():
            m = re.search(r"ch(\d+)-(\d+)\.json$", f.name)
            if m and int(m.group(1)) <= ch <= int(m.group(2)):
                return f
        return None


def load(name=None):
    return Project(name or os.environ.get("CHARVID_PROJECT") or DEFAULT)


def pop_project_arg(argv):
    """Strip --project NAME / --project=NAME from an argv list. -> (Project, remaining_args)."""
    out, name, i = [], None, 0
    while i < len(argv):
        a = argv[i]
        if a == "--project" and i + 1 < len(argv):
            name = argv[i + 1]
            i += 2
            continue
        if a.startswith("--project="):
            name = a.split("=", 1)[1]
            i += 1
            continue
        out.append(a)
        i += 1
    return load(name), out
