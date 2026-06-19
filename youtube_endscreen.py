#!/usr/bin/env python3
"""
YouTube end-screen linker (Studio UI automation).

For a range of chapters, add an end screen to each source video that links to the
NEXT chapter's video (250 -> 251, 251 -> 252, ... ), so a viewer is funneled to
the next chapter automatically.

WHY THIS IS UI AUTOMATION (NOT THE API)
---------------------------------------
The YouTube Data API v3 has *no* support for end screens or cards. The only way
to set them programmatically is to drive the YouTube Studio web UI with a real
browser. This script uses Playwright for that. The browser part is inherently
more fragile than the upload API and may need selector tweaks when Google changes
the Studio UI.

SAFETY GUARD (the important part)
---------------------------------
This script will ONLY modify videos whose privacyStatus == "unlisted".
Privacy is read from the YouTube Data API (reusing the same token.json the
uploader uses) BEFORE the browser ever touches a video. Public and private
videos are skipped and never edited. This guard does not depend on the fragile
UI layer.

TYPICAL USAGE
-------------
1. Plan only (no browser, safe, shows source->target + privacy):
     python youtube_endscreen.py --project lom_book2_coi --chapters 250-259 --plan-only

2. Dry run (opens a VISIBLE browser, does every click EXCEPT the final Save,
   and pauses after the first video so you can watch it work):
     python youtube_endscreen.py --project lom_book2_coi --chapters 250-259 --dry-run

3. Real run (saves end screens; still pauses on the first video unless --yes):
     python youtube_endscreen.py --project lom_book2_coi --chapters 250-259

FIRST-TIME SETUP
----------------
  pip install playwright
  playwright install chromium
The first browser launch uses a persistent profile (default: .yt_studio_profile/,
gitignored). Log into the Google account that owns the channel ONCE in that
window; later runs reuse the session.
"""

import sys
import re
import json
import time
import argparse
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Reuse the project/config/auth plumbing the uploader already uses.
sys.path.insert(0, str(Path(__file__).parent / "tts_pipeline"))
from tts_pipeline.utils.project_manager import ProjectManager  # noqa: E402
from tts_pipeline.api.youtube_uploader import YouTubeUploader  # noqa: E402

STUDIO = "https://studio.youtube.com"
DEFAULT_PROFILE_DIR = ".yt_studio_profile"


# --------------------------------------------------------------------------- #
# Tracker / mapping helpers (no browser, fully testable offline)
# --------------------------------------------------------------------------- #
def load_chapter_map(progress_file: Path) -> dict:
    """chapter_number -> {filename, video_id} from youtube_progress.json."""
    data = json.loads(progress_file.read_text(encoding="utf-8"))
    uploaded = data.get("uploaded_videos", {})
    chapters = {}
    for filename, info in uploaded.items():
        m = re.match(r"Chapter_(\d+)_", filename)
        if not m:
            continue
        num = int(m.group(1))
        chapters[num] = {
            "filename": filename,
            "video_id": info.get("video_id"),
        }
    return chapters


def parse_range(spec: str) -> tuple:
    """'250-259' -> (250, 259); '250' -> (250, 250)."""
    spec = spec.strip()
    if "-" in spec:
        lo, hi = spec.split("-", 1)
        return int(lo), int(hi)
    n = int(spec)
    return n, n


def build_plan(chapter_map: dict, lo: int, hi: int) -> list:
    """
    For each source chapter K in [lo, hi], pair it with target K+1.
    Returns list of dicts with source/target chapter, filename, video_id.
    Entries with a missing source or target video_id are flagged.
    """
    plan = []
    for k in range(lo, hi + 1):
        src = chapter_map.get(k)
        tgt = chapter_map.get(k + 1)
        plan.append({
            "source_chapter": k,
            "source": src,
            "target_chapter": k + 1,
            "target": tgt,
            "skip_reason": (
                "source video not in tracker" if not src or not src.get("video_id")
                else "target (next chapter) video not in tracker" if not tgt or not tgt.get("video_id")
                else None
            ),
        })
    return plan


def fetch_privacy(uploader: YouTubeUploader, video_ids: list) -> dict:
    """video_id -> privacyStatus via Data API (batches of 50)."""
    if not uploader.youtube_service:
        uploader.authenticate()
    result = {}
    for i in range(0, len(video_ids), 50):
        batch = [v for v in video_ids[i:i + 50] if v]
        if not batch:
            continue
        resp = uploader.youtube_service.videos().list(
            part="status", id=",".join(batch)
        ).execute()
        for item in resp.get("items", []):
            result[item["id"]] = item.get("status", {}).get("privacyStatus")
    return result


# --------------------------------------------------------------------------- #
# Browser automation (Playwright). Selectors are best-effort and verified live
# on the first run (which is why --dry-run pauses on video #1).
# --------------------------------------------------------------------------- #
def add_end_screen(page, source_video_id: str, target_video_id: str,
                   target_title: str, dry_run: bool, log) -> bool:
    """
    Navigate to the end-screen editor for source_video_id and add a single
    'specific video' element pointing at target_video_id.

    Returns True if it believes it succeeded (or, in dry-run, reached the Save
    step). Raises/returns False on trouble so the caller can decide.
    """
    import re as _re

    # The end-screen editor lives under the video's editor. Studio has used a
    # couple of path shapes over time; try the dedicated one, fall back to the
    # editor tab.
    candidates = [
        f"{STUDIO}/video/{source_video_id}/end-screens",
        f"{STUDIO}/video/{source_video_id}/editor",
    ]
    loaded = False
    for url in candidates:
        log(f"    navigating: {url}")
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3500)
        if "/end-screens" in page.url or page.get_by_text(
            _re.compile("end screen", _re.I)).count() > 0:
            loaded = True
            break
    if not loaded:
        log("    [WARN] could not confirm end-screen editor loaded")

    # ADD ELEMENT
    add_btn = page.get_by_role("button", name=_re.compile(r"add element", _re.I))
    if add_btn.count() == 0:
        add_btn = page.get_by_text(_re.compile(r"^\s*add element\s*$", _re.I))
    add_btn.first.click()
    page.wait_for_timeout(1200)

    # Choose "Video" from the element-type menu.
    page.get_by_text(_re.compile(r"^\s*video\s*$", _re.I)).first.click()
    page.wait_for_timeout(1200)

    # Prefer "specific video" if a sub-menu appears.
    specific = page.get_by_text(_re.compile(r"specific video|choose a video", _re.I))
    if specific.count() > 0:
        specific.first.click()
        page.wait_for_timeout(1500)

    # In the picker, search by the target video id (most precise) then title.
    search = page.get_by_role("textbox").filter(
        has_text=_re.compile("", _re.I))
    try:
        box = page.get_by_placeholder(_re.compile(r"search", _re.I))
        if box.count() == 0:
            box = search
        box.first.fill(target_video_id)
        page.wait_for_timeout(2000)
    except Exception:
        log("    [WARN] could not find a search box in the picker")

    # Click the first result.
    result = page.get_by_text(_re.compile(_re.escape(target_title[:20]), _re.I))
    if result.count() == 0:
        # fall back: click first selectable thumbnail/result row
        result = page.locator("ytcp-video-row, #video-list-item, ytcp-entity-card")
    if result.count() > 0:
        result.first.click()
        page.wait_for_timeout(1500)
    else:
        log("    [WARN] no picker result matched; manual selection may be needed")

    save_btn = page.get_by_role("button", name=_re.compile(r"^\s*save\s*$", _re.I))
    if dry_run:
        log("    [DRY-RUN] reached Save step — NOT clicking Save.")
        return True

    if save_btn.count() == 0:
        log("    [WARN] Save button not found")
        return False
    save_btn.first.click()
    page.wait_for_timeout(3000)
    log("    [OK] Save clicked")
    return True


def run_browser(plan_eligible: list, args, log):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("[ERROR] Playwright is not installed.")
        log("        pip install playwright && playwright install chromium")
        return 1

    profile_dir = Path(args.profile_dir).resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)
    log(f"Using browser profile: {profile_dir}")
    log("(First time: log into the channel's Google account in the window, once.)")

    processed = 0
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=args.headless,
            args=["--start-maximized"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Make sure we're logged in.
        page.goto(f"{STUDIO}/", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)
        if "accounts.google" in page.url or "signin" in page.url.lower():
            log("[ACTION NEEDED] Please complete Google sign-in in the browser window.")
            input("    Press Enter here once you are logged into YouTube Studio... ")

        for i, item in enumerate(plan_eligible, 1):
            sc = item["source_chapter"]
            tc = item["target_chapter"]
            svid = item["source"]["video_id"]
            tvid = item["target"]["video_id"]
            ttitle = item["target"]["filename"]
            log(f"\n[{i}/{len(plan_eligible)}] Chapter {sc} (id {svid}) "
                f"-> link Chapter {tc} (id {tvid})")
            try:
                ok = add_end_screen(page, svid, tvid, ttitle, args.dry_run, log)
                processed += 1 if ok else 0
            except Exception as e:
                log(f"    [ERROR] {e}")
                shot = profile_dir / f"error_ch{sc}.png"
                try:
                    page.screenshot(path=str(shot))
                    log(f"    screenshot saved: {shot}")
                except Exception:
                    pass

            # Pause after the FIRST video unless --yes, so the human can watch
            # and confirm before the batch continues unattended.
            if i == 1 and not args.yes:
                log("\n--- Paused after the first video so you can verify it. ---")
                resp = input("    Continue with the rest? (yes/no): ").strip().lower()
                if resp not in ("y", "yes"):
                    log("Stopping after first video by request.")
                    break

        if not args.headless:
            input("\nDone. Press Enter to close the browser... ")
        ctx.close()
    log(f"\nProcessed {processed} video(s).")
    return 0


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Add sequential end screens via YouTube Studio.")
    ap.add_argument("--project", default="lom_book2_coi")
    ap.add_argument("--chapters", required=True,
                    help="Source range, e.g. 250-259 (each links to the next chapter).")
    ap.add_argument("--plan-only", action="store_true",
                    help="Print the source->target plan + privacy, no browser.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Open the browser and do everything EXCEPT clicking Save.")
    ap.add_argument("--headless", action="store_true",
                    help="Run the browser without a window (not recommended first time).")
    ap.add_argument("--yes", action="store_true",
                    help="Do not pause after the first video.")
    ap.add_argument("--profile-dir", default=DEFAULT_PROFILE_DIR,
                    help=f"Persistent browser profile dir (default: {DEFAULT_PROFILE_DIR}).")
    args = ap.parse_args()

    def log(msg=""):
        print(msg, flush=True)

    log("=" * 78)
    log(f"YOUTUBE END-SCREEN LINKER — {args.project}")
    log("=" * 78)

    pm = ProjectManager()
    project = pm.load_project(args.project)

    config_path = Path(f"tts_pipeline/config/projects/{args.project}/youtube_config.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    progress_file = Path(project.get_output_directory()) / "youtube_progress.json"
    if not progress_file.exists():
        log(f"[ERROR] Tracker not found: {progress_file}")
        return 1

    chapter_map = load_chapter_map(progress_file)
    lo, hi = parse_range(args.chapters)
    plan = build_plan(chapter_map, lo, hi)

    # Resolve privacy for all source video ids via the Data API.
    uploader = YouTubeUploader(project, config)
    src_ids = [p["source"]["video_id"] for p in plan
               if p["source"] and p["source"].get("video_id")]
    log("\nReading privacy status from YouTube Data API (token.json)...")
    privacy = fetch_privacy(uploader, src_ids)

    # Build the eligible list applying the UNLISTED-ONLY guard.
    eligible = []
    log("\nPlan (source chapter -> next chapter):")
    log(f"{'SRC':>5}  {'->':^3} {'TGT':>5}  {'PRIVACY':<9}  STATUS")
    for item in plan:
        sc, tc = item["source_chapter"], item["target_chapter"]
        if item["skip_reason"]:
            log(f"{sc:>5}  ->  {tc:>5}  {'-':<9}  SKIP: {item['skip_reason']}")
            continue
        svid = item["source"]["video_id"]
        status = privacy.get(svid, "unknown")
        if status == "unlisted":
            eligible.append(item)
            log(f"{sc:>5}  ->  {tc:>5}  {status:<9}  ELIGIBLE")
        else:
            log(f"{sc:>5}  ->  {tc:>5}  {status:<9}  SKIP (guard: not unlisted)")

    log(f"\nEligible (unlisted) videos to edit: {len(eligible)} / {len(plan)}")

    if args.plan_only:
        log("\n[plan-only] No browser launched.")
        return 0
    if not eligible:
        log("Nothing eligible to process. Exiting.")
        return 0

    log("\nMode: " + ("DRY-RUN (no Save)" if args.dry_run else "LIVE (will Save end screens)"))
    return run_browser(eligible, args, log)


if __name__ == "__main__":
    sys.exit(main())
