"""
Pytest configuration and shared fixtures for TTS pipeline tests.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
import json
from typing import Dict, Any, List
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure we can import from the project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test isolation."""
    temp_dir = tempfile.mkdtemp(prefix="tts_pipeline_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_chapter_content():
    """Sample chapter content for testing."""
    return """Chapter 1: The Beginning

This is a sample chapter for testing purposes. It contains enough text to generate a reasonable audio file that would be longer than 5 minutes when converted to speech.

The story begins in a small town where nothing much ever happens. The protagonist, a young person with dreams bigger than their circumstances, finds themselves at a crossroads in life.

This sample text is designed to be long enough to generate an audio file of at least 5 minutes when processed through a text-to-speech system, making it suitable for testing the audio validation requirements of the TTS pipeline."""


@pytest.fixture
def test_chapter_structure(temp_dir, sample_chapter_content):
    """Create a test directory structure with sample chapters."""
    structure = {
        "1___VOLUME_1___CLOWN": [
            "Chapter_1_Crimson.txt",
            "Chapter_2_Situation.txt", 
            "Chapter_3_Melissa.txt"
        ],
        "2___VOLUME_2___FACELESS": [
            "Chapter_214_Land_of_Hope.txt",
            "Chapter_215_Mrs._Sammer.txt"
        ],
        "Side_Stories": [
            "Chapter_1430_Test_Story.txt"
        ]
    }
    
    created_files = {}
    
    for volume, chapters in structure.items():
        volume_path = Path(temp_dir) / volume
        volume_path.mkdir(parents=True, exist_ok=True)
        
        for chapter in chapters:
            chapter_path = volume_path / chapter
            chapter_path.write_text(sample_chapter_content, encoding='utf-8')
            created_files[str(chapter_path)] = sample_chapter_content
    
    return {
        "temp_dir": temp_dir,
        "structure": structure,
        "files": created_files
    }


@pytest.fixture
def test_azure_config():
    """Test Azure configuration."""
    return {
        "voice_name": "en-US-JennyNeural",
        "output_format": "audio-24khz-160kbitrate-mono-mp3",
        "rate": "+0%",
        "pitch": "+0Hz",
        "max_text_length": 5000,
        "timeout_seconds": 300,
        "language": "en-US",
        "voice_gender": "male"
    }


@pytest.fixture
def test_processing_config():
    """Test processing configuration."""
    return {
        "input_directory": "./test_input",
        "output_directory": "./test_output",
        "min_audio_duration_minutes": 5,
        "max_text_length": 5000,
        "retry_attempts": 3,
        "retry_delay_seconds": 30,
        "log_level": "INFO",
        "chapter_pattern": "Chapter_\\d+_.*\\.txt$",
        "volume_pattern": "\\d+___VOLUME_\\d+___.*"
    }


@pytest.fixture
def test_env_vars():
    """Test environment variables."""
    return {
        "AZURE_SPEECH_KEY": "test_key_12345",
        "AZURE_SPEECH_REGION": "test-region",
        "AZURE_SPEECH_LANGUAGE": "en-US",
        "AZURE_SPEECH_VOICE_GENDER": "male"
    }


@pytest.fixture
def mock_audio_file(temp_dir):
    """Create a mock audio file for testing."""
    audio_file = Path(temp_dir) / "test_audio.mp3"
    # Create a minimal mock audio file (just text for testing)
    audio_file.write_text("Mock audio file content")
    return str(audio_file)


@pytest.fixture
def sample_progress_data():
    """Sample progress tracking data."""
    return {
        "current_volume": "1___VOLUME_1___CLOWN",
        "current_chapter": "Chapter_1_Crimson.txt",
        "last_processed": "2024-01-18T10:30:00Z",
        "total_chapters_found": 1432,
        "chapters_processed": 5,
        "chapters_failed": 0,
        "estimated_remaining": "45 hours"
    }


@pytest.fixture
def sample_completed_data():
    """Sample completed chapters data."""
    return {
        "Chapter_1_Crimson.txt": {
            "processed_date": "2024-01-18T10:30:00Z",
            "audio_file": "Chapter_1_Crimson.mp3",
            "duration_seconds": 420,
            "file_size_mb": 3.2,
            "volume": "1___VOLUME_1___CLOWN"
        }
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as a regression test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on directory."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "regression" in str(item.fspath):
            item.add_marker(pytest.mark.regression)
        
        # Add slow marker for performance tests
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.slow)
