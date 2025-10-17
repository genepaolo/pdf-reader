#!/usr/bin/env python3
"""
PDF to Text Converter - Volume-by-Volume Processing with Progress Bars

This script converts PDF files into organized, TTS-friendly text files by processing
one volume at a time with real-time progress tracking. It uses the PDF's document
outline (bookmarks) to automatically detect volume and chapter structure.

Key Features:
- Volume-by-volume processing for memory efficiency
- Real-time progress bars with estimated time remaining
- TTS-optimized output format with proper headers
- Comprehensive error handling and validation
- Smart folder organization (PDF_Name/Volume_Folders/Chapter_Files)

Usage Examples:
    # Basic conversion
    python main.py document.pdf
    
    # Custom output directory
    python main.py document.pdf -o my_output_folder
    
    # Convert Lord of the Mysteries book
    python main.py ../pdfs/lotm_book1.pdf -o ../extracted_text

Output Structure:
    extracted_text/
    ├── lotm_book1/                    # PDF name-based folder
    │   ├── Volume_1_Clown.txt        # Complete volume file
    │   └── 1_Clown/                  # Volume-specific folder
    │       ├── Chapter_1_Crimson.txt # Individual chapter files
    │       ├── Chapter_2_Nightmare.txt
    │       └── Chapter_3_Awakening.txt

Author: PDF-to-Audio Pipeline Team
Version: 2.0 (Cleaned and Optimized)
"""

import argparse
import sys
from pathlib import Path
from pdf_converter_clean import PDFConverter


def validate_input_file(pdf_path: str) -> bool:
    """
    Validate that the input file exists and is a PDF.
    
    Args:
        pdf_path (str): Path to the PDF file to validate
        
    Returns:
        bool: True if file is valid, False otherwise
        
    Raises:
        SystemExit: If file doesn't exist or isn't a PDF
    """
    input_path = Path(pdf_path)
    
    if not input_path.exists():
        print(f"ERROR: File '{pdf_path}' does not exist")
        print("   Please check the file path and try again.")
        return False
    
    if not input_path.is_file():
        print(f"ERROR: '{pdf_path}' is not a file")
        print("   Please provide a valid file path.")
        return False
    
    if input_path.suffix.lower() != '.pdf':
        print(f"ERROR: '{pdf_path}' is not a PDF file")
        print("   Please provide a file with .pdf extension.")
        return False
    
    return True


def main():
    """
    Main function that handles command-line arguments and starts the conversion process.
    
    This function:
    1. Parses command-line arguments
    2. Validates the input PDF file
    3. Initializes the PDF converter
    4. Starts the conversion process with progress tracking
    
    Command Line Arguments:
        pdf_path: Path to the PDF file to convert
        -o, --output: Output directory (default: "extracted_text")
        
    Example Usage:
        python main.py document.pdf
        python main.py document.pdf -o custom_output
    """
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(
        description="Convert PDF files to TTS-friendly organized text files with volume-by-volume processing",
        epilog="""
Examples:
  python main.py document.pdf                    # Convert to default output folder
  python main.py document.pdf -o my_output       # Convert to custom output folder
  python main.py ../pdfs/lotm_book1.pdf          # Convert from pdfs folder
  
The converter will:
  • Extract text using the PDF's document outline (bookmarks)
  • Process one volume at a time with progress bars
  • Create organized folder structure for TTS processing
  • Generate TTS-friendly headers for each chapter
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Define command-line arguments
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file you want to convert"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="extracted_text",
        help="Output directory where converted text files will be saved (default: extracted_text)"
    )
    
    # Parse command-line arguments
    args = parser.parse_args()
    
    # Validate input file
    print("Validating input file...")
    if not validate_input_file(args.pdf_path):
        sys.exit(1)
    
    print(f"SUCCESS: Input file validated: {args.pdf_path}")
    print(f"Output directory: {args.output}")
    print()
    
    # Initialize the PDF converter
    print("Initializing PDF converter...")
    try:
        converter = PDFConverter(args.output)
        print("SUCCESS: Converter initialized successfully")
    except Exception as e:
        print(f"ERROR: Error initializing converter: {e}")
        sys.exit(1)
    
    # Start the conversion process
    print("Starting PDF conversion...")
    print("   This may take a while for large documents.")
    print("   Progress bars will show real-time updates.")
    print()
    
    try:
        converter.convert_pdf(str(args.pdf_path))
        print()
        print("SUCCESS: Conversion completed successfully!")
        print(f"Check the '{args.output}' directory for your converted files.")
        
    except KeyboardInterrupt:
        print("\nWARNING: Conversion interrupted by user")
        print("   Partial files may have been created.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\nERROR: Error during conversion: {e}")
        print("   Please check the error message and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
