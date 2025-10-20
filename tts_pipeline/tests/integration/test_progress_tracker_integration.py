"""
Integration tests for progress tracker with file organizer.
"""

import tempfile
import json
from pathlib import Path
from unittest.mock import patch
import pytest

from utils.progress_tracker import ProgressTracker
from utils.file_organizer import ChapterFileOrganizer


class TestProgressTrackerIntegration:
    """Integration tests for ProgressTracker with real file operations."""
    
    def test_full_workflow_simulation(self):
        """Test a complete workflow simulation with progress tracking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock chapter data
            mock_chapters = [
                {
                    "filename": "Chapter_1_Crimson.txt",
                    "file_path": "/mock/path/Chapter_1_Crimson.txt",
                    "volume_number": 1,
                    "volume_name": "1___VOLUME_1___CLOWN",
                    "chapter_number": 1,
                    "chapter_title": "Crimson",
                    "file_size": 1500,
                    "is_readable": True
                },
                {
                    "filename": "Chapter_2_New_Job.txt",
                    "file_path": "/mock/path/Chapter_2_New_Job.txt",
                    "volume_number": 1,
                    "volume_name": "1___VOLUME_1___CLOWN",
                    "chapter_number": 2,
                    "chapter_title": "New Job",
                    "file_size": 1800,
                    "is_readable": True
                },
                {
                    "filename": "Chapter_3_Sequence.txt",
                    "file_path": "/mock/path/Chapter_3_Sequence.txt",
                    "volume_number": 1,
                    "volume_name": "1___VOLUME_1___CLOWN",
                    "chapter_number": 3,
                    "chapter_title": "Sequence",
                    "file_size": 2000,
                    "is_readable": True
                }
            ]
            
            # Initialize progress tracker
            tracker = ProgressTracker(temp_dir)
            
            # Simulate processing workflow
            for i, chapter in enumerate(mock_chapters):
                # Get next chapter
                next_chapter = tracker.get_next_chapter(mock_chapters)
                assert next_chapter == chapter
                
                # Simulate processing success for first two chapters
                if i < 2:
                    audio_file = f"/output/audio_{chapter['filename'].replace('.txt', '.mp3')}"
                    
                    # Mock audio file creation
                    with patch('pathlib.Path.stat') as mock_stat:
                        mock_stat.return_value.st_size = 5000000  # 5MB audio file
                        
                        success = tracker.mark_chapter_completed(chapter, audio_file)
                        assert success is True
                
                # Simulate processing failure for third chapter
                else:
                    success = tracker.mark_chapter_failed(
                        chapter, 
                        "Azure TTS API rate limit exceeded",
                        "api_error"
                    )
                    assert success is True
            
            # Verify final state
            summary = tracker.get_progress_summary()
            assert summary["total_completed"] == 2
            assert summary["total_failed"] == 1
            assert summary["last_completed_chapter"] == "Chapter_2_New_Job.txt"
            
            # Verify next chapter is None (all processed)
            next_chapter = tracker.get_next_chapter(mock_chapters)
            assert next_chapter is None
            
            # Check failed chapters for retry
            retry_chapters = tracker.get_failed_chapters_for_retry()
            assert len(retry_chapters) == 1
            assert retry_chapters[0]["filename"] == "Chapter_3_Sequence.txt"
    
    def test_resume_functionality(self):
        """Test resume functionality after interruption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_chapters = [
                {
                    "filename": "Chapter_1_Crimson.txt",
                    "file_path": "/mock/path/Chapter_1_Crimson.txt",
                    "volume_number": 1,
                    "volume_name": "1___VOLUME_1___CLOWN",
                    "chapter_number": 1,
                    "chapter_title": "Crimson",
                    "file_size": 1500,
                    "is_readable": True
                },
                {
                    "filename": "Chapter_2_New_Job.txt",
                    "file_path": "/mock/path/Chapter_2_New_Job.txt",
                    "volume_number": 1,
                    "volume_name": "1___VOLUME_1___CLOWN",
                    "chapter_number": 2,
                    "chapter_title": "New Job",
                    "file_size": 1800,
                    "is_readable": True
                }
            ]
            
            # First session: Process first chapter
            tracker1 = ProgressTracker(temp_dir)
            tracker1.mark_chapter_completed(mock_chapters[0], "/output/audio1.mp3")
            
            # Simulate session interruption (tracker1 goes out of scope)
            del tracker1
            
            # Second session: Resume processing
            tracker2 = ProgressTracker(temp_dir)
            
            # Should remember first chapter was completed
            assert tracker2.is_chapter_completed(mock_chapters[0]) is True
            assert tracker2.is_chapter_completed(mock_chapters[1]) is False
            
            # Next chapter should be the second one
            next_chapter = tracker2.get_next_chapter(mock_chapters)
            assert next_chapter == mock_chapters[1]
            
            # Process remaining chapter
            tracker2.mark_chapter_completed(mock_chapters[1], "/output/audio2.mp3")
            
            # Verify final state
            summary = tracker2.get_progress_summary()
            assert summary["total_completed"] == 2
    
    def test_progress_persistence(self):
        """Test that progress is properly persisted to files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1,
                "chapter_title": "Test Chapter"
            }
            
            # Mark chapter as completed
            tracker.mark_chapter_completed(chapter_info, "/path/to/audio.mp3")
            
            # Check that files were created
            progress_file = tracker.progress_file
            metadata_file = tracker.metadata_file
            
            assert progress_file.exists()
            assert metadata_file.exists()
            
            # Verify file contents
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            
            assert len(progress_data) == 1
            assert progress_data[0]["chapter_info"]["filename"] == "Chapter_1_Test.txt"
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            assert metadata["total_completed"] == 1
            assert metadata["last_completed_chapter"] == "Chapter_1_Test.txt"
    
    def test_error_recovery_and_retry(self):
        """Test error recovery and retry functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            chapter_info = {
                "filename": "Chapter_1_Test.txt",
                "volume_number": 1,
                "chapter_number": 1
            }
            
            # Simulate multiple failures with different error types
            tracker.mark_chapter_failed(chapter_info, "Network timeout", "network_error")
            tracker.mark_chapter_failed(chapter_info, "API rate limit", "api_error")
            
            # Check retry count
            retry_count = tracker._get_retry_count(chapter_info)
            assert retry_count == 2
            
            # Should be available for retry
            retry_chapters = tracker.get_failed_chapters_for_retry(max_retries=3)
            assert len(retry_chapters) == 1
            
            # Simulate successful retry
            tracker.mark_chapter_completed(chapter_info, "/path/to/audio.mp3")
            
            # Should no longer be failed
            assert tracker.is_chapter_completed(chapter_info) is True
            assert tracker.is_chapter_failed(chapter_info) is False
    
    def test_progress_report_generation(self):
        """Test comprehensive progress report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            # Add mixed test data
            chapters = [
                {
                    "filename": "Chapter_1_Success.txt",
                    "volume_number": 1,
                    "chapter_number": 1
                },
                {
                    "filename": "Chapter_2_Failed.txt",
                    "volume_number": 1,
                    "chapter_number": 2
                },
                {
                    "filename": "Chapter_3_Success.txt",
                    "volume_number": 1,
                    "chapter_number": 3
                }
            ]
            
            # Mark chapters with different outcomes
            tracker.mark_chapter_completed(chapters[0], "/audio1.mp3")
            tracker.mark_chapter_failed(chapters[1], "Test error", "api_error")
            tracker.mark_chapter_completed(chapters[2], "/audio3.mp3")
            
            # Generate report
            report_path = tracker.export_progress_report()
            
            # Verify report content
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            assert "export_timestamp" in report
            assert "progress_summary" in report
            assert "completed_chapters" in report
            assert "failed_chapters" in report
            assert "metadata" in report
            
            # Verify summary data
            summary = report["progress_summary"]
            assert summary["total_completed"] == 2
            assert summary["total_failed"] == 1
            
            # Verify detailed data
            assert len(report["completed_chapters"]) == 2
            assert len(report["failed_chapters"]) == 1
    
    def test_large_dataset_handling(self):
        """Test progress tracker with a large number of chapters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            
            # Create many mock chapters
            large_chapter_list = []
            for i in range(100):
                chapter = {
                    "filename": f"Chapter_{i+1:03d}_Test.txt",
                    "volume_number": 1,
                    "chapter_number": i + 1
                }
                large_chapter_list.append(chapter)
            
            # Process every other chapter
            for i, chapter in enumerate(large_chapter_list):
                if i % 2 == 0:  # Even indices
                    tracker.mark_chapter_completed(chapter, f"/audio{i}.mp3")
                else:  # Odd indices
                    tracker.mark_chapter_failed(chapter, "Simulated error")
            
            # Verify summary
            summary = tracker.get_progress_summary()
            assert summary["total_completed"] == 50
            assert summary["total_failed"] == 50
            
            # Test getting next chapter (should be None since all are processed)
            next_chapter = tracker.get_next_chapter(large_chapter_list)
            assert next_chapter is None
            
            # Test performance of operations
            import time
            start_time = time.time()
            
            # Test is_chapter_completed performance
            for chapter in large_chapter_list[:10]:
                tracker.is_chapter_completed(chapter)
            
            elapsed = time.time() - start_time
            assert elapsed < 1.0  # Should be fast even with many chapters
