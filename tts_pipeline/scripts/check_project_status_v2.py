#!/usr/bin/env python3
"""
Simplified Project Status Checker

Uses file-based progress tracking for reliable status reporting.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from utils.project_manager import ProjectManager
from utils.file_based_progress_tracker import FileBasedProgressTracker

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def print_status(status: Dict[str, Any], detailed: bool = False):
    """
    Print formatted status report.
    
    Args:
        status: Status summary dictionary
        detailed: Whether to show detailed volume breakdown
    """
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
        print("Next Chapter: All video completed!")
    print()
    
    # Detailed volume breakdown
    if detailed and status['volume_breakdown']:
        print("VOLUME BREAKDOWN:")
        for vol_name, vol_data in status['volume_breakdown'].items():
            print(f"  {vol_data['name']}:")
            print(f"    Audio: {vol_data['audio_completed']}/{vol_data['total_chapters']} ({vol_data['audio_percentage']:.1f}%)")
            print(f"    Video: {vol_data['video_completed']}/{vol_data['total_chapters']} ({vol_data['video_percentage']:.1f}%)")
        print()
    
    print("=" * 60)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Check project status using file-based tracking")
    parser.add_argument("--project", required=True, help="Project name to check")
    parser.add_argument("--detailed", action="store_true", help="Show detailed volume breakdown")
    parser.add_argument("--next", type=int, help="Show next N chapters to process")
    
    args = parser.parse_args()
    
    try:
        setup_logging()
        
        # Load project
        pm = ProjectManager()
        project = pm.load_project(args.project)
        if not project:
            print(f"Error: Project '{args.project}' not found")
            return 1
        
        # Create file-based tracker
        tracker = FileBasedProgressTracker(project)
        
        # Get status summary
        status = tracker.get_progress_summary()
        
        # Print status
        print_status(status, args.detailed)
        
        # Show next chapters if requested
        if args.next:
            print(f"NEXT {args.next} CHAPTERS TO PROCESS:")
            next_chapters = tracker.get_next_chapters(args.next, 'audio')
            for i, chapter in enumerate(next_chapters, 1):
                print(f"  {i:2d}. {chapter['filename']} (Volume {chapter['volume_number']})")
            print()
        
        return 0
        
    except Exception as e:
        logging.error(f"Error checking project status: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
