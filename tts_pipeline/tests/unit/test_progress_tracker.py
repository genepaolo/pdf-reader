"""
Unit tests for progress tracker functionality.
Tests both legacy string-based initialization and new Project-based initialization.
"""

import json
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open, MagicMock
import pytest

# Add the utils directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / "utils"))

from progress_tracker import ProgressTracker


class TestProgressTrackerLegacy:
    """Test cases for ProgressTracker class with legacy string-based initialization."""
    
    def test_initialization(self):
        """Test progress tracker initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            assert tracker.tracking_directory == Path(temp_dir)
            assert tracker.completed_chapter_records == []
            assert tracker.failed_chapter_records == []
            assert tracker.metadata == {}
    
    def test_initialization_with_existing_files(self):
        """Test initialization with existing progress files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing progress files
            progress_data = [
                {
                    "timestamp": "2025-01-18T10:00:00",
                    "chapter_info": {"filename": "Chapter_1_Test.txt", "volume_number": 1, "chapter_number": 1},
                    "audio_file_path": "/path/to/audio1.mp3",
                    "audio_file_size": 1024
                }
            ]
            
            failed_data = [
                {
                    "timestamp": "2025-01-18T10:05:00",
                    "chapter_info": {"filename": "Chapter_2_Test.txt", "volume_number": 1, "chapter_number": 2},
                    "error_message": "Test error",
                    "error_type": "api_error",
                    "retry_count": 1
                }
            ]
            
            metadata = {
                "last_completed_chapter": "Chapter_1_Test.txt",
                "total_completed": 1,
                "total_failed": 1
            }
            
            # Write test data
            progress_file = Path(temp_dir) / "progress.json"
            failed_file = Path(temp_dir) / "failed.json"
            metadata_file = Path(temp_dir) / "metadata.json"
            
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f)
            with open(failed_file, 'w') as f:
                json.dump(failed_data, f)
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)
            
            # Initialize tracker
            tracker = ProgressTracker(temp_dir)
            
            assert len(tracker.completed_chapter_records) == 1
            assert len(tracker.failed_chapter_records) == 1
            assert tracker.metadata["total_completed"] == 1
    
    def test_mark_chapter_completed(self):
        """Test marking a chapter as completed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1,
                "chapter_title": "Test Chapter"
            }
            
            audio_file_path = "/path/to/audio.mp3"
            
            # Mock file size
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 2048
                
                result = tracker.mark_chapter_completed(chapter_info, audio_file_path)
                
                assert result is True
                assert len(tracker.completed_chapter_records) == 1
                assert tracker.completed_chapter_records[0]["chapter_info"] == chapter_info
                assert tracker.completed_chapter_records[0]["audio_file_path"] == audio_file_path
                assert tracker.completed_chapter_records[0]["audio_file_size"] == 2048
                assert tracker.metadata["total_completed"] == 1
    
    def test_mark_chapter_completed_duplicate(self):
        """Test marking the same chapter as completed twice."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            # Mark as completed first time
            tracker.mark_chapter_completed(chapter_info, "/path/to/audio1.mp3")
            first_count = len(tracker.completed_chapter_records)
            
            # Mark as completed second time
            result = tracker.mark_chapter_completed(chapter_info, "/path/to/audio2.mp3")
            
            assert result is True
            assert len(tracker.completed_chapter_records) == first_count  # Should not increase
    
    def test_mark_chapter_failed(self):
        """Test marking a chapter as failed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_2_Test.txt",
                "volume_number": 1,
                "chapter_number": 2
            }
            
            error_message = "API connection failed"
            error_type = "api_error"
            
            result = tracker.mark_chapter_failed(chapter_info, error_message, error_type)
            
            assert result is True
            assert len(tracker.failed_chapter_records) == 1
            assert tracker.failed_chapter_records[0]["chapter_info"] == chapter_info
            assert tracker.failed_chapter_records[0]["error_message"] == error_message
            assert tracker.failed_chapter_records[0]["error_type"] == error_type
            assert tracker.failed_chapter_records[0]["retry_count"] == 0
            assert tracker.metadata["total_failed"] == 1
    
    def test_is_chapter_completed(self):
        """Test checking if a chapter is completed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            # Initially not completed
            assert tracker.is_chapter_completed(chapter_info) is False
            
            # Mark as completed
            tracker.mark_chapter_completed(chapter_info, "/path/to/audio.mp3")
            
            # Now should be completed
            assert tracker.is_chapter_completed(chapter_info) is True
    
    def test_is_chapter_failed(self):
        """Test checking if a chapter has failed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_2_Test.txt",
                "volume_number": 1,
                "chapter_number": 2
            }
            
            # Initially not failed
            assert tracker.is_chapter_failed(chapter_info) is False
            
            # Mark as failed
            tracker.mark_chapter_failed(chapter_info, "Test error")
            
            # Now should be failed
            assert tracker.is_chapter_failed(chapter_info) is True
    
    def test_get_next_chapter(self):
        """Test getting the next chapter to process."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            all_chapters = [
                {
                    "filename": "Chapter_1_Test.txt",
                    "volume_number": 1,
                    "chapter_number": 1
                },
                {
                    "filename": "Chapter_2_Test.txt",
                    "volume_number": 1,
                    "chapter_number": 2
                },
                {
                    "filename": "Chapter_3_Test.txt",
                    "volume_number": 1,
                    "chapter_number": 3
                }
            ]
            
            # First chapter should be next
            next_chapter = tracker.get_next_chapter(all_chapters)
            assert next_chapter == all_chapters[0]
            
            # Mark first chapter as completed
            tracker.mark_chapter_completed(all_chapters[0], "/path/to/audio1.mp3")
            
            # Second chapter should be next
            next_chapter = tracker.get_next_chapter(all_chapters)
            assert next_chapter == all_chapters[1]
            
            # Mark second chapter as failed
            tracker.mark_chapter_failed(all_chapters[1], "Test error")
            
            # Third chapter should be next
            next_chapter = tracker.get_next_chapter(all_chapters)
            assert next_chapter == all_chapters[2]
            
            # Mark all chapters as completed/failed
            tracker.mark_chapter_completed(all_chapters[2], "/path/to/audio3.mp3")
            
            # No more chapters
            next_chapter = tracker.get_next_chapter(all_chapters)
            assert next_chapter is None
    
    def test_get_failed_chapters_for_retry(self):
        """Test getting failed chapters for retry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            # Mark chapter as failed
            tracker.mark_chapter_failed(chapter_info, "Test error")
            
            # Should be available for retry
            retry_chapters = tracker.get_failed_chapters_for_retry()
            assert len(retry_chapters) == 1
            assert retry_chapters[0] == chapter_info
            
            # Mark same chapter as failed again (simulating retry failure)
            tracker.mark_chapter_failed(chapter_info, "Test error again")
            
            # Should still be available for retry (retry_count < max_retries)
            retry_chapters = tracker.get_failed_chapters_for_retry(max_retries=3)
            assert len(retry_chapters) == 1
            
            # Should not be available if max_retries is 1
            retry_chapters = tracker.get_failed_chapters_for_retry(max_retries=1)
            assert len(retry_chapters) == 0
    
    def test_get_progress_summary(self):
        """Test getting progress summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            # Add some test data
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            tracker.mark_chapter_completed(chapter_info, "/path/to/audio.mp3")
            tracker.mark_chapter_failed({
                "filename": "Chapter_2_Test.txt",
                "volume_number": 1,
                "chapter_number": 2
            }, "Test error")
            
            summary = tracker.get_progress_summary()
            
            assert summary["total_completed"] == 1
            assert summary["total_failed"] == 1
            assert summary["last_completed_chapter"] == "Chapter_1_Test.txt"
            assert "total_audio_size_bytes" in summary
            assert "total_audio_size_mb" in summary
    
    def test_reset_progress(self):
        """Test resetting progress."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            # Add some test data
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            tracker.mark_chapter_completed(chapter_info, "/path/to/audio.mp3")
            tracker.mark_chapter_failed(chapter_info, "Test error")
            
            # Verify data exists
            assert len(tracker.completed_chapter_records) == 1
            assert len(tracker.failed_chapter_records) == 1
            
            # Reset progress
            result = tracker.reset_progress()
            
            assert result is True
            assert len(tracker.completed_chapter_records) == 0
            assert len(tracker.failed_chapter_records) == 0
            assert tracker.metadata == {}
    
    def test_clear_failed_chapters(self):
        """Test clearing failed chapters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            # Add failed chapter
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            tracker.mark_chapter_failed(chapter_info, "Test error")
            assert len(tracker.failed_chapter_records) == 1
            
            # Clear failed chapters
            result = tracker.clear_failed_chapters()
            
            assert result is True
            assert len(tracker.failed_chapter_records) == 0
            assert tracker.metadata["total_failed"] == 0
    
    def test_export_progress_report(self):
        """Test exporting progress report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            # Add test data
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            tracker.mark_chapter_completed(chapter_info, "/path/to/audio.mp3")
            
            # Export report
            report_path = tracker.export_progress_report()
            
            assert Path(report_path).exists()
            
            # Verify report content
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            assert "progress_summary" in report
            assert "completed_chapters" in report
            assert "failed_chapters" in report
            assert "metadata" in report
            assert report["progress_summary"]["total_completed"] == 1
    
    def test_export_progress_report_custom_path(self):
        """Test exporting progress report to custom path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            custom_path = Path(temp_dir) / "custom_report.json"
            report_path = tracker.export_progress_report(str(custom_path))
            
            assert report_path == str(custom_path)
            assert custom_path.exists()
    
    def test_get_chapter_id(self):
        """Test chapter ID generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            chapter_id = tracker._get_chapter_id(chapter_info)
            expected_id = "01_001_Chapter_1_Test.txt"
            
            assert chapter_id == expected_id
    
    def test_get_retry_count(self):
        """Test retry count calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            # Initially no retries
            retry_count = tracker._get_retry_count(chapter_info)
            assert retry_count == 0
            
            # Mark as failed multiple times
            tracker.mark_chapter_failed(chapter_info, "Error 1")
            tracker.mark_chapter_failed(chapter_info, "Error 2")
            
            retry_count = tracker._get_retry_count(chapter_info)
            assert retry_count == 2
    
    def test_file_io_errors(self):
        """Test handling of file I/O errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            # Mock file write failure
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = tracker.mark_chapter_completed(chapter_info, "/path/to/audio.mp3")
                assert result is False
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid JSON file
            progress_file = Path(temp_dir) / "progress.json"
            with open(progress_file, 'w') as f:
                f.write("invalid json content")
            
            # Should initialize with empty data
            tracker = ProgressTracker(temp_dir)
            assert tracker.completed_chapter_records == []
            assert tracker.failed_chapter_records == []
            assert tracker.metadata == {}


class TestProgressTrackerProject:
    """Test cases for ProgressTracker class with Project-based initialization."""
    
    def setup_method(self):
        """Set up mock Project object for testing."""
        # Create a mock Project object
        self.mock_project = MagicMock()
        self.mock_project.project_name = "test_project"
        self.mock_project.get_processing_config.return_value = {
            'tracking': {
                'retry_attempts': 5,
                'retry_delay_seconds': 60,
                'track_audio_file_sizes': True,
                'track_processing_times': True,
                'auto_backup_progress': True,
                'backup_interval_hours': 12,
                'error_categorization': True,
                'detailed_error_logging': True
            }
        }
    
    def test_project_initialization(self):
        """Test progress tracker initialization with Project object."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the tracking directory setup
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                tracker = ProgressTracker(self.mock_project)
                
                assert tracker.tracking_directory == Path(temp_dir)
                assert tracker.completed_chapter_records == []
                assert tracker.failed_chapter_records == []
                assert tracker.metadata == {}
                assert tracker.is_project_based() is True
                assert tracker.get_project_name() == "test_project"
    
    def test_project_initialization_with_custom_config(self):
        """Test Project initialization with custom tracking configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Update mock project with custom tracking config
            self.mock_project.get_processing_config.return_value = {
                'tracking': {
                    'retry_attempts': 10,
                    'retry_delay_seconds': 120,
                    'track_audio_file_sizes': False,
                    'auto_backup_progress': False
                }
            }
            
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                tracker = ProgressTracker(self.mock_project)
                
                config = tracker.get_tracking_config()
                assert config['retry_attempts'] == 10
                assert config['retry_delay_seconds'] == 120
                assert config['track_audio_file_sizes'] is False
                assert config['auto_backup_progress'] is False
    
    def test_project_utility_methods(self):
        """Test Project-based utility methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                tracker = ProgressTracker(self.mock_project)
                
                # Test utility methods
                assert tracker.is_project_based() is True
                assert tracker.get_project_name() == "test_project"
                
                tracking_info = tracker.get_tracking_info()
                assert tracking_info['initialization_mode'] == 'project'
                assert tracking_info['project_name'] == 'test_project'
                assert 'tracking_config' in tracking_info
    
    def test_project_folder_creation(self):
        """Test that project-specific tracking folder is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the project tracking directory setup
            project_tracking_dir = Path(temp_dir) / "test_project"
            
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = project_tracking_dir
                
                tracker = ProgressTracker(self.mock_project)
                
                # Verify the project-specific directory is used
                assert tracker.tracking_directory == project_tracking_dir
                assert tracker.tracking_directory.name == "test_project"
    
    def test_project_config_fallback(self):
        """Test fallback to default config when project config fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock project to raise exception when getting config
            self.mock_project.get_processing_config.side_effect = Exception("Config error")
            
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                tracker = ProgressTracker(self.mock_project)
                
                # Should fall back to default config
                config = tracker.get_tracking_config()
                assert config['retry_attempts'] == 3  # Default value
                assert config['retry_delay_seconds'] == 30  # Default value


class TestProgressTrackerDualMode:
    """Unit tests comparing legacy and Project-based initialization modes."""
    
    def test_legacy_vs_project_initialization(self):
        """Test that both initialization modes work correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test legacy initialization
            legacy_tracker = ProgressTracker(temp_dir)
            
            # Create mock project for project initialization
            mock_project = MagicMock()
            mock_project.project_name = "test_project"
            mock_project.get_processing_config.return_value = {
                'tracking': {
                    'retry_attempts': 3,
                    'retry_delay_seconds': 30,
                    'track_audio_file_sizes': True,
                    'track_processing_times': True,
                    'auto_backup_progress': False,
                    'backup_interval_hours': 6,
                    'error_categorization': True,
                    'detailed_error_logging': True
                }
            }
            
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                project_tracker = ProgressTracker(mock_project)
                
                # Both should have same tracking directory (in this test)
                assert legacy_tracker.tracking_directory == project_tracker.tracking_directory
                
                # But different initialization modes
                assert legacy_tracker.is_project_based() is False
                assert project_tracker.is_project_based() is True
                
                assert legacy_tracker.get_project_name() is None
                assert project_tracker.get_project_name() == "test_project"
    
    def test_tracking_config_comparison(self):
        """Test tracking config for both initialization modes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Legacy mode
            legacy_tracker = ProgressTracker(temp_dir)
            legacy_config = legacy_tracker.get_tracking_config()
            
            # Project mode
            mock_project = MagicMock()
            mock_project.project_name = "test_project"
            mock_project.get_processing_config.return_value = {
                'tracking': {
                    'retry_attempts': 3,
                    'retry_delay_seconds': 30,
                    'track_audio_file_sizes': True,
                    'track_processing_times': True,
                    'auto_backup_progress': False,
                    'backup_interval_hours': 6,
                    'error_categorization': True,
                    'detailed_error_logging': True
                }
            }
            
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                project_tracker = ProgressTracker(mock_project)
                project_config = project_tracker.get_tracking_config()
                
                # Same config values, different modes
                assert legacy_config['retry_attempts'] == project_config['retry_attempts']
                assert legacy_config['retry_delay_seconds'] == project_config['retry_delay_seconds']
                
                # Different initialization modes
                legacy_info = legacy_tracker.get_tracking_info()
                project_info = project_tracker.get_tracking_info()
                
                assert legacy_info['initialization_mode'] == 'legacy'
                assert project_info['initialization_mode'] == 'project'
    
    def test_custom_config_project_mode(self):
        """Test that Project mode uses custom config from project settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock project with custom tracking config
            mock_project = MagicMock()
            mock_project.project_name = "custom_project"
            mock_project.get_processing_config.return_value = {
                'tracking': {
                    'retry_attempts': 7,
                    'retry_delay_seconds': 90,
                    'track_audio_file_sizes': False,
                    'auto_backup_progress': True,
                    'backup_interval_hours': 24
                }
            }
            
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                tracker = ProgressTracker(mock_project)
                
                config = tracker.get_tracking_config()
                assert config['retry_attempts'] == 7
                assert config['retry_delay_seconds'] == 90
                assert config['track_audio_file_sizes'] is False
                assert config['auto_backup_progress'] is True
                assert config['backup_interval_hours'] == 24
                
                assert tracker.is_project_based() is True
                assert tracker.get_project_name() == "custom_project"
                
                tracking_info = tracker.get_tracking_info()
                assert tracking_info['initialization_mode'] == 'project'
                assert tracking_info['project_name'] == 'custom_project'


class TestProgressTrackerBackwardCompatibility:
    """Unit tests ensuring backward compatibility with existing code."""
    
    def test_existing_code_compatibility(self):
        """Test that existing code using string initialization still works."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # This is exactly how existing code would initialize the tracker
            tracker = ProgressTracker(temp_dir)
            
            # Should work exactly as before
            assert tracker.tracking_directory == Path(temp_dir)
            assert tracker.is_project_based() is False
            assert tracker.get_project_name() is None
            
            # Test basic functionality still works
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            result = tracker.mark_chapter_completed(chapter_info, "/path/to/audio.mp3")
            assert result is True
            assert len(tracker.completed_chapter_records) == 1
    
    def test_existing_code_with_defaults(self):
        """Test that existing code using default tracking directory still works."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # This is how existing code might initialize with defaults
            tracker = ProgressTracker(temp_dir)
            
            # Should use default tracking config
            config = tracker.get_tracking_config()
            assert config['retry_attempts'] == 3
            assert config['retry_delay_seconds'] == 30
            assert tracker.is_project_based() is False
    
    def test_retry_configuration_usage(self):
        """Test that retry configuration is used from tracking config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test legacy mode uses default config
            legacy_tracker = ProgressTracker(temp_dir)
            retry_chapters = legacy_tracker.get_failed_chapters_for_retry()
            # Should use default max_retries (3)
            
            # Test project mode uses project config
            mock_project = MagicMock()
            mock_project.project_name = "test_project"
            mock_project.get_processing_config.return_value = {
                'tracking': {
                    'retry_attempts': 5
                }
            }
            
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                project_tracker = ProgressTracker(mock_project)
                
                # Add a failed chapter
                chapter_info = {
                    "filename": "Chapter_1_Test.txt",
                    "volume_number": 1,
                    "chapter_number": 1
                }
                project_tracker.mark_chapter_failed(chapter_info, "Test error")
                
                # Should use project config max_retries (5)
                retry_chapters = project_tracker.get_failed_chapters_for_retry()
                assert len(retry_chapters) == 1  # Should be available for retry


if __name__ == "__main__":
    # Run the tests if this file is executed directly
    pytest.main([__file__, "-v"])
