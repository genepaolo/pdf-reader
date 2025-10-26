# TTS Pipeline Scripts Documentation

## 🚀 Quick Reference - Most Common Commands

### **Continue Processing from Where You Left Off** ⭐ **RECOMMENDED**
```bash
# Process next 50 chapters with videos (BEST WAY - auto-detects where you left off)
python tts_pipeline/scripts/process_project.py --project lotm_book1 --continue 50 --create-videos

# Process next 100 chapters with videos
python tts_pipeline/scripts/process_project.py --project lotm_book1 --continue 100 --create-videos

# Process next 20 chapters (audio only)
python tts_pipeline/scripts/process_project.py --project lotm_book1 --continue 20
```

### **Process Specific Chapter Ranges**
```bash
# Process chapters 103-152 with videos
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 103-152 --create-videos

# Process single chapter
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 103 --create-videos
```

### **Check Project Status**
```bash
# Check current progress
python tts_pipeline/scripts/check_project_status_v2.py --project lotm_book1
```

### **Upload Videos to YouTube**
```bash
# Upload with automatic resume (skips already uploaded videos)
python upload_queue.py --limit=10 --yes        # Upload 10 videos
python upload_queue.py --yes                   # Upload all remaining videos

# Test single chapter upload
python upload_test.py                          # Test Chapter 1 upload
```

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
  --continue N            ⭐ Process next N chapters from where you left off (auto-detects progress)
  --chapters RANGE        Chapter range (e.g., "1", "1-10", "5-15")
  --create-videos         Create videos after audio generation
  --dry-run               Test mode (no actual API calls)
  --batch-size SIZE       Override batch size configuration
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

**Resume After Interruption** ⭐ **USE THIS**
```bash
# Process next 50 chapters with videos (RECOMMENDED - auto-detects where you left off)
python tts_pipeline/scripts/process_project.py --project lotm_book1 --continue 50 --create-videos

# Process next 100 chapters with videos
python tts_pipeline/scripts/process_project.py --project lotm_book1 --continue 100 --create-videos

# Process next 20 chapters (audio only)
python tts_pipeline/scripts/process_project.py --project lotm_book1 --continue 20
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

# Process specific chapter ranges (automatically uses file-based detection)
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 103-152 --create-videos

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

## 🎥 YouTube Upload Scripts

### **1. `upload_test.py`**
**Test script for single video upload with full verification**

#### **Purpose**
- Test YouTube upload functionality
- Verify video uploads to correct playlist
- Check duplicate detection
- Verify playlist assignment

#### **Usage**
```bash
# Test Chapter 1 upload
python upload_test.py
```

#### **What It Does**
1. Checks if video is already uploaded (skips if found)
2. Creates/get playlist for the volume
3. Uploads video to YouTube
4. Adds video to playlist automatically
5. Verifies playlist assignment

---

### **2. `upload_queue.py`** ⭐ **RECOMMENDED**
**Queue-based upload script with automatic resume**

#### **Purpose**
- Upload multiple videos with automatic resume
- Respect rate limits (6 uploads/hour)
- Add videos to correct playlists
- Track progress automatically

#### **How Resume Works**
The script automatically determines where to resume by checking the `youtube_progress.json` file:

```python
# System checks file-based progress
uploaded_videos = {
    "Chapter_1_Crimson.mp4": {
        "video_id": "5_XXKMBXrFc",
        "upload_time": "2025-10-26T09:05:32",
        "playlist_id": "PLV2gvMHy77hp38Ft0ocxCzJESWShZqMr3"
    }
}

# Only uploads videos NOT in this list
videos_to_upload = [v for v in all_videos if v['filename'] not in uploaded_videos]
```

#### **Usage**
```bash
# Upload with limit (recommended for testing)
python upload_queue.py --limit=10 --yes        # Upload 10 videos
python upload_queue.py --limit=50 --yes        # Upload 50 videos

# Upload all remaining videos (auto-resumes from last upload)
python upload_queue.py --yes

# Interactive mode (asks for confirmation)
python upload_queue.py
```

#### **Features**
- ✅ **Automatic Resume**: Skips already uploaded videos
- ✅ **Rate Limiting**: Respects YouTube's 6 uploads/hour limit
- ✅ **Playlist Management**: Creates and adds videos to volume playlists
- ✅ **Progress Tracking**: Saves state after each upload
- ✅ **Error Handling**: Continues on failures, tracks them separately
- ✅ **Verification**: Checks that videos are in correct playlists

#### **Progress Tracking**
Progress is saved to: `F:\PDFReader\lotm_book1_output\youtube_progress.json`

```json
{
  "uploaded_videos": {
    "Chapter_1_Crimson.mp4": {
      "video_id": "5_XXKMBXrFc",
      "upload_time": "2025-10-26T09:05:32",
      "playlist_id": "PLV2gvMHy77hp38Ft0ocxCzJESWShZqMr3"
    }
  },
  "total_uploaded": 1
}
```

#### **Example Workflow**
```bash
# 1. Check what needs uploading
python upload_queue.py                    # Shows pending videos

# 2. Upload in batches (respects rate limit)
python upload_queue.py --limit=10 --yes   # Upload 10 videos (~3-4 hours)
python upload_queue.py --limit=10 --yes   # Upload next 10
# ... repeat until all uploaded

# 3. Or upload all at once (will take ~52 hours for 314 videos at 1 per 10 min)
python upload_queue.py --yes

# 4. Script automatically resumes if interrupted
# Just run again and it continues from last upload
python upload_queue.py --yes
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
# Process next 50 chapters from where you left off (RECOMMENDED)
python tts_pipeline/scripts/process_project.py --project lotm_book1 --continue 50 --create-videos

# Process specific chapter ranges
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 103-152 --create-videos

# Process next 100 chapters with videos
python tts_pipeline/scripts/process_project.py --project lotm_book1 --continue 100 --create-videos
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

# Process specific chapter ranges with videos
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 103-152 --create-videos
```

### **Performance Optimization**
```bash
# 1. Pre-resize portrait images (one-time setup)
python tts_pipeline/scripts/prepare_portrait_images.py

# 2. Process with optimized video creation
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1-30
# Result: ~30 seconds per video instead of 3-4 minutes
```

### **YouTube Upload Workflow** ⭐ **NEW**
```bash
# Complete workflow from text to YouTube

# 1. Process text and create videos
python tts_pipeline/scripts/process_project.py --project lotm_book1 --chapters 1-100 --create-videos

# 2. Test upload (verify one video works)
python upload_test.py

# 3. Upload in batches with automatic resume
python upload_queue.py --limit=10 --yes   # Upload 10 videos (~3-4 hours)
python upload_queue.py --limit=10 --yes   # Upload next 10

# 4. Continue until all uploaded
# Script automatically resumes from last upload
python upload_queue.py --yes

# If interrupted, just run again - it resumes automatically!
python upload_queue.py --yes
```

#### **How Resume Works**
- Progress is tracked in `F:\PDFReader\lotm_book1_output\youtube_progress.json`
- Script checks which videos are already uploaded
- Automatically skips uploaded videos
- Continues from next video that needs uploading
- Rate limiting is respected (6 uploads/hour)

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
