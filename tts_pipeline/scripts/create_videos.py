#!/usr/bin/env python3
"""
Manual Video Creation Script

This script allows you to manually create videos for individual chapters or batches
of chapters. It provides fine-grained control over video creation parameters.

Features:
- Create videos for specific chapters
- Batch processing with progress tracking
- Custom background images
- Multiple video types (still image, animated, slideshow)
- Resume functionality for interrupted batches
- Preview mode for testing settings

Usage:
    # Create video for a single chapter
    python scripts/create_videos.py --project lotm_book1 --chapters 1 --video-type still_image
    
    # Create videos for multiple chapters
    python scripts/create_videos.py --project lotm_book1 --chapters 1-10 --video-type animated_background
    
    # Create videos with custom background
    python scripts/create_videos.py --project lotm_book1 --chapters 1-5 --background-image ./assets/custom_bg.jpg
    
    # Preview mode (test settings without creating files)
    python scripts/create_videos.py --project lotm_book1 --chapters 1 --preview
    
    # Resume interrupted batch
    python scripts/create_videos.py --project lotm_book1 --resume
"""

import argparse
import sys
import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.project_manager import ProjectManager, Project
from utils.file_organizer import ChapterFileOrganizer
from utils.progress_tracker import ProgressTracker
from api.video_processor import VideoProcessor


def setup_logging(level: str = "INFO"):
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


class VideoCreator:
    """Handles manual video creation with progress tracking."""
    
    def __init__(self, project: Project, video_type: str = "still_image", 
                 background_image: Optional[str] = None, preview_mode: bool = False):
        """
        Initialize the video creator.
        
        Args:
            project: Project object containing configuration
            video_type: Type of video to create
            background_image: Custom background image path
            preview_mode: If True, simulate video creation without actual processing
        """
        self.project = project
        self.video_type = video_type
        self.background_image = background_image
        self.preview_mode = preview_mode
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.file_organizer = ChapterFileOrganizer(project)
        self.progress_tracker = ProgressTracker(project)
        
        # Initialize video processor
        self.video_processor = VideoProcessor(project.processing_config)
        
        # Processing state
        self.start_time = None
        self.processed_count = 0
        self.failed_count = 0
        
        self.logger.info(f"Initialized video creator for project: {project.project_name}")
        self.logger.info(f"Video type: {video_type}, Preview mode: {preview_mode}")
        
        if background_image:
            self.logger.info(f"Custom background image: {background_image}")
    
    def discover_chapters(self) -> List[Dict[str, Any]]:
        """Discover all chapters for the project."""
        self.logger.info("Discovering chapters...")
        chapters = self.file_organizer.discover_chapters()
        self.logger.info(f"Discovered {len(chapters)} chapters")
        return chapters
    
    def get_audio_file_path(self, chapter: Dict[str, Any]) -> Optional[Path]:
        """Get the audio file path for a chapter."""
        try:
            # Look for audio file in the expected location
            chapter_name = chapter['filename'].replace('.txt', '.mp3')
            volume_name = chapter['volume_name']
            
            # Try different possible locations
            possible_paths = [
                Path(self.project.processing_config['output_directory']) / volume_name / chapter_name,
                Path(self.project.processing_config.get('ssd_directory', './output')) / volume_name / chapter_name,
            ]
            
            for path in possible_paths:
                if path.exists():
                    return path
            
            self.logger.warning(f"No audio file found for chapter: {chapter['filename']}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding audio file for {chapter['filename']}: {e}")
            return None
    
    def get_video_output_path(self, chapter: Dict[str, Any]) -> Path:
        """Generate the video output path for a chapter."""
        chapter_name = chapter['filename'].replace('.txt', '.mp4')
        volume_name = chapter['volume_name']
        
        # Use video output directory from config
        video_output_dir = Path(self.project.processing_config['video']['output_directory'])
        return video_output_dir / volume_name / chapter_name
    
    def create_video_for_chapter(self, chapter: Dict[str, Any]) -> bool:
        """
        Create a video for a single chapter.
        
        Args:
            chapter: Chapter information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        chapter_name = chapter['filename']
        self.logger.info(f"Creating video for chapter: {chapter_name}")
        
        try:
            if self.preview_mode:
                # Preview mode - just simulate
                self.logger.info(f"[PREVIEW] Would create video for: {chapter_name}")
                time.sleep(0.1)  # Simulate processing time
                
                # Simulate success/failure (95% success rate for preview)
                import random
                success = random.random() < 0.95
                
                if success:
                    self.logger.info(f"[PREVIEW] Successfully created video: {chapter_name}")
                    self.processed_count += 1
                    return True
                else:
                    self.logger.warning(f"[PREVIEW] Failed to create video: {chapter_name}")
                    self.failed_count += 1
                    return False
            
            # Real video creation
            audio_path = self.get_audio_file_path(chapter)
            if not audio_path:
                raise ValueError(f"No audio file found for chapter: {chapter_name}")
            
            video_path = self.get_video_output_path(chapter)
            
            # Create output directory
            video_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Creating video: {audio_path.name} -> {video_path.name}")
            
            # Create the video
            success = self.video_processor.create_video(
                str(audio_path),
                str(video_path),
                video_type=self.video_type,
                background_image=self.background_image,
                chapter_info=chapter
            )
            
            if success:
                # Validate the created video
                if self.video_processor.validate_video(str(video_path)):
                    self.logger.info(f"Successfully created and validated video: {video_path}")
                    
                    # Update progress tracking
                    try:
                        progress_tracker = ProgressTracker(self.project)
                        progress_tracker.mark_video_completed(chapter, str(video_path))
                        self.logger.info(f"Updated progress tracking for: {chapter_name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to update progress tracking for {chapter_name}: {e}")
                    
                    self.processed_count += 1
                    return True
                else:
                    self.logger.error(f"Video validation failed: {video_path}")
                    self.failed_count += 1
                    return False
            else:
                self.logger.error(f"Failed to create video: {video_path}")
                self.failed_count += 1
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating video for chapter {chapter_name}: {e}")
            self.failed_count += 1
            return False
    
    def create_videos_for_chapters(self, chapters: List[Dict[str, Any]], 
                                 start_chapter: Optional[int] = None,
                                 end_chapter: Optional[int] = None,
                                 max_chapters: Optional[int] = None) -> Dict[str, Any]:
        """
        Create videos for multiple chapters.
        
        Args:
            chapters: List of chapter information dictionaries
            start_chapter: Starting chapter number (1-based)
            end_chapter: Ending chapter number (1-based)
            max_chapters: Maximum number of chapters to process
            
        Returns:
            Processing results summary
        """
        self.start_time = datetime.now()
        self.logger.info(f"Starting video creation for project: {self.project.project_name}")
        
        # Filter chapters based on parameters
        filtered_chapters = self._filter_chapters(chapters, start_chapter, end_chapter, max_chapters)
        
        self.logger.info(f"Creating videos for {len(filtered_chapters)} chapters")
        
        # Process chapters in parallel (GPU can handle more concurrent operations)
        max_workers = min(6, len(filtered_chapters))  # Increased from 3 to 6 for GPU acceleration
        self.logger.info(f"Processing {len(filtered_chapters)} chapters with {max_workers} parallel workers")
        
        processed_count = 0
        failed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chapters for processing
            future_to_chapter = {
                executor.submit(self.create_video_for_chapter, chapter): chapter 
                for chapter in filtered_chapters
            }
            
            # Process completed futures
            for future in as_completed(future_to_chapter):
                chapter = future_to_chapter[future]
                try:
                    success = future.result()
                    if success:
                        processed_count += 1
                        self.logger.info(f"✓ Completed: {chapter['filename']}")
                    else:
                        failed_count += 1
                        self.logger.error(f"✗ Failed: {chapter['filename']}")
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"✗ Error processing {chapter['filename']}: {e}")
                
                # Log progress
                total_processed = processed_count + failed_count
                self.logger.info(f"Progress: {total_processed}/{len(filtered_chapters)} chapters")
                
                # Log summary every 5 chapters
                if total_processed % 5 == 0:
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
        self.logger.info(f"Progress: {self.processed_count} successful, {self.failed_count} failed, "
                        f"elapsed: {elapsed}")
    
    def _get_processing_summary(self) -> Dict[str, Any]:
        """Get final processing summary."""
        elapsed = datetime.now() - self.start_time
        
        return {
            'project_name': self.project.project_name,
            'total_chapters': self.processed_count + self.failed_count,
            'successful_videos': self.processed_count,
            'failed_videos': self.failed_count,
            'processing_time': str(elapsed),
            'preview_mode': self.preview_mode,
            'video_type': self.video_type
        }


def main():
    """Main entry point for manual video creation."""
    parser = argparse.ArgumentParser(
        description="Create videos for TTS audio files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create video for single chapter
  python scripts/create_videos.py --project lotm_book1 --chapters 1
  
  # Create videos for multiple chapters
  python scripts/create_videos.py --project lotm_book1 --chapters 1-10
  
  # Create animated background videos
  python scripts/create_videos.py --project lotm_book1 --chapters 1-5 --video-type animated_background
  
  # Use custom background image
  python scripts/create_videos.py --project lotm_book1 --chapters 1-3 --background-image ./assets/custom_bg.jpg
  
  # Preview mode (test settings)
  python scripts/create_videos.py --project lotm_book1 --chapters 1 --preview
  
  # Resume interrupted batch
  python scripts/create_videos.py --project lotm_book1 --resume
        """
    )
    
    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Project name to process'
    )
    
    parser.add_argument(
        '--chapters',
        help='Chapter range to process (e.g., "1", "1-10", "5-15")'
    )
    
    parser.add_argument(
        '--video-type',
        choices=['still_image', 'animated_background', 'slideshow'],
        default='still_image',
        help='Type of video to create (default: still_image)'
    )
    
    parser.add_argument(
        '--background-image',
        help='Custom background image path'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview mode - simulate video creation without actual processing'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from where video creation was interrupted'
    )
    
    parser.add_argument(
        '--max-chapters',
        type=int,
        help='Maximum number of chapters to process'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    
    try:
        # Load project
        project_manager = ProjectManager()
        project = project_manager.load_project(args.project)
        
        if not project:
            logging.error(f"Project not found: {args.project}")
            return 1
        
        # Initialize video creator
        video_creator = VideoCreator(
            project=project,
            video_type=args.video_type,
            background_image=args.background_image,
            preview_mode=args.preview
        )
        
        # Discover chapters
        chapters = video_creator.discover_chapters()
        
        if not chapters:
            logging.error("No chapters found")
            return 1
        
        # Parse chapter range
        start_chapter = None
        end_chapter = None
        
        if args.chapters:
            if '-' in args.chapters:
                start_chapter, end_chapter = map(int, args.chapters.split('-'))
            else:
                start_chapter = end_chapter = int(args.chapters)
        
        # Create videos
        logging.info(f"Starting video creation for project: {args.project}")
        
        results = video_creator.create_videos_for_chapters(
            chapters=chapters,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            max_chapters=args.max_chapters
        )
        
        # Print summary
        print("\n" + "="*60)
        print("VIDEO CREATION SUMMARY")
        print("="*60)
        print(f"Project: {results['project_name']}")
        print(f"Total chapters processed: {results['total_chapters']}")
        print(f"Successful videos: {results['successful_videos']}")
        print(f"Failed videos: {results['failed_videos']}")
        print(f"Processing time: {results['processing_time']}")
        print(f"Video type: {results['video_type']}")
        print(f"Preview mode: {results['preview_mode']}")
        print("="*60)
        
        if results['failed_videos'] > 0:
            logging.warning(f"{results['failed_videos']} videos failed to create")
            return 1
        
        logging.info("Video creation completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logging.info("Video creation interrupted by user")
        return 1
    except Exception as e:
        logging.error(f"Error during video creation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
