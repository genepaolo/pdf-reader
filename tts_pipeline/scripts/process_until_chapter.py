#!/usr/bin/env python3
"""
Process Until Chapter Script

Processes chapters starting from where you left off until reaching a specific chapter.
This is useful for processing up to a certain point without going beyond it.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the parent directory to the path so we can import our modules
sys.path.append('.')

from tts_pipeline.utils.project_manager import ProjectManager
from tts_pipeline.utils.file_organizer import ChapterFileOrganizer
from tts_pipeline.utils.progress_tracker import ProgressTracker
from tts_pipeline.scripts.process_project import TTSProcessor

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def find_chapters_until_target(chapters: List[Dict[str, Any]], 
                              progress_tracker: ProgressTracker,
                              target_chapter: int) -> List[Dict[str, Any]]:
    """
    Find chapters to process until reaching the target chapter.
    
    Args:
        chapters: List of all chapters
        progress_tracker: Progress tracker instance
        target_chapter: Target chapter number (inclusive)
        
    Returns:
        List of chapters to process
    """
    chapters_to_process = []
    
    for chapter in chapters:
        chapter_num = chapter['chapter_number']
        
        # Stop if we've reached the target chapter
        if chapter_num > target_chapter:
            break
        
        # Skip chapters that have already been completed with real processing
        if not progress_tracker.is_chapter_completed_real(chapter):
            chapters_to_process.append(chapter)
    
    return chapters_to_process

def main():
    """Main entry point for processing until target chapter."""
    parser = argparse.ArgumentParser(
        description="Process chapters until reaching a specific chapter number",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process until chapter 50
  python scripts/process_until_chapter.py --project lotm_book1 --until 50
  
  # Process until chapter 100 with video creation
  python scripts/process_until_chapter.py --project lotm_book1 --until 100 --create-videos
  
  # Process until chapter 25 with dry run
  python scripts/process_until_chapter.py --project lotm_book1 --until 25 --dry-run
  
  # Show what would be processed without actually processing
  python scripts/process_until_chapter.py --project lotm_book1 --until 30 --preview
        """
    )
    
    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Project name to process'
    )
    
    parser.add_argument(
        '--until', '-u',
        type=int,
        required=True,
        help='Process until this chapter number (inclusive)'
    )
    
    parser.add_argument(
        '--create-videos',
        action='store_true',
        help='Create videos after audio generation'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode (no actual API calls)'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Show what would be processed without processing'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    logger = logging.getLogger(__name__)
    
    try:
        # Load project
        pm = ProjectManager()
        project = pm.load_project(args.project)
        if not project:
            logger.error(f"Project '{args.project}' not found")
            return 1
        
        if not project.is_valid():
            logger.error(f"Project {args.project} has invalid configuration")
            return 1
        
        logger.info(f"Loaded project: {project.project_name}")
        
        # Initialize components
        file_organizer = ChapterFileOrganizer(project)
        progress_tracker = ProgressTracker(project)
        
        # Discover chapters
        chapters = file_organizer.discover_chapters()
        logger.info(f"Discovered {len(chapters)} chapters")
        
        # Find chapters to process until target
        chapters_to_process = find_chapters_until_target(chapters, progress_tracker, args.until)
        
        if not chapters_to_process:
            logger.info(f"All chapters up to {args.until} have been completed!")
            return 0
        
        logger.info(f"Found {len(chapters_to_process)} chapters to process (up to chapter {args.until}):")
        for i, chapter in enumerate(chapters_to_process, 1):
            logger.info(f"  {i}. {chapter['filename']} (Chapter {chapter['chapter_number']})")
        
        # Preview mode
        if args.preview:
            logger.info("PREVIEW MODE: No actual processing will be performed")
            logger.info(f"Would process {len(chapters_to_process)} chapters up to chapter {args.until}")
            if args.create_videos:
                logger.info("Would create videos after audio generation")
            return 0
        
        # Process chapters
        processor = TTSProcessor(project, dry_run=args.dry_run, create_videos=args.create_videos)
        
        # Process the chapters
        processed_count = 0
        failed_count = 0
        
        for i, chapter in enumerate(chapters_to_process, 1):
            logger.info(f"Processing chapter {i}/{len(chapters_to_process)}: {chapter['filename']}")
            
            try:
                success = processor.process_chapter(chapter)
                if success:
                    processed_count += 1
                    logger.info(f"✓ Successfully processed: {chapter['filename']}")
                else:
                    failed_count += 1
                    logger.error(f"✗ Failed to process: {chapter['filename']}")
            except Exception as e:
                failed_count += 1
                logger.error(f"✗ Error processing {chapter['filename']}: {e}")
        
        # Summary
        logger.info("=" * 60)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Project: {project.project_name}")
        logger.info(f"Target chapter: {args.until}")
        logger.info(f"Chapters processed: {processed_count}")
        logger.info(f"Chapters failed: {failed_count}")
        logger.info(f"Total attempted: {len(chapters_to_process)}")
        logger.info(f"Dry run: {args.dry_run}")
        logger.info(f"Video creation: {args.create_videos}")
        logger.info("=" * 60)
        
        if failed_count > 0:
            logger.warning(f"{failed_count} chapters failed to process")
            return 1
        
        logger.info("All chapters processed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Error processing until chapter: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
