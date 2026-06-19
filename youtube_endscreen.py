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

LOGGING IN (IMPORTANT)
----------------------
Google blocks sign-in from a Playwright-launched browser ("this browser or app
may not be secure" -> accounts.google.com/.../signin/rejected). So the reliable
path is to sign in with your OWN Chrome and let this script ATTACH to it:

  1. Close all Chrome windows, then launch a dedicated debuggable Chrome:
       & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" \
         --remote-debugging-port=9222 \
         --user-data-dir="%USERPROFILE%\\yt-studio-chrome"
  2. In that window, sign into the Google account that owns the channel and open
     studio.youtube.com once (normal Chrome -> Google allows the login).
  3. Run this script with --connect-port 9222. It attaches to that Chrome; the
     login persists in the yt-studio-chrome profile for future runs.

The fallback --plan-only mode needs no browser at all.
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


def fetch_meta(uploader: YouTubeUploader, video_ids: list) -> dict:
    """video_id -> {'privacy': str, 'title': str} via Data API (batches of 50)."""
    if not uploader.youtube_service:
        uploader.authenticate()
    result = {}
    ids = [v for v in video_ids if v]
    for i in range(0, len(ids), 50):
        batch = ids[i:i + 50]
        resp = uploader.youtube_service.videos().list(
            part="status,snippet", id=",".join(batch)
        ).execute()
        for item in resp.get("items", []):
            result[item["id"]] = {
                "privacy": item.get("status", {}).get("privacyStatus"),
                "title": item.get("snippet", {}).get("title", ""),
            }
    return result


# --------------------------------------------------------------------------- #
# Browser automation (Playwright). Selectors are best-effort and verified live
# on the first run (which is why --dry-run pauses on video #1).
# --------------------------------------------------------------------------- #
def _dismiss_welcome(page):
    """Dismiss the first-run video-editor 'Get started' promo if it appears."""
    for label in ("Get started", "Got it", "No thanks"):
        b = page.get_by_role("button", name=label, exact=True)
        if b.count() > 0:
            try:
                b.first.click(timeout=4000)
                page.wait_for_timeout(1500)
                return
            except Exception:
                pass


def _pick_result_card(page, target_chapter: int, target_title: str):
    """
    Return the result card locator matching the target, or None.
    Matches on 'Chapter <n>' with a digit boundary (so 252 != 1252/2520).
    """
    cards = page.locator("ytcp-entity-card")
    n = cards.count()
    pat = re.compile(rf"Chapter\s*0*{target_chapter}(?!\d)")
    for i in range(n):
        try:
            txt = (cards.nth(i).inner_text() or "").strip()
        except Exception:
            continue
        if pat.search(txt):
            return cards.nth(i)
    return None


def add_end_screen(page, source_video_id: str, target_video_id: str,
                   target_title: str, target_chapter: int,
                   dry_run: bool, log) -> bool:
    """
    Open the video Editor for source_video_id and add one end-screen 'Video'
    element pointing at the target video (the next chapter).

    Verified flow (Studio, 2026-06):
      /video/<id>/editor -> dismiss 'Get started' -> #add-endscreen-icon-button
      -> menu item 'Video' -> #choose-video radio -> #search-yours -> click the
      matching result card -> #save-button.

    Returns True on success (or, in dry_run, on reaching the Save step).
    """
    url = f"{STUDIO}/video/{source_video_id}/editor"
    log(f"    open editor: {url}")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(7000)
    _dismiss_welcome(page)

    # If an end screen already exists, the icon opens edit mode instead of the
    # type menu; either way clicking it then choosing 'Video' adds an element.
    log("    add end screen -> Video")
    page.locator("#add-endscreen-icon-button").first.click(timeout=20000)
    page.wait_for_timeout(2000)
    page.locator("tp-yt-paper-item", has_text=re.compile(r"^\s*Video\s*$")).first.click(timeout=10000)
    page.wait_for_timeout(3500)

    log("    choose specific video")
    page.locator("#choose-video").first.click(timeout=10000)
    page.wait_for_timeout(3000)

    query = target_title or f"Chapter {target_chapter}"
    log(f"    search: {query!r}")
    box = page.locator("#search-yours")
    box.first.fill(query)
    page.wait_for_timeout(1200)
    page.keyboard.press("Enter")
    page.wait_for_timeout(4500)

    card = _pick_result_card(page, target_chapter, target_title)
    if card is None:
        log(f"    [WARN] no result matched 'Chapter {target_chapter}'. "
            "Leaving picker open for inspection.")
        return False
    log(f"    select target: Chapter {target_chapter}")
    card.click()
    page.wait_for_timeout(2500)

    if dry_run:
        log("    [DRY-RUN] target selected, end screen staged — NOT clicking Save.")
        return True

    save_btn = page.locator("#save-button")
    if save_btn.count() == 0:
        log("    [WARN] Save button not found")
        return False
    save_btn.first.click(timeout=10000)
    page.wait_for_timeout(4000)
    log("    [OK] Save clicked")
    return True


def run_browser(plan_eligible: list, args, log):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("[ERROR] Playwright is not installed.")
        log("        pip install playwright && playwright install chromium")
        return 1

    # screenshots go here regardless of how the browser is obtained
    profile_dir = Path(args.profile_dir).resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    interactive = sys.stdin.isatty()
    if not interactive:
        log("(Non-interactive run: will stop after the first video for inspection.)")

    processed = 0
    with sync_playwright() as p:
        owns_browser = True
        if args.connect_port:
            # Connect to a REAL Chrome the user launched with
            # --remote-debugging-port. This is the reliable way past Google's
            # automation login block: the user signs in normally in that Chrome,
            # and we just attach to it.
            endpoint = f"http://localhost:{args.connect_port}"
            log(f"Connecting to your Chrome over CDP at {endpoint} ...")
            try:
                browser = p.chromium.connect_over_cdp(endpoint)
            except Exception as e:
                log(f"[ABORT] Could not connect to Chrome on port {args.connect_port}.")
                log(f"        {e}")
                log("        Start Chrome first (all other Chrome windows closed):")
                log('        & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" '
                    f'--remote-debugging-port={args.connect_port} '
                    '--user-data-dir="%USERPROFILE%\\yt-studio-chrome"')
                return 1
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            owns_browser = False
        else:
            log(f"Using browser profile: {profile_dir}")
            log("(First time: log into the channel's Google account in the window, once.)")
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=args.headless,
                args=["--start-maximized"],
                no_viewport=True,
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Auto-accept "Leave site? Changes may not be saved" prompts so moving
        # between videos never blocks.
        page.on("dialog", lambda d: d.accept())

        # Make sure we're logged in.
        page.goto(f"{STUDIO}/", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        def logged_in():
            u = page.url
            return ("accounts.google" not in u
                    and "signin" not in u.lower()
                    and "studio.youtube.com" in u)

        if not logged_in():
            if not owns_browser:
                log("[ABORT] The connected Chrome is not signed into YouTube Studio yet.")
                log("        Sign into the channel's Google account in that Chrome window, "
                    "then re-run this command.")
                return 1
            log("[ACTION NEEDED] Log into the channel's Google account in the browser window.")
            if interactive:
                input("    Press Enter here once you are logged into YouTube Studio... ")
            else:
                waited = 0
                while waited < args.login_timeout and not logged_in():
                    page.wait_for_timeout(5000)
                    waited += 5
                    if waited % 20 == 0:
                        log(f"    ...waiting for login ({waited}s/{args.login_timeout}s) "
                            f"— current url: {page.url}")
                if not logged_in():
                    log("[ABORT] Not logged in within timeout. Re-run when ready to sign in "
                        "(the login is saved after the first time).")
                    ctx.close()
                    return 1
        log("[OK] Logged into YouTube Studio.")

        for i, item in enumerate(plan_eligible, 1):
            sc = item["source_chapter"]
            tc = item["target_chapter"]
            svid = item["source"]["video_id"]
            tvid = item["target"]["video_id"]
            ttitle = item["target"].get("title") or item["target"]["filename"]
            log(f"\n[{i}/{len(plan_eligible)}] Chapter {sc} (id {svid}) "
                f"-> link Chapter {tc} (id {tvid})")
            try:
                ok = add_end_screen(page, svid, tvid, ttitle, tc, args.dry_run, log)
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
                try:
                    page.screenshot(path=str(profile_dir / "first_video_result.png"))
                    log(f"    screenshot: {profile_dir / 'first_video_result.png'}")
                except Exception:
                    pass
                if interactive:
                    log("\n--- Paused after the first video so you can verify it. ---")
                    resp = input("    Continue with the rest? (yes/no): ").strip().lower()
                    if resp not in ("y", "yes"):
                        log("Stopping after first video by request.")
                        break
                else:
                    log("\n--- Non-interactive: stopping after the first video for "
                        "inspection. Re-run with --yes to process the whole batch. ---")
                    page.wait_for_timeout(3000)
                    break

        if owns_browser:
            if not args.headless and interactive:
                input("\nDone. Press Enter to close the browser... ")
            ctx.close()
        else:
            log("(Left your Chrome window open.)")
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
    ap.add_argument("--login-timeout", type=int, default=240,
                    help="Seconds to wait for sign-in when run non-interactively (default 240).")
    ap.add_argument("--connect-port", type=int, default=None,
                    help="Attach to a real Chrome already running with "
                         "--remote-debugging-port=PORT (recommended; avoids Google's "
                         "automation login block). E.g. --connect-port 9222.")
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

    # Resolve privacy + exact titles for sources and targets via the Data API.
    uploader = YouTubeUploader(project, config)
    all_ids = []
    for p in plan:
        for side in ("source", "target"):
            if p[side] and p[side].get("video_id"):
                all_ids.append(p[side]["video_id"])
    log("\nReading privacy + titles from YouTube Data API (token.json)...")
    meta = fetch_meta(uploader, all_ids)

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
        status = (meta.get(svid) or {}).get("privacy", "unknown")
        # attach the target's real YouTube title for accurate searching
        item["target"]["title"] = (meta.get(item["target"]["video_id"]) or {}).get("title", "")
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
