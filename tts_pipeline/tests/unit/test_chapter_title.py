"""Unit tests for chapter title resolution from formatted text."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.chapter_title import (
    find_chapter_text_file,
    parse_chapter_header_line,
    read_chapter_title_from_file,
    resolve_chapter_title,
    title_from_filename_fallback,
)


class TestChapterTitle(unittest.TestCase):
    def test_parse_chapter_header_line(self):
        self.assertEqual(
            parse_chapter_header_line("Chapter 215: Jenna's Worry"),
            (215, "Jenna's Worry"),
        )
        self.assertEqual(
            parse_chapter_header_line("  Chapter 1: Crimson  "),
            (1, "Crimson"),
        )
        self.assertIsNone(parse_chapter_header_line("Lord of Mysteries 2"))

    def test_read_and_resolve_from_formatted_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vol = root / "Volume_2_Light_Chaser"
            vol.mkdir()
            chapter = vol / "Chapter_215_Jenna's_Worry.txt"
            chapter.write_text(
                "Lord of Mysteries 2: Circle of Inevitability\n"
                "Chapter 215: Jenna's Worry\n"
                "Body text here.\n",
                encoding="utf-8",
            )

            self.assertEqual(read_chapter_title_from_file(chapter, 215), "Jenna's Worry")

            found = find_chapter_text_file(
                root,
                chapter_number=215,
                volume_number=2,
                chapter_pattern=r"Chapter_(\d+)_",
                volume_pattern=r"Volume_(\d+)_",
            )
            self.assertEqual(found, chapter)

            title = resolve_chapter_title(
                root,
                chapter_number=215,
                volume_number=2,
                chapter_pattern=r"Chapter_(\d+)_",
                volume_pattern=r"Volume_(\d+)_",
                filename_fallback="Chapter_215_Jenna_s_Worry.mp4",
            )
            self.assertEqual(title, "Jenna's Worry")

    def test_filename_fallback_loses_apostrophe_when_underscored(self):
        fb = title_from_filename_fallback("Chapter_215_Jenna's_Worry.mp4", 215)
        self.assertEqual(fb, "Jenna's Worry")
        bad = title_from_filename_fallback("Chapter_215_Jenna_s_Worry.mp4", 215)
        self.assertEqual(bad, "Jenna s Worry")


if __name__ == "__main__":
    unittest.main()
