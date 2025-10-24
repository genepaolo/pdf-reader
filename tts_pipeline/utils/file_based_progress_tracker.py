#!/usr/bin/env python3
"""
File-Based Progress Tracker

A simplified progress tracking system that counts actual audio and video files
instead of maintaining a complex database. This approach is more reliable and
self-healing since it always reflects the actual state of files.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add the project root to the Python path
sys.path.append('.')

from tts_pipeline.utils.project_manager import ProjectManager
from tts_pipeline.utils.file_organizer import ChapterFileOrganizer


class FileBasedProgressTracker:
    """
    Simplified progress tracker that counts actual files instead of maintaining a database.
    """
    
    def __init__(self, project):
        self.project = project
        self.file_organizer = ChapterFileOrganizer(project)
        
        # Get paths from project config
        self.audio_output_dir = Path(project.processing_config['output_directory'])
        self.video_output_dir = Path(project.processing_config['video']['output_directory'])
        
        # Cache for performance
        self._audio_files_cache = None
        self._video_files_cache = None
        self._cache_timestamp = None
    
    def _scan_files(self) -> Tuple[Dict[str, Path], Dict[str, Path]]:
        """
        Scan for actual audio and video files.
        
        Returns:
            Tuple of (audio_files_dict, video_files_dict) where keys are chapter filenames
        """
        audio_files = {}
        video_files = {}
        
        # Scan audio files
        if self.audio_output_dir.exists():
            for volume_dir in self.audio_output_dir.iterdir():
                if volume_dir.is_dir():
                    for audio_file in volume_dir.glob("*.mp3"):
                        if audio_file.stat().st_size > 0:  # Only count non-empty files
                            chapter_name = audio_file.stem + '.txt'
                            audio_files[chapter_name] = audio_file
        
        # Scan video files
        if self.video_output_dir.exists():
            for volume_dir in self.video_output_dir.iterdir():
                if volume_dir.is_dir():
                    for video_file in volume_dir.glob("*.mp4"):
                        if video_file.stat().st_size > 0:  # Only count non-empty files
                            chapter_name = video_file.stem + '.txt'
                            video_files[chapter_name] = video_file
        
        return audio_files, video_files
    
    def _get_cached_files(self) -> Tuple[Dict[str, Path], Dict[str, Path]]:
        """
        Get cached file scan results or scan if cache is stale.
        """
        now = datetime.now()
        
        # Use cache if it's less than 30 seconds old
        if (self._cache_timestamp and 
            (now - self._cache_timestamp).total_seconds() < 30 and
            self._audio_files_cache is not None and
            self._video_files_cache is not None):
            return self._audio_files_cache, self._video_files_cache
        
        # Scan files and cache results
        self._audio_files_cache, self._video_files_cache = self._scan_files()
        self._cache_timestamp = now
        
        return self._audio_files_cache, self._video_files_cache
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive progress summary based on actual files.
        
        Returns:
            Dictionary with progress information
        """
        audio_files, video_files = self._get_cached_files()
        
        # Get all chapters from file organizer
        all_chapters = self.file_organizer.discover_chapters()
        total_chapters = len(all_chapters)
        
        # Count completions
        audio_completed = len(audio_files)
        video_completed = len(video_files)
        
        # Find next chapters to process
        next_audio_chapter = self._find_next_chapter(all_chapters, audio_files, 'audio')
        next_video_chapter = self._find_next_chapter(all_chapters, video_files, 'video')
        
        # Calculate percentages
        audio_percentage = (audio_completed / total_chapters * 100) if total_chapters > 0 else 0
        video_percentage = (video_completed / total_chapters * 100) if total_chapters > 0 else 0
        
        # Get volume breakdown
        volume_breakdown = self._get_volume_breakdown(all_chapters, audio_files, video_files)
        
        return {
            'project_name': self.project.project_name,
            'display_name': self.project.project_config.get('display_name', self.project.project_name),
            'total_chapters': total_chapters,
            'total_volumes': len(set(ch['volume_name'] for ch in all_chapters)),
            'audio_completed': audio_completed,
            'video_completed': video_completed,
            'audio_percentage': audio_percentage,
            'video_percentage': video_percentage,
            'next_audio_chapter': next_audio_chapter,
            'next_video_chapter': next_video_chapter,
            'volume_breakdown': volume_breakdown,
            'last_updated': datetime.now().isoformat(),
            'audio_files': audio_files,
            'video_files': video_files
        }
    
    def _find_next_chapter(self, chapters: List[Dict[str, Any]], 
                          completed_files: Dict[str, Path], 
                          completion_type: str) -> Optional[Dict[str, Any]]:
        """
        Find the next chapter that needs processing.
        
        Args:
            chapters: List of all chapters
            completed_files: Dictionary of completed files (key = chapter filename)
            completion_type: 'audio' or 'video' (for logging)
            
        Returns:
            Next chapter to process, or None if all completed
        """
        for chapter in chapters:
            chapter_filename = chapter['filename']
            if chapter_filename not in completed_files:
                return chapter
        
        return None  # All chapters completed
    
    def _get_volume_breakdown(self, chapters: List[Dict[str, Any]], 
                            audio_files: Dict[str, Path], 
                            video_files: Dict[str, Path]) -> Dict[str, Dict[str, Any]]:
        """
        Get completion breakdown by volume.
        
        Args:
            chapters: List of all chapters
            audio_files: Dictionary of audio files
            video_files: Dictionary of video files
            
        Returns:
            Dictionary with volume breakdown
        """
        # Group chapters by volume
        volumes = {}
        for chapter in chapters:
            vol_name = chapter['volume_name']
            if vol_name not in volumes:
                volumes[vol_name] = {
                    'name': vol_name,
                    'chapters': [],
                    'audio_completed': 0,
                    'video_completed': 0
                }
            volumes[vol_name]['chapters'].append(chapter)
        
        # Count completions per volume
        for vol_name, vol_data in volumes.items():
            for chapter in vol_data['chapters']:
                chapter_filename = chapter['filename']
                if chapter_filename in audio_files:
                    vol_data['audio_completed'] += 1
                if chapter_filename in video_files:
                    vol_data['video_completed'] += 1
        
        # Calculate percentages
        for vol_name, vol_data in volumes.items():
            total_chapters = len(vol_data['chapters'])
            vol_data['total_chapters'] = total_chapters
            vol_data['audio_percentage'] = (vol_data['audio_completed'] / total_chapters * 100) if total_chapters > 0 else 0
            vol_data['video_percentage'] = (vol_data['video_completed'] / total_chapters * 100) if total_chapters > 0 else 0
        
        return volumes
    
    def is_chapter_completed(self, chapter_filename: str, completion_type: str = 'both') -> bool:
        """
        Check if a chapter is completed.
        
        Args:
            chapter_filename: Name of the chapter file (e.g., 'Chapter_1_Crimson.txt')
            completion_type: 'audio', 'video', or 'both'
            
        Returns:
            True if chapter is completed according to completion_type
        """
        audio_files, video_files = self._get_cached_files()
        
        if completion_type == 'audio':
            return chapter_filename in audio_files
        elif completion_type == 'video':
            return chapter_filename in video_files
        elif completion_type == 'both':
            return chapter_filename in audio_files and chapter_filename in video_files
        else:
            raise ValueError(f"Invalid completion_type: {completion_type}")
    
    def get_next_chapters(self, count: int, completion_type: str = 'audio') -> List[Dict[str, Any]]:
        """
        Get the next N chapters that need processing.
        
        Args:
            count: Number of chapters to return
            completion_type: 'audio', 'video', or 'both'
            
        Returns:
            List of chapter dictionaries that need processing
        """
        all_chapters = self.file_organizer.discover_chapters()
        audio_files, video_files = self._get_cached_files()
        
        next_chapters = []
        for chapter in all_chapters:
            chapter_filename = chapter['filename']
            
            # Check if chapter needs processing based on completion_type
            needs_processing = False
            if completion_type == 'audio':
                needs_processing = chapter_filename not in audio_files
            elif completion_type == 'video':
                needs_processing = chapter_filename not in video_files
            elif completion_type == 'both':
                needs_processing = (chapter_filename not in audio_files or 
                                  chapter_filename not in video_files)
            
            if needs_processing:
                next_chapters.append(chapter)
                if len(next_chapters) >= count:
                    break
        
        return next_chapters
    
    def clear_cache(self):
        """Clear the file scan cache to force a fresh scan."""
        self._audio_files_cache = None
        self._video_files_cache = None
        self._cache_timestamp = None


def main():
    """Test the file-based progress tracker."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test file-based progress tracker")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--next", type=int, help="Show next N chapters to process")
    
    args = parser.parse_args()
    
    # Load project
    pm = ProjectManager()
    project = pm.load_project(args.project)
    
    # Create tracker
    tracker = FileBasedProgressTracker(project)
    
    # Get progress summary
    summary = tracker.get_progress_summary()
    
    print("=" * 60)
    print(f"PROJECT STATUS: {summary['display_name']}")
    print("=" * 60)
    print(f"Project: {summary['project_name']}")
    print(f"Total Chapters: {summary['total_chapters']:,} across {summary['total_volumes']} volumes")
    print(f"Last Updated: {summary['last_updated']}")
    print()
    
    print("AUDIO STATUS:")
    print(f"Completed: {summary['audio_completed']:,}/{summary['total_chapters']:,} chapters ({summary['audio_percentage']:.1f}%)")
    if summary['next_audio_chapter']:
        next_ch = summary['next_audio_chapter']
        print(f"Next Chapter: {next_ch['filename']} (Volume {next_ch['volume_number']})")
    else:
        print("Next Chapter: All audio completed!")
    print()
    
    print("VIDEO STATUS:")
    print(f"Completed: {summary['video_completed']:,}/{summary['total_chapters']:,} chapters ({summary['video_percentage']:.1f}%)")
    if summary['next_video_chapter']:
        next_ch = summary['next_video_chapter']
        print(f"Next Chapter: {next_ch['filename']} (Volume {next_ch['volume_number']})")
    else:
        print("Next Chapter: All video completed!")
    print()
    
    if args.next:
        print(f"NEXT {args.next} CHAPTERS TO PROCESS:")
        next_chapters = tracker.get_next_chapters(args.next, 'audio')
        for i, chapter in enumerate(next_chapters, 1):
            print(f"  {i:2d}. {chapter['filename']} (Volume {chapter['volume_number']})")
        print()
    
    print("=" * 60)


if __name__ == "__main__":
    main()
