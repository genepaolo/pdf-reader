# PDF to Text Converter - Volume-by-Volume Processing

## Overview

The `pdf_to_txt` module is the first stage of a comprehensive PDF-to-Audio pipeline that converts PDF documents into organized, TTS-friendly text files. This streamlined module extracts text content from PDFs and structures it by volumes and chapters using the document's outline, processing one volume at a time with real-time progress tracking.

## Project Context

This module is part of a larger system that converts PDF documents into audiobooks:

```
PDF Document → [pdf_to_txt] → Organized Text Files → [tts_pipeline] → Audio Files
```

The `pdf_to_txt` module bridges the gap between raw PDF documents and structured text content ready for TTS processing.

## Key Features

### 🎯 **Volume-by-Volume Processing**
- Processes PDFs one volume at a time for better memory management
- Shows real-time progress bars with estimated time remaining
- Handles large documents efficiently without memory issues

### 📊 **Real-Time Progress Tracking**
- Dual progress bars showing both page and chapter completion
- Estimated time remaining (ETA) for long conversions
- Detailed status updates for each volume and chapter

### 📁 **Smart Folder Organization**
- Creates organized folder structure: `PDF_Name/Volume_Folders/Chapter_Files`
- Uses PDF's document outline (bookmarks) for accurate structure detection
- Generates TTS-friendly file names and headers

### 🔧 **Robust Error Handling**
- Comprehensive error handling for corrupted pages
- Fallback text extraction methods (pdfplumber + PyPDF2)
- Detailed error reporting and validation

## Module Components

### Core Files

#### 1. **main.py** - Command Line Interface
- **Purpose**: Simple, clean entry point for the converter
- **Features**:
  - Command-line argument parsing
  - Input validation (PDF file existence and format)
  - Output directory specification
  - Error handling and user feedback
- **Usage**: `python main.py input.pdf -o output_directory`

#### 2. **pdf_converter_clean.py** - Core Conversion Engine
- **Purpose**: Main conversion logic with volume-by-volume processing
- **Key Features**:
  - Document outline extraction and parsing
  - Volume-by-volume text extraction with progress tracking
  - TTS-optimized output formatting
  - Comprehensive error handling and validation
  - Safe filename generation for all operating systems
- **Classes**: `PDFConverter` (main converter class)

#### 3. **requirements.txt** - Dependencies
- **Purpose**: Lists required Python packages
- **Dependencies**:
  - PyPDF2 (3.0.1) - PDF text extraction and outline processing
  - pdfplumber (0.10.3) - Advanced PDF processing and text extraction
  - python-docx (1.1.0) - Document processing utilities

## How It Works

### 1. **Document Analysis**
- Extracts the PDF's document outline (bookmarks/table of contents)
- Identifies volume and chapter structure automatically
- Counts total pages and chapters for progress tracking

### 2. **Volume Processing**
- Processes one volume at a time to manage memory efficiently
- Extracts all pages for the current volume
- Creates both volume summary files and individual chapter files

### 3. **Chapter Organization**
- Organizes chapters within volume-specific folders
- Generates TTS-friendly headers for each chapter
- Validates chapter boundaries and content

### 4. **Progress Tracking**
- Shows real-time progress bars for pages and chapters
- Calculates estimated time remaining
- Provides detailed status updates

## Usage

### Basic Conversion
```bash
# Convert a PDF file to organized text files
python main.py path/to/your/document.pdf

# Specify custom output directory
python main.py path/to/your/document.pdf -o my_output_folder
```

### Example Output Structure
```
extracted_text/
├── lotm_book1/                    # PDF name-based folder
│   ├── Volume_1_Clown.txt        # Complete volume file
│   └── 1_Clown/                  # Volume-specific folder
│       ├── Chapter_1_Crimson.txt # Individual chapter files
│       ├── Chapter_2_Nightmare.txt
│       └── Chapter_3_Awakening.txt
```

### TTS-Friendly Output Format
Each chapter file includes optimized headers for text-to-speech:
```
Lord of the Mysteries
Chapter 1
Crimson

[Chapter content here...]
```

## Processing Flow

```
Input PDF
    ↓
[main.py] - Validate input and initialize converter
    ↓
[PDFConverter.__init__] - Set up output directory
    ↓
[convert_pdf] - Main conversion process
    ↓
[extract_text_chunked] - Get page count and outline
    ↓
[extract_outline] - Extract document structure
    ↓
[_parse_outline] - Parse outline recursively
    ↓
[process_pdf_by_volumes] - Process each volume
    ↓
[_process_volumes] - Volume-by-volume processing with progress
    ↓
Organized Text Files (Ready for TTS Pipeline)
```

## Integration with TTS Pipeline

The `pdf_to_txt` module serves as the foundation for the TTS pipeline:

1. **Output Structure**: Creates organized text files in `extracted_text/` directory
2. **File Format**: TTS-friendly format with proper headers and metadata
3. **Organization**: Volume/chapter structure that TTS pipeline can process selectively
4. **Quality**: Clean, formatted text optimized for speech synthesis

The TTS pipeline (`../tts_pipeline/`) then:
- Copies specific text files from `extracted_text/` to its `input/` directory
- Processes files in batches using various TTS services
- Tracks conversion progress and handles failures
- Generates organized audio files

## Error Handling

The module includes comprehensive error handling:

- **PDF Extraction Errors**: Automatic fallback between pdfplumber and PyPDF2
- **Outline Detection Failures**: Graceful fallback to single-file output
- **Page Extraction Errors**: Skip corrupted pages and continue processing
- **File System Errors**: Safe filename generation and directory creation
- **Memory Management**: Volume-by-volume processing prevents memory issues

## Progress Tracking Features

### Real-Time Progress Bars
```
Processing Volume 1:
  Pages:   [##########----------] 50.0% (125/250)
  Chapters: [#######-------------] 35.0% (7/20) ETA: 45s
```

### Status Updates
- Volume processing status
- Chapter completion counts
- Error reporting for failed pages/chapters
- Final summary with success/failure statistics

## Supported PDF Types

- **Novels and Books**: Automatic volume/chapter detection
- **Technical Documents**: Uses document outline structure
- **Multi-language Documents**: Handles various character encodings
- **Large Documents**: Efficient processing without memory issues

## Fallback Behavior

If the PDF doesn't have a proper outline structure:
- Creates a single `full_content.txt` file with all text
- Includes proper TTS-friendly headers
- Maintains text formatting and structure

## Performance Characteristics

- **Memory Efficient**: Processes one volume at a time
- **Progress Tracking**: Real-time feedback for long conversions
- **Error Resilient**: Continues processing even with corrupted pages
- **Fast Processing**: Optimized for large document conversion

## Troubleshooting

### Common Issues

1. **No outline found**: The PDF might not have bookmarks/table of contents
   - **Solution**: Module will create a single file with all content

2. **Text extraction errors**: Some PDFs may have complex formatting
   - **Solution**: Automatic fallback between pdfplumber and PyPDF2

3. **Memory issues**: Very large PDFs might cause memory problems
   - **Solution**: Volume-by-volume processing prevents this

4. **Encoding issues**: Special characters might not display correctly
   - **Solution**: UTF-8 encoding with ASCII fallbacks

### Getting Help

- Check the console output for detailed error messages
- Ensure your PDF has a proper document outline/bookmarks
- Verify the PDF file is not corrupted or password-protected
- Check that you have sufficient disk space for output files

## Dependencies and Requirements

- **Python 3.7+**
- **PyPDF2**: PDF text extraction and outline processing
- **pdfplumber**: Advanced PDF processing and text extraction
- **python-docx**: Document processing utilities

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run conversion
python main.py your_document.pdf
```

## Future Enhancements

Potential improvements for the module:

- **OCR Support**: Handle image-based PDFs
- **Custom Pattern Detection**: Fallback pattern matching for PDFs without outlines
- **Web Interface**: Browser-based conversion interface
- **Batch Processing**: Convert multiple PDFs simultaneously
- **Advanced Text Processing**: Better formatting preservation

## License

This module is part of the larger PDF-to-Audio pipeline project and follows the same licensing terms.