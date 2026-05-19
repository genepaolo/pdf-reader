"""
Resolve chapter titles from formatted source text (not video/audio filenames).

Formatted chapter files are expected to include a header line:
  Chapter N: Full Title With Punctuation
(typically the second line; see epub_to_text output).
"""

import logging
import re
from pathlib import Path
from typing import Optional, Pattern, Tuple, Union

logger = logging.getLogger(__name__)

# Matches epub_to_text / CLAUDE.md chapter header line
CHAPTER_HEADER_RE = re.compile(r"^Chapter\s+(\d+)\s*:\s*(.+)\s*$", re.IGNORECASE)

DEFAULT_MAX_HEADER_LINES = 10


def parse_chapter_header_line(line: str) -> Optional[Tuple[int, str]]:
    """Parse 'Chapter N: Title' from a single line."""
    match = CHAPTER_HEADER_RE.match((line or "").strip())
    if not match:
        return None
    return int(match.group(1)), match.group(2).strip()


def read_chapter_title_from_file(
    file_path: Path,
    expected_chapter_number: Optional[int] = None,
    max_lines: int = DEFAULT_MAX_HEADER_LINES,
) -> Optional[str]:
    """
    Read the chapter title from the formatted text header.

    Scans the first ``max_lines`` lines for ``Chapter N: <title>``.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle):
                if index >= max_lines:
                    break
                parsed = parse_chapter_header_line(line)
                if not parsed:
                    continue
                chapter_number, title = parsed
                if expected_chapter_number is not None and chapter_number != expected_chapter_number:
                    continue
                if title:
                    return title
    except OSError as exc:
        logger.warning("Could not read chapter title from %s: %s", file_path, exc)
    return None


def _compile_pattern(pattern: Union[str, Pattern]) -> Pattern:
    return re.compile(pattern) if isinstance(pattern, str) else pattern


def volume_number_from_dir(dir_name: str, volume_pattern: Union[str, Pattern]) -> Optional[int]:
    """Extract volume number from a volume directory name."""
    if dir_name.lower() == "side_stories":
        return 9
    match = _compile_pattern(volume_pattern).match(dir_name)
    if match:
        return int(match.group(1))
    return None


def find_chapter_text_file(
    input_directory: Path,
    chapter_number: int,
    volume_number: int,
    chapter_pattern: Union[str, Pattern],
    volume_pattern: Union[str, Pattern],
) -> Optional[Path]:
    """Locate the source .txt for a chapter within a volume folder."""
    if not input_directory.exists():
        return None

    chapter_re = _compile_pattern(chapter_pattern)
    volume_re = _compile_pattern(volume_pattern)

    for volume_dir in input_directory.iterdir():
        if not volume_dir.is_dir():
            continue
        vol_num = volume_number_from_dir(volume_dir.name, volume_re)
        if vol_num != volume_number:
            continue
        for text_file in volume_dir.glob("*.txt"):
            match = chapter_re.search(text_file.name)
            if match and int(match.group(1)) == chapter_number:
                return text_file
    return None


def title_from_filename_fallback(
    filename: str,
    chapter_number: int,
    chapter_pattern: Optional[Union[str, Pattern]] = None,
) -> Optional[str]:
    """Last-resort title when source text is missing (underscores only)."""
    stem = Path(filename).stem
    if chapter_pattern is not None:
        match = _compile_pattern(chapter_pattern).search(stem)
        if match:
            suffix = stem[match.end() :].lstrip("_")
            return suffix.replace("_", " ").strip() or None
    match = re.match(rf"Chapter_{chapter_number}_(.+)", stem, re.IGNORECASE)
    if match:
        return match.group(1).replace("_", " ").strip() or None
    return None


def resolve_chapter_title(
    input_directory: Path,
    chapter_number: int,
    volume_number: int,
    chapter_pattern: Union[str, Pattern],
    volume_pattern: Union[str, Pattern],
    filename_fallback: Optional[str] = None,
) -> str:
    """
    Resolve display title for uploads/metadata for any project.

    Prefer the ``Chapter N: …`` line from formatted source text; fall back to
    filename parsing only when the source file or header is unavailable.
    """
    source_path = find_chapter_text_file(
        input_directory,
        chapter_number,
        volume_number,
        chapter_pattern,
        volume_pattern,
    )
    if source_path:
        title = read_chapter_title_from_file(source_path, chapter_number)
        if title:
            return title
        logger.warning(
            "Chapter %s source %s has no parseable header; using filename fallback",
            chapter_number,
            source_path,
        )

    if filename_fallback:
        fallback = title_from_filename_fallback(
            filename_fallback, chapter_number, chapter_pattern
        )
        if fallback:
            return fallback

    logger.warning(
        "No title found for chapter %s (volume %s); using generic label",
        chapter_number,
        volume_number,
    )
    return f"Chapter {chapter_number}"
