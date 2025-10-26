#!/usr/bin/env python3
"""
Generate CSV file for manual YouTube uploads
"""

import sys
import csv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add tts_pipeline to path
sys.path.insert(0, str(Path(__file__).parent / "tts_pipeline"))

from tts_pipeline.utils.project_manager import ProjectManager
from tts_pipeline.api.youtube_uploader import YouTubeUploader
import json
import os

print("Generating upload CSV...")

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

# Initialize uploader
uploader = YouTubeUploader(project, config)

# Discover all videos
all_videos = uploader.discover_videos()
print(f"Found {len(all_videos)} total videos")

# Get videos that need uploading
videos_to_upload = uploader.get_videos_to_upload(all_videos)
print(f"Videos to upload: {len(videos_to_upload)}")

# Generate text file
txt_file = "youtube_upload_queue.txt"
with open(txt_file, 'w', encoding='utf-8') as f:
    for i, video in enumerate(videos_to_upload):
        # Generate metadata
        metadata = uploader.generate_metadata(video)
        
        # Write chapter info in the format from template (simplified)
        f.write(f"\n{'='*80}\n")
        f.write(f"CHAPTER {video['chapter_number']}: {video['chapter_title']}\n")
        f.write(f"{'='*80}\n")
        f.write(f"Lord of the Mysteries\n")
        f.write(f"Volume {video['volume_number']}:{video['volume_name']}\n")
        f.write(f"Chapter {video['chapter_number']}: {video['chapter_title']}\n")
        f.write(f"\n")
        f.write(f"\n")
        f.write(f"🎧 If you enjoy the content and audio, I'd love your support! Like, comment, share and sub if you'd like more.\n")
        f.write(f"\n")
        f.write(f"☕ Lord of the Bread wouldn't mind coffee either ❤️: https://buymeacoffee.com/breadmoretti\n")
        f.write(f"\n")
        f.write(f"#audiobook #lotm #fantasy\n")
        
        # Add separator between chapters
        if i < len(videos_to_upload) - 1:
            f.write(f"\n{'-'*80}\n")
    
    f.write(f"\n{'='*80}\n")

print(f"\nText file generated: {txt_file}")
print(f"Total videos to upload: {len(videos_to_upload)}")
print("\nThis file contains all the information needed to upload videos to YouTube manually.")

