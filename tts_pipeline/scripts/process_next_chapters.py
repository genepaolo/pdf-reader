#!/usr/bin/env python3
"""
Process Next Chapters Script

Processes the next X chapters starting from where you left off.
This is useful for batch processing without having to specify exact chapter ranges.
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
from tts_pipeline.utils.file_based_progress_tracker import FileBasedProgressTracker
from tts_pipeline.scripts.process_project import TTSProcessor

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def find_next_chapters_to_process(chapters: List[Dict[str, Any]], 
                                 progress_tracker: FileBasedProgressTracker,
                                 count: int) -> List[Dict[str, Any]]:
    """
    Find the next N chapters that need processing.
    
    Args:
        chapters: List of all chapters
        progress_tracker: File-based progress tracker instance
        count: Number of chapters to find
        
    Returns:
        List of next chapters to process
    """
    return progress_tracker.get_next_chapters(count, 'audio')

def main():
    """Main entry point for processing next chapters."""
    parser = argparse.ArgumentParser(
        description="Process the next X chapters starting from where you left off",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process next 10 chapters
  python scripts/process_next_chapters.py --project lotm_book1 --count 10
  
  # Process next 5 chapters with video creation
  python scripts/process_next_chapters.py --project lotm_book1 --count 5 --create-videos
  
  # Process next 20 chapters with dry run
  python scripts/process_next_chapters.py --project lotm_book1 --count 20 --dry-run
  
  # Show what would be processed without actually processing
  python scripts/process_next_chapters.py --project lotm_book1 --count 10 --preview
        """
    )
    
    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Project name to process'
    )
    
    parser.add_argument(
        '--count', '-c',
        type=int,
        required=True,
        help='Number of chapters to process'
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
        progress_tracker = FileBasedProgressTracker(project)
        
        # Discover chapters
        chapters = file_organizer.discover_chapters()
        logger.info(f"Discovered {len(chapters)} chapters")
        
        # Find next chapters to process
        next_chapters = find_next_chapters_to_process(chapters, progress_tracker, args.count)
        
        if not next_chapters:
            logger.info("All chapters have been completed!")
            return 0
        
        logger.info(f"Found {len(next_chapters)} chapters to process:")
        for i, chapter in enumerate(next_chapters, 1):
            logger.info(f"  {i}. {chapter['filename']} (Chapter {chapter['chapter_number']})")
        
        # Preview mode
        if args.preview:
            logger.info("PREVIEW MODE: No actual processing will be performed")
            logger.info(f"Would process {len(next_chapters)} chapters")
            if args.create_videos:
                logger.info("Would create videos after audio generation")
            return 0
        
        # Process chapters
        processor = TTSProcessor(project, dry_run=args.dry_run, create_videos=args.create_videos)
        
        # Process the next chapters
        processed_count = 0
        failed_count = 0
        
        for i, chapter in enumerate(next_chapters, 1):
            logger.info(f"Processing chapter {i}/{len(next_chapters)}: {chapter['filename']}")
            
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
        logger.info(f"Chapters processed: {processed_count}")
        logger.info(f"Chapters failed: {failed_count}")
        logger.info(f"Total attempted: {len(next_chapters)}")
        logger.info(f"Dry run: {args.dry_run}")
        logger.info(f"Video creation: {args.create_videos}")
        logger.info("=" * 60)
        
        if failed_count > 0:
            logger.warning(f"{failed_count} chapters failed to process")
            return 1
        
        logger.info("All chapters processed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Error processing next chapters: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
