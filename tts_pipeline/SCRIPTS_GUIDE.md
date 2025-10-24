# TTS Pipeline Scripts Documentation

## 📋 Overview

This document provides comprehensive documentation for all scripts in the TTS Pipeline system, including usage examples, command-line options, and practical scenarios.

---

## 🚀 Main Processing Scripts

### **1. `process_project.py`**
**Primary script for TTS processing and audio generation**

#### **Purpose**
- Process text chapters into audio files using Azure TTS
- Support resume functionality for interrupted processing
- Handle text chunking for large chapters
- Optional video creation integration

#### **Basic Usage**
```bash
# Process specific chapter range
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-10

# Resume processing from where you left off
python tts_pipeline/scripts/process_project.py --project lotm_book1

# Process with video creation
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-5 --create-videos

# Dry run (test without making API calls)
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-3 --dry-run
```

#### **Command Line Options**
```bash
python tts_pipeline/scripts/process_project.py [OPTIONS]

Required:
  --project PROJECT_NAME    Project name to process

Optional:
  --chapters RANGE         Chapter range (e.g., "1", "1-10", "5-15")
  --max-chapters N         Maximum number of chapters to process
  --dry-run               Test mode (no actual API calls)
  --create-videos         Create videos after audio generation
  --retry-failed          Retry previously failed chapters
  --clear-dry-run         Clear dry-run data and start fresh
  --list-projects         List all available projects
  --log-level LEVEL       Set logging level (DEBUG, INFO, WARNING, ERROR)
```

#### **Practical Examples**

**Starting a New Project**
```bash
# Test with a few chapters first
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-3 --dry-run

# Process first 10 chapters
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-10

# Continue processing more chapters
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 11-20
```

**Resume After Interruption**
```bash
# Simply run without chapter range to resume
python tts_pipeline/scripts/process_project.py --project lotm_book1
```

**Batch Processing with Videos**
```bash
# Process 50 chapters and create videos automatically
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-50 --create-videos
```

---

## 🎬 Video Creation Scripts

### **2. `create_videos.py`**
**Manual video creation from existing audio files**

#### **Purpose**
- Create videos from existing MP3 files
- Support multiple video types (still image, animated background)
- Parallel processing for faster video creation
- GPU-accelerated video encoding

#### **Basic Usage**
```bash
# Create single video
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1

# Create multiple videos with parallel processing
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1-10

# Use animated background
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1-5 --video-type animated_background
```

#### **Command Line Options**
```bash
python tts_pipeline/scripts/create_videos.py [OPTIONS]

Required:
  --project PROJECT_NAME    Project name

Optional:
  --chapters RANGE         Chapter range (e.g., "1", "1-10", "5-15")
  --video-type TYPE        Video type: still_image, animated_background, slideshow
  --background-image PATH  Custom background image path
  --preview               Preview mode (test settings)
  --log-level LEVEL       Set logging level
```

#### **Video Types**
- **`still_image`**: Static portrait image background (default, fastest)
- **`animated_background`**: Looping video background (muted audio)
- **`slideshow`**: Multiple images with transitions

#### **Practical Examples**

**Creating Videos for Existing Audio**
```bash
# Create videos for chapters 1-20 (using pre-resized portraits)
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1-20

# Create videos with custom background
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1-5 --background-image ./custom_bg.jpg

# Test video creation settings
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1 --preview
```

**Performance Optimization**
```bash
# Process multiple videos in parallel (up to 6 concurrent)
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1-30
# Output: "Processing 30 chapters with 6 parallel workers"
```

---

## 🔧 Utility Scripts

### **File-Based Progress Tracking System** ⭐ **NEW**

The TTS Pipeline now uses a **file-based progress tracking system** that provides superior reliability and accuracy compared to traditional database approaches.

#### **Key Features**
- **File-Based Truth**: Counts actual audio and video files on disk
- **Self-Healing**: Automatically corrects discrepancies
- **Gap Detection**: Finds missing chapters in sequence
- **No Database Corruption**: Eliminates phantom records and inconsistencies
- **Real-Time Accuracy**: Always reflects current file system state

#### **How It Works**
```python
# The system scans actual files:
audio_files = {
    "Chapter_1_Crimson.txt": Path("Chapter_1_Crimson.mp3"),
    "Chapter_2_Situation.txt": Path("Chapter_2_Situation.mp3"),
    # ... only files that actually exist
}

# Then finds the first missing chapter:
for chapter in chapters_1_to_1432:
    if chapter_filename not in audio_files:
        return chapter  # This is the next chapter to process
```

#### **Benefits Over Database Tracking**
- ✅ **No corruption issues** - files can't be "phantom"
- ✅ **Gap detection** - automatically finds missing chapters
- ✅ **Self-healing** - corrects inconsistencies automatically
- ✅ **Real-time accuracy** - reflects actual file state
- ✅ **Simpler maintenance** - no database repair needed

#### **Usage Examples**
```bash
# Check status using file-based tracking
python tts_pipeline/scripts/check_project_status_v2.py --project lotm_book1

# Process next chapters (automatically uses file-based detection)
python tts_pipeline/scripts/process_next_chapters.py --project lotm_book1 --count 10

# Show next 5 chapters that need processing
python tts_pipeline/scripts/check_project_status_v2.py --project lotm_book1 --next 5
```

---

### **3. `check_project_status_v2.py`** ⭐ **RECOMMENDED**
**File-based project status monitoring and progress tracking**

#### **Purpose**
- Display comprehensive project status using file-based tracking
- Show audio and video completion counts based on actual files
- Identify next chapters to process with gap detection
- Volume-by-volume breakdown
- **Self-healing**: Always reflects actual file system state

#### **Basic Usage**
```bash
# Basic status check (file-based)
python tts_pipeline/scripts/check_project_status_v2.py --project lotm_book1

# Detailed status with volume breakdown
python tts_pipeline/scripts/check_project_status_v2.py --project lotm_book1 --detailed

# Show next N chapters to process
python tts_pipeline/scripts/check_project_status_v2.py --project lotm_book1 --next 10
```

#### **Command Line Options**
```bash
python tts_pipeline/scripts/check_project_status_v2.py [OPTIONS]

Required:
  --project PROJECT_NAME    Project name to check

Optional:
  --detailed              Show detailed volume breakdown
  --next N                Show next N chapters to process
  --log-level LEVEL       Set logging level
```

#### **Key Advantages**
- **No database corruption** - counts actual files only
- **Gap detection** - automatically finds missing chapters
- **Real-time accuracy** - reflects current file system state
- **Self-healing** - corrects discrepancies automatically

### **3b. `check_project_status.py`** (Legacy)
**Legacy database-based status checker (deprecated)**

#### **Sample Output**
```
============================================================
PROJECT STATUS: Lord of the Mysteries - Book 1
============================================================
Project: lotm_book1
Total Chapters: 1,432 across 9 volumes
Last Updated: 2025-10-24T11:24:03.807770

AUDIO STATUS:
Completed: 45/1,432 chapters (3.1%)
Next Chapter: Chapter_46_Portrait.txt (Volume 1)

VIDEO STATUS:
Completed: 45/1,432 chapters (3.1%)
Next Chapter: Chapter_46_Portrait.txt (Volume 1)

============================================================
```

#### **With Detailed Breakdown**
```bash
python tts_pipeline/scripts/check_project_status_v2.py --project lotm_book1 --detailed
```

```
VOLUME BREAKDOWN:
  1___VOLUME_1___CLOWN:
    Audio: 45/213 chapters (21.1%)
    Video: 45/213 chapters (21.1%)
  2___VOLUME_2___FACELESS:
    Audio: 0/213 chapters (0.0%)
    Video: 0/213 chapters (0.0%)
  [... other volumes ...]
```

---

### **4. `prepare_portrait_images.py`**
**Pre-resize portrait images for optimal video performance**

#### **Purpose**
- Resize all portrait images to 1920x1080
- Eliminate scaling bottleneck during video creation
- Maintain aspect ratio with black padding
- Significant performance improvement (5-8x faster video creation)

#### **Usage**
```bash
# Resize all portrait images
python tts_pipeline/scripts/prepare_portrait_images.py
```

#### **What It Does**
- Scans `tts_pipeline/assets/images/` for portrait files
- Creates resized versions in `tts_pipeline/assets/images/resized/`
- Names files as `{original_name}_1920x1080.{extension}`
- Skips already resized images

#### **Performance Impact**
- **Before**: 3-4 minutes per video (with scaling)
- **After**: ~30 seconds per video (pre-resized)
- **Improvement**: 5-8x faster video creation

---


## 📝 Text Processing Scripts

### **5. `format_text_for_tts.py`**
**Format raw text files for TTS processing**

#### **Purpose**
- Convert PDF-extracted text to TTS-friendly format
- Join broken sentences within paragraphs
- Preserve paragraph breaks
- Optimize for Azure TTS processing

#### **Usage**
```bash
# Format single file
python tts_pipeline/scripts/format_text_for_tts.py --input Chapter_1.txt --output formatted_Chapter_1.txt

# Format entire directory
python tts_pipeline/scripts/format_text_for_tts.py --input extracted_text/lotm_book1 --output formatted_text/lotm_book1
```

#### **Command Line Options**
```bash
python tts_pipeline/scripts/format_text_for_tts.py [OPTIONS]

Required:
  --input PATH            Input file or directory
  --output PATH           Output file or directory

Optional:
  --log-level LEVEL       Set logging level
```

#### **Text Transformation**
**Before (PDF-extracted):**
```
This is a sentence that was
broken across multiple lines
because of page boundaries.

This is another paragraph
with more broken sentences.
```

**After (TTS-optimized):**
```
This is a sentence that was broken across multiple lines because of page boundaries.

This is another paragraph with more broken sentences.
```

### **6. `process_next_chapters.py`**
**Process the next X chapters starting from where you left off**

#### **Purpose**
- Process a specific number of chapters starting from the next unprocessed chapter
- Useful for batch processing without specifying exact chapter ranges
- Automatically skips already completed chapters

#### **Usage**
```bash
# Process next 10 chapters
python tts_pipeline/scripts/process_next_chapters.py --project lotm_book1 --count 10

# Process next 5 chapters with video creation
python tts_pipeline/scripts/process_next_chapters.py --project lotm_book1 --count 5 --create-videos

# Preview what would be processed
python tts_pipeline/scripts/process_next_chapters.py --project lotm_book1 --count 10 --preview
```

#### **Command Line Options**
```bash
python tts_pipeline/scripts/process_next_chapters.py [OPTIONS]

Required:
  --project PROJECT_NAME    Project name to process
  --count N                Number of chapters to process

Optional:
  --create-videos         Create videos after audio generation
  --dry-run              Test mode (no actual API calls)
  --preview              Show what would be processed without processing
  --log-level LEVEL      Set logging level
```

---

### **7. `process_until_chapter.py`**
**Process chapters until reaching a specific chapter number**

#### **Purpose**
- Process chapters starting from where you left off until reaching a target chapter
- Useful for processing up to a certain point without going beyond it
- Automatically skips already completed chapters

#### **Usage**
```bash
# Process until chapter 50
python tts_pipeline/scripts/process_until_chapter.py --project lotm_book1 --until 50

# Process until chapter 100 with video creation
python tts_pipeline/scripts/process_until_chapter.py --project lotm_book1 --until 100 --create-videos

# Preview what would be processed
python tts_pipeline/scripts/process_until_chapter.py --project lotm_book1 --until 30 --preview
```

#### **Command Line Options**
```bash
python tts_pipeline/scripts/process_until_chapter.py [OPTIONS]

Required:
  --project PROJECT_NAME    Project name to process
  --until N                Process until this chapter number (inclusive)

Optional:
  --create-videos         Create videos after audio generation
  --dry-run              Test mode (no actual API calls)
  --preview              Show what would be processed without processing
  --log-level LEVEL      Set logging level
```

---

---

## 🔧 Utility Scripts

### **8. `fix_progress_tracking_v2.py`**
**Comprehensive progress tracking repair and maintenance tool**

#### **Purpose**
- Fix inconsistencies in progress.json files
- Update audio/video completion status based on actual files
- Remove orphaned records
- Add missing records for existing files
- Handle both old and new progress file formats

#### **Usage**
```bash
# Fix progress tracking for a project
python tts_pipeline/scripts/fix_progress_tracking_v2.py --project lotm_book1
```

#### **What It Does**
- Scans actual audio and video files
- Updates completion status to match actual files
- Removes records for non-existent files
- Adds missing records for existing files
- Maintains data integrity

### **9. `setup_ffmpeg_path.py`**
**Automatic FFmpeg setup and PATH configuration**

#### **Purpose**
- Detect FFmpeg installation
- Automatically add FFmpeg to system PATH
- Verify FFmpeg functionality
- Handle Windows-specific PATH issues

#### **Usage**
```bash
# Set up FFmpeg automatically
python tts_pipeline/scripts/setup_ffmpeg_path.py
```

---

## 📊 Common Workflows

### **Starting a New Project**
```bash
# 1. Check project status (file-based)
python tts_pipeline/scripts/check_project_status_v2.py --project lotm_book1 --detailed

# 2. Test with dry run
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-3 --dry-run

# 3. Process first batch
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-10

# 4. Create videos for processed chapters
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1-10
```

### **Batch Processing with Specific Counts**
```bash
# Process next 20 chapters from where you left off
python tts_pipeline/scripts/process_next_chapters.py --project lotm_book1 --count 20

# Process until chapter 50 (from where you left off)
python tts_pipeline/scripts/process_until_chapter.py --project lotm_book1 --until 50

# Process next 10 chapters with videos (RECOMMENDED)
python tts_pipeline/scripts/process_next_chapters.py --project lotm_book1 --count 10 --create-videos
```

### **Resuming After Interruption**
```bash
# 1. Check current status (file-based)
python tts_pipeline/scripts/check_project_status_v2.py --project lotm_book1

# 2. Resume processing
python tts_pipeline/scripts/process_project.py --project lotm_book1

# 3. Create videos for new audio files
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 11-20
```

### **Batch Processing with Videos** ⭐ **RECOMMENDED**
```bash
# Process 50 chapters with automatic video creation
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-50 --create-videos

# OR use the more efficient approach:
python tts_pipeline/scripts/process_next_chapters.py --project lotm_book1 --count 50 --create-videos
```

### **Performance Optimization**
```bash
# 1. Pre-resize portrait images (one-time setup)
python tts_pipeline/scripts/prepare_portrait_images.py

# 2. Process with optimized video creation
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1-30
# Result: ~30 seconds per video instead of 3-4 minutes
```

---

## 🔍 Troubleshooting

### **Common Issues and Solutions**

#### **"Project not found" Error**
```bash
# List available projects
python tts_pipeline/scripts/process_project.py --list-projects

# Check project configuration
ls tts_pipeline/config/projects/
```

#### **"FFmpeg not found" Error**
```bash
# Install FFmpeg (Windows)
# Download from https://ffmpeg.org/download.html
# Add to PATH: C:\ffmpeg\bin

# Verify installation
ffmpeg -version
```

#### **"Azure TTS connection failed" Error**
```bash
# Check .env file
cat .env
# Should contain:
# AZURE_TTS_SUBSCRIPTION_KEY=your_key_here
# AZURE_TTS_REGION=westus

# Test connection
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1 --dry-run
```

#### **Video Creation Timeouts**
```bash
# Use pre-resized images
python tts_pipeline/scripts/prepare_portrait_images.py

# Process fewer videos at once
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1-5
```

---

## 📈 Performance Tips

### **Audio Processing**
- **Chunking**: Large chapters are automatically split into chunks
- **Retry Logic**: Failed chunks are retried with exponential backoff
- **Resume**: Processing can be resumed from any interruption point

### **Video Creation**
- **Pre-resize Images**: Use `prepare_portrait_images.py` for 5-8x speed improvement
- **Parallel Processing**: Up to 6 concurrent video workers
- **GPU Acceleration**: NVIDIA NVENC encoding for faster processing
- **Audio Copy**: Direct audio copy preserves quality without re-encoding

### **Storage Optimization**
- **SSD Usage**: Configure SSD paths for faster I/O
- **Temp Cleanup**: Temporary files are automatically cleaned up
- **Progress Tracking**: Efficient O(1) lookups for completion status

---

## 📚 Additional Resources

### **Configuration Files**
- **Project Config**: `tts_pipeline/config/projects/{project_name}/project.json`
- **Processing Config**: `tts_pipeline/config/projects/{project_name}/processing_config.json`
- **Portrait Mapping**: `tts_pipeline/config/projects/{project_name}/portrait_mapping.json`

### **Output Directories**
- **Audio Files**: `{output_directory}/{volume_name}/Chapter_X.mp3`
- **Video Files**: `{output_directory}/video/{volume_name}/Chapter_X.mp4`
- **Progress Tracking**: `tracking/{project_name}/progress.json`

### **Logging**
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Log Files**: Check console output for detailed processing information
- **Error Handling**: Comprehensive error messages with suggested solutions

---

*Last Updated: October 24, 2025*  
*TTS Pipeline Version: Production Ready* ✅
