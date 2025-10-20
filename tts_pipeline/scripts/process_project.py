#!/usr/bin/env python3
"""
TTS Pipeline Main Script - Project-Based Processing

This is the main entry point for the TTS pipeline, providing a command-line interface
for processing text-to-speech projects using the project-based architecture.

Features:
- Project discovery and management
- Chapter processing with progress tracking
- Resume functionality for interrupted processing
- Comprehensive error handling and logging
- Dry-run mode for testing without Azure API calls
- Progress reporting and status updates

Usage:
    python scripts/process_project.py --help
    python scripts/process_project.py --list-projects
    python scripts/process_project.py --project lotm_book1 --dry-run
    python scripts/process_project.py --project lotm_book1 --resume
    python scripts/process_project.py --project lotm_book1 --chapters 1-10
"""

import argparse
import sys
import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.project_manager import ProjectManager, Project
from utils.file_organizer import ChapterFileOrganizer
from utils.progress_tracker import ProgressTracker


class TTSProcessor:
    """Main TTS processing class with project-based architecture."""
    
    def __init__(self, project: Project, dry_run: bool = False):
        """
        Initialize the TTS processor.
        
        Args:
            project: Project object containing configuration and metadata
            dry_run: If True, simulate processing without making actual API calls
        """
        self.project = project
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.file_organizer = ChapterFileOrganizer(project)
        self.progress_tracker = ProgressTracker(project)
        
        # Processing state
        self.start_time = None
        self.processed_count = 0
        self.failed_count = 0
        
        self.logger.info(f"Initialized TTS processor for project: {project.project_name}")
        if dry_run:
            self.logger.info("DRY RUN MODE: No actual API calls will be made")
    
    def discover_chapters(self) -> List[Dict[str, Any]]:
        """Discover all chapters for the project."""
        self.logger.info("Discovering chapters...")
        chapters = self.file_organizer.discover_chapters()
        self.logger.info(f"Discovered {len(chapters)} chapters")
        return chapters
    
    def get_next_chapter_to_process(self, chapters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get the next chapter that needs processing (ignores dry-run completions)."""
        for chapter in chapters:
            if not self.progress_tracker.is_chapter_completed_real(chapter):
                return chapter
        return None
    
    def process_chapter(self, chapter: Dict[str, Any]) -> bool:
        """
        Process a single chapter.
        
        Args:
            chapter: Chapter information dictionary
            
        Returns:
            True if processing succeeded, False otherwise
        """
        chapter_name = chapter['filename']
        self.logger.info(f"Processing chapter: {chapter_name}")
        
        try:
            if self.dry_run:
                # Simulate processing in dry-run mode
                self.logger.info(f"[DRY RUN] Would process: {chapter_name}")
                time.sleep(0.1)  # Simulate processing time
                
                # Simulate success/failure (90% success rate for testing)
                import random
                success = random.random() < 0.9
                
                if success:
                    self.logger.info(f"[DRY RUN] Successfully processed: {chapter_name}")
                    result = self.progress_tracker.mark_chapter_completed(
                        chapter, f"/mock/audio/{chapter_name.replace('.txt', '.mp3')}", dry_run=True
                    )
                    self.logger.info(f"[DRY RUN] Mark completion result: {result}")
                    self.processed_count += 1
                    return True
                else:
                    self.logger.warning(f"[DRY RUN] Failed to process: {chapter_name}")
                    self.progress_tracker.mark_chapter_failed(
                        chapter, "Simulated processing error", "dry_run_error"
                    )
                    self.failed_count += 1
                    return False
            else:
                # TODO: Implement actual Azure TTS processing
                self.logger.info(f"[REAL] Processing: {chapter_name}")
                # This will be implemented in Step 10
                raise NotImplementedError("Real processing not yet implemented")
                
        except Exception as e:
            self.logger.error(f"Error processing chapter {chapter_name}: {e}")
            self.progress_tracker.mark_chapter_failed(chapter, str(e), "processing_error")
            self.failed_count += 1
            return False
    
    def process_chapters(self, chapters: List[Dict[str, Any]], 
                        start_chapter: Optional[int] = None,
                        end_chapter: Optional[int] = None,
                        max_chapters: Optional[int] = None) -> Dict[str, Any]:
        """
        Process multiple chapters.
        
        Args:
            chapters: List of chapter information dictionaries
            start_chapter: Starting chapter number (1-based)
            end_chapter: Ending chapter number (1-based)
            max_chapters: Maximum number of chapters to process
            
        Returns:
            Processing results summary
        """
        self.start_time = datetime.now()
        self.logger.info(f"Starting chapter processing for project: {self.project.project_name}")
        
        # Filter chapters based on parameters
        filtered_chapters = self._filter_chapters(chapters, start_chapter, end_chapter, max_chapters)
        
        self.logger.info(f"Processing {len(filtered_chapters)} chapters")
        
        # Process chapters
        processed_count = 0
        for i, chapter in enumerate(filtered_chapters, 1):
            # Skip chapters that have already been completed with real processing
            if self.progress_tracker.is_chapter_completed_real(chapter):
                self.logger.info(f"Skipping Chapter {chapter['chapter_number']} - already completed with real processing")
                continue
            
            # Check if we've reached the max_chapters limit
            if max_chapters and processed_count >= max_chapters:
                self.logger.info(f"Reached max_chapters limit ({max_chapters}), stopping processing")
                break
                
            self.logger.info(f"Progress: {processed_count + 1}/{max_chapters or len(filtered_chapters)} chapters")
            
            success = self.process_chapter(chapter)
            processed_count += 1
            
            # Log progress every 10 chapters
            if processed_count % 10 == 0:
                self._log_progress_summary()
        
        # Final summary
        return self._get_processing_summary()
    
    def _filter_chapters(self, chapters: List[Dict[str, Any]], 
                        start_chapter: Optional[int],
                        end_chapter: Optional[int],
                        max_chapters: Optional[int]) -> List[Dict[str, Any]]:
        """Filter chapters based on processing parameters."""
        filtered = chapters.copy()
        
        # Filter by chapter number range
        if start_chapter is not None:
            filtered = [c for c in filtered if c['chapter_number'] >= start_chapter]
        
        if end_chapter is not None:
            filtered = [c for c in filtered if c['chapter_number'] <= end_chapter]
        
        # Limit by max chapters
        if max_chapters is not None:
            filtered = filtered[:max_chapters]
        
        return filtered
    
    def _log_progress_summary(self):
        """Log current progress summary."""
        elapsed = datetime.now() - self.start_time
        summary = self.progress_tracker.get_progress_summary()
        
        self.logger.info(f"Progress Summary:")
        self.logger.info(f"  - Completed: {summary['total_completed']}")
        self.logger.info(f"  - Failed: {summary['total_failed']}")
        self.logger.info(f"  - Elapsed: {elapsed}")
        self.logger.info(f"  - This session: {self.processed_count} processed, {self.failed_count} failed")
    
    def _get_processing_summary(self) -> Dict[str, Any]:
        """Get final processing summary."""
        elapsed = datetime.now() - self.start_time
        summary = self.progress_tracker.get_progress_summary()
        
        return {
            'project_name': self.project.project_name,
            'total_chapters': len(self.file_organizer.discover_chapters()),
            'completed_chapters': summary['total_completed'],
            'failed_chapters': summary['total_failed'],
            'session_processed': self.processed_count,
            'session_failed': self.failed_count,
            'processing_time': str(elapsed),
            'dry_run': self.dry_run
        }
    
    def get_failed_chapters_for_retry(self) -> List[Dict[str, Any]]:
        """Get chapters that failed and can be retried."""
        return self.progress_tracker.get_failed_chapters_for_retry()
    
    def retry_failed_chapters(self) -> Dict[str, Any]:
        """Retry all failed chapters."""
        failed_chapters = self.get_failed_chapters_for_retry()
        
        if not failed_chapters:
            self.logger.info("No failed chapters to retry")
            return {'retried': 0, 'successful': 0, 'failed': 0}
        
        self.logger.info(f"Retrying {len(failed_chapters)} failed chapters")
        
        successful = 0
        failed = 0
        
        for chapter in failed_chapters:
            if self.process_chapter(chapter):
                successful += 1
            else:
                failed += 1
        
        return {
            'retried': len(failed_chapters),
            'successful': successful,
            'failed': failed
        }


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="TTS Pipeline - Project-Based Text-to-Speech Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available projects
  python scripts/process_project.py --list-projects
  
  # Process all chapters in dry-run mode
  python scripts/process_project.py --project lotm_book1 --dry-run
  
  # Process specific chapter range
  python scripts/process_project.py --project lotm_book1 --chapters 1-10
  
  # Resume processing from where it left off
  python scripts/process_project.py --project lotm_book1 --resume
  
  # Retry failed chapters only
  python scripts/process_project.py --project lotm_book1 --retry-failed
  
  # Process with custom log level
  python scripts/process_project.py --project lotm_book1 --log-level DEBUG
        """
    )
    
    # Project selection
    parser.add_argument(
        '--project', '-p',
        help='Project name to process'
    )
    
    parser.add_argument(
        '--list-projects', '-l',
        action='store_true',
        help='List available projects and exit'
    )
    
    # Processing options
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Simulate processing without making actual API calls'
    )
    
    parser.add_argument(
        '--clear-dry-run',
        action='store_true',
        help='Clear all dry-run completion records to start fresh with real processing'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume processing from where it left off'
    )
    
    parser.add_argument(
        '--retry-failed',
        action='store_true',
        help='Retry only failed chapters'
    )
    
    parser.add_argument(
        '--chapters', '-c',
        help='Chapter range to process (e.g., "1-10" or "5")'
    )
    
    parser.add_argument(
        '--max-chapters', '-m',
        type=int,
        help='Maximum number of chapters to process'
    )
    
    # Logging options
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        help='Log to file in addition to console'
    )
    
    return parser


def parse_chapter_range(chapter_str: str) -> tuple[Optional[int], Optional[int]]:
    """Parse chapter range string (e.g., '1-10' or '5')."""
    if '-' in chapter_str:
        start, end = chapter_str.split('-', 1)
        return int(start.strip()), int(end.strip())
    else:
        chapter_num = int(chapter_str.strip())
        return chapter_num, chapter_num


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize project manager
        pm = ProjectManager()
        
        # Handle list projects command
        if args.list_projects:
            projects = pm.list_projects()
            if projects:
                print("Available projects:")
                for project_name in projects:
                    project = pm.load_project(project_name)
                    if project:
                        print(f"  - {project_name}: {project.project_config.get('display_name', 'No display name')}")
                    else:
                        print(f"  - {project_name}: (invalid configuration)")
            else:
                print("No projects found.")
            return 0
        
        # Handle clear dry-run command
        if args.clear_dry_run:
            if not args.project:
                logger.error("Project name is required for --clear-dry-run")
                return 1
            
            project = pm.load_project(args.project)
            if not project:
                logger.error(f"Project '{args.project}' not found")
                return 1
            
            processor = TTSProcessor(project)
            if processor.progress_tracker.clear_dry_run_data():
                logger.info("Successfully cleared all dry-run completion records")
                logger.info("You can now start real processing from Chapter 1")
            else:
                logger.error("Failed to clear dry-run data")
                return 1
            return 0
        
        # Validate project argument
        if not args.project:
            parser.error("Project name is required (use --project or -p)")
        
        # Load project
        project = pm.load_project(args.project)
        if not project:
            logger.error(f"Failed to load project: {args.project}")
            return 1
        
        if not project.is_valid():
            logger.error(f"Project {args.project} has invalid configuration")
            return 1
        
        logger.info(f"Loaded project: {project.project_name}")
        logger.info(f"Display name: {project.project_config.get('display_name', 'N/A')}")
        
        # Initialize processor
        processor = TTSProcessor(project, dry_run=args.dry_run)
        
        # Discover chapters
        chapters = processor.discover_chapters()
        if not chapters:
            logger.warning("No chapters found to process")
            return 0
        
        logger.info(f"Found {len(chapters)} chapters")
        
        # Handle different processing modes
        if args.retry_failed:
            # Retry failed chapters
            logger.info("Retrying failed chapters...")
            result = processor.retry_failed_chapters()
            logger.info(f"Retry results: {result}")
            
        elif args.resume:
            # Resume processing
            logger.info("Resuming processing...")
            result = processor.process_chapters(chapters)
            logger.info(f"Processing completed: {result}")
            
        else:
            # Normal processing with optional chapter range
            start_chapter = None
            end_chapter = None
            
            if args.chapters:
                start_chapter, end_chapter = parse_chapter_range(args.chapters)
                logger.info(f"Processing chapters {start_chapter}-{end_chapter}")
            
            result = processor.process_chapters(
                chapters,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
                max_chapters=args.max_chapters
            )
            
            logger.info(f"Processing completed: {result}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug("Full traceback:", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
