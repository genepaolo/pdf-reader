# TTS Pipeline Quick Start Guide

## 🚀 Getting Started

### 1. Test the Pipeline
```bash
cd tts_pipeline
python test_pipeline.py
```

### 2. List Available Files
```bash
python scripts/file_organizer.py --list
```

### 3. Copy Files for Processing
```bash
# Copy 5 files
python scripts/file_organizer.py --count 5

# Copy specific volume
python scripts/file_organizer.py --volume "1_Clown"

# Copy specific chapters
python scripts/file_organizer.py --volume "1_Clown" --chapters "1,2,3"
```

### 4. Process Files
```bash
# Process with simulated TTS (for testing)
python scripts/batch_processor.py --count 5 --service simulated

# Process with Azure TTS (requires config)
python scripts/batch_processor.py --count 5 --service azure --voice "en-US-AriaNeural"
```

### 5. Monitor Progress
```bash
# Check status
python scripts/progress_tracker.py --summary

# Show batch history
python scripts/progress_tracker.py --history 5

# Export report
python scripts/progress_tracker.py --export report.json
```

## 📁 Directory Structure
```
tts_pipeline/
├── input/          # Text files ready for TTS
├── output/         # Generated audio files
├── config/         # TTS service configurations
├── tracking/       # Progress and metadata
└── scripts/        # Processing scripts
```

## ⚙️ Configuration

### Azure TTS Setup
1. Copy `config/azure_config.json.example` to `config/azure_config.json`
2. Add your Azure subscription key and region
3. Choose your preferred voice

### Google TTS Setup
1. Copy `config/google_config.json.example` to `config/google_config.json`
2. Add path to your Google credentials file
3. Configure voice and audio settings

## 🔄 Typical Workflow

1. **Organize Files**: Copy text files to `input/`
2. **Configure Service**: Set up TTS service credentials
3. **Process Batch**: Convert files to audio
4. **Monitor Progress**: Track conversion status
5. **Handle Failures**: Retry failed conversions
6. **Generate Reports**: Export conversion statistics

## 📊 Example Commands

```bash
# Complete workflow example
python scripts/file_organizer.py --count 10
python scripts/batch_processor.py --count 10 --service azure
python scripts/progress_tracker.py --summary
```

## 🆘 Troubleshooting

- **No input files**: Use `--list` to see available files
- **Config errors**: Check your service configuration files
- **Failed conversions**: Use `--retry-failed` to retry
- **Progress issues**: Check `tracking/` directory for logs
