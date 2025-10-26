#!/usr/bin/env python3
"""
Test YouTube upload for Chapter 1

Demonstrates:
- Checking if a video has been uploaded: uploader.is_video_uploaded(filename)
- Getting upload info: uploader.get_video_info(filename)
- Getting/creating playlists: uploader.get_playlist_id(volume_number, volume_name)
- Checking if video is in playlist: uploader.is_video_in_playlist(video_id, playlist_id)
- Uploading videos with automatic playlist assignment
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add tts_pipeline to path
sys.path.insert(0, str(Path(__file__).parent / "tts_pipeline"))

from tts_pipeline.utils.project_manager import ProjectManager
from tts_pipeline.api.youtube_uploader import YouTubeUploader
import json
import os

print("=" * 60)
print("YOUTUBE UPLOAD TEST - Chapter 1")
print("=" * 60)

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

# Initialize uploader
uploader = YouTubeUploader(project, config)

# Find Chapter 1
videos = uploader.discover_videos()
chapter_1 = next((v for v in videos if v['chapter_number'] == 1), None)

if not chapter_1:
    print("ERROR: Chapter 1 not found!")
    sys.exit(1)

# Check if already uploaded
if uploader.is_video_uploaded(chapter_1['filename']):
    existing = uploader.get_video_info(chapter_1['filename'])
    print(f"[ALREADY UPLOADED] Chapter 1 is already uploaded!")
    print(f"  Video ID: {existing['video_id']}")
    print(f"  Upload Time: {existing['upload_time']}")
    print(f"  YouTube URL: https://youtube.com/watch?v={existing['video_id']}")
    sys.exit(0)

print(f"Found Chapter 1: {chapter_1['filename']}")
print(f"File: {chapter_1['filepath']}")

# Check if file exists
if not Path(chapter_1['filepath']).exists():
    print("ERROR: Video file not found!")
    sys.exit(1)

file_size = Path(chapter_1['filepath']).stat().st_size / (1024 * 1024)
print(f"File size: {file_size:.2f} MB")
print()

# Generate and show metadata
metadata = uploader.generate_metadata(chapter_1)
print("Metadata:")
print(f"  Title: {metadata['title']}")
print(f"  Privacy: {metadata['privacyStatus']}")
print(f"  Tags: {', '.join(metadata['tags'])}")
print()

# Ready to upload
print("Ready to upload to YouTube!")
print("This will:")
print("  1. Open browser for OAuth2 authentication (first time only)")
print("  2. Upload Chapter 1 video")
print("  3. Set metadata automatically")
print()

# Get playlist ID for this volume
volume_number = chapter_1['volume_number']
volume_name = chapter_1['volume_name']
playlist_id = uploader.get_playlist_id(volume_number, volume_name)

if playlist_id:
    print(f"\nPlaylist: Volume {volume_number} - {volume_name}")
    print(f"  Playlist ID: {playlist_id}")
    print(f"  URL: https://www.youtube.com/playlist?list={playlist_id}")
else:
    print("\n[INFO] No playlist will be created (disabled or error)")

# Upload
print("\nStarting upload...")
try:
    video_id = uploader.upload_video(chapter_1, add_to_playlist=True)
    
    if video_id:
        print(f"\n[SUCCESS] Video uploaded: {video_id}")
        print(f"YouTube URL: https://youtube.com/watch?v={video_id}")
        
        # Mark as uploaded with playlist info
        uploader.mark_video_uploaded(chapter_1['filename'], video_id, playlist_id)
        print("\nVideo tracked in progress file.")
        
        if playlist_id:
            # Check if added to playlist
            if uploader.is_video_in_playlist(video_id, playlist_id):
                print(f"[SUCCESS] Video added to playlist!")
            else:
                print(f"[WARNING] Video may not be in playlist")
    else:
        print("\n[FAILED] Upload failed!")
        
except Exception as e:
    print(f"\n[ERROR] Error during upload: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

