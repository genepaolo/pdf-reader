# TTS Pipeline Architecture

## Overview

The TTS Pipeline is a comprehensive system for converting text chapters into high-quality audio and video files using Azure Cognitive Services. The system is designed with a project-based architecture that allows for multiple book series with different configurations, narrators, and processing parameters.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        TTS Pipeline System                     │
├─────────────────────────────────────────────────────────────────┤
│  Input Layer:                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   Text Files    │    │   Project       │                    │
│  │ (extracted_text)│    │ Configuration   │                    │
│  └─────────────────┘    └─────────────────┘                    │
├─────────────────────────────────────────────────────────────────┤
│  Processing Layer:                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │ File Organizer  │───▶│ Progress Tracker│───▶│ Azure TTS   │  │
│  │                 │    │                 │    │ Client      │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│           │                       │                     │       │
│           ▼                       ▼                     ▼       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │ Audio Processor │    │ Video Creator   │    │ Validation  │  │
│  │                 │    │                 │    │ System      │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Output Layer:                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  Audio Files    │    │  Video Files    │                    │
│  │  (Compressed)   │    │  (Compressed)   │                    │
│  └─────────────────┘    └─────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Project-Based Configuration System

The system uses a project-based architecture where each book series is a separate project with its own configuration files.

#### Project Structure
```
config/
├── projects/                    # Project-specific configurations
│   ├── lotm_book1/
│   │   ├── project.json        # Project metadata
│   │   ├── azure_config.json   # Azure TTS settings
│   │   ├── processing_config.json
│   │   └── video_config.json
│   ├── lotm_book2/
│   │   ├── project.json        # Different narrator!
│   │   ├── azure_config.json
│   │   ├── processing_config.json
│   │   └── video_config.json
│   └── other_series/
│       └── ...
└── defaults/                    # Default templates
    ├── azure_config.json
    ├── processing_config.json
    └── video_config.json
```

## Component Architecture

### 1. Project Manager (`utils/project_manager.py`)

**Responsibility:** Manages project configurations and orchestrates the entire processing pipeline.

```python
class ProjectManager:
    """Manages project configurations and orchestrates processing."""
    
    def list_projects(self) -> List[str]:
        """List all available projects."""
        
    def load_project(self, project_name: str) -> Project:
        """Load a specific project configuration."""
        
    def create_project(self, project_name: str, template: str = "default"):
        """Create a new project from template."""

class Project:
    """Represents a single TTS project with its configurations."""
    
    def get_input_directory(self) -> Path:
        """Get input directory for this project."""
        
    def get_output_directory(self) -> Path:
        """Get output directory for this project."""
        
    def get_azure_config(self) -> Dict:
        """Get Azure TTS configuration."""
        
    def process(self, chapter: Optional[str] = None):
        """Process the project."""
```

### 2. File Organizer (`utils/file_organizer.py`)

**Responsibility:** Discovers and organizes chapter files for processing.

```python
class ChapterFileOrganizer:
    """Organizes and discovers chapter files for TTS processing."""
    
    def __init__(self, project: Project):
        """Initialize with project configuration."""
        
    def discover_chapters(self) -> List[Dict[str, any]]:
        """Discover all chapter files and return them sorted."""
        
    def get_next_chapter(self) -> Optional[Dict[str, any]]:
        """Get the next chapter to process."""
```

### 3. Progress Tracker (`utils/progress_tracker.py`)

**Responsibility:** Tracks processing progress and enables resume functionality.

```python
class ProgressTracker:
    """Tracks processing progress and enables resume functionality."""
    
    def __init__(self, project: Project):
        """Initialize with project configuration."""
        
    def get_progress(self) -> Dict[str, any]:
        """Get current processing progress."""
        
    def update_progress(self, chapter: str, status: str):
        """Update progress for a specific chapter."""
        
    def can_resume(self) -> bool:
        """Check if processing can be resumed."""
```

### 4. Azure TTS Client (`api/azure_tts_client.py`)

**Responsibility:** Interfaces with Azure Cognitive Services for text-to-speech conversion.

```python
class AzureTTSClient:
    """Azure Cognitive Services TTS client."""
    
    def __init__(self, config: Dict):
        """Initialize with Azure configuration."""
        
    def synthesize_text(self, text: str) -> bytes:
        """Convert text to speech audio."""
        
    def get_voice_info(self) -> Dict[str, Any]:
        """Get current voice configuration information."""
        
    def test_connection(self) -> bool:
        """Test Azure TTS connection."""
```

### 5. Video Creator (`api/video_creator.py`)

**Responsibility:** Creates video files by combining audio with images.

```python
class VideoCreator:
    """Creates video files from audio and images."""
    
    def __init__(self, config: Dict):
        """Initialize with video configuration."""
        
    def create_video(self, audio_path: str, image_path: str, output_path: str):
        """Combine audio and image into video."""
        
    def compress_video(self, input_path: str, output_path: str):
        """Compress video for storage/YouTube."""
        
    def validate_video(self, video_path: str):
        """Validate video duration, playability."""
```

## Data Flow

### Processing Flow

```
1. Project Selection
   ↓
2. Configuration Loading
   ├── Project metadata (project.json)
   ├── Azure TTS settings (azure_config.json)
   ├── Processing parameters (processing_config.json)
   └── Video settings (video_config.json)
   ↓
3. Chapter Discovery
   ├── Scan input directory
   ├── Apply chapter/volume patterns
   └── Sort by volume and chapter number
   ↓
4. Progress Check
   ├── Load existing progress
   ├── Determine resume point
   └── Skip completed chapters
   ↓
5. Audio Generation
   ├── Load chapter text
   ├── Generate SSML
   ├── Call Azure TTS API
   └── Save high-quality audio
   ↓
6. Audio Compression
   ├── Compress audio using FFmpeg
   ├── Validate compressed audio
   └── Save to SSD output directory
   ↓
7. Video Creation
   ├── Load image asset
   ├── Combine audio + image using FFmpeg
   └── Save uncompressed video
   ↓
8. Video Compression
   ├── Compress video using FFmpeg
   ├── Validate compressed video
   └── Save to SSD output directory
   ↓
9. Progress Update
   ├── Update tracking files
   ├── Log processing results
   └── Prepare for next chapter
```

### Configuration Hierarchy

```
1. Command-line arguments (highest priority)
   ↓
2. Project-specific configuration
   ↓
3. Default configuration
   ↓
4. Environment variables (fallback)
```

## Storage Architecture

### Directory Structure

```
Project Output (e.g., D:/lotm_book1_output/)
├── audio/                       # Compressed audio files
│   ├── 1___VOLUME_1___CLOWN/
│   ├── 2___VOLUME_2___FACELESS/
│   └── ...
├── video/                       # Compressed video files
│   ├── 1___VOLUME_1___CLOWN/
│   ├── 2___VOLUME_2___FACELESS/
│   └── ...
├── temp_processing/             # Temporary files
│   ├── audio_temp/
│   ├── video_temp/
│   └── cleanup/
└── backups/                     # Failed processing
    └── failed_processing/
```

### SSD Optimization

- **Input**: Source text files (HDD)
- **Processing**: Temporary files (SSD)
- **Output**: Final audio/video files (SSD)
- **Benefits**: 40-60% faster processing, 5-50x faster I/O operations

## Error Handling

### Error Categories

1. **Configuration Errors**
   - Missing project configuration
   - Invalid Azure credentials
   - Malformed configuration files

2. **Processing Errors**
   - Text length limits exceeded
   - Azure API rate limits
   - File system errors

3. **Validation Errors**
   - Audio quality issues
   - Video compression failures
   - File corruption

### Retry Logic

- **Transient errors**: Retry up to 3 times with exponential backoff
- **Permanent errors**: Log and skip to next chapter
- **Rate limiting**: Implement delays between API calls

## Security Considerations

### Credential Management

- **Environment Variables**: Azure credentials stored in `.env` file
- **Git Protection**: `.cursorignore` prevents AI from reading sensitive files
- **Local Only**: Credentials never committed to repository

### File Access

- **Read-only**: Source text files are never modified
- **Temporary**: Processing files are cleaned up after completion
- **Backup**: Failed processing attempts are preserved for debugging

## Performance Characteristics

### Processing Times (per 15-minute chapter)

| Operation | HDD | SSD | Improvement |
|-----------|-----|-----|-------------|
| Audio Generation | 30s | 30s | N/A (API call) |
| Audio Compression | 10s | 3s | 3x faster |
| Video Creation | 45s | 15s | 3x faster |
| Video Compression | 30s | 10s | 3x faster |
| File Operations | 15s | 2s | 7x faster |
| **Total** | **130s** | **60s** | **54% faster** |

### Storage Requirements

| Content Type | File Size | Total (2,134 chapters) |
|--------------|-----------|------------------------|
| Audio (compressed) | 12-15 MB | 25-30 GB |
| Video (compressed) | 40-50 MB | 85-110 GB |
| **Total** | **52-65 MB** | **110-140 GB** |

## Scalability

### Horizontal Scaling

- **Multiple Projects**: Each project is independent
- **Parallel Processing**: Can process multiple projects simultaneously
- **Resource Isolation**: Each project has its own configuration and output

### Vertical Scaling

- **SSD Storage**: Faster processing with better storage
- **Memory**: Efficient processing with minimal memory usage
- **CPU**: FFmpeg operations are CPU-bound and benefit from more cores

## Future Enhancements

### Phase 2 Features

1. **YouTube Integration**
   - Automated upload system
   - Playlist management
   - Metadata generation

2. **Batch Processing**
   - Process multiple chapters in parallel
   - Queue management
   - Resource optimization

3. **Web Interface**
   - Browser-based monitoring
   - Real-time progress updates
   - Configuration management

### Phase 3 Features

1. **Advanced Audio Processing**
   - Noise reduction
   - Audio enhancement
   - Custom voice training

2. **Video Enhancements**
   - Dynamic backgrounds
   - Chapter-specific images
   - Subtitles integration

3. **Analytics**
   - Processing metrics
   - Performance monitoring
   - Usage statistics

## Maintenance

### Regular Tasks

1. **Configuration Updates**
   - Azure TTS pricing changes
   - New voice options
   - Quality improvements

2. **Dependency Updates**
   - Python package updates
   - FFmpeg version updates
   - Security patches

3. **Storage Management**
   - Cleanup temporary files
   - Archive completed projects
   - Backup critical data

### Monitoring

1. **Processing Metrics**
   - Success/failure rates
   - Processing times
   - Resource usage

2. **Error Tracking**
   - Failed processing attempts
   - API errors
   - System issues

3. **Quality Assurance**
   - Audio quality validation
   - Video compression checks
   - File integrity verification
