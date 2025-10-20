# TTS Pipeline Plan: Chapter-by-Chapter Audio Generation

## Overview
The TTS Pipeline will process extracted text files from the LOTM book series in chapter order, converting them to audio files using Azure AI services. The system will maintain progress tracking to resume from where it left off and validate audio output quality.

## Core Requirements

### 1. Sequential Processing
- **One file at a time**: Process only a single chapter file per execution
- **Chapter order**: Process chapters in numerical order (Chapter_1, Chapter_2, etc.)
- **Volume order**: Process volumes in order (Volume 1 → Volume 2 → etc.)
- **Resume capability**: Track progress and continue from last processed chapter

### 2. Chapter Identification
- **File naming pattern**: `Chapter_XXX_Title.txt`
- **Volume structure**: Organized in folders like `1___VOLUME_1___CLOWN/`
- **Sequential numbering**: Chapters numbered 1, 2, 3, etc. across all volumes

### 3. Progress Tracking
- **State persistence**: Store progress in JSON file
- **Resume mechanism**: Automatically detect and continue from last processed chapter
- **Error handling**: Track failed chapters for retry

### 4. Audio Validation
- **Minimum duration**: Audio files must be at least 5 minutes long
- **File integrity**: Verify audio file is valid and playable
- **Quality check**: Ensure audio quality meets standards

## System Architecture

### 1. Directory Structure
```
tts_pipeline/
├── config/
│   ├── azure_config.json          # Azure AI settings (non-sensitive)
│   └── processing_config.json     # Processing parameters
├── tracking/
│   ├── progress.json              # Current progress state
│   ├── completed.json             # Successfully processed chapters
│   ├── failed.json                # Failed chapters for retry
│   └── metadata.json              # Chapter metadata and stats
├── input/                         # Source text files (symlink to extracted_text)
├── output/                        # Generated audio files
├── logs/                          # Processing logs
├── api/
│   ├── azure_tts_client.py        # Azure TTS integration
│   └── base_tts_client.py         # Abstract base class for TTS providers
├── scripts/
│   ├── chapter_processor.py       # Main processing script
│   ├── audio_validator.py         # Audio validation
│   └── config_manager.py          # Configuration management
├── utils/
│   ├── file_organizer.py          # File discovery and organization
│   └── progress_tracker.py        # Progress management
├── .gitignore                     # Git ignore file (excludes .env)
└── tests/                         # Unit and integration tests
    ├── test_helpers.py            # Test utilities and fixtures
    ├── mock_azure_client.py       # Mock Azure TTS client for testing
    ├── test_data/                 # Sample test files and data
    ├── test_configs/              # Test configuration files
    ├── test_chapter_discovery.py  # Tests for file discovery
    ├── test_progress_tracker.py   # Tests for progress tracking
    ├── test_azure_tts_client.py   # Tests for Azure integration
    ├── test_audio_validator.py    # Tests for audio validation
    └── test_end_to_end.py         # Integration tests
```

### 2. Core Components

#### A. Chapter Discovery System
- **File scanner**: Recursively scan `extracted_text/lotm_book1/` for chapter files
- **Pattern matching**: Identify files matching `Chapter_XXX_Title.txt` pattern
- **Sorting**: Sort chapters by volume and chapter number
- **Validation**: Ensure files are readable text files

#### B. Progress Tracking System
- **State management**: Track current processing position
- **Resume logic**: Determine next chapter to process
- **Error tracking**: Log failed chapters with error details
- **Statistics**: Track processing metrics (time, success rate, etc.)

#### C. Azure TTS Integration
- **Authentication**: Load Azure credentials from environment variables
- **Text processing**: Prepare text for TTS (cleaning, chunking if needed)
- **API calls**: Send text to Azure TTS service using secure credentials
- **Audio retrieval**: Download generated audio files
- **Error handling**: Handle authentication and API errors gracefully
- **Provider abstraction**: Base class for future TTS provider integrations

#### D. Audio Validation System
- **Duration check**: Verify audio is at least 5 minutes long
- **Format validation**: Ensure audio file is valid (WAV/MP3)
- **Quality metrics**: Basic audio quality verification
- **File integrity**: Verify file can be opened and played

### 3. Processing Workflow

#### Step 1: Initialization
1. Load environment variables from root directory `.env` file (`../.env`)
2. Validate required credentials are present
3. Load configuration files
4. Initialize Azure TTS client with environment credentials
5. Scan for available chapters
6. Load progress tracking state

#### Step 2: Chapter Selection
1. Determine next chapter to process
2. Validate chapter file exists and is readable
3. Check if chapter was already processed successfully
4. Skip to next chapter if current one is invalid

#### Step 3: Text Processing
1. Read chapter text file
2. Clean and prepare text for TTS
3. Handle text length limits (chunk if necessary)
4. Apply any text preprocessing rules

#### Step 4: Audio Generation
1. Send text to Azure TTS service via API client
2. Monitor API response and handle errors
3. Download generated audio file (high quality)
4. Save to temporary directory with proper naming

#### Step 5: Audio Compression
1. Load compression configuration settings
2. Compress audio using FFmpeg (SSD-optimized)
3. Validate compressed audio quality and duration
4. Save compressed file to SSD output directory
5. Clean up temporary high-quality files (optional)

#### Step 6: Video Creation
1. Load video configuration and image assets
2. Create video by combining audio + image using FFmpeg
3. Save uncompressed video to SSD temp directory
4. Validate video creation and duration

#### Step 7: Video Compression
1. Compress video using FFmpeg (SSD-optimized preset)
2. Validate compressed video quality and file size
3. Save compressed video to SSD final output directory
4. Clean up temporary video files

#### Step 8: Validation
1. Check compressed audio and video files exist and are valid
2. Verify audio duration (≥ 5 minutes)
3. Validate audio and video quality and file sizes
4. Test audio and video playback capability
5. Record validation results

#### Step 9: Progress Update
1. Update progress tracking with final compressed file info
2. Log successful processing, compression, and video creation stats
3. Save current state
4. Prepare for next chapter

### 4. Configuration Management

#### Environment Variables Security
- **`.env` file**: Located in root directory (`pdf_reader/.env`) contains sensitive credentials (Azure keys, regions)
- **Git ignore**: `.env` file should be added to `.gitignore` to prevent accidental commits
- **Environment loading**: Use `python-dotenv` library to load environment variables from root directory
- **Validation**: Check for required environment variables on startup
- **Fallback**: Provide clear error messages if credentials are missing

#### Required Environment Variables
```bash
AZURE_SPEECH_KEY=your_subscription_key
AZURE_SPEECH_REGION=your_region
```

#### Optional Environment Variables
```bash
AZURE_SPEECH_ENDPOINT=your_custom_endpoint
AZURE_SPEECH_LANGUAGE=en-US
AZURE_SPEECH_VOICE_GENDER=female
```

#### Azure Configuration (`azure_config.json`)
```json
{
  "voice_name": "en-US-SteffanNeural",
  "output_format": "audio-24khz-160kbitrate-mono-mp3",
  "rate": "+0%",
  "pitch": "+0Hz",
  "max_text_length": 20000,
  "timeout_seconds": 1200,
  "compression": {
    "enabled": true,
    "target_format": "audio-22khz-128kbitrate-mono-mp3",
    "quality_preset": "high",
    "keep_original": false
  }
}
```

#### Processing Configuration (`processing_config.json`)
```json
{
  "input_directory": "../extracted_text/lotm_book1",
  "output_directory": "D:/lotm_book1_output",
  "temp_directory": "./temp",
  "ssd_directory": "D:/lotm_book1_output",
  "min_audio_duration_minutes": 5,
  "max_audio_duration_minutes": 20,
  "expected_audio_duration_minutes": 15,
  "max_text_length": 20000,
  "retry_attempts": 3,
  "retry_delay_seconds": 30,
  "log_level": "INFO",
  "storage": {
    "use_dedicated_ssd": true,
    "ssd_path": "D:/lotm_book1_output",
    "temp_on_ssd": true,
    "backup_enabled": false,
    "preserve_hierarchy": true
  },
  "compression": {
    "enabled": true,
    "target_bitrate": "128k",
    "target_sample_rate": "22050",
    "quality_check": true,
    "cleanup_temp": true
  },
  "video": {
    "enabled": true,
    "video_type": "still_image",
    "default_image": "./assets/images/default_cover.jpg",
    "output_directory": "D:/lotm_book1_output/video",
    "temp_directory": "D:/lotm_book1_output/temp_processing/video_temp",
    "ssd_optimized": true,
    "format": {
      "resolution": "1920x1080",
      "video_codec": "libx264",
      "audio_codec": "aac",
      "audio_bitrate": "128k",
      "pixel_format": "yuv420p"
    },
    "compression": {
      "enabled": true,
      "crf": 23,
      "preset": "fast",
      "optimize_streaming": true
    }
  }
}
```

#### Environment Variables (`.env`)
```bash
# Azure Cognitive Services Credentials
AZURE_SPEECH_KEY=your_azure_subscription_key_here
AZURE_SPEECH_REGION=your_azure_region_here

# Optional: Azure endpoint (if using custom endpoint)
# AZURE_SPEECH_ENDPOINT=https://your-region.cognitiveservices.azure.com/

# Optional: Additional Azure settings
# AZURE_SPEECH_LANGUAGE=en-US
# AZURE_SPEECH_VOICE_GENDER=female
```

#### Processing Configuration (`processing_config.json`)
```json
{
  "input_directory": "../extracted_text/lotm_book1",
  "output_directory": "./output",
  "min_audio_duration_minutes": 5,
  "max_text_length": 5000,
  "retry_attempts": 3,
  "retry_delay_seconds": 30,
  "log_level": "INFO"
}
```

### 5. Progress Tracking Format

#### Progress State (`progress.json`)
```json
{
  "current_volume": "1___VOLUME_1___CLOWN",
  "current_chapter": "Chapter_1_Crimson.txt",
  "last_processed": "2024-01-15T10:30:00Z",
  "total_chapters_found": 2134,
  "chapters_processed": 45,
  "chapters_failed": 2,
  "estimated_remaining": "45 hours"
}
```

#### Completed Chapters (`completed.json`)
```json
{
  "Chapter_1_Crimson.txt": {
    "processed_date": "2024-01-15T10:30:00Z",
    "audio_file": "Chapter_1_Crimson.mp3",
    "video_file": "Chapter_1_Crimson.mp4",
    "duration_seconds": 900,
    "audio_size_mb": 12.5,
    "video_size_mb": 45.2,
    "original_audio_size_mb": 18.2,
    "original_video_size_mb": 85.7,
    "audio_compression_ratio": 0.69,
    "video_compression_ratio": 0.53,
    "volume": "1___VOLUME_1___CLOWN",
    "ssd_optimized": true
  }
}
```

### 6. SSD-Optimized Audio & Video Processing

#### Three-Phase Processing Strategy
1. **Phase 1: High-Quality Generation**
   - Generate audio at maximum quality (24kHz, 160kbps)
   - Save to temporary directory
   - Validate original audio quality

2. **Phase 2: Audio Compression**
   - Compress audio using SSD-optimized FFmpeg
   - Validate compressed audio quality
   - Save to SSD output directory
   - Clean up temporary audio files

3. **Phase 3: Video Creation & Compression**
   - Create video by combining audio + image
   - Compress video using SSD-optimized settings
   - Validate compressed video quality
   - Save to SSD output directory
   - Clean up temporary video files

#### SSD Performance Benefits
- **Processing Speed**: 40-60% faster end-to-end processing
- **File I/O**: 5-50x faster read/write operations
- **Video Encoding**: 3-5x faster FFmpeg operations
- **Concurrent Operations**: Parallel file processing
- **Storage Reduction**: 20-30% smaller audio files, 40-50% smaller video files

#### Compression Settings
```json
{
  "compression": {
    "enabled": true,
    "target_format": "audio-22khz-128kbitrate-mono-mp3",
    "quality_preset": "high",
    "keep_original": false,
    "quality_check": true,
    "min_duration_minutes": 5,
    "max_duration_minutes": 20
  }
}
```

#### Compression Tools
- **FFmpeg**: Industry standard audio processing
- **pydub**: Python audio manipulation library
- **Quality Validation**: Automated quality checks

#### Storage Impact (SSD-Optimized)
- **Audio Original**: ~18-20 MB per 15-minute chapter
- **Audio Compressed**: ~12-15 MB per 15-minute chapter
- **Video Original**: ~80-100 MB per 15-minute chapter
- **Video Compressed**: ~40-50 MB per 15-minute chapter
- **Total LOTM Audio**: ~25-30 GB compressed
- **Total LOTM Video**: ~85-110 GB compressed
- **Total LOTM Combined**: ~110-140 GB (vs 200-250 GB uncompressed)
- **Savings**: 90-110 GB storage reduction

### 7. SSD Directory Structure

#### Hierarchical Organization (Maintaining Volume Structure)
```
D:/lotm_book1_output/
├── audio/
│   ├── 1___VOLUME_1___CLOWN/
│   │   ├── Chapter_1_Crimson.mp3
│   │   ├── Chapter_2_August.mp3
│   │   └── ...
│   ├── 2___VOLUME_2___FACELESS/
│   │   ├── Chapter_1_Moonlight.mp3
│   │   └── ...
│   └── ...
├── video/
│   ├── 1___VOLUME_1___CLOWN/
│   │   ├── Chapter_1_Crimson.mp4
│   │   ├── Chapter_2_August.mp4
│   │   └── ...
│   ├── 2___VOLUME_2___FACELESS/
│   │   ├── Chapter_1_Moonlight.mp4
│   │   └── ...
│   └── ...
├── temp_processing/
│   ├── audio_temp/
│   ├── video_temp/
│   └── cleanup/
└── backups/
    └── failed_processing/
```

#### SSD Performance Optimization
- **Preserve Hierarchy**: Maintains same volume/chapter structure as source text
- **Parallel Processing**: SSD enables concurrent file operations
- **Fast Access**: Quick retrieval for specific volumes or chapters
- **Organized Storage**: Easy navigation and management
- **Backup Friendly**: Simple to backup entire volumes or series

### 8. Error Handling

#### Retry Logic
- **Transient errors**: Retry up to 3 times with exponential backoff
- **Permanent errors**: Log and skip to next chapter
- **Rate limiting**: Implement delays between API calls

#### Error Categories
- **File errors**: Missing files, permission issues, corrupted text
- **API errors**: Azure service issues, authentication problems
- **Validation errors**: Audio quality issues, duration problems
- **System errors**: Network issues, disk space, memory problems

### 7. Logging and Monitoring

#### Log Levels
- **DEBUG**: Detailed processing information
- **INFO**: General progress updates
- **WARNING**: Non-critical issues
- **ERROR**: Processing failures
- **CRITICAL**: System failures

#### Log Format
```
2024-01-15 10:30:15 INFO [Chapter_1_Crimson.txt] Processing started
2024-01-15 10:30:16 DEBUG [Chapter_1_Crimson.txt] Text length: 4,523 characters
2024-01-15 10:32:45 INFO [Chapter_1_Crimson.txt] Audio generated successfully
2024-01-15 10:32:46 INFO [Chapter_1_Crimson.txt] Duration: 7 minutes 32 seconds
2024-01-15 10:32:47 INFO [Chapter_1_Crimson.txt] Processing completed
```

### 8. Usage Examples

#### Basic Usage
```bash
# Start processing from beginning
python scripts/chapter_processor.py

# Resume from last position
python scripts/chapter_processor.py --resume

# Process specific chapter
python scripts/chapter_processor.py --chapter "Chapter_1_Crimson.txt"

# Process specific volume
python scripts/chapter_processor.py --volume "1___VOLUME_1___CLOWN"
```

#### Configuration
```bash
# Update Azure settings
python utils/config_manager.py --update-azure

# Validate configuration
python utils/config_manager.py --validate

# Reset progress (start over)
python utils/config_manager.py --reset-progress
```

#### Security Setup
```bash
# Create .env file with your credentials in root directory
echo "AZURE_SPEECH_KEY=your_key_here" > ../.env
echo "AZURE_SPEECH_REGION=your_region_here" >> ../.env

# Ensure .gitignore includes .env file (in root directory)
echo ".env" >> ../.gitignore
echo "*.env" >> ../.gitignore
```

### 9. Testing Strategy

#### Unit Tests
- Chapter discovery and sorting
- Progress tracking logic
- Audio validation functions
- Configuration management

#### Integration Tests
- Azure TTS API integration
- End-to-end processing workflow with compression
- Audio compression quality validation
- Error handling scenarios
- Resume functionality
- API client integration with progress tracker

#### Performance Tests
- Large text file processing (20,000 characters)
- Audio compression performance
- Memory usage optimization
- API rate limiting
- Concurrent processing limits
- Compression quality validation

### 10. Future Enhancements

#### Phase 2 Features
- **Batch processing**: Process multiple chapters in parallel
- **Quality optimization**: Advanced audio quality metrics
- **Custom voices**: Support for different voice options
- **Chapter merging**: Combine multiple chapters into single audio files

#### Phase 3 Features
- **Web interface**: Browser-based monitoring and control
- **Real-time progress**: Live progress updates
- **Audio editing**: Post-processing audio enhancements
- **Distribution**: Automated audio file distribution

## Implementation Priority

### Phase 1 (Core Functionality)
1. ✅ Basic chapter discovery and sorting
2. ✅ Progress tracking system
3. ✅ Azure TTS integration
4. ⏳ SSD-optimized audio compression
5. ⏳ Video creation (audio + image)
6. ⏳ Video compression optimization
7. ⏳ Audio & video validation
8. ✅ Resume functionality
9. ⏳ Error handling and logging

### Phase 2 (Enhancements)
1. 🔄 Advanced audio & video validation
2. 🔄 SSD performance optimization
3. 🔄 Configuration management UI
4. 🔄 Comprehensive testing including video creation
5. 🔄 Compression quality metrics
6. 🔄 YouTube integration preparation

### Phase 3 (Advanced Features)
1. ⏳ Batch processing with SSD optimization
2. ⏳ YouTube API integration
3. ⏳ Automated upload system
4. ⏳ Web interface
5. ⏳ Advanced monitoring
6. ⏳ Adaptive compression based on content

## Success Criteria

### Functional Requirements
- ✅ Process chapters in correct order
- ✅ Resume from last processed chapter
- ✅ Validate audio duration (≥ 5 minutes)
- ✅ Handle errors gracefully
- ✅ Maintain processing state
- ⏳ Compress audio files efficiently using SSD
- ⏳ Create video files (audio + image)
- ⏳ Compress video files efficiently using SSD
- ⏳ Validate compression quality for audio and video

### Performance Requirements
- ✅ Process one chapter per execution
- ✅ Complete processing within reasonable time
- ✅ Handle large text files efficiently (20,000 characters)
- ✅ Minimize API rate limiting issues
- ⏳ Achieve 40-60% faster processing with SSD optimization
- ⏳ Achieve 20-30% audio file size reduction
- ⏳ Achieve 40-50% video file size reduction
- ⏳ Maintain SSD-optimized compression processing speed

### Quality Requirements
- ✅ Generate high-quality audio output
- ✅ Ensure audio files are playable
- ✅ Maintain consistent audio quality
- ✅ Handle various text formats and lengths
- ⏳ Create high-quality video output with consistent image
- ⏳ Maintain excellent speech quality after compression
- ⏳ Validate compressed audio and video integrity
- ⏳ Ensure video files are YouTube-ready

---

## Project-Based Configuration System

### Overview
The TTS pipeline uses a project-based configuration system that allows for multiple book series with different settings, narrators, and processing parameters. Each project is self-contained with its own configuration files and output directories.

### Project Structure
```
tts_pipeline/
├── config/
│   ├── projects/                    # Project-specific configurations
│   │   ├── lotm_book1/
│   │   │   ├── project.json        # Project metadata and settings
│   │   │   ├── azure_config.json   # Azure TTS configuration
│   │   │   ├── processing_config.json
│   │   │   └── video_config.json
│   │   ├── lotm_book2/
│   │   │   ├── project.json
│   │   │   ├── azure_config.json   # Different narrator!
│   │   │   ├── processing_config.json
│   │   │   └── video_config.json
│   │   └── other_series/
│   │       └── ...
│   └── defaults/                    # Default configuration templates
│       ├── azure_config.json
│       ├── processing_config.json
│       └── video_config.json
├── scripts/
│   └── process_project.py          # Main entry point with --project flag
├── utils/
│   ├── project_manager.py          # Project configuration management
│   ├── file_organizer.py           # Updated to use Project objects
│   └── progress_tracker.py         # Updated to use Project objects
└── api/
    ├── azure_tts_client.py         # Updated to use project configs
    └── video_creator.py            # Updated to use project configs
```

### Project Configuration (`project.json`)
```json
{
  "project_name": "lotm_book1",
  "display_name": "Lord of the Mysteries - Book 1",
  "input_directory": "../extracted_text/lotm_book1",
  "output_directory": "D:/lotm_book1_output",
  "description": "Complete LOTM Book 1 with 2,134 chapters",
  "metadata": {
    "series": "Lord of the Mysteries",
    "book_number": 1,
    "total_volumes": 8,
    "total_chapters": 2134,
    "language": "en-US",
    "genre": "fantasy"
  },
  "created_date": "2024-10-20",
  "last_modified": "2024-10-20"
}
```

### Usage Examples

#### Command Line Interface
```bash
# Process specific project
python scripts/process_project.py --project lotm_book1

# Process with specific chapter
python scripts/process_project.py --project lotm_book1 --chapter "Chapter_1_Crimson.txt"

# Process specific volume
python scripts/process_project.py --project lotm_book1 --volume "1___VOLUME_1___CLOWN"

# List available projects
python scripts/process_project.py --list-projects

# Create new project from template
python scripts/process_project.py --create-project other_series
```

#### Python API
```python
from utils.project_manager import ProjectManager

# Load project configuration
pm = ProjectManager()
project = pm.load_project("lotm_book1")

# Get project-specific configs
azure_config = project.get_azure_config()
processing_config = project.get_processing_config()
video_config = project.get_video_config()

# Process project
project.process()
```

### Configuration Hierarchy
1. **Project-specific config** (highest priority)
2. **Default config** (fallback)
3. **Environment variables** (override)
4. **Command-line arguments** (highest override)

### Benefits
- **Flexibility**: Different narrators for different books
- **Scalability**: Easy to add new projects
- **Organization**: Clear separation of project configurations
- **Maintainability**: Centralized project management
- **Reusability**: Pipeline code remains generic

---

**Note**: This plan focuses on single-file processing as requested. The system is designed to be robust, resumable, and maintainable while ensuring high-quality audio output for each chapter. The project-based architecture makes it scalable for multiple book series with different configurations.
