"""
File organizer for discovering and sorting chapter files.
Handles the discovery of chapter files from extracted text directories
and organizes them in proper sequential order for TTS processing.

Supports both legacy string-based initialization and new Project-based initialization.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import logging


class ChapterFileOrganizer:
    """Organizes and discovers chapter files for TTS processing."""
    
    def __init__(self, input_source: Union[str, 'Project'], chapter_pattern: str = None, 
                 volume_pattern: str = None):
        """
        Initialize the file organizer.
        
        Args:
            input_source: Either a string path to directory OR a Project object
            chapter_pattern: Regex pattern to extract chapter numbers (optional if Project provided)
            volume_pattern: Regex pattern to extract volume numbers (optional if Project provided)
        """
        self.logger = logging.getLogger(__name__)
        
        # Handle both Project objects and string paths for backward compatibility
        if hasattr(input_source, 'get_input_directory'):
            # New Project-based initialization
            self.project = input_source
            self.input_directory = self.project.get_input_directory()
            
            # Get patterns from project configuration
            processing_config = self.project.get_processing_config()
            self.chapter_pattern = re.compile(
                processing_config.get('chapter_pattern', r"Chapter_(\d+)_")
            )
            self.volume_pattern = re.compile(
                processing_config.get('volume_pattern', r"(\d+)___VOLUME_\d+___")
            )
            
            self.logger.info(f"Initialized with Project: {self.project.project_name}")
        else:
            # Legacy string-based initialization
            self.project = None
            self.input_directory = Path(input_source)
            
            # Use provided patterns or defaults
            self.chapter_pattern = re.compile(
                chapter_pattern or r"Chapter_(\d+)_"
            )
            self.volume_pattern = re.compile(
                volume_pattern or r"(\d+)___VOLUME_\d+___"
            )
            
            self.logger.info(f"Initialized with legacy string path: {self.input_directory}")
        
        # Store original patterns for reference
        self._chapter_pattern_str = self.chapter_pattern.pattern
        self._volume_pattern_str = self.volume_pattern.pattern
    
    def is_project_based(self) -> bool:
        """Check if this organizer was initialized with a Project object."""
        return self.project is not None
    
    def get_project_name(self) -> Optional[str]:
        """Get the project name if initialized with a Project object, otherwise None."""
        return self.project.project_name if self.project else None
    
    def get_patterns_info(self) -> Dict[str, str]:
        """Get information about the patterns being used."""
        return {
            'chapter_pattern': self._chapter_pattern_str,
            'volume_pattern': self._volume_pattern_str,
            'initialization_mode': 'project' if self.is_project_based() else 'legacy'
        }
    
    def discover_chapters(self) -> List[Dict[str, any]]:
        """
        Discover all chapter files and return them sorted by volume and chapter number.
        
        Returns:
            List of dictionaries containing chapter information sorted in processing order
        """
        self.logger.info(f"Discovering chapters in: {self.input_directory}")
        
        if not self.input_directory.exists():
            self.logger.error(f"Input directory does not exist: {self.input_directory}")
            return []
        
        chapters = []
        
        # Scan all volume directories
        for volume_dir in self.input_directory.iterdir():
            if volume_dir.is_dir() and self._is_volume_directory(volume_dir.name):
                volume_number = self._extract_volume_number(volume_dir.name)
                volume_name = volume_dir.name
                
                self.logger.debug(f"Processing volume: {volume_name} (Volume {volume_number})")
                
                # Find all chapter files in this volume
                volume_chapters = self._discover_volume_chapters(volume_dir, volume_number, volume_name)
                chapters.extend(volume_chapters)
        
        # Sort chapters by volume number, then by chapter number
        chapters.sort(key=lambda x: (x['volume_number'], x['chapter_number']))
        
        self.logger.info(f"Discovered {len(chapters)} chapters across {len(set(c['volume_number'] for c in chapters))} volumes")
        
        return chapters
    
    def _is_volume_directory(self, dir_name: str) -> bool:
        """Check if a directory name matches the volume pattern."""
        # Check for standard volume pattern
        if self.volume_pattern.match(dir_name):
            return True
        
        # Check for Side_Stories directory (special case)
        if dir_name.lower() == "side_stories":
            return True
            
        return False
    
    def _extract_volume_number(self, dir_name: str) -> int:
        """Extract volume number from directory name."""
        # Handle Side_Stories as a special case (treat as volume 9)
        if dir_name.lower() == "side_stories":
            return 9
        
        # Handle standard volume pattern
        match = self.volume_pattern.match(dir_name)
        if match:
            return int(match.group(1))
        return 0
    
    def _discover_volume_chapters(self, volume_dir: Path, volume_number: int, volume_name: str) -> List[Dict[str, any]]:
        """Discover all chapter files in a specific volume directory."""
        chapters = []
        
        for file_path in volume_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.txt':
                chapter_info = self._parse_chapter_file(file_path, volume_number, volume_name)
                if chapter_info:
                    chapters.append(chapter_info)
        
        self.logger.debug(f"Found {len(chapters)} chapters in {volume_name}")
        return chapters
    
    def _parse_chapter_file(self, file_path: Path, volume_number: int, volume_name: str) -> Optional[Dict[str, any]]:
        """Parse chapter file information."""
        filename = file_path.name
        
        # Extract chapter number from filename
        match = self.chapter_pattern.search(filename)
        if not match:
            self.logger.warning(f"Skipping file (doesn't match chapter pattern): {filename}")
            return None
        
        chapter_number = int(match.group(1))
        
        # Validate file is readable
        if not self._validate_chapter_file(file_path):
            self.logger.warning(f"Skipping unreadable file: {filename}")
            return None
        
        return {
            'filename': filename,
            'file_path': str(file_path),
            'volume_number': volume_number,
            'volume_name': volume_name,
            'chapter_number': chapter_number,
            'chapter_title': self._extract_chapter_title(filename),
            'file_size': file_path.stat().st_size,
            'is_readable': True
        }
    
    def _extract_chapter_title(self, filename: str) -> str:
        """Extract chapter title from filename."""
        # Remove file extension
        name_without_ext = Path(filename).stem
        
        # Try to extract title after chapter number
        match = self.chapter_pattern.search(name_without_ext)
        if match:
            title_part = name_without_ext[match.end():]
            return title_part.replace('_', ' ').strip()
        
        return name_without_ext
    
    def _validate_chapter_file(self, file_path: Path) -> bool:
        """Validate that a chapter file is readable and contains text."""
        try:
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                return False
            
            # Check if file has content
            if file_path.stat().st_size == 0:
                return False
            
            # Try to read a small portion to check if it's text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(100)
                # Basic check: if we can read it and it has some content, it's probably valid
                return len(sample.strip()) > 0
                
        except (OSError, IOError, UnicodeDecodeError) as e:
            self.logger.warning(f"Error validating file {file_path}: {e}")
            return False
    
    def get_next_chapter(self, completed_chapters: List[str]) -> Optional[Dict[str, any]]:
        """
        Get the next chapter to process based on completed chapters.
        
        Args:
            completed_chapters: List of chapter filenames that have been completed
            
        Returns:
            Next chapter to process, or None if all chapters are completed
        """
        all_chapters = self.discover_chapters()
        
        for chapter in all_chapters:
            if chapter['filename'] not in completed_chapters:
                return chapter
        
        return None
    
    def get_chapter_by_name(self, chapter_name: str) -> Optional[Dict[str, any]]:
        """
        Get a specific chapter by filename.
        
        Args:
            chapter_name: Name of the chapter file to find
            
        Returns:
            Chapter information if found, None otherwise
        """
        all_chapters = self.discover_chapters()
        
        for chapter in all_chapters:
            if chapter['filename'] == chapter_name:
                return chapter
        
        return None
    
    def get_volume_chapters(self, volume_number: int) -> List[Dict[str, any]]:
        """
        Get all chapters for a specific volume.
        
        Args:
            volume_number: Volume number to get chapters for
            
        Returns:
            List of chapters in the specified volume
        """
        all_chapters = self.discover_chapters()
        return [chapter for chapter in all_chapters if chapter['volume_number'] == volume_number]


def main():
    """Test function for the file organizer."""
    import json
    
    # Test with the actual directory structure
    organizer = ChapterFileOrganizer("../extracted_text/lotm_book1")
    
    chapters = organizer.discover_chapters()
    
    print(f"Discovered {len(chapters)} chapters:")
    for i, chapter in enumerate(chapters[:10]):  # Show first 10
        print(f"{i+1}. Volume {chapter['volume_number']} - Chapter {chapter['chapter_number']}: {chapter['chapter_title']}")
    
    if len(chapters) > 10:
        print(f"... and {len(chapters) - 10} more chapters")
    
    # Test getting next chapter
    next_chapter = organizer.get_next_chapter([])
    if next_chapter:
        print(f"\nNext chapter to process: {next_chapter['filename']}")


if __name__ == "__main__":
    main()
