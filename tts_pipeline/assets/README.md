# Video Assets Setup

This directory contains video assets for the TTS pipeline.

## Default Background Image

The `default_cover.jpg` file should be a high-quality image suitable for YouTube videos:
- Resolution: 1920x1080 or higher
- Format: JPG or PNG
- Content: Book cover, series artwork, or generic fantasy background
- File size: Under 5MB for efficient processing

## Custom Background Images

You can place custom background images here and reference them in:
- Manual video creation: `--background-image ./assets/images/custom_bg.jpg`
- Project configuration: Update `default_image` in video config

## Recommended Image Types

1. **Book Covers**: Official book covers work great
2. **Series Artwork**: Character art or scene illustrations
3. **Generic Backgrounds**: Abstract patterns or textures
4. **Chapter-Specific**: Different images per volume/chapter

## Usage Examples

```bash
# Use default image
python scripts/create_videos.py --project lotm_book1 --chapters 1-5

# Use custom background
python scripts/create_videos.py --project lotm_book1 --chapters 1-5 --background-image ./assets/images/lotm_cover.jpg

# Create animated background videos
python scripts/create_videos.py --project lotm_book1 --chapters 1-3 --video-type animated_background
```

## File Organization

```
assets/
├── images/
│   ├── lotm_*.jpg                 # LOTM character portraits
│   ├── resized/                   # Pre-resized images (1920x1080)
│   └── lotm_cover.jpg             # LOTM specific cover
├── videos/
│   └── lotm.mp4                   # Animated background video
└── README.md                      # This file
```

## 🔧 FFmpeg Setup

### **Automatic Setup (Recommended)**
FFmpeg is automatically detected and set up by the system:

```bash
# FFmpeg is auto-detected when needed
python tts_pipeline/scripts/create_videos.py --project lotm_book1 --chapters 1-5
```

### **Manual Setup**
If you need to install FFmpeg manually:

```bash
# Windows (Chocolatey)
choco install ffmpeg

# macOS (Homebrew)  
brew install ffmpeg

# Linux (apt)
sudo apt install ffmpeg
```

### **Project-Local FFmpeg**
- **Location**: `ffmpeg/` directory in project root
- **Auto-detection**: Scripts automatically find and use local FFmpeg
- **Not committed**: FFmpeg binaries are in `.gitignore`
- **Cross-platform**: Works on Windows, Linux, macOS


