"""
Unit tests for the file organizer component.
Tests both legacy string-based initialization and new Project-based initialization.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add the utils directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / "utils"))

from file_organizer import ChapterFileOrganizer


class TestFileOrganizerLegacy:
    """Unit tests for ChapterFileOrganizer class with legacy string-based initialization."""
    
    def test_initialization(self):
        """Test that ChapterFileOrganizer initializes correctly."""
        organizer = ChapterFileOrganizer("./test_input")
        
        assert organizer.input_directory == Path("./test_input")
        assert organizer.chapter_pattern.pattern == r"Chapter_(\d+)_"
        assert organizer.volume_pattern.pattern == r"(\d+)___VOLUME_\d+___"
    
    def test_volume_directory_detection(self):
        """Test volume directory detection logic."""
        organizer = ChapterFileOrganizer("./test_input")
        
        # Test standard volume directories
        assert organizer._is_volume_directory("1___VOLUME_1___CLOWN") is True
        assert organizer._is_volume_directory("2___VOLUME_2___FACELESS") is True
        assert organizer._is_volume_directory("8___VOLUME_8___FOOL") is True
        
        # Test Side_Stories directory
        assert organizer._is_volume_directory("Side_Stories") is True
        assert organizer._is_volume_directory("side_stories") is True
        assert organizer._is_volume_directory("SIDE_STORIES") is True
        
        # Test invalid directories
        assert organizer._is_volume_directory("invalid_dir") is False
        assert organizer._is_volume_directory("Chapter_1.txt") is False
        assert organizer._is_volume_directory("") is False
    
    def test_volume_number_extraction(self):
        """Test volume number extraction from directory names."""
        organizer = ChapterFileOrganizer("./test_input")
        
        # Test standard volume directories
        assert organizer._extract_volume_number("1___VOLUME_1___CLOWN") == 1
        assert organizer._extract_volume_number("2___VOLUME_2___FACELESS") == 2
        assert organizer._extract_volume_number("8___VOLUME_8___FOOL") == 8
        
        # Test Side_Stories directory
        assert organizer._extract_volume_number("Side_Stories") == 9
        assert organizer._extract_volume_number("side_stories") == 9
        assert organizer._extract_volume_number("SIDE_STORIES") == 9
        
        # Test invalid directories
        assert organizer._extract_volume_number("invalid_dir") == 0
        assert organizer._extract_volume_number("") == 0
    
    def test_chapter_title_extraction(self):
        """Test chapter title extraction from filenames."""
        organizer = ChapterFileOrganizer("./test_input")
        
        # Test standard chapter filenames
        assert organizer._extract_chapter_title("Chapter_1_Crimson.txt") == "Crimson"
        assert organizer._extract_chapter_title("Chapter_214_Land_of_Hope.txt") == "Land of Hope"
        assert organizer._extract_chapter_title("Chapter_1430_Test_Story.txt") == "Test Story"
        
        # Test edge cases
        assert organizer._extract_chapter_title("Chapter_1.txt") == "Chapter_1"
        assert organizer._extract_chapter_title("Chapter_1_") == ""
        assert organizer._extract_chapter_title("Chapter_1_A_B_C.txt") == "A B C"
    
    @patch('os.access')
    @patch('pathlib.Path.stat')
    @patch('builtins.open', new_callable=mock_open, read_data="Sample content")
    def test_chapter_file_validation(self, mock_file, mock_stat, mock_access):
        """Test chapter file validation logic."""
        organizer = ChapterFileOrganizer("./test_input")
        
        # Mock file statistics
        mock_stat.return_value.st_size = 100
        mock_access.return_value = True
        
        # Create a mock file path
        test_file = Path("./test_file.txt")
        
        # Test valid file
        assert organizer._validate_chapter_file(test_file) is True
        
        # Test unreadable file
        mock_access.return_value = False
        assert organizer._validate_chapter_file(test_file) is False
        
        # Test empty file
        mock_access.return_value = True
        mock_stat.return_value.st_size = 0
        assert organizer._validate_chapter_file(test_file) is False
        
        # Test file with no content
        mock_stat.return_value.st_size = 100
        mock_file.return_value.read.return_value = "   \n\n   "
        assert organizer._validate_chapter_file(test_file) is False
    
    def test_chapter_file_parsing(self):
        """Test chapter file parsing logic."""
        organizer = ChapterFileOrganizer("./test_input")
        
        # Mock file validation to return True
        with patch.object(organizer, '_validate_chapter_file', return_value=True):
            # Test valid chapter file
            test_file = Path("./Chapter_1_Crimson.txt")
            # Mock the file size for the result
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1000
                result = organizer._parse_chapter_file(test_file, 1, "1___VOLUME_1___CLOWN")
            
            assert result is not None
            assert result['filename'] == "Chapter_1_Crimson.txt"
            assert result['volume_number'] == 1
            assert result['volume_name'] == "1___VOLUME_1___CLOWN"
            assert result['chapter_number'] == 1
            assert result['chapter_title'] == "Crimson"
            assert result['is_readable'] is True
            assert result['file_size'] == 1000
        
        # Test invalid chapter file (doesn't match pattern)
        with patch.object(organizer, '_validate_chapter_file', return_value=True):
            test_file = Path("./Invalid_File.txt")
            result = organizer._parse_chapter_file(test_file, 1, "1___VOLUME_1___CLOWN")
            assert result is None
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_chapters_empty_directory(self, mock_iterdir, mock_exists):
        """Test chapter discovery with empty directory."""
        organizer = ChapterFileOrganizer("./test_input")
        
        # Mock directory existence
        mock_exists.return_value = True
        
        # Mock empty directory
        mock_iterdir.return_value = []
        
        chapters = organizer.discover_chapters()
        assert len(chapters) == 0
    
    @patch('pathlib.Path.exists')
    def test_discover_chapters_nonexistent_directory(self, mock_exists):
        """Test chapter discovery with non-existent directory."""
        organizer = ChapterFileOrganizer("./nonexistent")
        
        # Mock directory not existing
        mock_exists.return_value = False
        
        chapters = organizer.discover_chapters()
        assert len(chapters) == 0
    
    def test_get_next_chapter(self):
        """Test getting next chapter functionality."""
        organizer = ChapterFileOrganizer("./test_input")
        
        # Mock chapter discovery
        mock_chapters = [
            {'filename': 'Chapter_1_Crimson.txt'},
            {'filename': 'Chapter_2_Situation.txt'},
            {'filename': 'Chapter_3_Melissa.txt'}
        ]
        
        with patch.object(organizer, 'discover_chapters', return_value=mock_chapters):
            # Test with no completed chapters
            next_chapter = organizer.get_next_chapter([])
            assert next_chapter is not None
            assert next_chapter['filename'] == 'Chapter_1_Crimson.txt'
            
            # Test with some completed chapters
            next_chapter = organizer.get_next_chapter(['Chapter_1_Crimson.txt'])
            assert next_chapter is not None
            assert next_chapter['filename'] == 'Chapter_2_Situation.txt'
            
            # Test with all chapters completed
            next_chapter = organizer.get_next_chapter([
                'Chapter_1_Crimson.txt', 'Chapter_2_Situation.txt', 'Chapter_3_Melissa.txt'
            ])
            assert next_chapter is None
    
    def test_get_chapter_by_name(self):
        """Test getting specific chapter by name."""
        organizer = ChapterFileOrganizer("./test_input")
        
        # Mock chapter discovery
        mock_chapters = [
            {'filename': 'Chapter_1_Crimson.txt', 'volume_number': 1},
            {'filename': 'Chapter_2_Situation.txt', 'volume_number': 1},
        ]
        
        with patch.object(organizer, 'discover_chapters', return_value=mock_chapters):
            # Test finding existing chapter
            chapter = organizer.get_chapter_by_name('Chapter_1_Crimson.txt')
            assert chapter is not None
            assert chapter['filename'] == 'Chapter_1_Crimson.txt'
            
            # Test finding non-existent chapter
            chapter = organizer.get_chapter_by_name('Chapter_999_Nonexistent.txt')
            assert chapter is None
    
    def test_get_volume_chapters(self):
        """Test getting chapters for specific volume."""
        organizer = ChapterFileOrganizer("./test_input")
        
        # Mock chapter discovery
        mock_chapters = [
            {'filename': 'Chapter_1_Crimson.txt', 'volume_number': 1},
            {'filename': 'Chapter_2_Situation.txt', 'volume_number': 1},
            {'filename': 'Chapter_214_Land_of_Hope.txt', 'volume_number': 2},
        ]
        
        with patch.object(organizer, 'discover_chapters', return_value=mock_chapters):
            # Test getting volume 1 chapters
            volume_1_chapters = organizer.get_volume_chapters(1)
            assert len(volume_1_chapters) == 2
            assert all(ch['volume_number'] == 1 for ch in volume_1_chapters)
            
            # Test getting volume 2 chapters
            volume_2_chapters = organizer.get_volume_chapters(2)
            assert len(volume_2_chapters) == 1
            assert volume_2_chapters[0]['filename'] == 'Chapter_214_Land_of_Hope.txt'
            
            # Test getting non-existent volume
            volume_3_chapters = organizer.get_volume_chapters(3)
            assert len(volume_3_chapters) == 0


class TestFileOrganizerProject:
    """Unit tests for ChapterFileOrganizer class with Project-based initialization."""
    
    def setup_method(self):
        """Set up mock Project object for testing."""
        # Create a mock Project object
        self.mock_project = MagicMock()
        self.mock_project.project_name = "test_project"
        self.mock_project.get_input_directory.return_value = Path("./test_input")
        self.mock_project.get_processing_config.return_value = {
            'chapter_pattern': r'Chapter_(\d+)_',
            'volume_pattern': r'(\d+)___VOLUME_\d+___'
        }
    
    def test_project_initialization(self):
        """Test that ChapterFileOrganizer initializes correctly with Project object."""
        organizer = ChapterFileOrganizer(self.mock_project)
        
        assert organizer.input_directory == Path("./test_input")
        assert organizer.chapter_pattern.pattern == r"Chapter_(\d+)_"
        assert organizer.volume_pattern.pattern == r"(\d+)___VOLUME_\d+___"
        assert organizer.is_project_based() is True
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
        assert organizer.is_project_based() is True
    
    def test_project_utility_methods(self):
        """Test Project-based utility methods."""
        organizer = ChapterFileOrganizer(self.mock_project)
        
        # Test utility methods
        assert organizer.is_project_based() is True
        assert organizer.get_project_name() == "test_project"
        
        patterns_info = organizer.get_patterns_info()
        assert patterns_info['initialization_mode'] == 'project'
        assert patterns_info['chapter_pattern'] == r'Chapter_(\d+)_'
        assert patterns_info['volume_pattern'] == r'(\d+)___VOLUME_\d+___'


class TestFileOrganizerDualMode:
    """Unit tests comparing legacy and Project-based initialization modes."""
    
    def test_legacy_vs_project_initialization(self):
        """Test that both initialization modes work correctly."""
        # Test legacy initialization
        legacy_organizer = ChapterFileOrganizer("./test_input")
        
        # Create mock project for project initialization
        mock_project = MagicMock()
        mock_project.project_name = "test_project"
        mock_project.get_input_directory.return_value = Path("./test_input")
        mock_project.get_processing_config.return_value = {
            'chapter_pattern': r'Chapter_(\d+)_',
            'volume_pattern': r'(\d+)___VOLUME_\d+___'
        }
        
        project_organizer = ChapterFileOrganizer(mock_project)
        
        # Both should have same input directory
        assert legacy_organizer.input_directory == project_organizer.input_directory
        
        # Both should have same patterns (when project uses defaults)
        assert legacy_organizer.chapter_pattern.pattern == project_organizer.chapter_pattern.pattern
        assert legacy_organizer.volume_pattern.pattern == project_organizer.volume_pattern.pattern
        
        # But different initialization modes
        assert legacy_organizer.is_project_based() is False
        assert project_organizer.is_project_based() is True
        
        assert legacy_organizer.get_project_name() is None
        assert project_organizer.get_project_name() == "test_project"
    
    def test_patterns_info_comparison(self):
        """Test patterns info for both initialization modes."""
        # Legacy mode
        legacy_organizer = ChapterFileOrganizer("./test_input")
        legacy_info = legacy_organizer.get_patterns_info()
        
        # Project mode
        mock_project = MagicMock()
        mock_project.project_name = "test_project"
        mock_project.get_input_directory.return_value = Path("./test_input")
        mock_project.get_processing_config.return_value = {
            'chapter_pattern': r'Chapter_(\d+)_',
            'volume_pattern': r'(\d+)___VOLUME_\d+___'
        }
        
        project_organizer = ChapterFileOrganizer(mock_project)
        project_info = project_organizer.get_patterns_info()
        
        # Same patterns, different modes
        assert legacy_info['chapter_pattern'] == project_info['chapter_pattern']
        assert legacy_info['volume_pattern'] == project_info['volume_pattern']
        assert legacy_info['initialization_mode'] == 'legacy'
        assert project_info['initialization_mode'] == 'project'
    
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
        assert organizer.is_project_based() is True
        assert organizer.get_project_name() == "custom_project"
        
        patterns_info = organizer.get_patterns_info()
        assert patterns_info['initialization_mode'] == 'project'
        assert patterns_info['chapter_pattern'] == r'Custom_Chapter_(\d+)\.txt$'
        assert patterns_info['volume_pattern'] == r'Volume_(\d+)_'


class TestFileOrganizerBackwardCompatibility:
    """Unit tests ensuring backward compatibility with existing code."""
    
    def test_existing_code_compatibility(self):
        """Test that existing code using string initialization still works."""
        # This is exactly how existing code would initialize the organizer
        organizer = ChapterFileOrganizer(
            "./test_input",
            chapter_pattern=r"Chapter_(\d+)_",
            volume_pattern=r"(\d+)___VOLUME_\d+___"
        )
        
        # Should work exactly as before
        assert organizer.input_directory == Path("./test_input")
        assert organizer.chapter_pattern.pattern == r"Chapter_(\d+)_"
        assert organizer.volume_pattern.pattern == r"(\d+)___VOLUME_\d+___"
        assert organizer.is_project_based() is False
        assert organizer.get_project_name() is None
    
    def test_existing_code_with_defaults(self):
        """Test that existing code using only directory path still works."""
        # This is how existing code might initialize with defaults
        organizer = ChapterFileOrganizer("./test_input")
        
        # Should use default patterns
        assert organizer.chapter_pattern.pattern == r"Chapter_(\d+)_"
        assert organizer.volume_pattern.pattern == r"(\d+)___VOLUME_\d+___"
        assert organizer.is_project_based() is False


if __name__ == "__main__":
    # Run the tests if this file is executed directly
    pytest.main([__file__, "-v"])
