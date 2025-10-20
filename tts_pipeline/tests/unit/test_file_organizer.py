"""
Unit tests for file organizer functionality.
Tests Project-based initialization only.
"""

import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import pytest

# Add the utils directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / "utils"))

from file_organizer import ChapterFileOrganizer


class TestFileOrganizerProject:
    """Test cases for ChapterFileOrganizer class with Project-based initialization."""
    
    def setup_method(self):
        """Set up mock Project object for testing."""
        # Create a mock Project object
        self.mock_project = MagicMock()
        self.mock_project.project_name = "test_project"
        self.mock_project.get_input_directory.return_value = Path("./test_input")
        self.mock_project.get_processing_config.return_value = {
            'chapter_pattern': r"Chapter_(\d+)_",
            'volume_pattern': r"(\d+)___VOLUME_\d+___"
        }
    
    def test_project_initialization(self):
        """Test that ChapterFileOrganizer initializes correctly with Project object."""
        organizer = ChapterFileOrganizer(self.mock_project)
        
        assert organizer.input_directory == Path("./test_input")
        assert organizer.chapter_pattern.pattern == r"Chapter_(\d+)_"
        assert organizer.volume_pattern.pattern == r"(\d+)___VOLUME_\d+___"
        assert organizer.get_project_name() == "test_project"
    
    def test_project_initialization_with_custom_patterns(self):
        """Test Project initialization with custom patterns from config."""
        # Update mock project with custom patterns
        self.mock_project.get_processing_config.return_value = {
            'chapter_pattern': r'Custom_Chapter_(\d+)\.txt$',
            'volume_pattern': r'Vol_(\d+)_'
        }
        
        organizer = ChapterFileOrganizer(self.mock_project)
        
        assert organizer.chapter_pattern.pattern == r"Custom_Chapter_(\d+)\.txt$"
        assert organizer.volume_pattern.pattern == r"Vol_(\d+)_"
        assert organizer.get_project_name() == "test_project"
    
    def test_project_utility_methods(self):
        """Test Project-based utility methods."""
        organizer = ChapterFileOrganizer(self.mock_project)
        
        # Test utility methods
        assert organizer.get_project_name() == "test_project"
        
        patterns_info = organizer.get_patterns_info()
        assert patterns_info['project_name'] == 'test_project'
        assert patterns_info['chapter_pattern'] == r"Chapter_(\d+)_"
        assert patterns_info['volume_pattern'] == r"(\d+)___VOLUME_\d+___"
    
    def test_custom_patterns_project_mode(self):
        """Test that Project mode uses custom patterns from config."""
        # Create mock project with custom patterns
        mock_project = MagicMock()
        mock_project.project_name = "custom_project"
        mock_project.get_input_directory.return_value = Path("./test_input")
        mock_project.get_processing_config.return_value = {
            'chapter_pattern': r'Custom_Chapter_(\d+)\.txt$',
            'volume_pattern': r'Volume_(\d+)_'
        }
        
        organizer = ChapterFileOrganizer(mock_project)
        
        assert organizer.chapter_pattern.pattern == r'Custom_Chapter_(\d+)\.txt$'
        assert organizer.volume_pattern.pattern == r'Volume_(\d+)_'
        assert organizer.get_project_name() == "custom_project"
        
        patterns_info = organizer.get_patterns_info()
        assert patterns_info['project_name'] == 'custom_project'


if __name__ == "__main__":
    # Run the tests if this file is executed directly
    pytest.main([__file__, "-v"])