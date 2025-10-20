"""
Regression test to verify chapter count hasn't changed.
This test ensures the chapter discovery system consistently finds the expected number of chapters.
"""

import pytest
import sys
import os
from pathlib import Path

# Add the utils directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / "utils"))

from file_organizer import ChapterFileOrganizer


class TestChapterCountRegression:
    """Regression tests for chapter count verification."""
    
    def test_chapter_count_consistency(self):
        """
        Test that chapter discovery consistently finds the expected number of chapters.
        This is a critical regression test to ensure nothing has broken.
        """
        # Initialize the file organizer with the actual extracted text directory
        # Handle both running from tts_pipeline/ and from root directory
        import os
        current_dir = os.getcwd()
        if current_dir.endswith('tts_pipeline'):
            # Running from tts_pipeline/
            input_path = "../extracted_text/lotm_book1"
        else:
            # Running from root directory
            input_path = "extracted_text/lotm_book1"
        
        organizer = ChapterFileOrganizer(input_path)
        
        # Discover all chapters
        chapters = organizer.discover_chapters()
        
        # Expected results (update these if the source data changes)
        expected_total_chapters = 1432
        expected_volumes = 9  # Volumes 1-8 + Side_Stories (volume 9)
        expected_side_stories_included = True
        
        # Verify total chapter count
        assert len(chapters) == expected_total_chapters, \
            f"Expected {expected_total_chapters} chapters, but found {len(chapters)}"
        
        # Verify volume count
        volumes = set(chapter['volume_number'] for chapter in chapters)
        assert len(volumes) == expected_volumes, \
            f"Expected {expected_volumes} volumes, but found {len(volumes)}: {sorted(volumes)}"
        
        # Verify Side_Stories is included
        side_stories_volume = 9
        assert side_stories_volume in volumes, \
            f"Expected volume {side_stories_volume} (Side_Stories) to be present"
        
        # Verify volume range
        assert min(volumes) == 1, f"Expected minimum volume to be 1, but found {min(volumes)}"
        assert max(volumes) == 9, f"Expected maximum volume to be 9, but found {max(volumes)}"
        
        # Verify chapters are properly sorted
        for i in range(1, len(chapters)):
            current = chapters[i]
            previous = chapters[i-1]
            
            # Check that chapters are sorted by volume first, then by chapter number
            if current['volume_number'] == previous['volume_number']:
                assert current['chapter_number'] > previous['chapter_number'], \
                    f"Chapters not properly sorted: {previous['filename']} should come before {current['filename']}"
            else:
                assert current['volume_number'] > previous['volume_number'], \
                    f"Volumes not properly sorted: Volume {previous['volume_number']} should come before Volume {current['volume_number']}"
    
    def test_side_stories_volume_assignment(self):
        """Test that Side_Stories is correctly assigned as volume 9."""
        # Handle both running from tts_pipeline/ and from root directory
        import os
        current_dir = os.getcwd()
        if current_dir.endswith('tts_pipeline'):
            # Running from tts_pipeline/
            input_path = "../extracted_text/lotm_book1"
        else:
            # Running from root directory
            input_path = "extracted_text/lotm_book1"
        
        organizer = ChapterFileOrganizer(input_path)
        chapters = organizer.discover_chapters()
        
        # Find Side_Stories chapters
        side_stories_chapters = [c for c in chapters if c['volume_name'] == 'Side_Stories']
        
        assert len(side_stories_chapters) > 0, "No Side_Stories chapters found"
        
        # Verify all Side_Stories chapters have volume number 9
        for chapter in side_stories_chapters:
            assert chapter['volume_number'] == 9, \
                f"Side_Stories chapter {chapter['filename']} should have volume number 9, but has {chapter['volume_number']}"
    
    def test_chapter_file_validation(self):
        """Test that all discovered chapters are valid text files."""
        # Handle both running from tts_pipeline/ and from root directory
        import os
        current_dir = os.getcwd()
        if current_dir.endswith('tts_pipeline'):
            # Running from tts_pipeline/
            input_path = "../extracted_text/lotm_book1"
        else:
            # Running from root directory
            input_path = "extracted_text/lotm_book1"
        
        organizer = ChapterFileOrganizer(input_path)
        chapters = organizer.discover_chapters()
        
        # Check first few chapters for validation
        for chapter in chapters[:10]:  # Test first 10 chapters
            file_path = Path(chapter['file_path'])
            
            # Verify file exists and is readable
            assert file_path.exists(), f"Chapter file does not exist: {chapter['file_path']}"
            assert file_path.is_file(), f"Chapter path is not a file: {chapter['file_path']}"
            assert os.access(file_path, os.R_OK), f"Chapter file is not readable: {chapter['file_path']}"
            
            # Verify file has content
            assert file_path.stat().st_size > 0, f"Chapter file is empty: {chapter['file_path']}"
            
            # Verify file extension
            assert file_path.suffix.lower() == '.txt', f"Chapter file is not a .txt file: {chapter['file_path']}"
    
    def test_chapter_metadata_completeness(self):
        """Test that all chapters have complete metadata."""
        # Handle both running from tts_pipeline/ and from root directory
        import os
        current_dir = os.getcwd()
        if current_dir.endswith('tts_pipeline'):
            # Running from tts_pipeline/
            input_path = "../extracted_text/lotm_book1"
        else:
            # Running from root directory
            input_path = "extracted_text/lotm_book1"
        
        organizer = ChapterFileOrganizer(input_path)
        chapters = organizer.discover_chapters()
        
        required_fields = [
            'filename', 'file_path', 'volume_number', 'volume_name',
            'chapter_number', 'chapter_title', 'file_size', 'is_readable'
        ]
        
        for chapter in chapters[:10]:  # Test first 10 chapters
            for field in required_fields:
                assert field in chapter, f"Chapter missing required field '{field}': {chapter['filename']}"
                assert chapter[field] is not None, f"Chapter field '{field}' is None: {chapter['filename']}"
            
            # Verify specific field types and values
            assert isinstance(chapter['volume_number'], int), f"volume_number should be int: {chapter['filename']}"
            assert isinstance(chapter['chapter_number'], int), f"chapter_number should be int: {chapter['filename']}"
            assert chapter['volume_number'] >= 1, f"volume_number should be >= 1: {chapter['filename']}"
            assert chapter['chapter_number'] >= 1, f"chapter_number should be >= 1: {chapter['filename']}"
            assert chapter['is_readable'] is True, f"is_readable should be True: {chapter['filename']}"


if __name__ == "__main__":
    # Run the tests if this file is executed directly
    pytest.main([__file__, "-v"])
