# PDF to Text Converter

A Python tool for converting PDF files into organized text files by volumes and chapters.

## Features

- **Automatic Structure Detection**: Automatically detects volumes and chapters in PDF files using configurable regex patterns
- **Multiple Language Support**: Includes patterns for English, Chinese, French, and Spanish
- **Flexible Organization**: Organizes output into volume/chapter folder structure
- **Batch Processing**: Convert multiple PDF files at once
- **Configurable Patterns**: Customize detection patterns for different document formats
- **Text Processing**: Clean and format extracted text with configurable options

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

#### Convert a single PDF file:
```bash
python main.py path/to/your/file.pdf
```

#### Convert all PDFs in a directory:
```bash
python main.py path/to/pdf/directory --batch
```

#### Specify output directory:
```bash
python main.py path/to/file.pdf -o my_output_folder
```

#### Update configuration interactively:
```bash
python main.py --update-config
```

### Python API

#### Basic Usage:
```python
from advanced_converter import AdvancedPDFConverter

# Initialize converter
converter = AdvancedPDFConverter()

# Convert a single PDF
converter.convert_pdf("path/to/your/file.pdf")

# Batch convert all PDFs in a directory
converter.batch_convert("path/to/pdf/directory")
```

#### Custom Configuration:
```python
from advanced_converter import AdvancedPDFConverter
from config import ConverterConfig

# Create custom configuration
config = ConverterConfig("my_config.json")

# Add custom patterns
config.update_patterns(
    volume_patterns=["custom_volume_pattern_(\d+)"],
    chapter_patterns=["custom_chapter_pattern_(\d+)"]
)

# Use with converter
converter = AdvancedPDFConverter("my_config.json")
converter.convert_pdf("path/to/file.pdf")
```

## Configuration

The tool uses a JSON configuration file (`config.json`) that is automatically created with default settings:

```json
{
  "output_directory": "extracted_text",
  "volume_patterns": [
    "volume\\s+(\\d+)",
    "vol\\.?\\s+(\\d+)",
    "book\\s+(\\d+)",
    "part\\s+(\\d+)",
    "第\\s*(\\d+)\\s*卷",
    "第\\s*(\\d+)\\s*册"
  ],
  "chapter_patterns": [
    "chapter\\s+(\\d+)",
    "ch\\.?\\s+(\\d+)",
    "第\\s*(\\d+)\\s*章",
    "第\\s*(\\d+)\\s*节",
    "(\\d+)\\.\\s*[A-Z]"
  ],
  "file_naming": {
    "volume_format": "Volume_{volume:02d}",
    "chapter_format": "Chapter_{chapter:02d}.txt",
    "volume_content_format": "Volume_{volume:02d}_content.txt"
  },
  "text_processing": {
    "remove_page_numbers": true,
    "clean_whitespace": true,
    "preserve_formatting": false
  }
}
```

### Configuration Options

- **volume_patterns**: Regex patterns to detect volume markers
- **chapter_patterns**: Regex patterns to detect chapter markers
- **file_naming**: Templates for naming output files and folders
- **text_processing**: Options for cleaning and formatting extracted text

## Output Structure

The tool creates an organized folder structure:

```
extracted_text/
├── Volume_01/
│   ├── Chapter_01.txt
│   ├── Chapter_02.txt
│   └── Volume_01_content.txt
├── Volume_02/
│   ├── Chapter_01.txt
│   └── Chapter_02.txt
└── full_content.txt (if no structure detected)
```

Each text file includes metadata headers:
```
# Volume 1, Chapter 1
# Pages: 1-15
# Word Count: 2500

[Chapter content here...]
```

## Supported Patterns

### Volume Detection
- `volume 1`, `vol. 1`, `book 1`, `part 1`
- `第1卷`, `第1册` (Chinese)
- `livre 1` (French)
- `tomo 1` (Spanish)

### Chapter Detection
- `chapter 1`, `ch. 1`
- `第1章`, `第1节` (Chinese)
- `chapitre 1` (French)
- `capítulo 1` (Spanish)
- `1. Title` (numbered sections)

## Examples

### Example 1: Basic Conversion
```bash
python main.py "my_novel.pdf"
```

### Example 2: Batch Processing
```bash
python main.py "pdf_collection/" --batch -o "converted_texts"
```

### Example 3: Custom Configuration
```python
from advanced_converter import AdvancedPDFConverter

# Create converter with custom config
converter = AdvancedPDFConverter("custom_config.json")

# Add patterns for a specific document format
converter.config.update_patterns(
    volume_patterns=["Section\\s+(\\d+)"],
    chapter_patterns=["Lesson\\s+(\\d+)"]
)

# Convert document
converter.convert_pdf("textbook.pdf")
```
## Troubleshooting

### Common Issues

1. **No structure detected**: The PDF might not follow standard volume/chapter patterns. Check the configuration and add custom patterns.

2. **Text extraction errors**: Some PDFs may have complex formatting. The tool uses both pdfplumber and PyPDF2 as fallback.

3. **Encoding issues**: The tool uses UTF-8 encoding. For special characters, ensure your PDF supports proper text extraction.

### Adding Custom Patterns

To add patterns for your specific document format:

1. Edit `config.json` directly, or
2. Use the interactive configuration update: `python main.py --update-config`
3. Use the Python API to update patterns programmatically

## Dependencies

- PyPDF2: PDF text extraction
- pdfplumber: Advanced PDF processing
- python-docx: Document processing utilities

## License

This project is open source and available under the MIT License.

