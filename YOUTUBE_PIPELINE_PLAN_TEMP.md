# YouTube Upload Pipeline Plan - TEMPORARY

**⚠️ DELETE THIS FILE TOMORROW - This is a temporary planning document**

## 🎬 **Video-to-YouTube Pipeline Plan**

### **📋 Overview**
Create a comprehensive pipeline that automatically uploads generated videos to YouTube with proper metadata, thumbnails, and playlist management.

---

## 🏗️ **Architecture Design**

### **Phase 7: YouTube Upload Pipeline**

#### **Core Components**
```
api/youtube_uploader.py
├── YouTubeUploader      # Main upload orchestrator
├── Authentication      # OAuth2 and API key management
├── Metadata Manager    # Video metadata and descriptions
├── Thumbnail Generator # Custom thumbnail creation
└── Playlist Manager    # Playlist and series management

scripts/upload_to_youtube.py
├── Batch Upload        # Upload multiple videos
├── Resume Upload       # Resume interrupted uploads
├── Metadata Override   # Custom metadata per video
└── Dry Run Mode        # Test without actual uploads
```

#### **Integration Points**
- **Video Creation**: Automatic upload after video generation
- **Progress Tracking**: Track upload status and URLs
- **Project Management**: YouTube-specific project configurations
- **Error Handling**: Retry logic and failure recovery

---

## 🔧 **Technical Implementation**

### **1. YouTube Data API v3 Integration**

#### **Authentication Methods**
- **OAuth2**: For user-specific uploads (recommended)
- **API Key**: For service account uploads (limited)
- **Service Account**: For automated uploads (enterprise)

#### **Required Scopes**
```python
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
```

### **2. Video Metadata System**

#### **Project-Based Metadata**
```json
{
  "youtube": {
    "channel_id": "UC...",
    "playlist_id": "PL...",
    "default_privacy": "unlisted",
    "default_category": "Entertainment",
    "default_tags": ["audiobook", "lotm", "fantasy"],
    "description_template": "Chapter {chapter_number} of {book_title}...",
    "thumbnail_template": "Chapter {chapter_number} - {chapter_title}"
  }
}
```

#### **Dynamic Metadata Generation**
- **Title**: "Chapter X: [Chapter Name] - [Book Title]"
- **Description**: Auto-generated with chapter summary, book info, timestamps
- **Tags**: Book-specific tags + chapter-specific tags
- **Thumbnail**: Custom generated thumbnails with chapter info

### **3. Upload Pipeline Features**

#### **Resumable Uploads**
- **Chunked Upload**: Handle large video files
- **Resume Logic**: Continue from interruption point
- **Progress Tracking**: Real-time upload progress
- **Error Recovery**: Retry failed uploads

#### **Batch Processing**
- **Queue System**: Upload multiple videos in sequence
- **Parallel Uploads**: Multiple concurrent uploads (API limits)
- **Priority Queue**: Upload chapters in order
- **Rate Limiting**: Respect YouTube API limits

---

## 📁 **File Structure**

### **New Files to Create**
```
tts_pipeline/
├── api/
│   └── youtube_uploader.py          # YouTube upload API client
├── config/
│   └── projects/
│       └── lotm_book1/
│           └── youtube_config.json   # YouTube-specific settings
├── scripts/
│   ├── upload_to_youtube.py         # YouTube upload script
│   └── generate_thumbnails.py       # Thumbnail generation
├── assets/
│   ├── thumbnails/                  # Generated thumbnails
│   └── templates/                   # Description templates
└── utils/
    └── youtube_metadata.py          # Metadata generation utilities
```

---

## 🎯 **Implementation Phases**

### **Phase 7A: Research & Setup** (Next Session)
1. **YouTube API Research**
   - Study YouTube Data API v3 documentation
   - Understand authentication requirements
   - Research upload limits and best practices
   - Test API access and permissions

2. **Project Configuration**
   - Design YouTube configuration schema
   - Create project-specific YouTube settings
   - Set up authentication credentials
   - Test API connectivity

### **Phase 7B: Core Uploader** (Session 2)
1. **YouTube Uploader Class**
   - Implement `YouTubeUploader` class
   - OAuth2 authentication flow
   - Basic video upload functionality
   - Error handling and retry logic

2. **Metadata Management**
   - Dynamic title generation
   - Description templates
   - Tag management
   - Category and privacy settings

### **Phase 7C: Advanced Features** (Session 3)
1. **Thumbnail Generation**
   - Custom thumbnail creation
   - Chapter-specific thumbnails
   - Template-based design
   - Automatic upload

2. **Playlist Management**
   - Series playlist creation
   - Chapter ordering
   - Playlist updates
   - Series metadata

### **Phase 7D: Integration** (Session 4)
1. **Workflow Integration**
   - Integrate with video creation
   - Automatic upload after video generation
   - Progress tracking updates
   - Error handling

2. **Batch Processing**
   - Queue system for multiple uploads
   - Resume functionality
   - Rate limiting
   - Progress monitoring

---

## 🔧 **Configuration Examples**

### **YouTube Project Configuration**
```json
{
  "youtube": {
    "enabled": true,
    "channel_id": "UC_your_channel_id",
    "playlist_id": "PL_your_playlist_id",
    "upload_settings": {
      "privacy": "unlisted",
      "category": "Entertainment",
      "default_tags": ["audiobook", "lotm", "fantasy", "chinese-novel"],
      "auto_generate_thumbnails": true,
      "upload_after_video_creation": true
    },
    "metadata": {
      "title_template": "Chapter {chapter_number}: {chapter_title} - {book_title}",
      "description_template": "Chapter {chapter_number} of {book_title}\n\n{chapter_summary}\n\n📚 Book: {book_title}\n📖 Chapter: {chapter_number}\n⏱️ Duration: {duration}\n\n#audiobook #lotm #fantasy",
      "thumbnail_template": "Chapter {chapter_number} - {chapter_title}"
    },
    "playlist": {
      "name": "Lord of the Mysteries - Book 1 (Audiobook)",
      "description": "Complete audiobook of Lord of the Mysteries Book 1",
      "privacy": "public"
    }
  }
}
```

### **Upload Script Usage**
```bash
# Upload single video
python tts_pipeline/scripts/upload_to_youtube.py --project lotm_book1 --video Chapter_1_Crimson.mp4

# Upload multiple videos
python tts_pipeline/scripts/upload_to_youtube.py --project lotm_book1 --videos 1-10

# Upload with custom metadata
python tts_pipeline/scripts/upload_to_youtube.py --project lotm_book1 --video Chapter_1_Crimson.mp4 --title "Custom Title" --description "Custom Description"

# Dry run (test without uploading)
python tts_pipeline/scripts/upload_to_youtube.py --project lotm_book1 --videos 1-5 --dry-run
```

---

## 🚀 **Integration with Existing Pipeline**

### **Updated Workflow**
```bash
# Complete pipeline: Text → Audio → Video → YouTube
python tts_pipeline/scripts/process_next_chapters.py --project lotm_book1 --count 10 --create-videos --upload-youtube

# Or step by step:
python tts_pipeline/scripts/process_next_chapters.py --project lotm_book1 --count 10 --create-videos
python tts_pipeline/scripts/upload_to_youtube.py --project lotm_book1 --videos 1-10
```

### **Progress Tracking Updates**
- **Upload Status**: Track which videos have been uploaded
- **YouTube URLs**: Store video URLs in progress tracking
- **Upload Errors**: Track failed uploads for retry
- **Metadata**: Store YouTube video IDs and metadata

---

## 📊 **Expected Benefits**

### **Automation**
- **One-Click Upload**: Automatic upload after video creation
- **Batch Processing**: Upload multiple videos efficiently
- **Resume Capability**: Continue interrupted uploads
- **Error Recovery**: Automatic retry of failed uploads

### **Content Management**
- **Organized Playlists**: Automatic series organization
- **Consistent Metadata**: Standardized titles and descriptions
- **Custom Thumbnails**: Professional-looking thumbnails
- **SEO Optimization**: Proper tags and descriptions

### **Scalability**
- **Multiple Projects**: Support different book series
- **Rate Limiting**: Respect YouTube API limits
- **Queue Management**: Handle large upload batches
- **Progress Monitoring**: Real-time upload status

---

## 🎯 **Next Steps**

1. **Research YouTube API** - Study documentation and requirements
2. **Set up YouTube Channel** - Create channel and get API credentials
3. **Design Configuration** - Plan project-specific YouTube settings
4. **Implement Core Uploader** - Basic upload functionality
5. **Test with Sample Videos** - Upload test videos to verify functionality
6. **Integrate with Pipeline** - Connect to existing video creation workflow

This pipeline will complete our **Text → Audio → Video → YouTube** workflow, making it a fully automated content creation and distribution system! 🚀

---

**⚠️ REMINDER: DELETE THIS FILE TOMORROW - This is a temporary planning document**
