"""
Regression tests for chapter discovery over the real lotm_book1 corpus.

Runs discovery through the actual Project config (formatted_text/lotm_book1,
Volume_N_Name layout) so it also guards the config <-> directory-layout
alignment. Skips cleanly if the corpus isn't present on this machine.
"""

import pytest
from pathlib import Path

from utils.project_manager import ProjectManager
from utils.file_organizer import ChapterFileOrganizer

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CORPUS = REPO_ROOT / "formatted_text" / "lotm_book1"

pytestmark = pytest.mark.skipif(
    not CORPUS.exists(), reason="formatted_text/lotm_book1 corpus not present"
)

EXPECTED_TOTAL_CHAPTERS = 1432
EXPECTED_VOLUMES = 9  # Volumes 1-8 + Side Stories (volume 9)


@pytest.fixture(scope="module")
def chapters():
    project = ProjectManager().load_project("lotm_book1")
    assert project is not None, "lotm_book1 project config failed to load"
    # Discovery resolves input relative to cwd; pin it via the absolute corpus path
    organizer = ChapterFileOrganizer(project)
    organizer.input_directory = CORPUS
    result = organizer.discover_chapters()
    assert result, "chapter discovery returned nothing"
    return result


class TestChapterCountRegression:
    def test_total_chapter_count(self, chapters):
        assert len(chapters) == EXPECTED_TOTAL_CHAPTERS, (
            f"Expected {EXPECTED_TOTAL_CHAPTERS} chapters, found {len(chapters)}"
        )

    def test_volume_count_and_range(self, chapters):
        volumes = {c["volume_number"] for c in chapters}
        assert len(volumes) == EXPECTED_VOLUMES, f"volumes found: {sorted(volumes)}"
        assert min(volumes) == 1
        assert max(volumes) == 9

    def test_sorted_by_volume_then_chapter(self, chapters):
        for prev, cur in zip(chapters, chapters[1:]):
            if cur["volume_number"] == prev["volume_number"]:
                assert cur["chapter_number"] > prev["chapter_number"], (
                    f"{prev['filename']} should sort before {cur['filename']}"
                )
            else:
                assert cur["volume_number"] > prev["volume_number"]

    def test_side_stories_assigned_volume_9(self, chapters):
        side = [c for c in chapters if "Side_Stories" in c["volume_name"]]
        assert side, "no Side Stories chapters found"
        assert all(c["volume_number"] == 9 for c in side)

    def test_chapter_files_valid(self, chapters):
        for chapter in chapters[:10]:
            file_path = Path(chapter["file_path"])
            assert file_path.exists() and file_path.is_file()
            assert file_path.stat().st_size > 0
            assert file_path.suffix.lower() == ".txt"

    def test_chapter_metadata_complete(self, chapters):
        required = [
            "filename", "file_path", "volume_number", "volume_name",
            "chapter_number", "chapter_title", "file_size", "is_readable",
        ]
        for chapter in chapters[:10]:
            for field in required:
                assert chapter.get(field) is not None, (
                    f"missing/None field '{field}' in {chapter['filename']}"
                )
            assert isinstance(chapter["volume_number"], int)
            assert isinstance(chapter["chapter_number"], int)
            assert chapter["is_readable"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
