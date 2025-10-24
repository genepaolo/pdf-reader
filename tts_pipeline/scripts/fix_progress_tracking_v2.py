#!/usr/bin/env python3
"""
Fix Progress Tracking Inconsistencies v2

This script fixes inconsistencies in progress.json by:
1. Checking for actual audio files and updating audio_completed status
2. Checking for actual video files and updating video_completed status
3. Removing orphaned records that don't have corresponding files
4. Ensuring audio and video counts match actual file counts

Usage:
    python tts_pipeline/scripts/fix_progress_tracking_v2.py --project lotm_book1
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Set
from datetime import datetime

# Add the project root to the Python path
sys.path.append('.')

from tts_pipeline.utils.project_manager import ProjectManager
from tts_pipeline.utils.progress_tracker import ProgressTracker


def find_actual_audio_files(project) -> Set[str]:
    """Find all actual audio files in the project output directory."""
    audio_files = set()
    output_dir = Path(project.processing_config['output_directory'])
    
    if not output_dir.exists():
        print(f"Output directory does not exist: {output_dir}")
        return audio_files
    
    # Look for MP3 files in all volume directories
    for volume_dir in output_dir.iterdir():
        if volume_dir.is_dir():
            for audio_file in volume_dir.glob("*.mp3"):
                if audio_file.stat().st_size > 0:  # Only count non-empty files
                    audio_files.add(audio_file.name)
    
    return audio_files


def find_actual_video_files(project) -> Set[str]:
    """Find all actual video files in the project video directory."""
    video_files = set()
    video_dir = Path(project.processing_config['video']['output_directory'])
    
    if not video_dir.exists():
        print(f"Video directory does not exist: {video_dir}")
        return video_files
    
    # Look for MP4 files in all volume directories
    for volume_dir in video_dir.iterdir():
        if volume_dir.is_dir():
            for video_file in volume_dir.glob("*.mp4"):
                if video_file.stat().st_size > 0:  # Only count non-empty files
                    video_files.add(video_file.name)
    
    return video_files


def get_chapter_filename_from_audio(audio_filename: str) -> str:
    """Convert audio filename to chapter filename."""
    return audio_filename.replace('.mp3', '.txt')


def get_chapter_filename_from_video(video_filename: str) -> str:
    """Convert video filename to chapter filename."""
    return video_filename.replace('.mp4', '.txt')


def fix_progress_tracking(project_name: str) -> bool:
    """Fix progress tracking inconsistencies for the given project."""
    print(f"[FIX] Fixing progress tracking for project: {project_name}")
    
    # Load project
    pm = ProjectManager()
    project = pm.load_project(project_name)
    
    # Load progress tracker
    progress_tracker = ProgressTracker(project)
    
    print(f"[STATUS] Current progress tracking status:")
    print(f"   Completed records: {len(progress_tracker.completed_chapter_records)}")
    print(f"   Failed records: {len(progress_tracker.failed_chapter_records)}")
    
    # Find actual files
    print(f"[SCAN] Scanning for actual files...")
    actual_audio_files = find_actual_audio_files(project)
    actual_video_files = find_actual_video_files(project)
    
    print(f"   Found {len(actual_audio_files)} audio files")
    print(f"   Found {len(actual_video_files)} video files")
    
    # Create sets of chapter filenames from actual files
    chapters_with_audio = {get_chapter_filename_from_audio(audio) for audio in actual_audio_files}
    chapters_with_video = {get_chapter_filename_from_video(video) for video in actual_video_files}
    
    print(f"   Chapters with audio: {len(chapters_with_audio)}")
    print(f"   Chapters with video: {len(chapters_with_video)}")
    
    # Track changes
    changes_made = 0
    records_to_remove = []
    
    # Fix existing completion records
    print(f"[FIX] Fixing existing completion records...")
    for i, record in enumerate(progress_tracker.completed_chapter_records):
        chapter_info = record['chapter_info']
        chapter_filename = chapter_info['filename']
        
        # Check if audio file actually exists
        audio_exists = chapter_filename in chapters_with_audio
        video_exists = chapter_filename in chapters_with_video
        
        # Update audio completion status
        if audio_exists and not record.get('audio_completed', False):
            record['audio_completed'] = True
            # Try to find the actual audio file path
            volume_name = chapter_info['volume_name']
            audio_filename = chapter_filename.replace('.txt', '.mp3')
            audio_output_dir = Path(project.processing_config['output_directory'])
            audio_path = audio_output_dir / volume_name / audio_filename
            
            if audio_path.exists():
                record['audio_file_path'] = str(audio_path)
                record['audio_file_size'] = audio_path.stat().st_size
            changes_made += 1
            print(f"   [OK] Fixed audio completion for: {chapter_filename}")
        
        elif not audio_exists and record.get('audio_completed', False):
            record['audio_completed'] = False
            record['audio_file_path'] = ""
            record['audio_file_size'] = 0
            changes_made += 1
            print(f"   [REMOVED] Fixed audio completion (removed) for: {chapter_filename}")
        
        # Update video completion status
        if video_exists and not record.get('video_completed', False):
            record['video_completed'] = True
            # Try to find the actual video file path
            volume_name = chapter_info['volume_name']
            video_filename = chapter_filename.replace('.txt', '.mp4')
            video_output_dir = Path(project.processing_config['video']['output_directory'])
            video_path = video_output_dir / volume_name / video_filename
            
            if video_path.exists():
                record['video_file_path'] = str(video_path)
                record['video_file_size'] = video_path.stat().st_size
            changes_made += 1
            print(f"   [OK] Fixed video completion for: {chapter_filename}")
        
        elif not video_exists and record.get('video_completed', False):
            record['video_completed'] = False
            record['video_file_path'] = ""
            record['video_file_size'] = 0
            changes_made += 1
            print(f"   [REMOVED] Fixed video completion (removed) for: {chapter_filename}")
        
        # Check if record should be removed (no audio and no video)
        if not audio_exists and not video_exists:
            records_to_remove.append(i)
            print(f"   [REMOVE] Marked for removal (no files): {chapter_filename}")
    
    # Remove orphaned records (in reverse order to maintain indices)
    for i in reversed(records_to_remove):
        removed_record = progress_tracker.completed_chapter_records.pop(i)
        chapter_id = progress_tracker._get_chapter_id(removed_record['chapter_info'])
        progress_tracker.completed_chapter_ids.discard(chapter_id)
        changes_made += 1
        print(f"   [REMOVED] Removed orphaned record: {removed_record['chapter_info']['filename']}")
    
    # Add missing records for files that exist but aren't tracked
    print(f"[ADD] Adding missing records for existing files...")
    all_tracked_chapters = {record['chapter_info']['filename'] for record in progress_tracker.completed_chapter_records}
    
    # Add missing audio records
    for chapter_filename in chapters_with_audio:
        if chapter_filename not in all_tracked_chapters:
            # Create a basic chapter info structure
            # We'll need to get this from the file organizer
            try:
                from tts_pipeline.utils.file_organizer import FileOrganizer
                organizer = FileOrganizer(project)
                chapters = organizer.discover_chapters()
                
                chapter_info = None
                for chapter in chapters:
                    if chapter['filename'] == chapter_filename:
                        chapter_info = chapter
                        break
                
                if chapter_info:
                    # Find the audio file
                    volume_name = chapter_info['volume_name']
                    audio_filename = chapter_filename.replace('.txt', '.mp3')
                    audio_output_dir = Path(project.processing_config['output_directory'])
                    audio_path = audio_output_dir / volume_name / audio_filename
                    
                    # Create completion record
                    completion_record = {
                        "timestamp": progress_tracker.metadata.get("last_updated", ""),
                        "chapter_info": chapter_info,
                        "audio_file_path": str(audio_path),
                        "audio_file_size": audio_path.stat().st_size if audio_path.exists() else 0,
                        "audio_completed": True,
                        "video_completed": chapter_filename in chapters_with_video,
                        "dry_run": False
                    }
                    
                    # Add video info if video exists
                    if chapter_filename in chapters_with_video:
                        video_filename = chapter_filename.replace('.txt', '.mp4')
                        video_output_dir = Path(project.processing_config['video']['output_directory'])
                        video_path = video_output_dir / volume_name / video_filename
                        completion_record.update({
                            "video_file_path": str(video_path),
                            "video_file_size": video_path.stat().st_size if video_path.exists() else 0,
                            "video_timestamp": progress_tracker.metadata.get("last_updated", "")
                        })
                    
                    # Add to progress tracker
                    chapter_id = progress_tracker._get_chapter_id(chapter_info)
                    progress_tracker.completed_chapter_ids.add(chapter_id)
                    progress_tracker.completed_chapter_records.append(completion_record)
                    changes_made += 1
                    print(f"   [ADDED] Added missing record for: {chapter_filename}")
                else:
                    print(f"   [WARNING] Could not find chapter info for: {chapter_filename}")
                    
            except Exception as e:
                print(f"   [ERROR] Error adding missing record for {chapter_filename}: {e}")
    
    # Update metadata
    progress_tracker.metadata["total_completed"] = len(progress_tracker.completed_chapter_records)
    progress_tracker.metadata["total_failed"] = len(progress_tracker.failed_chapter_records)
    progress_tracker.metadata["last_updated"] = datetime.now().isoformat()
    
    # Save changes
    if changes_made > 0:
        print(f"[SAVE] Saving {changes_made} changes to progress tracking...")
        success = progress_tracker._save_progress()
        if success:
            print(f"[SUCCESS] Successfully saved progress tracking changes")
        else:
            print(f"[ERROR] Failed to save progress tracking changes")
            return False
    else:
        print(f"[INFO] No changes needed - progress tracking is already consistent")
    
    # Final status
    print(f"\n[FINAL] Final progress tracking status:")
    print(f"   Completed records: {len(progress_tracker.completed_chapter_records)}")
    print(f"   Failed records: {len(progress_tracker.failed_chapter_records)}")
    
    # Count audio and video completions
    audio_completed = sum(1 for record in progress_tracker.completed_chapter_records 
                         if record.get('audio_completed', False))
    video_completed = sum(1 for record in progress_tracker.completed_chapter_records 
                         if record.get('video_completed', False))
    
    print(f"   Audio completed: {audio_completed}")
    print(f"   Video completed: {video_completed}")
    print(f"   Actual audio files: {len(actual_audio_files)}")
    print(f"   Actual video files: {len(actual_video_files)}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Fix progress tracking inconsistencies")
    parser.add_argument("--project", required=True, help="Project name to fix")
    
    args = parser.parse_args()
    
    try:
        success = fix_progress_tracking(args.project)
        if success:
            print(f"\n[SUCCESS] Progress tracking fix completed successfully!")
        else:
            print(f"\n[ERROR] Progress tracking fix failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error fixing progress tracking: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
