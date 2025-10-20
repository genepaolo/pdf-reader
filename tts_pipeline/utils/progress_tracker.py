"""
Progress tracker for TTS pipeline state management.
Handles saving/loading progress, tracking completed chapters, and resume functionality.

Supports both legacy string-based initialization and new Project-based initialization.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
import logging


class ProgressTracker:
    """Tracks TTS processing progress and enables resume functionality."""
    
    def __init__(self, tracking_source: Union[str, 'Project']):
        """
        Initialize the progress tracker.
        
        Args:
            tracking_source: Either a string path to tracking directory OR a Project object
        """
        self.logger = logging.getLogger(__name__)
        
        # Handle both Project objects and string paths for backward compatibility
        if hasattr(tracking_source, 'get_input_directory'):
            # New Project-based initialization
            self.project = tracking_source
            self.tracking_directory = self._setup_project_tracking_directory()
            
            # Load tracking settings from project configuration
            self.tracking_config = self._load_tracking_config()
            
            self.logger.info(f"Initialized with Project: {self.project.project_name}")
        else:
            # Legacy string-based initialization
            self.project = None
            self.tracking_directory = Path(tracking_source)
            self.tracking_config = self._get_default_tracking_config()
            
            self.logger.info(f"Initialized with legacy tracking directory: {self.tracking_directory}")
        
        # Create tracking directory
        self.tracking_directory.mkdir(parents=True, exist_ok=True)
        
        # Progress file paths
        self.progress_file = self.tracking_directory / "progress.json"
        self.failed_file = self.tracking_directory / "failed.json"
        self.metadata_file = self.tracking_directory / "metadata.json"
        
        # Load existing progress
        self._load_progress()
    
    def _setup_project_tracking_directory(self) -> Path:
        """Set up project-specific tracking directory."""
        # Create tracking directory structure: tracking/{project_name}/
        base_tracking_dir = Path("./tracking")
        project_tracking_dir = base_tracking_dir / self.project.project_name
        return project_tracking_dir
    
    def _load_tracking_config(self) -> Dict[str, Any]:
        """Load tracking configuration from project config."""
        try:
            processing_config = self.project.get_processing_config()
            return processing_config.get('tracking', self._get_default_tracking_config())
        except Exception as e:
            self.logger.warning(f"Could not load tracking config from project: {e}. Using defaults.")
            return self._get_default_tracking_config()
    
    def _get_default_tracking_config(self) -> Dict[str, Any]:
        """Get default tracking configuration."""
        return {
            'retry_attempts': 3,
            'retry_delay_seconds': 30,
            'track_audio_file_sizes': True,
            'track_processing_times': True,
            'auto_backup_progress': False,
            'backup_interval_hours': 6,
            'error_categorization': True,
            'detailed_error_logging': True
        }
    
    def is_project_based(self) -> bool:
        """Check if this tracker was initialized with a Project object."""
        return self.project is not None
    
    def get_project_name(self) -> Optional[str]:
        """Get the project name if initialized with a Project object, otherwise None."""
        return self.project.project_name if self.project else None
    
    def get_tracking_config(self) -> Dict[str, Any]:
        """Get the tracking configuration being used."""
        return self.tracking_config.copy()
    
    def get_tracking_info(self) -> Dict[str, Any]:
        """Get information about the tracking setup."""
        return {
            'tracking_directory': str(self.tracking_directory),
            'initialization_mode': 'project' if self.is_project_based() else 'legacy',
            'project_name': self.get_project_name(),
            'tracking_config': self.get_tracking_config()
        }
    
    def _load_progress(self) -> None:
        """Load existing progress from files."""
        self.completed_chapter_records = self._load_json_file(self.progress_file, [])
        self.failed_chapter_records = self._load_json_file(self.failed_file, [])
        self.metadata = self._load_json_file(self.metadata_file, {})
        
        # Initialize efficient lookup structures
        self._initialize_efficient_structures()
        
        self.logger.info(f"Loaded progress: {len(self.completed_chapter_records)} completed, {len(self.failed_chapter_records)} failed")
    
    def _initialize_efficient_structures(self) -> None:
        """Initialize efficient O(1) lookup structures."""
        # Fast lookup structures for O(1) operations
        self.completed_chapter_ids = set()
        self.failed_chapter_ids = set()
        self.chapter_failure_counts = {}
        
        # Build completed chapter IDs set
        for record in self.completed_chapter_records:
            chapter_id = self._get_chapter_id(record["chapter_info"])
            self.completed_chapter_ids.add(chapter_id)
        
        # Build failed chapter IDs set and failure counts
        for record in self.failed_chapter_records:
            chapter_id = self._get_chapter_id(record["chapter_info"])
            self.failed_chapter_ids.add(chapter_id)
            self.chapter_failure_counts[chapter_id] = self.chapter_failure_counts.get(chapter_id, 0) + 1
    
    def _load_json_file(self, file_path: Path, default_value: Any) -> Any:
        """Load JSON data from file, return default if file doesn't exist or is invalid."""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default_value
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Could not load {file_path}: {e}. Using default value.")
            return default_value
    
    def _save_json_file(self, file_path: Path, data: Any) -> bool:
        """Save data to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            self.logger.error(f"Could not save {file_path}: {e}")
            return False
    
    def mark_chapter_completed(self, chapter_info: Dict[str, Any], audio_file_path: str) -> bool:
        """
        Mark a chapter as successfully completed.
        
        Args:
            chapter_info: Chapter metadata from file organizer
            audio_file_path: Path to the generated audio file
            
        Returns:
            True if saved successfully, False otherwise
        """
        chapter_id = self._get_chapter_id(chapter_info)
        
        # Check if already completed (O(1) lookup)
        if chapter_id not in self.completed_chapter_ids:
            completion_record = {
                "timestamp": datetime.now().isoformat(),
                "chapter_info": chapter_info,
                "audio_file_path": audio_file_path,
                "audio_file_size": Path(audio_file_path).stat().st_size if Path(audio_file_path).exists() else 0
            }
            
            # Add to efficient lookup structures (O(1) operations)
            self.completed_chapter_ids.add(chapter_id)
            self.completed_chapter_records.append(completion_record)
            
            # Remove from failed if it was there (O(1) operations)
            if chapter_id in self.failed_chapter_ids:
                self.failed_chapter_ids.remove(chapter_id)
                # Clean up failure records (remove all failure records for this chapter)
                self.failed_chapter_records = [r for r in self.failed_chapter_records 
                                             if self._get_chapter_id(r["chapter_info"]) != chapter_id]
                # Remove from failure counts
                if chapter_id in self.chapter_failure_counts:
                    del self.chapter_failure_counts[chapter_id]
            
            # Update metadata
            self.metadata["last_completed_chapter"] = chapter_info["filename"]
            self.metadata["total_completed"] = len(self.completed_chapter_records)
            self.metadata["total_failed"] = len(self.failed_chapter_records)
            self.metadata["last_updated"] = datetime.now().isoformat()
            
            return self._save_progress()
        
        return True  # Already completed
    
    def mark_chapter_failed(self, chapter_info: Dict[str, Any], error_message: str, 
                           error_type: str = "unknown") -> bool:
        """
        Mark a chapter as failed.
        
        Args:
            chapter_info: Chapter metadata from file organizer
            error_message: Description of the error
            error_type: Type of error (e.g., "api_error", "file_error", "validation_error")
            
        Returns:
            True if saved successfully, False otherwise
        """
        chapter_id = self._get_chapter_id(chapter_info)
        
        # Get current retry count (O(1) lookup)
        current_retry_count = self.chapter_failure_counts.get(chapter_id, 0)
        
        failure_record = {
            "timestamp": datetime.now().isoformat(),
            "chapter_info": chapter_info,
            "error_message": error_message,
            "error_type": error_type,
            "retry_count": current_retry_count
        }
        
        # Add to efficient lookup structures (O(1) operations)
        self.failed_chapter_ids.add(chapter_id)
        self.failed_chapter_records.append(failure_record)
        self.chapter_failure_counts[chapter_id] = current_retry_count + 1
        
        # Update metadata
        self.metadata["total_failed"] = len(self.failed_chapter_records)
        self.metadata["last_updated"] = datetime.now().isoformat()
        
        return self._save_progress()
    
    def _get_chapter_id(self, chapter_info: Dict[str, Any]) -> str:
        """Generate a unique ID for a chapter."""
        return f"{chapter_info['volume_number']:02d}_{chapter_info['chapter_number']:03d}_{chapter_info['filename']}"
    
    def _get_retry_count(self, chapter_info: Dict[str, Any]) -> int:
        """Get the number of times this chapter has failed (O(1) lookup)."""
        chapter_id = self._get_chapter_id(chapter_info)
        return self.chapter_failure_counts.get(chapter_id, 0)
    
    def is_chapter_completed(self, chapter_info: Dict[str, Any]) -> bool:
        """Check if a chapter has been completed successfully (O(1) lookup)."""
        chapter_id = self._get_chapter_id(chapter_info)
        return chapter_id in self.completed_chapter_ids
    
    def is_chapter_failed(self, chapter_info: Dict[str, Any]) -> bool:
        """Check if a chapter has failed (and is not completed) (O(1) lookup)."""
        # If chapter is completed, it's not considered failed
        if self.is_chapter_completed(chapter_info):
            return False
        
        chapter_id = self._get_chapter_id(chapter_info)
        return chapter_id in self.failed_chapter_ids
    
    def get_next_chapter(self, all_chapters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Get the next chapter that needs to be processed.
        
        Args:
            all_chapters: List of all chapters from file organizer
            
        Returns:
            Next chapter to process, or None if all are completed
        """
        for chapter in all_chapters:
            if not self.is_chapter_completed(chapter) and not self.is_chapter_failed(chapter):
                return chapter
        
        return None
    
    def get_failed_chapters_for_retry(self, max_retries: int = None) -> List[Dict[str, Any]]:
        """
        Get chapters that have failed but can be retried (O(n) with O(1) lookups).
        
        Args:
            max_retries: Maximum number of retries allowed (uses config default if None)
            
        Returns:
            List of chapters that can be retried
        """
        # Use config default if not specified
        if max_retries is None:
            max_retries = self.tracking_config.get('retry_attempts', 3)
        retry_chapters = []
        
        # Use efficient lookup structures (O(1) per operation)
        for chapter_id in self.failed_chapter_ids:
            # Check if not completed and within retry limit
            if (chapter_id not in self.completed_chapter_ids and 
                self.chapter_failure_counts.get(chapter_id, 0) < max_retries):
                
                # Find the chapter info from failure records
                for failure_record in self.failed_chapter_records:
                    if self._get_chapter_id(failure_record["chapter_info"]) == chapter_id:
                        retry_chapters.append(failure_record["chapter_info"])
                        break
        
        return retry_chapters
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of current progress."""
        total_completed = len(self.completed_chapter_records)
        total_failed = len(self.failed_chapter_records)
        
        # Calculate total audio file size
        total_audio_size = 0
        for completed in self.completed_chapter_records:
            total_audio_size += completed.get("audio_file_size", 0)
        
        return {
            "total_completed": total_completed,
            "total_failed": total_failed,
            "total_audio_size_bytes": total_audio_size,
            "total_audio_size_mb": round(total_audio_size / (1024 * 1024), 2),
            "last_completed_chapter": self.metadata.get("last_completed_chapter"),
            "last_updated": self.metadata.get("last_updated"),
            "tracking_directory": str(self.tracking_directory)
        }
    
    def _save_progress(self) -> bool:
        """Save all progress data to files."""
        success = True
        
        success &= self._save_json_file(self.progress_file, self.completed_chapter_records)
        success &= self._save_json_file(self.failed_file, self.failed_chapter_records)
        success &= self._save_json_file(self.metadata_file, self.metadata)
        
        return success
    
    def reset_progress(self) -> bool:
        """Reset all progress (use with caution!)."""
        self.completed_chapter_records = []
        self.failed_chapter_records = []
        self.completed_chapter_ids = set()
        self.failed_chapter_ids = set()
        self.chapter_failure_counts = {}
        self.metadata = {}
        
        return self._save_progress()
    
    def clear_failed_chapters(self) -> bool:
        """Clear the failed chapters list (for retry scenarios)."""
        self.failed_chapter_records = []
        self.failed_chapter_ids = set()
        self.chapter_failure_counts = {}
        self.metadata["total_failed"] = 0
        
        return self._save_json_file(self.failed_file, self.failed_chapter_records) and \
               self._save_json_file(self.metadata_file, self.metadata)
    
    def export_progress_report(self, output_file: str = None) -> str:
        """
        Export a detailed progress report.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to the exported report file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.tracking_directory / f"progress_report_{timestamp}.json"
        else:
            output_file = Path(output_file)
        
        report = {
            "export_timestamp": datetime.now().isoformat(),
            "progress_summary": self.get_progress_summary(),
            "completed_chapters": self.completed_chapter_records,
            "failed_chapters": self.failed_chapter_records,
            "metadata": self.metadata
        }
        
        if self._save_json_file(output_file, report):
            self.logger.info(f"Progress report exported to: {output_file}")
            return str(output_file)
        else:
            raise IOError(f"Failed to export progress report to: {output_file}")
