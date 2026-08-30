#!/usr/bin/env python3
"""
Prepare per-project background images for video rendering.

Workflow:
    1. Drop raw images (any size, jpg/png/webp) into
       tts_pipeline/assets/projects/<project>/dropoff/
    2. Run:  py -3.12 tts_pipeline/scripts/prepare_backgrounds.py --project <project>
    3. Each image is moved to backgrounds/ and a 1920x1080 letterboxed copy is
       written to backgrounds/resized/<stem>_1920x1080<ext> (what the renderer uses).
    4. Edit tts_pipeline/config/projects/<project>/portrait_mapping.json to map
       chapter ranges to the new filenames.

Use --status to see the current mapping vs. available images without changing anything.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_ROOT = REPO_ROOT / "tts_pipeline" / "assets" / "projects"
CONFIG_ROOT = REPO_ROOT / "tts_pipeline" / "config" / "projects"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
TARGET = "1920:1080"


def project_dirs(project: str):
    base = ASSETS_ROOT / project
    return base / "dropoff", base / "backgrounds", base / "backgrounds" / "resized"


def resize_letterbox(src: Path, dst: Path) -> bool:
    """Scale to fit inside 1920x1080 and pad with black (matches existing assets)."""
    vf = (
        f"scale={TARGET}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET}:(ow-iw)/2:(oh-ih)/2:black"
    )
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", vf, "-q:v", "1", str(dst)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [ERROR] ffmpeg failed for {src.name}: {result.stderr.strip()}")
        return False
    return True


def cmd_prepare(project: str) -> int:
    dropoff, backgrounds, resized = project_dirs(project)
    for d in (dropoff, backgrounds, resized):
        d.mkdir(parents=True, exist_ok=True)

    images = sorted(p for p in dropoff.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if not images:
        print(f"No images in {dropoff} — nothing to do.")
        return 0

    ok = 0
    for src in images:
        # webp originals are converted to jpg so ffmpeg/renderer paths stay simple
        out_ext = ".jpg" if src.suffix.lower() == ".webp" else src.suffix.lower()
        final = backgrounds / (src.stem + out_ext)
        resized_out = resized / f"{src.stem}_1920x1080{out_ext}"

        print(f"[{src.name}]")
        if not resize_letterbox(src, resized_out):
            continue
        if out_ext != src.suffix.lower():
            # write a converted copy, then archive the original so dropoff/ empties
            if not resize_letterbox(src, final):
                continue
            shutil.move(str(src), str(backgrounds / src.name))
        else:
            shutil.move(str(src), str(final))
        print(f"  original -> {final.relative_to(REPO_ROOT)}")
        print(f"  resized  -> {resized_out.relative_to(REPO_ROOT)}")
        ok += 1

    print(f"\nPrepared {ok}/{len(images)} image(s).")
    print(f"Now map chapter ranges to these filenames in "
          f"{(CONFIG_ROOT / project / 'portrait_mapping.json').relative_to(REPO_ROOT)}")
    return 0 if ok == len(images) else 1


def cmd_status(project: str) -> int:
    dropoff, backgrounds, resized = project_dirs(project)
    mapping_file = CONFIG_ROOT / project / "portrait_mapping.json"

    print(f"Project: {project}")
    print(f"\nBackgrounds ({backgrounds.relative_to(REPO_ROOT)}):")
    have = set()
    if backgrounds.exists():
        for p in sorted(backgrounds.iterdir()):
            if p.suffix.lower() not in IMAGE_EXTS:
                continue
            # .webp originals are only archives of converted files — skip them
            # when their converted counterpart exists.
            if p.suffix.lower() == ".webp" and any(
                (backgrounds / f"{p.stem}{ext}").exists() for ext in (".jpg", ".jpeg", ".png")
            ):
                continue
            have.add(p.name)
            r = resized / f"{p.stem}_1920x1080{p.suffix}"
            print(f"  {p.name:45s} resized: {'yes' if r.exists() else 'MISSING'}")
    if dropoff.exists():
        pending = [p.name for p in dropoff.iterdir() if p.suffix.lower() in IMAGE_EXTS]
        if pending:
            print(f"\nWaiting in dropoff/ (run without --status to process): {', '.join(pending)}")

    if not mapping_file.exists():
        print(f"\nNo portrait_mapping.json for {project} — every chapter would fail loudly.")
        return 1

    data = json.loads(mapping_file.read_text(encoding="utf-8"))
    print(f"\nMapping ({mapping_file.relative_to(REPO_ROOT)}):")
    missing = 0
    for rng, cfg in data.get("portrait_mapping", {}).items():
        img = cfg.get("image")
        if img is None:
            state = "TODO (no art)"
            missing += 1
        elif img in have:
            state = "ok"
        else:
            state = "IMAGE FILE MISSING"
            missing += 1
        print(f"  {rng:12s} -> {str(img):40s} [{state}]")
    print(f"\n{missing} range(s) still need attention." if missing else "\nAll ranges mapped.")
    return 1 if missing else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, help="Project name (e.g. lom_book2_coi)")
    ap.add_argument("--status", action="store_true", help="Report mapping/image state; change nothing")
    args = ap.parse_args()

    if not (CONFIG_ROOT / args.project).exists():
        print(f"Unknown project: {args.project} (no config dir under {CONFIG_ROOT.relative_to(REPO_ROOT)})")
        sys.exit(2)

    sys.exit(cmd_status(args.project) if args.status else cmd_prepare(args.project))


if __name__ == "__main__":
    main()
