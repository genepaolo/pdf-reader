# TTS Pipeline - Text-to-Speech Audio Generation

A comprehensive pipeline for converting organized text files into high-quality audio using various TTS services.

## Overview

This pipeline allows you to:
- **Selectively convert** text files in batches (not all at once)
- **Track progress** of converted vs unconverted files
- **Resume interrupted** conversions
- **Monitor quality** and re-convert failed files
- **Support multiple TTS services** (Azure, Google, Amazon, OpenAI)

## Directory Structure

```
tts_pipeline/
├── input/                     # Text files ready for TTS conversion
├── output/                    # Generated audio files
├── config/                    # TTS service configurations
├── tracking/                  # Conversion progress and metadata
│   ├── converted.json         # List of successfully converted files
│   ├── failed.json           # List of failed conversions
│   ├── metadata.json         # File metadata and timestamps
│   └── progress.json         # Current batch progress
├── scripts/                   # TTS processing scripts
│   ├── batch_processor.py     # Main batch conversion script
│   ├── file_organizer.py     # Copy files from extracted_text
│   ├── progress_tracker.py   # Track conversion status
│   └── quality_validator.py  # Validate audio quality
└── README.md                 # This file
```

## Features

### 🎯 Selective Batch Processing
- Convert 5, 10, 50, or any number of files at a time
- Choose specific volumes or chapters to process
- Skip already converted files automatically

### 📊 Progress Tracking
- Track which files have been converted
- Monitor failed conversions with error details
- Resume interrupted batches
- Generate conversion reports

### 🔧 Multi-Service Support
- **Azure Neural TTS** (Recommended for quality)
- **Google Cloud Text-to-Speech**
- **Amazon Polly**
- **OpenAI TTS**
- Easy switching between services

### 🎵 Audio Quality Control
- Validate generated audio files
- Re-convert failed or low-quality files
- Support multiple audio formats (MP3, WAV, OGG)
- Configurable audio quality settings

## Quick Start

### 1. Setup Configuration
```bash
# Copy your TTS service credentials to config/
cp your_azure_key.json config/azure_config.json
```

### 2. Organize Files
```bash
# Copy specific chapters to input/
python scripts/file_organizer.py --volume "1_Clown" --chapters 1-10
```

### 3. Convert to Audio
```bash
# Convert 5 files at a time
python scripts/batch_processor.py --count 5 --service azure
```

### 4. Monitor Progress
```bash
# Check conversion status
python scripts/progress_tracker.py --status
```

## Usage Examples

### Convert First 10 Chapters of Volume 1
```bash
python scripts/file_organizer.py --source "../extracted_text/lotm_book1/1_Clown" --count 10
python scripts/batch_processor.py --count 10 --service azure --voice "en-US-AriaNeural"
```

### Resume Failed Conversions
```bash
python scripts/batch_processor.py --resume --retry-failed
```

### Convert Specific Chapters
```bash
python scripts/file_organizer.py --chapters "1,5,10,15" --volume "1_Clown"
python scripts/batch_processor.py --count 4 --service azure
```

### Check What's Been Converted
```bash
python scripts/progress_tracker.py --summary
# Output: 45/1432 chapters converted (3.1%)
```

## Configuration

### Azure Neural TTS (Recommended)
```json
{
  "service": "azure",
  "subscription_key": "your_key_here",
  "region": "eastus",
  "voice": "en-US-AriaNeural",
  "rate": "+0%",
  "pitch": "+0Hz",
  "output_format": "audio-24khz-160kbitrate-mono-mp3"
}
```

### Google Cloud TTS
```json
{
  "service": "google",
  "credentials_file": "path/to/credentials.json",
  "voice": "en-US-Wavenet-A",
  "speaking_rate": 1.0,
  "pitch": 0.0,
  "output_format": "MP3"
}
```

## Tracking System

### File Status Tracking
- ✅ **Converted**: Successfully generated audio
- ❌ **Failed**: Conversion failed (with error details)
- ⏳ **In Progress**: Currently being processed
- ⏸️ **Paused**: Conversion paused/interrupted
- 🔄 **Retry**: Marked for re-conversion

### Metadata Tracking
- File size and duration
- Conversion timestamp
- TTS service used
- Audio quality metrics
- Error logs for failed conversions

## Batch Processing Workflow

1. **Select Files**: Choose which text files to convert
2. **Copy to Input**: Move files to `input/` directory
3. **Configure Service**: Set up TTS service credentials
4. **Start Batch**: Begin conversion with specified count
5. **Monitor Progress**: Track conversion status
6. **Validate Quality**: Check generated audio files
7. **Handle Failures**: Retry failed conversions
8. **Generate Report**: Create conversion summary

## Error Handling

- **Service Errors**: Automatic retry with exponential backoff
- **File Errors**: Skip corrupted files and continue
- **Network Issues**: Resume from last successful conversion
- **Quality Issues**: Flag for manual review or re-conversion

## Performance Optimization

- **Parallel Processing**: Convert multiple files simultaneously
- **Caching**: Avoid re-converting identical content
- **Rate Limiting**: Respect TTS service limits
- **Batch Optimization**: Minimize API calls

## Future Enhancements

- [ ] Web interface for file selection and monitoring
- [ ] Audio post-processing (noise reduction, normalization)
- [ ] Custom voice training support
- [ ] Integration with audiobook players
- [ ] Automated chapter merging for seamless playback

## Troubleshooting

### Common Issues
- **Authentication Errors**: Check service credentials
- **Rate Limiting**: Reduce batch size or add delays
- **File Encoding**: Ensure UTF-8 encoding for text files
- **Audio Quality**: Adjust voice settings or try different voices

### Support
- Check `tracking/failed.json` for detailed error logs
- Use `--verbose` flag for detailed processing logs
- Review service-specific documentation for advanced settings