"""
Unit tests for the main TTS processing script.
Tests command-line interface, argument parsing, and core processing logic.
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from io import StringIO
import argparse

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.process_project import (
    TTSProcessor, setup_logging, create_argument_parser, 
    parse_chapter_range, main
)


class TestTTSProcessor:
    """Test cases for TTSProcessor class."""
    
    def setup_method(self):
        """Set up mock project for testing."""
        self.mock_project = MagicMock()
        self.mock_project.project_name = "test_project"
        self.mock_project.project_config = {
            'display_name': 'Test Project',
            'metadata': {'total_chapters': 100}
        }
        
        # Mock file organizer
        self.mock_chapters = [
            {
                'filename': 'Chapter_1_Test.txt',
                'volume_number': 1,
                'chapter_number': 1,
                'chapter_title': 'Test Chapter 1',
                'file_path': Path('/test/Chapter_1_Test.txt')
            },
            {
                'filename': 'Chapter_2_Test.txt',
                'volume_number': 1,
                'chapter_number': 2,
                'chapter_title': 'Test Chapter 2',
                'file_path': Path('/test/Chapter_2_Test.txt')
            },
            {
                'filename': 'Chapter_3_Test.txt',
                'volume_number': 1,
                'chapter_number': 3,
                'chapter_title': 'Test Chapter 3',
                'file_path': Path('/test/Chapter_3_Test.txt')
            }
        ]
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    def test_initialization(self, mock_tracker_class, mock_organizer_class):
        """Test TTSProcessor initialization."""
        processor = TTSProcessor(self.mock_project, dry_run=True)
        
        assert processor.project == self.mock_project
        assert processor.dry_run is True
        assert processor.processed_count == 0
        assert processor.failed_count == 0
        assert processor.start_time is None
        
        # Verify components were initialized
        mock_organizer_class.assert_called_once_with(self.mock_project)
        mock_tracker_class.assert_called_once_with(self.mock_project)
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    def test_discover_chapters(self, mock_tracker_class, mock_organizer_class):
        """Test chapter discovery."""
        mock_organizer = mock_organizer_class.return_value
        mock_organizer.discover_chapters.return_value = self.mock_chapters
        
        processor = TTSProcessor(self.mock_project)
        chapters = processor.discover_chapters()
        
        assert chapters == self.mock_chapters
        mock_organizer.discover_chapters.assert_called_once()
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    def test_get_next_chapter_to_process(self, mock_tracker_class, mock_organizer_class):
        """Test getting next chapter to process."""
        mock_tracker = mock_tracker_class.return_value
        mock_tracker.is_chapter_completed_real.side_effect = [True, False, False]
        
        processor = TTSProcessor(self.mock_project)
        next_chapter = processor.get_next_chapter_to_process(self.mock_chapters)
        
        assert next_chapter == self.mock_chapters[1]
        assert mock_tracker.is_chapter_completed_real.call_count == 2
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    @patch('scripts.process_project.time.sleep')
    @patch('random.random')
    def test_process_chapter_dry_run_success(self, mock_random, mock_sleep, 
                                           mock_tracker_class, mock_organizer_class):
        """Test processing chapter in dry-run mode (success)."""
        mock_tracker = mock_tracker_class.return_value
        mock_random.return_value = 0.5  # < 0.9, so success
        
        processor = TTSProcessor(self.mock_project, dry_run=True)
        chapter = self.mock_chapters[0]
        
        result = processor.process_chapter(chapter)
        
        assert result is True
        assert processor.processed_count == 1
        assert processor.failed_count == 0
        mock_tracker.mark_chapter_completed.assert_called_once()
        mock_sleep.assert_called_once_with(0.1)
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    @patch('scripts.process_project.time.sleep')
    @patch('random.random')
    def test_process_chapter_dry_run_failure(self, mock_random, mock_sleep,
                                           mock_tracker_class, mock_organizer_class):
        """Test processing chapter in dry-run mode (failure)."""
        mock_tracker = mock_tracker_class.return_value
        mock_random.return_value = 0.95  # > 0.9, so failure
        
        processor = TTSProcessor(self.mock_project, dry_run=True)
        chapter = self.mock_chapters[0]
        
        result = processor.process_chapter(chapter)
        
        assert result is False
        assert processor.processed_count == 0
        assert processor.failed_count == 1
        mock_tracker.mark_chapter_failed.assert_called_once()
        mock_sleep.assert_called_once_with(0.1)
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    def test_process_chapter_real_mode_not_implemented(self, mock_tracker_class, mock_organizer_class):
        """Test that real processing mode raises NotImplementedError."""
        processor = TTSProcessor(self.mock_project, dry_run=False)
        chapter = self.mock_chapters[0]
        
        # The NotImplementedError is caught and logged, so we check the return value
        result = processor.process_chapter(chapter)
        assert result is False
        assert processor.failed_count == 1
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    @patch('scripts.process_project.time.sleep')
    @patch('random.random')
    def test_process_chapters(self, mock_random, mock_sleep, mock_tracker_class, mock_organizer_class):
        """Test processing multiple chapters."""
        mock_tracker = mock_tracker_class.return_value
        mock_organizer = mock_organizer_class.return_value
        mock_random.return_value = 0.5  # Success
        
        # Mock the discover_chapters method to return our test chapters
        mock_organizer.discover_chapters.return_value = self.mock_chapters
        
        # Mock is_chapter_completed_real to return False so chapters aren't skipped
        mock_tracker.is_chapter_completed_real.return_value = False
        
        processor = TTSProcessor(self.mock_project, dry_run=True)
        result = processor.process_chapters(self.mock_chapters)
        
        assert result['project_name'] == 'test_project'
        assert result['total_chapters'] == 3
        assert result['session_processed'] == 3
        assert result['session_failed'] == 0
        assert result['dry_run'] is True
        assert 'processing_time' in result
        
        # Verify all chapters were processed
        assert mock_tracker.mark_chapter_completed.call_count == 3
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    @patch('scripts.process_project.time.sleep')
    @patch('random.random')
    def test_process_chapters_with_range(self, mock_random, mock_sleep, 
                                       mock_tracker_class, mock_organizer_class):
        """Test processing chapters with range filter."""
        mock_tracker = mock_tracker_class.return_value
        mock_random.return_value = 0.5  # Success
        
        # Mock is_chapter_completed_real to return False so chapters aren't skipped
        mock_tracker.is_chapter_completed_real.return_value = False
        
        processor = TTSProcessor(self.mock_project, dry_run=True)
        result = processor.process_chapters(self.mock_chapters, start_chapter=2, end_chapter=2)
        
        assert result['session_processed'] == 1
        assert mock_tracker.mark_chapter_completed.call_count == 1
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    def test_get_failed_chapters_for_retry(self, mock_tracker_class, mock_organizer_class):
        """Test getting failed chapters for retry."""
        mock_tracker = mock_tracker_class.return_value
        mock_tracker.get_failed_chapters_for_retry.return_value = [self.mock_chapters[0]]
        
        processor = TTSProcessor(self.mock_project)
        failed_chapters = processor.get_failed_chapters_for_retry()
        
        assert failed_chapters == [self.mock_chapters[0]]
        mock_tracker.get_failed_chapters_for_retry.assert_called_once()
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    @patch('scripts.process_project.time.sleep')
    @patch('random.random')
    def test_retry_failed_chapters(self, mock_random, mock_sleep, 
                                 mock_tracker_class, mock_organizer_class):
        """Test retrying failed chapters."""
        mock_tracker = mock_tracker_class.return_value
        mock_tracker.get_failed_chapters_for_retry.return_value = [self.mock_chapters[0]]
        mock_random.return_value = 0.5  # Success
        
        processor = TTSProcessor(self.mock_project, dry_run=True)
        result = processor.retry_failed_chapters()
        
        assert result['retried'] == 1
        assert result['successful'] == 1
        assert result['failed'] == 0


class TestArgumentParser:
    """Test cases for argument parser functionality."""
    
    def test_create_argument_parser(self):
        """Test argument parser creation."""
        parser = create_argument_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.description is not None
        assert parser.epilog is not None
    
    def test_parse_chapter_range_single(self):
        """Test parsing single chapter number."""
        start, end = parse_chapter_range("5")
        assert start == 5
        assert end == 5
    
    def test_parse_chapter_range_range(self):
        """Test parsing chapter range."""
        start, end = parse_chapter_range("1-10")
        assert start == 1
        assert end == 10
    
    def test_parse_chapter_range_with_spaces(self):
        """Test parsing chapter range with spaces."""
        start, end = parse_chapter_range(" 1 - 10 ")
        assert start == 1
        assert end == 10


class TestLoggingSetup:
    """Test cases for logging setup."""
    
    def test_setup_logging_default(self):
        """Test default logging setup."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            setup_logging()
            
            mock_logger.setLevel.assert_called_once()
            assert len(mock_logger.addHandler.call_args_list) == 1
    
    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.FileHandler') as mock_file_handler:
            
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            setup_logging(log_file="test.log")
            
            mock_logger.setLevel.assert_called_once()
            assert len(mock_logger.addHandler.call_args_list) == 2
            mock_file_handler.assert_called_once_with("test.log")


class TestMainFunction:
    """Test cases for main function."""
    
    @patch('scripts.process_project.ProjectManager')
    @patch('sys.argv', ['process_project.py', '--list-projects'])
    def test_main_list_projects(self, mock_pm_class):
        """Test main function with --list-projects."""
        mock_pm = mock_pm_class.return_value
        mock_pm.list_projects.return_value = ['project1', 'project2']
        
        mock_project = MagicMock()
        mock_project.project_config = {'display_name': 'Test Project'}
        mock_pm.load_project.return_value = mock_project
        
        with patch('builtins.print') as mock_print:
            result = main()
            
            assert result == 0
            mock_print.assert_called()
    
    @patch('scripts.process_project.ProjectManager')
    @patch('scripts.process_project.TTSProcessor')
    @patch('sys.argv', ['process_project.py', '--project', 'test_project', '--dry-run'])
    def test_main_process_project_dry_run(self, mock_processor_class, mock_pm_class):
        """Test main function processing project in dry-run mode."""
        mock_pm = mock_pm_class.return_value
        mock_project = MagicMock()
        mock_project.is_valid.return_value = True
        mock_project.project_name = 'test_project'
        mock_project.project_config = {'display_name': 'Test Project'}
        mock_pm.load_project.return_value = mock_project
        
        mock_processor = mock_processor_class.return_value
        mock_processor.discover_chapters.return_value = []
        
        result = main()
        
        assert result == 0
        mock_processor_class.assert_called_once_with(mock_project, dry_run=True)
    
    @patch('scripts.process_project.ProjectManager')
    @patch('sys.argv', ['process_project.py'])
    def test_main_no_project_error(self, mock_pm_class):
        """Test main function with no project specified."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2
    
    @patch('scripts.process_project.ProjectManager')
    @patch('sys.argv', ['process_project.py', '--project', 'nonexistent'])
    def test_main_invalid_project(self, mock_pm_class):
        """Test main function with invalid project."""
        mock_pm = mock_pm_class.return_value
        mock_pm.load_project.return_value = None
        
        result = main()
        
        assert result == 1
    
    @patch('scripts.process_project.ProjectManager')
    @patch('sys.argv', ['process_project.py', '--project', 'invalid_project'])
    def test_main_invalid_project_config(self, mock_pm_class):
        """Test main function with invalid project configuration."""
        mock_pm = mock_pm_class.return_value
        mock_project = MagicMock()
        mock_project.is_valid.return_value = False
        mock_pm.load_project.return_value = mock_project
        
        result = main()
        
        assert result == 1


class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    def setup_method(self):
        """Set up mock project for testing."""
        self.mock_project = MagicMock()
        self.mock_project.project_name = "test_project"
        self.mock_project.project_config = {
            'display_name': 'Test Project',
            'metadata': {'total_chapters': 100}
        }
    
    @patch('scripts.process_project.ChapterFileOrganizer')
    @patch('scripts.process_project.ProgressTracker')
    @patch('scripts.process_project.time.sleep')
    @patch('random.random')
    def test_complete_processing_workflow(self, mock_random, mock_sleep,
                                         mock_tracker_class, mock_organizer_class):
        """Test complete processing workflow."""
        # Setup mocks
        mock_tracker = mock_tracker_class.return_value
        mock_organizer = mock_organizer_class.return_value
        
        chapters = [
            {'filename': 'Chapter_1.txt', 'volume_number': 1, 'chapter_number': 1},
            {'filename': 'Chapter_2.txt', 'volume_number': 1, 'chapter_number': 2}
        ]
        mock_organizer.discover_chapters.return_value = chapters
        
        # Mock is_chapter_completed_real to return False so chapters aren't skipped
        mock_tracker.is_chapter_completed_real.return_value = False
        
        # Simulate mixed success/failure
        mock_random.side_effect = [0.5, 0.95]  # First success, second failure
        
        # Create processor and run workflow
        processor = TTSProcessor(self.mock_project, dry_run=True)
        
        # Discover chapters
        discovered_chapters = processor.discover_chapters()
        assert len(discovered_chapters) == 2
        
        # Process chapters
        result = processor.process_chapters(discovered_chapters)
        
        # Verify results
        assert result['session_processed'] == 1
        assert result['session_failed'] == 1
        assert result['dry_run'] is True
        
        # Verify tracker calls
        assert mock_tracker.mark_chapter_completed.call_count == 1
        assert mock_tracker.mark_chapter_failed.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
