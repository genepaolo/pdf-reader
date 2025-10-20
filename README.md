# PDF to Text Converter & TTS Pipeline

A comprehensive system for converting PDF documents into high-quality audiobooks through organized text extraction and text-to-speech processing.

## 🎯 **Complete Pipeline**

```
PDF Document → [pdf_to_txt] → Organized Text Files → [tts_pipeline] → Audio/Video Files
```

### **Stage 1: PDF to Text (`pdf_to_txt/`)**
Converts PDF files into organized text files by volumes and chapters.

### **Stage 2: Text to Speech (`tts_pipeline/`)**
Converts organized text files into high-quality audio and video files using Azure Cognitive Services.

## 🚀 **NEW: Project-Based Architecture**

The TTS pipeline now features a **project-based configuration system** that allows you to:
- **Multiple Book Series**: Process different books with different settings
- **Custom Narrators**: Use different Azure TTS voices for different projects
- **Flexible Configuration**: Each project has its own Azure, processing, and video settings
- **Easy Management**: Create, list, and manage multiple TTS projects

### **Project Management Examples**

```bash
# List all available projects
python tts_pipeline/scripts/process_project.py --list-projects

# Test with dry-run (safe, no Azure billing)
python tts_pipeline/scripts/process_project.py --project lotm_book1 --dry-run --max-chapters 5

# Process specific chapter range
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-10

# Resume processing from where it left off
python tts_pipeline/scripts/process_project.py --project lotm_book1 --resume

# Retry only failed chapters
python tts_pipeline/scripts/process_project.py --project lotm_book1 --retry-failed
```

### **Project Structure**
```
tts_pipeline/config/projects/
├── lotm_book1/                    # Lord of the Mysteries Book 1
│   ├── project.json              # Project metadata
│   ├── azure_config.json         # Male narrator (SteffanNeural)
│   ├── processing_config.json    # LOTM-specific settings
│   └── video_config.json         # Video creation settings
├── lotm_book2/                    # Lord of the Mysteries Book 2
│   ├── project.json
│   ├── azure_config.json         # Female narrator (JennyNeural)
│   └── ...
└── other_series/                  # Any other book series
    └── ...
```

## Features

### **PDF to Text (`pdf_to_txt/`)**
- **Automatic Structure Detection**: Automatically detects volumes and chapters in PDF files using configurable regex patterns
- **Multiple Language Support**: Includes patterns for English, Chinese, French, and Spanish
- **Flexible Organization**: Organizes output into volume/chapter folder structure
- **Batch Processing**: Convert multiple PDF files at once
- **Configurable Patterns**: Customize detection patterns for different document formats
- **Text Processing**: Clean and format extracted text with configurable options

### **Text to Speech (`tts_pipeline/`)**
- **Azure TTS Integration**: High-quality text-to-speech using Azure Cognitive Services
- **Project-Based Configuration**: Manage multiple book series with different settings
- **SSD Optimization**: 40-60% faster processing with dedicated SSD storage
- **Video Creation**: Generate YouTube-ready videos with audio + image combination
- **Progress Tracking**: Resume processing from any point with comprehensive state management
- **Error Handling**: Robust retry logic and error recovery
- **Audio Compression**: Optimize file sizes while maintaining quality
- **Comprehensive Testing**: 24+ unit tests ensuring reliability

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### **PDF to Text Pipeline**

#### Convert a single PDF file:
```bash
python pdf_to_txt/main.py path/to/your/file.pdf
```

#### Convert all PDFs in a directory:
```bash
python pdf_to_txt/main.py path/to/pdf/directory --batch
```

#### Specify output directory:
```bash
python pdf_to_txt/main.py path/to/file.pdf -o my_output_folder
```

### **Text to Speech Pipeline**

#### Project Management:
```bash
# List available projects
python tts_pipeline/scripts/process_project.py --list-projects

# Test with dry-run (safe, no Azure billing)
python tts_pipeline/scripts/process_project.py --project lotm_book1 --dry-run --max-chapters 3

# Process specific chapter range
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-10

# Process single chapter
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 5

# Resume processing from where it left off
python tts_pipeline/scripts/process_project.py --project lotm_book1 --resume

# Retry only failed chapters
python tts_pipeline/scripts/process_project.py --project lotm_book1 --retry-failed

# Enable debug logging
python tts_pipeline/scripts/process_project.py --project lotm_book1 --dry-run --log-level DEBUG
```

#### Configuration:
```bash
# Set up Azure credentials
echo "AZURE_TTS_SUBSCRIPTION_KEY=your_key_here" > .env
echo "AZURE_TTS_REGION=your_region_here" >> .env

# Test Azure connectivity (integration test)
python tts_pipeline/tests/integration/test_azure_tts_connectivity.py
```

### **Complete Pipeline Example**

#### From PDF to Audiobook:
```bash
# Step 1: Convert PDF to organized text
python pdf_to_txt/main.py lotm_book1.pdf -o extracted_text/lotm_book1

# Step 2: Test TTS pipeline (dry-run first!)
python tts_pipeline/scripts/process_project.py --project lotm_book1 --dry-run --max-chapters 3

# Step 3: Process specific chapters
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-10

# Step 4: Resume if interrupted
python tts_pipeline/scripts/process_project.py --project lotm_book1 --resume
```

#### Python API:
```python
# PDF to Text
from pdf_to_txt.pdf_converter_clean import PDFConverter
converter = PDFConverter()
converter.convert_pdf("lotm_book1.pdf")

# Text to Speech
from tts_pipeline.utils.project_manager import ProjectManager
pm = ProjectManager()
project = pm.load_project("lotm_book1")
# Process project...
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

