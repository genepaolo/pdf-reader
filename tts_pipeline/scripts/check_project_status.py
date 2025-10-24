#!/usr/bin/env python3
"""
Project Status Checker Script

Displays comprehensive status information for TTS projects including:
- Audio completion counts and percentages
- Video completion counts and percentages
- Volume breakdown
- Next chapters to process
- Processing estimates
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add the parent directory to the path so we can import our modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.project_manager import ProjectManager
from utils.file_based_progress_tracker import FileBasedProgressTracker

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

class ProjectStatusChecker:
    """Checks and displays project status information."""
    
    def __init__(self, project_name: str):
        """
        Initialize the status checker.
        
        Args:
            project_name: Name of the project to check
        """
        self.logger = logging.getLogger(__name__)
        
        # Load project
        pm = ProjectManager()
        self.project = pm.load_project(project_name)
        if not self.project:
            raise ValueError(f"Project '{project_name}' not found")
        
        # Initialize components
        self.progress_tracker = FileBasedProgressTracker(self.project)
        
        self.logger.info(f"Initialized status checker for project: {project_name}")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive status summary for the project.
        
        Returns:
            Dictionary containing all status information
        """
        return self.progress_tracker.get_progress_summary()
    
    def _find_next_chapter(self, chapters: List[Dict[str, Any]], 
                          progress_data: List[Dict[str, Any]], 
                          completion_type: str) -> Optional[Dict[str, Any]]:
        """
        Find the next chapter that needs processing.
        
        Args:
            chapters: List of all chapters
            progress_data: Progress tracking data
            completion_type: 'audio' or 'video'
            
        Returns:
            Next chapter to process, or None if all completed
        """
        completed_chapter_ids = set()
        
        for record in progress_data:
            if record.get(f'{completion_type}_completed', False):
                chapter_info = record['chapter_info']
                # Use filename as chapter_id since we don't have volume_number/chapter_number
                chapter_id = chapter_info['filename']
                completed_chapter_ids.add(chapter_id)
        
        # Find first chapter not in completed set
        for chapter in chapters:
            # Use filename for comparison since our progress records use filename as ID
            chapter_id = chapter['filename']
            if chapter_id not in completed_chapter_ids:
                return chapter
        
        return None
    
    def _get_volume_breakdown(self, chapters: List[Dict[str, Any]], 
                             progress_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Get completion breakdown by volume.
        
        Args:
            chapters: List of all chapters
            progress_data: Progress tracking data
            
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
        for record in progress_data:
            chapter_info = record['chapter_info']
            vol_name = chapter_info['volume_name']
            
            if vol_name in volumes:
                if record.get('audio_completed', False):
                    volumes[vol_name]['audio_completed'] += 1
                if record.get('video_completed', False):
                    volumes[vol_name]['video_completed'] += 1
        
        # Calculate percentages
        for vol_name, vol_data in volumes.items():
            total_chapters = len(vol_data['chapters'])
            vol_data['total_chapters'] = total_chapters
            vol_data['audio_percentage'] = (vol_data['audio_completed'] / total_chapters * 100) if total_chapters > 0 else 0
            vol_data['video_percentage'] = (vol_data['video_completed'] / total_chapters * 100) if total_chapters > 0 else 0
        
        return volumes
    
    def print_status_report(self, detailed: bool = False):
        """
        Print a formatted status report.
        
        Args:
            detailed: Whether to include detailed volume breakdown
        """
        status = self.get_status_summary()
        
        print("=" * 60)
        print(f"PROJECT STATUS: {status['display_name']}")
        print("=" * 60)
        print(f"Project: {status['project_name']}")
        print(f"Total Chapters: {status['total_chapters']:,} across {status['total_volumes']} volumes")
        print(f"Last Updated: {status['last_updated']}")
        print()
        
        # Audio Status
        print("AUDIO STATUS:")
        print(f"Completed: {status['audio_completed']:,}/{status['total_chapters']:,} chapters ({status['audio_percentage']:.1f}%)")
        if status['next_audio_chapter']:
            next_ch = status['next_audio_chapter']
            print(f"Next Chapter: {next_ch['filename']} (Volume {next_ch['volume_number']})")
        else:
            print("Next Chapter: All audio completed!")
        print()
        
        # Video Status
        print("VIDEO STATUS:")
        print(f"Completed: {status['video_completed']:,}/{status['total_chapters']:,} chapters ({status['video_percentage']:.1f}%)")
        if status['next_video_chapter']:
            next_ch = status['next_video_chapter']
            print(f"Next Chapter: {next_ch['filename']} (Volume {next_ch['volume_number']})")
        else:
            print("Next Chapter: All videos completed!")
        print()
        
        # Volume Breakdown (if detailed)
        if detailed:
            print("VOLUME BREAKDOWN:")
            for vol_num in sorted(status['volume_breakdown'].keys()):
                vol_data = status['volume_breakdown'][vol_num]
                print(f"Volume {vol_num} ({vol_data['name']}):")
                print(f"  Audio: {vol_data['audio_completed']}/{vol_data['total_chapters']} chapters ({vol_data['audio_percentage']:.1f}%)")
                print(f"  Video: {vol_data['video_completed']}/{vol_data['total_chapters']} chapters ({vol_data['video_percentage']:.1f}%)")
            print()
        
        print("=" * 60)

def main():
    """Main entry point for the status checker."""
    parser = argparse.ArgumentParser(
        description="Check TTS project status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic status check
  python scripts/check_project_status.py --project lotm_book1
  
  # Detailed status with volume breakdown
  python scripts/check_project_status.py --project lotm_book1 --detailed
        """
    )
    
    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Project name to check'
    )
    
    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed volume breakdown'
    )
    
    parser.add_argument(
        '--log-level',
        default='WARNING',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Initialize status checker
        checker = ProjectStatusChecker(args.project)
        
        # Print status report
        checker.print_status_report(detailed=args.detailed)
        
    except Exception as e:
        logging.error(f"Error checking project status: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
