#!/usr/bin/env python3
"""
Text Formatter for TTS-Friendly Reading

This script reformats extracted text files to be more suitable for text-to-speech:
- Joins sentences broken across lines due to PDF page width
- Preserves paragraph breaks
- Maintains chapter structure
- Creates continuous paragraphs for natural speech flow

Usage:
    python tts_pipeline/scripts/format_text_for_tts.py --input extracted_text/lotm_book1 --output formatted_text/lotm_book1
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Optional
import re

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def setup_logging(level: str = "INFO"):
    """Set up logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def is_sentence_end(line: str) -> bool:
    """
    Check if a line ends with a sentence-ending punctuation.
    
    Args:
        line: Line to check
        
    Returns:
        True if line ends a sentence, False otherwise
    """
    line = line.strip()
    if not line:
        return False
    
    # Check for sentence-ending punctuation
    sentence_endings = ['.', '!', '?', '."', '!"', '?"', '."', '!"', '?"']
    return any(line.endswith(ending) for ending in sentence_endings)


def is_paragraph_break(lines: List[str], current_idx: int) -> bool:
    """
    Check if there should be a paragraph break at the current position.
    
    Args:
        lines: All lines in the file
        current_idx: Current line index
        
    Returns:
        True if this should be a paragraph break, False otherwise
    """
    if current_idx >= len(lines):
        return False
    
    current_line = lines[current_idx].strip()
    
    # Empty line indicates paragraph break
    if not current_line:
        return True
    
    # Check for dialogue or thought patterns that should start new paragraphs
    dialogue_patterns = [
        r'^"[^"]*$',  # Starts with quote
        r'^[A-Z][a-z]* said',  # "He said", "She said"
        r'^[A-Z][a-z]* thought',  # "He thought", "She thought"
        r'^[A-Z][a-z]* wondered',  # "He wondered", "She wondered"
    ]
    
    for pattern in dialogue_patterns:
        if re.match(pattern, current_line):
            return True
    
    return False


def format_chapter_text(lines: List[str]) -> List[str]:
    """
    Format chapter text for TTS-friendly reading.
    
    Args:
        lines: List of lines from the chapter file
        
    Returns:
        List of formatted lines
    """
    if not lines:
        return []
    
    formatted_lines = []
    current_paragraph = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines at the beginning
        if not line and not current_paragraph:
            continue
        
        # Handle chapter metadata (title, chapter number, etc.)
        if i < 3 and (line.startswith('Lord of the Mysteries') or 
                     line.startswith('Chapter') or 
                     line in ['Crimson']):
            formatted_lines.append(line)
            continue
        
        # If this is an empty line and we have content, it's a paragraph break
        if not line and current_paragraph:
            if current_paragraph:
                # Join the current paragraph and add it
                paragraph_text = ' '.join(current_paragraph).strip()
                formatted_lines.append(paragraph_text)
                formatted_lines.append('')  # Empty line for paragraph break
                current_paragraph = []
            continue
        
        # If this line should start a new paragraph and we have content
        if is_paragraph_break(lines, i) and current_paragraph:
            # Join the current paragraph and add it
            paragraph_text = ' '.join(current_paragraph).strip()
            formatted_lines.append(paragraph_text)
            formatted_lines.append('')  # Empty line for paragraph break
            current_paragraph = []
        
        # Add line to current paragraph (if it's not empty)
        if line:
            current_paragraph.append(line)
    
    # Add the last paragraph if it exists
    if current_paragraph:
        paragraph_text = ' '.join(current_paragraph).strip()
        formatted_lines.append(paragraph_text)
    
    return formatted_lines


def format_file(input_path: Path, output_path: Path) -> bool:
    """
    Format a single text file for TTS.
    
    Args:
        input_path: Path to input file
        output_path: Path to output file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove newlines and strip whitespace
        lines = [line.rstrip('\n\r') for line in lines]
        
        # Format the text
        formatted_lines = format_chapter_text(lines)
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write formatted text
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in formatted_lines:
                f.write(line + '\n')
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to format {input_path}: {e}")
        return False


def format_directory(input_dir: Path, output_dir: Path) -> int:
    """
    Format all text files in a directory structure.
    
    Args:
        input_dir: Input directory
        output_dir: Output directory
        
    Returns:
        Number of files successfully formatted
    """
    if not input_dir.exists():
        logging.error(f"Input directory does not exist: {input_dir}")
        return 0
    
    formatted_count = 0
    
    # Process all .txt files recursively
    for txt_file in input_dir.rglob('*.txt'):
        # Calculate relative path
        relative_path = txt_file.relative_to(input_dir)
        output_file = output_dir / relative_path
        
        logging.info(f"Formatting: {relative_path}")
        
        if format_file(txt_file, output_file):
            formatted_count += 1
        else:
            logging.error(f"Failed to format: {relative_path}")
    
    return formatted_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Format text files for TTS-friendly reading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Format a single directory
  python scripts/format_text_for_tts.py --input extracted_text/lotm_book1 --output formatted_text/lotm_book1
  
  # Format with debug logging
  python scripts/format_text_for_tts.py --input extracted_text/lotm_book1 --output formatted_text/lotm_book1 --log-level DEBUG
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input directory containing text files to format'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output directory for formatted text files'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    logging.info(f"Formatting text files from {input_path} to {output_path}")
    
    # Check if input is a file or directory
    if input_path.is_file():
        # Single file
        if format_file(input_path, output_path):
            formatted_count = 1
            logging.info(f"Successfully formatted: {input_path}")
        else:
            formatted_count = 0
            logging.error(f"Failed to format: {input_path}")
    else:
        # Directory
        formatted_count = format_directory(input_path, output_path)
    
    logging.info(f"Successfully formatted {formatted_count} files")
    
    if formatted_count == 0:
        logging.error("No files were formatted")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


