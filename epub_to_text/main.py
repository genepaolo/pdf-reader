#!/usr/bin/env python3
"""
EPUB to Text converter entrypoint.
"""

import argparse
import sys
from pathlib import Path

from epub_converter import EpubConverter


def validate_input_file(epub_path: str) -> bool:
    path = Path(epub_path)
    if not path.exists():
        print(f"ERROR: File does not exist: {epub_path}")
        return False
    if not path.is_file():
        print(f"ERROR: Not a file: {epub_path}")
        return False
    if path.suffix.lower() != ".epub":
        print(f"ERROR: Expected .epub file, got: {path.suffix}")
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert EPUB to TTS-ready text files in volume/chapter hierarchy."
    )
    parser.add_argument("epub_path", help="Path to .epub file")
    parser.add_argument(
        "-o",
        "--output",
        default="formatted_text",
        help="Output base directory (default: formatted_text)",
    )
    parser.add_argument(
        "-p",
        "--project-name",
        default=None,
        help="Project folder name (default: EPUB file stem)",
    )
    parser.add_argument(
        "--inspect-only",
        action="store_true",
        help="Only print detected hierarchy; do not write files",
    )
    parser.add_argument(
        "--volume-map",
        default=None,
        help="JSON file with chapter ranges per volume (default: volume_map.json beside EPUB or parent folder)",
    )
    args = parser.parse_args()

    if not validate_input_file(args.epub_path):
        sys.exit(1)

    try:
        converter = EpubConverter(output_dir=args.output)
        converter.convert_epub(
            epub_path=args.epub_path,
            project_name=args.project_name,
            inspect_only=args.inspect_only,
            volume_map_path=args.volume_map,
        )
    except Exception as exc:
        print(f"ERROR: Conversion failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
