#!/usr/bin/env python3
"""
Queue-based YouTube upload script

Uploads multiple videos to YouTube with:
- Duplicate detection
- Automatic playlist assignment
- Rate limiting
- Progress tracking
- Error handling
"""

import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add tts_pipeline to path
sys.path.insert(0, str(Path(__file__).parent / "tts_pipeline"))

from tts_pipeline.utils.project_manager import ProjectManager
from tts_pipeline.api.youtube_uploader import YouTubeUploader
import json
import os

print("=" * 80)
print("YOUTUBE UPLOAD QUEUE")
print("=" * 80)

# Load project and config
project_manager = ProjectManager()
project = project_manager.load_project("lotm_book1")

config_path = Path("tts_pipeline/config/projects/lotm_book1/youtube_config.json")
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Override with env
if config.get("channel_id") == "from_env":
    config["channel_id"] = os.getenv("YOUTUBE_CHANNEL_ID", "")
if config.get("oauth2_credentials") == "from_env":
    config["oauth2_credentials"] = os.getenv("YOUTUBE_CREDENTIALS_PATH", "")

print(f"\nChannel ID: {config['channel_id']}")
print(f"Credentials: {config['oauth2_credentials']}")
print()

# Initialize uploader and authenticate
uploader = YouTubeUploader(project, config)
uploader.authenticate()  # Authenticate early so we can verify videos exist

# Verify tracker accuracy with YouTube channel
print("Verifying tracker against YouTube channel...")
print("(This may take a moment)")
verification_results = uploader.verify_tracker_with_youtube()

print(f"\nVerification Results:")
print(f"  Videos in tracker: {verification_results['total_in_tracker']}")
print(f"  Videos on YouTube: {verification_results['total_on_youtube']}")
print(f"  Verified matches: {verification_results['verified_count']}")
print()

if len(verification_results['missing_in_tracker']) > 0:
    print(f"[WARNING] Found {len(verification_results['missing_in_tracker'])} videos on YouTube not in tracker:")
    for video in verification_results['missing_in_tracker'][:5]:
        print(f"  - {video['title']} ({video['video_id']})")
    if len(verification_results['missing_in_tracker']) > 5:
        print(f"  ... and {len(verification_results['missing_in_tracker']) - 5} more")
    print()

if len(verification_results['missing_on_youtube']) > 0:
    print(f"[WARNING] Found {len(verification_results['missing_on_youtube'])} videos in tracker but not on YouTube:")
    for video in verification_results['missing_on_youtube'][:5]:
        print(f"  - {video['filename']} ({video['video_id']})")
    if len(verification_results['missing_on_youtube']) > 5:
        print(f"  ... and {len(verification_results['missing_on_youtube']) - 5} more")
    print()

print("[OK] Verification complete")
print()

# Discover all videos
print("Discovering videos...")
all_videos = uploader.discover_videos()
print(f"Found {len(all_videos)} total videos")
print()

# Get videos that need uploading
videos_to_upload = uploader.get_videos_to_upload(all_videos)
print(f"Videos to upload: {len(videos_to_upload)}")
print()

if len(videos_to_upload) == 0:
    print("All videos are already uploaded!")
    sys.exit(0)

# Check for limit flag
limit = None
for arg in sys.argv:
    if arg.startswith('--limit='):
        limit = int(arg.split('=')[1])
    elif arg == '--limit':
        # Will be handled by next arg, just mark that we should look for it
        pass

# Handle limit=0 (just verification, no upload)
if limit == 0:
    print("[INFO] Limit set to 0 - verification only, no uploads")
    print("\nVerification complete. Add --limit=N to upload N videos.")
    sys.exit(0)

# Apply limit if specified
if limit is not None:
    if limit > len(videos_to_upload):
        print(f"[INFO] Limit ({limit}) is greater than videos to upload ({len(videos_to_upload)})")
        print(f"[INFO] Will upload all {len(videos_to_upload)} videos")
    else:
        print(f"[INFO] Limiting to first {limit} videos")
        videos_to_upload = videos_to_upload[:limit]

# Show what will be uploaded
print("Videos to upload:")
for video in videos_to_upload[:10]:  # Show first 10
    print(f"  - Chapter {video['chapter_number']}: {video['chapter_title']}")
if len(videos_to_upload) > 10:
    print(f"  ... and {len(videos_to_upload) - 10} more")
print()

# Check for auto-confirm flag
auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

if not auto_confirm:
    # Confirm upload
    print("Ready to start upload process!")
    print(f"\nWill upload exactly {len(videos_to_upload)} video(s):")
    for i, video in enumerate(videos_to_upload, 1):
        print(f"  {i}. Chapter {video['chapter_number']}: {video['chapter_title']}")
    
    print("\nThis will:")
    print("  1. Authenticate with YouTube (if needed)")
    print("  2. Upload each video")
    print("  3. Add videos to correct playlists automatically")
    print("   (One playlist per volume)")
    print("  4. Respect rate limits")
    print("  5. Track progress")
    print()

    try:
        response = input("Start upload? (yes/no): ").strip().lower()
        if response != 'yes' and response != 'y':
            print("Upload cancelled.")
            sys.exit(0)
    except EOFError:
        print("[INFO] Running in non-interactive mode. Use --yes to auto-confirm.")
        sys.exit(1)
else:
    print("[INFO] Auto-confirm enabled (--yes flag)")
    print(f"\nWill upload exactly {len(videos_to_upload)} video(s):")
    for i, video in enumerate(videos_to_upload, 1):
        print(f"  {i}. Chapter {video['chapter_number']}: {video['chapter_title']}")

print("\n" + "=" * 80)
print("STARTING UPLOAD PROCESS")
print("=" * 80)

# Upload each video
successful = 0
failed = 0

for i, video_info in enumerate(videos_to_upload, 1):
    chapter_num = video_info['chapter_number']
    chapter_title = video_info['chapter_title']
    filename = video_info['filename']
    
    print(f"\n[{i}/{len(videos_to_upload)}] Uploading Chapter {chapter_num}: {chapter_title}")
    print(f"Filename: {filename}")
    
    # Check if already uploaded (safety check)
    if uploader.is_video_uploaded(filename):
        existing = uploader.get_video_info(filename)
        print(f"[SKIP] Already uploaded: {existing['video_id']}")
        continue
    
    # Check rate limit
    if not uploader.can_upload_now():
        wait_time = uploader.time_until_next_upload()
        print(f"[WAIT] Rate limit - waiting {wait_time} seconds...")
        time.sleep(wait_time)
    
    # Get playlist info
    volume_number = video_info['volume_number']
    volume_name = video_info['volume_name']
    playlist_id = uploader.get_playlist_id(volume_number, volume_name)
    
    if playlist_id:
        print(f"Playlist: Volume {volume_number} - {volume_name} ({playlist_id})")
    
    try:
        # Upload video
        video_id = uploader.upload_video(video_info, add_to_playlist=True)
        
        if video_id:
            print(f"[SUCCESS] Video uploaded: {video_id}")
            print(f"YouTube URL: https://youtube.com/watch?v={video_id}")
            
            # Mark as uploaded with playlist info
            uploader.mark_video_uploaded(filename, video_id, playlist_id)
            
            # Verify in playlist
            if playlist_id and uploader.is_video_in_playlist(video_id, playlist_id):
                print(f"[SUCCESS] Video confirmed in playlist")
            elif playlist_id:
                print(f"[WARNING] Video may not be in playlist")
            
            successful += 1
        else:
            print(f"[FAILED] Upload returned no video ID")
            failed += 1
            
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        failed += 1
        
        # Show progress
        print(f"\nProgress: {successful} successful, {failed} failed")

# Final summary
print("\n" + "=" * 80)
print("UPLOAD COMPLETE")
print("=" * 80)
print(f"Successfully uploaded: {successful}")
print(f"Failed: {failed}")
print(f"Total processed: {len(videos_to_upload)}")
print()

