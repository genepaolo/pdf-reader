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
from api.azure_tts_client import AzureTTSClient
from api.video_processor import VideoProcessor
from dotenv import load_dotenv

load_dotenv()  # This loads the .env file


class TTSProcessor:
    """Main TTS processing class with project-based architecture."""
    
    def __init__(self, project: Project, dry_run: bool = False, create_videos: bool = False):
        """
        Initialize the TTS processor.
        
        Args:
            project: Project object containing configuration and metadata
            dry_run: If True, simulate processing without making actual API calls
            create_videos: If True, create videos after audio generation
        """
        self.project = project
        self.dry_run = dry_run
        self.create_videos = create_videos
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.file_organizer = ChapterFileOrganizer(project)
        self.progress_tracker = ProgressTracker(project)
        self.azure_client = AzureTTSClient(project)
        
        # Initialize video processor if video creation is enabled
        if self.create_videos:
            self.video_processor = VideoProcessor(project.processing_config)
            if not self.video_processor.enabled:
                self.logger.warning("Video creation requested but disabled in configuration")
                self.create_videos = False
        
        # Processing state
        self.start_time = None
        self.processed_count = 0
        self.failed_count = 0
        
        self.logger.info(f"Initialized TTS processor for project: {project.project_name}")
        if dry_run:
            self.logger.info("DRY RUN MODE: No actual API calls will be made")
        if self.create_videos:
            self.logger.info("VIDEO CREATION ENABLED: Videos will be created after audio generation")
    
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
    
    def _check_existing_audio(self, chapter: Dict[str, Any]) -> Optional[Path]:
        """
        Check if audio file already exists for a chapter.
        
        Args:
            chapter: Chapter information dictionary
            
        Returns:
            Path to existing audio file if it exists, None otherwise
        """
        chapter_name = chapter['filename']
        volume_name = chapter['volume_name']
        
        # Generate expected audio file path
        audio_filename = chapter_name.replace('.txt', '.mp3')
        audio_output_dir = Path(self.project.processing_config['output_directory'])
        audio_path = audio_output_dir / volume_name / audio_filename
        
        # Check if audio file exists and has content
        if audio_path.exists() and audio_path.stat().st_size > 0:
            self.logger.info(f"Found existing audio file: {audio_path}")
            return audio_path
        
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
                    # Only try to update progress if the tracker supports it
                    if hasattr(self.progress_tracker, 'mark_audio_completed'):
                        result = self.progress_tracker.mark_audio_completed(
                            chapter, f"/mock/audio/{chapter_name.replace('.txt', '.mp3')}", dry_run=True
                        )
                        self.logger.info(f"[DRY RUN] Mark completion result: {result}")
                    else:
                        self.logger.info(f"[DRY RUN] Progress tracker doesn't support dry-run updates (file-based tracker)")
                    self.processed_count += 1
                    return True
                else:
                    self.logger.warning(f"[DRY RUN] Failed to process: {chapter_name}")
                    # Only try to update progress if the tracker supports it
                    if hasattr(self.progress_tracker, 'mark_chapter_failed'):
                        self.progress_tracker.mark_chapter_failed(
                            chapter, "Simulated processing error", "dry_run_error"
                        )
                    else:
                        self.logger.info(f"[DRY RUN] Progress tracker doesn't support dry-run updates (file-based tracker)")
                    self.failed_count += 1
                    return False
            else:
                # Real Azure TTS processing
                self.logger.info(f"[REAL] Processing: {chapter_name}")
                
                # Check if audio file already exists
                existing_audio_path = self._check_existing_audio(chapter)
                
                if existing_audio_path:
                    # Audio already exists, skip audio generation
                    self.logger.info(f"Using existing audio file: {existing_audio_path}")
                    output_path = existing_audio_path
                else:
                    # Generate new audio
                    self.logger.info(f"Generating new audio for: {chapter_name}")
                    
                    # Load chapter text content and split into chunks
                    text_chunks = self._load_chapter_text_chunks(chapter)
                    if not text_chunks:
                        raise ValueError("Failed to load chapter text content")
                    
                    self.logger.info(f"Split chapter into {len(text_chunks)} chunks")
                    
                    # Generate output file path
                    output_path = self._generate_output_path(chapter)
                    
                    # Create output directory if it doesn't exist
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Test Azure connection first
                    self.logger.info("Testing Azure TTS connection...")
                    if not self._test_azure_connection():
                        raise ValueError("Azure TTS connection test failed - check credentials and network")
                    
                    self.logger.info("Azure TTS connection test passed - proceeding with synthesis")
                    
                    # Generate audio for each chunk and combine
                    self.logger.info(f"Generating audio for {chapter_name} -> {output_path}")
                    success = self._process_text_chunks(text_chunks, output_path, chapter_name)
                    
                    if not success:
                        raise ValueError("Azure TTS synthesis failed")
                
                # Verify audio file was created and has content
                if output_path.exists() and output_path.stat().st_size > 0:
                    self.logger.info(f"Audio file ready: {output_path}")
                    
                    # Create video if enabled
                    video_success = True
                    if self.create_videos and not self.dry_run:
                        video_success = self._create_video_for_chapter(chapter, output_path)
                    
                    # Only mark as completed if both audio and video succeed
                    if video_success:
                        # Video creation already updated progress tracking via mark_video_completed
                        # Now mark the overall chapter as completed
                        result = self.progress_tracker.mark_audio_completed(
                            chapter, str(output_path), dry_run=False
                        )
                        
                        if result:
                            self.processed_count += 1
                            return True
                        else:
                            self.logger.error(f"Failed to update progress tracking for {chapter_name}")
                            return False
                    else:
                        # Video creation failed - keep audio file but don't mark as completed
                        self.logger.error(f"Video creation failed for {chapter_name}")
                        self.logger.info(f"Audio file preserved for retry: {output_path}")
                        return False
                else:
                    raise ValueError(f"Audio file was not created or is empty: {output_path}")
                
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
    
    def _load_chapter_text_chunks(self, chapter: Dict[str, Any]) -> List[str]:
        """
        Load text content from a chapter file and split into chunks.
        
        Args:
            chapter: Chapter information dictionary
            
        Returns:
            List of text chunks, or empty list if failed
        """
        try:
            chapter_path = Path(chapter['file_path'])
            if not chapter_path.exists():
                self.logger.error(f"Chapter file does not exist: {chapter_path}")
                return []
            
            with open(chapter_path, 'r', encoding='utf-8') as f:
                text_content = f.read().strip()
            
            if not text_content:
                self.logger.error(f"Chapter file is empty: {chapter_path}")
                return []
            
            # Split text into chunks
            chunks = self._split_text_into_chunks(text_content)
            self.logger.info(f"Text length: {len(text_content)} characters, split into {len(chunks)} chunks")
            for i, chunk in enumerate(chunks, 1):
                self.logger.debug(f"Chunk {i}: {len(chunk)} characters")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to load chapter text from {chapter['filename']}: {e}")
            return []
    
    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 5000) -> List[str]:
        """
        Split text into chunks while preserving sentence boundaries.
        
        Args:
            text: Full text to split
            max_chunk_size: Maximum characters per chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_chunk_size:
            return [text]
        
        # Split into sentences first
        sentences = text.split('. ')
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Add the period back (except for the last sentence)
            if sentence != sentences[-1]:
                sentence += ". "
            
            # Check if adding this sentence would exceed the limit
            if len(current_chunk + sentence) > max_chunk_size and current_chunk:
                # Save current chunk and start new one
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # Add sentence to current chunk
                current_chunk += sentence
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _process_text_chunks(self, text_chunks: List[str], output_path: Path, chapter_name: str) -> bool:
        """
        Process text chunks by generating audio for each and combining them.
        
        Args:
            text_chunks: List of text chunks to process
            output_path: Final output path for combined audio
            chapter_name: Name of the chapter being processed
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if len(text_chunks) == 1:
                # Single chunk - process directly
                self.logger.info(f"Processing single chunk for {chapter_name}")
                return self.azure_client.synthesize_text(text_chunks[0], str(output_path))
            
            # Multiple chunks - process each and combine
            temp_dir = output_path.parent / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            chunk_files = []
            
            for i, chunk in enumerate(text_chunks, 1):
                chunk_filename = f"{output_path.stem}_part{i}.mp3"
                chunk_path = temp_dir / chunk_filename
                
                self.logger.info(f"Processing chunk {i}/{len(text_chunks)} for {chapter_name}")
                
                # Retry logic for chunk processing
                success = self._process_chunk_with_retry(chunk, str(chunk_path), chapter_name, i)
                if not success:
                    self.logger.error(f"Failed to process chunk {i} for {chapter_name} after retries")
                    return False
                
                chunk_files.append(chunk_path)
            
            # Combine all chunk files
            self.logger.info(f"Combining {len(chunk_files)} audio files for {chapter_name}")
            success = self._combine_audio_files(chunk_files, output_path)
            
            # Clean up temporary files
            for chunk_file in chunk_files:
                try:
                    chunk_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Failed to delete temp file {chunk_file}: {e}")
            
            # Remove temp directory if empty
            try:
                temp_dir.rmdir()
            except OSError:
                pass  # Directory not empty or other error
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error processing text chunks for {chapter_name}: {e}")
            return False
    
    def _process_chunk_with_retry(self, chunk_text: str, chunk_path: str, chapter_name: str, chunk_num: int, max_retries: int = 3) -> bool:
        """
        Process a single chunk with retry logic for connection issues.
        
        Args:
            chunk_text: Text content for this chunk
            chunk_path: Output path for this chunk
            chapter_name: Name of the chapter
            chunk_num: Chunk number for logging
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt + 1}/{max_retries} for chunk {chunk_num} of {chapter_name}")
                    # Wait before retry
                    import time
                    time.sleep(5 * attempt)  # Exponential backoff: 5, 10, 15 seconds
                
                success = self.azure_client.synthesize_text(chunk_text, chunk_path)
                if success:
                    self.logger.info(f"Successfully processed chunk {chunk_num} of {chapter_name}")
                    return True
                else:
                    self.logger.warning(f"Chunk {chunk_num} synthesis failed on attempt {attempt + 1}")
                    
            except Exception as e:
                self.logger.warning(f"Chunk {chunk_num} processing error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    self.logger.error(f"All retry attempts failed for chunk {chunk_num} of {chapter_name}")
                    return False
        
        return False

    def _create_video_for_chapter(self, chapter: Dict[str, Any], audio_path: Path) -> bool:
        """
        Create a video for a chapter after audio generation.
        
        Args:
            chapter: Chapter information dictionary
            audio_path: Path to the generated audio file
            
        Returns:
            True if video creation succeeded, False otherwise
        """
        try:
            chapter_name = chapter['filename']
            self.logger.info(f"Creating video for chapter: {chapter_name}")
            
            # Generate video output path
            video_filename = chapter_name.replace('.txt', '.mp4')
            volume_name = chapter['volume_name']
            video_output_dir = Path(self.project.processing_config['video']['output_directory'])
            video_path = video_output_dir / volume_name / video_filename
            
            # Create output directory
            video_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create the video
            success = self.video_processor.create_video(
                str(audio_path),
                str(video_path),
                video_type=self.video_processor.video_type,
                chapter_info=chapter
            )
            
            if success:
                # Validate the created video
                if self.video_processor.validate_video(str(video_path)):
                    self.logger.info(f"Successfully created video: {video_path}")
                    
                    # Update progress tracking with video completion
                    try:
                        self.progress_tracker.mark_video_completed(chapter, str(video_path))
                        self.logger.info(f"Updated progress tracking for video: {chapter_name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to update progress tracking for video {chapter_name}: {e}")
                    
                    return True
                else:
                    self.logger.error(f"Video validation failed: {video_path}")
                    return False
            else:
                self.logger.error(f"Failed to create video: {video_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating video for chapter {chapter_name}: {e}")
            return False

    def _combine_audio_files(self, audio_files: List[Path], output_path: Path) -> bool:
        """
        Combine multiple audio files into a single file.
        
        Args:
            audio_files: List of audio file paths to combine
            output_path: Path for the combined output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Simple binary concatenation for MP3 files
            with open(output_path, 'wb') as outfile:
                for audio_file in audio_files:
                    if audio_file.exists():
                        with open(audio_file, 'rb') as infile:
                            outfile.write(infile.read())
                    else:
                        self.logger.error(f"Audio file not found: {audio_file}")
                        return False
            
            self.logger.info(f"Successfully combined {len(audio_files)} files into {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to combine audio files: {e}")
            return False

    def _load_chapter_text(self, chapter: Dict[str, Any]) -> Optional[str]:
        """
        Load text content from a chapter file.
        
        Args:
            chapter: Chapter information dictionary
            
        Returns:
            Chapter text content or None if failed
        """
        try:
            chapter_path = Path(chapter['file_path'])
            if not chapter_path.exists():
                self.logger.error(f"Chapter file does not exist: {chapter_path}")
                return None
            
            with open(chapter_path, 'r', encoding='utf-8') as f:
                text_content = f.read().strip()
            
            if not text_content:
                self.logger.error(f"Chapter file is empty: {chapter_path}")
                return None
            
            self.logger.debug(f"Loaded {len(text_content)} characters from {chapter['filename']}")
            return text_content
            
        except Exception as e:
            self.logger.error(f"Failed to load chapter text from {chapter['filename']}: {e}")
            return None
    
    def _generate_output_path(self, chapter: Dict[str, Any]) -> Path:
        """
        Generate output file path for a chapter's audio file.
        
        Args:
            chapter: Chapter information dictionary
            
        Returns:
            Path object for the output audio file
        """
        # Get output directory from project configuration
        processing_config = self.project.get_processing_config()
        output_dir = Path(processing_config.get('output_directory', './output'))
        
        # Create chapter-specific subdirectory based on volume
        volume_name = chapter.get('volume_name', 'unknown_volume')
        chapter_subdir = output_dir / volume_name
        
        # Generate audio filename (replace .txt with .mp3)
        audio_filename = chapter['filename'].replace('.txt', '.mp3')
        
        return chapter_subdir / audio_filename
    
    def _test_azure_connection(self) -> bool:
        """
        Test Azure TTS connection with a simple request.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Use the built-in connection test method
            return self.azure_client.test_connection()
                
        except Exception as e:
            self.logger.error(f"Azure TTS connection test error: {e}")
            return False


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
    
    parser.add_argument(
        '--create-videos',
        action='store_true',
        help='Create videos after audio generation (requires video config)'
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
        processor = TTSProcessor(project, dry_run=args.dry_run, create_videos=args.create_videos)
        
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
