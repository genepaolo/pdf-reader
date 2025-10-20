"""
Unit tests for progress tracker functionality.
Tests Project-based initialization only.
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
                assert tracker.get_project_name() == "test_project"
                
                tracking_info = tracker.get_tracking_info()
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
    
    def test_mark_chapter_completed(self):
        """Test marking a chapter as completed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                tracker = ProgressTracker(self.mock_project)
            
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
    
    def test_mark_chapter_failed(self):
        """Test marking a chapter as failed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                tracker = ProgressTracker(self.mock_project)
            
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
    
    def test_get_progress_summary(self):
        """Test getting progress summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ProgressTracker, '_setup_project_tracking_directory') as mock_setup:
                mock_setup.return_value = Path(temp_dir)
                
                tracker = ProgressTracker(self.mock_project)
            
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
                
                assert tracker.get_project_name() == "custom_project"
                
                tracking_info = tracker.get_tracking_info()
                assert tracking_info['project_name'] == 'custom_project'


if __name__ == "__main__":
    # Run the tests if this file is executed directly
    pytest.main([__file__, "-v"])