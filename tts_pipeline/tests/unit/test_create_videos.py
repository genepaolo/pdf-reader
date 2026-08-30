"""
Unit tests for create_videos.py audio-path resolution.

The audio files on disk can have drifted names (older Azure runs sanitized
special characters to '_' and truncated long titles to ~40 chars), so
get_audio_file_path must fall back to chapter-number matching.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from create_videos import VideoCreator


def make_creator(tmp_path):
    project = MagicMock()
    project.project_name = "test_project"
    project.processing_config = {
        "output_directory": str(tmp_path),
        "video": {"enabled": True, "output_directory": str(tmp_path / "video")},
    }
    project.get_processing_config.return_value = project.processing_config
    project.get_input_directory.return_value = tmp_path / "input"
    return VideoCreator(project, preview_mode=True)


@pytest.fixture
def vol(tmp_path):
    d = tmp_path / "Volume_3_Conspirer"
    d.mkdir()
    return d


class TestGetAudioFilePath:
    def test_exact_name_match(self, tmp_path, vol):
        (vol / "Chapter_351_Killing_Intent.mp3").write_bytes(b"x")
        vc = make_creator(tmp_path)
        chapter = {
            "filename": "Chapter_351_Killing_Intent.txt",
            "volume_name": "Volume_3_Conspirer",
            "chapter_number": 351,
        }
        assert vc.get_audio_file_path(chapter).name == "Chapter_351_Killing_Intent.mp3"

    def test_fallback_sanitized_truncated_name(self, tmp_path, vol):
        # disk name: sanitized + truncated; text name: full with apostrophe
        (vol / "Chapter_357_Monette_s_True_Identity.mp3").write_bytes(b"x")
        vc = make_creator(tmp_path)
        chapter = {
            "filename": "Chapter_357_Monette's_True_Identity.txt",
            "volume_name": "Volume_3_Conspirer",
            "chapter_number": 357,
        }
        assert vc.get_audio_file_path(chapter).name == "Chapter_357_Monette_s_True_Identity.mp3"

    def test_fallback_does_not_cross_match_prefix_numbers(self, tmp_path, vol):
        # Chapter_35_* must not match Chapter_357_*
        (vol / "Chapter_357_Other.mp3").write_bytes(b"x")
        vc = make_creator(tmp_path)
        chapter = {
            "filename": "Chapter_35_Something.txt",
            "volume_name": "Volume_3_Conspirer",
            "chapter_number": 35,
        }
        assert vc.get_audio_file_path(chapter) is None

    def test_missing_audio_returns_none(self, tmp_path, vol):
        vc = make_creator(tmp_path)
        chapter = {
            "filename": "Chapter_999_Nope.txt",
            "volume_name": "Volume_3_Conspirer",
            "chapter_number": 999,
        }
        assert vc.get_audio_file_path(chapter) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
