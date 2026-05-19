#!/usr/bin/env python3
"""
Generate CSV file for manual YouTube uploads
"""

import sys
import argparse
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

parser = argparse.ArgumentParser(description="Generate upload metadata text file")
parser.add_argument('--project', default='lom_book2_coi')
args = parser.parse_args()

project_name = args.project

print(f"Generating upload CSV for {project_name}...")

# Load project and config
project_manager = ProjectManager()
project = project_manager.load_project(project_name)

config_path = Path(f"tts_pipeline/config/projects/{project_name}/youtube_config.json")
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
        
        f.write(f"\n{'='*80}\n")
        f.write(f"CHAPTER {video['chapter_number']}: {video['chapter_title']}\n")
        f.write(f"{'='*80}\n")
        f.write(f"Title: {metadata['title']}\n")
        f.write(f"Volume {video['volume_number']}: {video['volume_name']}\n")
        f.write(f"\nDescription:\n")
        f.write(f"{metadata['description']}\n")
        
        # Add separator between chapters
        if i < len(videos_to_upload) - 1:
            f.write(f"\n{'-'*80}\n")
    
    f.write(f"\n{'='*80}\n")

print(f"\nText file generated: {txt_file}")
print(f"Total videos to upload: {len(videos_to_upload)}")
print("\nThis file contains all the information needed to upload videos to YouTube manually.")

