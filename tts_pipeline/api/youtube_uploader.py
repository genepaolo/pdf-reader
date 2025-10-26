"""
YouTube Uploader for TTS Pipeline

Handles video uploads to YouTube with proper metadata, playlists, and queue management.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


class YouTubeUploader:
    """Main class for YouTube video uploads."""
    
    def __init__(self, project, youtube_config: Dict[str, Any]):
        """
        Initialize YouTube uploader.
        
        Args:
            project: Project object
            youtube_config: YouTube configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.project = project
        self.config = youtube_config
        
        # Setup paths
        self.video_dir = Path(project.get_output_directory()) / "video"
        self.queue_file = Path(project.get_output_directory()) / "youtube_queue.json"
        self.progress_file = Path(project.get_output_directory()) / "youtube_progress.json"
        
        # Initialize progress tracking
        self.uploaded_videos = self._load_progress()
        self.queue = []
        
        self.logger.info(f"Initialized YouTube uploader for project: {project.project_name}")
        
        # YouTube API setup
        self.youtube_service = None
        self.credentials_path = Path(self.config.get("oauth2_credentials", ""))
        
        # OAuth2 scope required for uploads and playlists
        self.SCOPES = [
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube'
        ]
    
    def _load_progress(self) -> Dict[str, Any]:
        """Load upload progress from file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading progress: {e}")
        
        return {
            "uploaded_videos": {},
            "failed_videos": {},
            "last_upload": None,
            "total_uploaded": 0
        }
    
    def _save_progress(self):
        """Save upload progress to file."""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.uploaded_videos, f, indent=2)
            self.logger.debug(f"Progress saved to {self.progress_file}")
        except Exception as e:
            self.logger.error(f"Error saving progress: {e}")
    
    def discover_videos(self) -> List[Dict[str, Any]]:
        """
        Discover all video files for upload.
        
        Returns:
            List of video information dictionaries
        """
        if not self.video_dir.exists():
            self.logger.error(f"Video directory not found: {self.video_dir}")
            return []
        
        videos = []
        
        # Scan all volume directories
        for volume_dir in self.video_dir.iterdir():
            if volume_dir.is_dir():
                for video_file in volume_dir.glob("*.mp4"):
                    video_info = self._parse_video_filename(video_file)
                    if video_info:
                        videos.append(video_info)
        
        # Sort by volume and chapter number
        videos.sort(key=lambda x: (x.get('volume_number', 0), x.get('chapter_number', 0)))
        
        self.logger.info(f"Discovered {len(videos)} videos")
        return videos
    
    def _parse_video_filename(self, video_path: Path) -> Optional[Dict[str, Any]]:
        """Parse video filename to extract chapter and volume info."""
        import re
        
        # Extract filename
        filename = video_path.stem  # e.g., "Chapter_1_Crimson"
        
        # Parse chapter number and title
        match = re.match(r"Chapter_(\d+)_(.+)", filename)
        if not match:
            return None
        
        chapter_number = int(match.group(1))
        chapter_title = match.group(2).replace("_", " ")
        
        # Extract volume from parent directory
        volume_dir = video_path.parent.name  # e.g., "1___VOLUME_1___CLOWN"
        volume_match = re.match(r"(\d+)___VOLUME_\d+___(.+)", volume_dir)
        
        if volume_match:
            volume_number = int(volume_match.group(1))
            volume_name = volume_match.group(2)
        else:
            volume_number = 1
            volume_name = "Unknown"
        
        return {
            "filename": video_path.name,
            "filepath": str(video_path),
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "volume_number": volume_number,
            "volume_name": volume_name,
            "directory": str(video_path.parent)
        }
    
    def is_video_uploaded(self, filename: str) -> bool:
        """
        Check if a specific video has already been uploaded.
        
        Args:
            filename: Video filename (e.g., "Chapter_1_Crimson.mp4")
            
        Returns:
            True if uploaded, False otherwise
        """
        return filename in self.uploaded_videos.get("uploaded_videos", {})
    
    def get_video_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get upload information for a specific video.
        
        Args:
            filename: Video filename (e.g., "Chapter_1_Crimson.mp4")
            
        Returns:
            Dictionary with video_id and upload_time, or None if not uploaded
        """
        return self.uploaded_videos.get("uploaded_videos", {}).get(filename)
    
    def get_videos_to_upload(self, all_videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get videos that need to be uploaded (not in uploaded_videos).
        
        Args:
            all_videos: List of all discovered videos
            
        Returns:
            List of videos that need uploading
        """
        uploaded = set(self.uploaded_videos.get("uploaded_videos", {}).keys())
        
        videos_to_upload = [
            v for v in all_videos 
            if v["filename"] not in uploaded
        ]
        
        self.logger.info(f"Found {len(videos_to_upload)} videos to upload")
        return videos_to_upload
    
    def generate_metadata(self, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate YouTube metadata for a video.
        
        Args:
            video_info: Video information dictionary
            
        Returns:
            Dictionary with title, description, tags, etc.
        """
        # Get templates from config
        title_template = self.config["metadata"]["title_template"]
        desc_template = self.config["metadata"]["description_template"]
        
        # Extract project metadata
        project_meta = self.project.get_metadata()
        
        # Generate title and description
        title = title_template.format(
            chapter_number=video_info["chapter_number"],
            chapter_title=video_info["chapter_title"]
        )
        
        description = desc_template.format(
            book_title=project_meta.get("series", "Lord of the Mysteries"),
            chapter_number=video_info["chapter_number"],
            volume_number=video_info["volume_number"],
            volume_name=video_info["volume_name"]
        )
        
        tags = self.config["upload_settings"]["default_tags"]
        
        return {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "24",  # Entertainment
            "privacyStatus": self.config["upload_settings"]["privacy"]
        }
    
    def get_playlist_id(self, volume_number: int, volume_name: str) -> Optional[str]:
        """
        Get or create playlist for a volume.
        
        Args:
            volume_number: Volume number
            volume_name: Volume name
            
        Returns:
            Playlist ID or None if not configured or fails
        """
        if not self.config.get("playlists", {}).get("create_per_volume", False):
            return None
        
        if not self.youtube_service:
            self.authenticate()
        
        # Generate playlist name and description
        name_template = self.config["playlists"]["name_template"]
        desc_template = self.config["playlists"]["description_template"]
        
        playlist_name = name_template.format(
            volume_number=volume_number,
            volume_name=volume_name
        )
        playlist_desc = desc_template.format(
            volume_number=volume_number,
            volume_name=volume_name
        )
        
        # Check if playlist already exists
        existing_playlist_id = self._find_existing_playlist(playlist_name)
        if existing_playlist_id:
            self.logger.info(f"Found existing playlist: {playlist_name} ({existing_playlist_id})")
            return existing_playlist_id
        
        # Create new playlist
        try:
            self.logger.info(f"Creating new playlist: {playlist_name}")
            playlist_body = {
                'snippet': {
                    'title': playlist_name,
                    'description': playlist_desc
                },
                'status': {
                    'privacyStatus': self.config["playlists"].get("privacy", "public")
                }
            }
            
            request = self.youtube_service.playlists().insert(
                part='snippet,status',
                body=playlist_body
            )
            response = request.execute()
            
            playlist_id = response['id']
            self.logger.info(f"Created playlist: {playlist_id}")
            return playlist_id
            
        except Exception as e:
            self.logger.error(f"Error creating playlist: {e}")
            return None
    
    def _find_existing_playlist(self, playlist_name: str) -> Optional[str]:
        """Search for existing playlist by name."""
        if not self.youtube_service:
            return None
        
        try:
            # Get channel's playlists
            request = self.youtube_service.playlists().list(
                part='snippet',
                mine=True,
                maxResults=50
            )
            response = request.execute()
            
            # Search for matching playlist
            for item in response.get('items', []):
                if item['snippet']['title'] == playlist_name:
                    return item['id']
            
            return None
        except Exception as e:
            self.logger.error(f"Error searching for playlists: {e}")
            return None
    
    def add_video_to_playlist(self, video_id: str, playlist_id: str) -> bool:
        """
        Add a video to a playlist.
        
        Args:
            video_id: YouTube video ID
            playlist_id: YouTube playlist ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.youtube_service:
            self.authenticate()
        
        try:
            self.logger.info(f"Adding video {video_id} to playlist {playlist_id}")
            request = self.youtube_service.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video_id
                        }
                    }
                }
            )
            request.execute()
            self.logger.info(f"Successfully added video to playlist")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding video to playlist: {e}")
            return False
    
    def is_video_in_playlist(self, video_id: str, playlist_id: str) -> bool:
        """
        Check if a video is in a specific playlist.
        
        Args:
            video_id: YouTube video ID
            playlist_id: YouTube playlist ID
            
        Returns:
            True if video is in playlist, False otherwise
        """
        if not self.youtube_service:
            self.authenticate()
        
        try:
            # Get playlist items
            request = self.youtube_service.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50
            )
            response = request.execute()
            
            # Check if video is in list
            for item in response.get('items', []):
                if item['snippet']['resourceId']['videoId'] == video_id:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking playlist: {e}")
            return False
    
    def verify_tracker_with_youtube(self) -> Dict[str, Any]:
        """
        Verify that progress tracker matches actual YouTube channel videos.
        
        Returns:
            Dictionary with verification results including:
            - missing_in_tracker: videos on YouTube but not in tracker
            - missing_on_youtube: videos in tracker but not on YouTube
            - verified_count: videos that match
        """
        if not self.youtube_service:
            self.authenticate()
        
        results = {
            "missing_in_tracker": [],
            "missing_on_youtube": [],
            "verified_count": 0,
            "total_on_youtube": 0,
            "total_in_tracker": len(self.uploaded_videos.get("uploaded_videos", {}))
        }
        
        try:
            self.logger.info("Fetching videos from YouTube channel...")
            
            # Get all videos from YouTube channel
            channel_id = self.config.get("channel_id")
            if not channel_id:
                self.logger.warning("No channel ID configured, skipping verification")
                return results
            
            youtube_videos = {}
            next_page_token = None
            
            while True:
                # Request videos from channel
                # Note: search API only supports 'snippet' part, not 'contentDetails'
                request_params = {
                    'part': 'snippet',
                    'channelId': channel_id,
                    'type': 'video',
                    'maxResults': 50,
                    'order': 'date'
                }
                
                if next_page_token:
                    request_params['pageToken'] = next_page_token
                
                request = self.youtube_service.search().list(**request_params)
                response = request.execute()
                
                # Store video IDs
                for item in response.get('items', []):
                    video_id = item['id']['videoId']
                    title = item['snippet']['title']
                    published = item['snippet']['publishedAt']
                    
                    # Try to match with our videos by checking if title contains chapter number
                    youtube_videos[video_id] = {
                        'title': title,
                        'published': published
                    }
                
                results["total_on_youtube"] = len(youtube_videos)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            # Compare with tracker
            tracker_videos = self.uploaded_videos.get("uploaded_videos", {})
            
            for filename, info in tracker_videos.items():
                video_id = info.get("video_id")
                if video_id and video_id in youtube_videos:
                    results["verified_count"] += 1
                else:
                    results["missing_on_youtube"].append({
                        "filename": filename,
                        "video_id": video_id
                    })
            
            # Find videos on YouTube not in tracker (manual uploads?)
            for video_id in youtube_videos:
                video_info = youtube_videos[video_id]
                found = False
                
                for filename, info in tracker_videos.items():
                    if info.get("video_id") == video_id:
                        found = True
                        break
                
                if not found:
                    results["missing_in_tracker"].append({
                        "video_id": video_id,
                        "title": video_info['title'],
                        "published": video_info['published']
                    })
            
            self.logger.info(f"Verification complete: {results['verified_count']} verified, "
                           f"{len(results['missing_in_tracker'])} on YouTube not in tracker, "
                           f"{len(results['missing_on_youtube'])} in tracker but not on YouTube")
            
        except Exception as e:
            self.logger.error(f"Error verifying with YouTube: {e}")
            results["error"] = str(e)
        
        return results
    
    def can_upload_now(self) -> bool:
        """Check if enough time has passed since last upload to respect rate limits."""
        last_upload = self.uploaded_videos.get("last_upload")
        
        if last_upload is None:
            return True
        
        # Get rate limit from config (default 6 per hour)
        upload_rate = self.config["upload_settings"].get("upload_rate", 6)
        rate_unit = self.config["upload_settings"].get("rate_unit", "per_hour")
        
        # Calculate minimum time between uploads
        if rate_unit == "per_hour":
            min_interval = timedelta(hours=1) / upload_rate
        else:
            min_interval = timedelta(minutes=10)  # Default: 10 minutes
        
        last_upload_time = datetime.fromisoformat(last_upload)
        time_since_last = datetime.now() - last_upload_time
        
        return time_since_last >= min_interval
    
    def time_until_next_upload(self) -> Optional[int]:
        """Calculate seconds until next upload is allowed."""
        last_upload = self.uploaded_videos.get("last_upload")
        
        if last_upload is None:
            return 0
        
        upload_rate = self.config["upload_settings"].get("upload_rate", 6)
        min_interval = timedelta(hours=1) / upload_rate
        last_upload_time = datetime.fromisoformat(last_upload)
        time_since_last = datetime.now() - last_upload_time
        
        remaining = min_interval - time_since_last
        
        if remaining.total_seconds() > 0:
            return int(remaining.total_seconds())
        
        return 0
    
    def authenticate(self):
        """Authenticate with YouTube API."""
        creds = None
        token_file = Path("token.json")
        
        # Load existing token
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)
        
        # If there are no (valid) credentials, get them
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    self.logger.error(f"Credentials file not found: {self.credentials_path}")
                    raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.youtube_service = build('youtube', 'v3', credentials=creds)
        self.logger.info("Successfully authenticated with YouTube API")
    
    def upload_video(self, video_info: Dict[str, Any], add_to_playlist: bool = True) -> Optional[str]:
        """
        Upload a video to YouTube.
        
        Args:
            video_info: Video information dictionary
            add_to_playlist: Whether to automatically add to volume playlist
            
        Returns:
            YouTube video ID or None if upload failed
        """
        if not self.youtube_service:
            self.authenticate()
        
        # Generate metadata
        metadata = self.generate_metadata(video_info)
        
        # Create media file upload
        media = MediaFileUpload(
            video_info['filepath'],
            chunksize=-1,
            resumable=True
        )
        
        # Upload with retry logic
        try:
            self.logger.info(f"Uploading {video_info['filename']} to YouTube...")
            request = self.youtube_service.videos().insert(
                part=','.join(['snippet', 'status']),
                body={
                    'snippet': {
                        'title': metadata['title'],
                        'description': metadata['description'],
                        'tags': metadata['tags'],
                        'categoryId': metadata['categoryId']
                    },
                    'status': {
                        'privacyStatus': metadata['privacyStatus']
                    }
                },
                media_body=media
            )
            
            # Execute upload with resumable support
            response = None
            while response is None:
                status, response = request.next_chunk()
                if response:
                    video_id = response['id']
                    self.logger.info(f"Successfully uploaded: {video_id}")
                    
                    # Add to playlist if enabled
                    if add_to_playlist and self.config.get("playlists", {}).get("create_per_volume", False):
                        self._add_video_to_volume_playlist(video_id, video_info)
                    
                    return video_id
            
        except Exception as e:
            self.logger.error(f"Error uploading video: {e}")
            return None
    
    def _add_video_to_volume_playlist(self, video_id: str, video_info: Dict[str, Any]) -> Optional[str]:
        """
        Add video to its volume's playlist.
        
        Args:
            video_id: YouTube video ID
            video_info: Video information dictionary
            
        Returns:
            Playlist ID if successful, None otherwise
        """
        try:
            volume_number = video_info["volume_number"]
            volume_name = video_info["volume_name"]
            
            # Get or create playlist for this volume
            playlist_id = self.get_playlist_id(volume_number, volume_name)
            
            if not playlist_id:
                self.logger.warning("No playlist ID returned, skipping playlist addition")
                return None
            
            # Check if already in playlist
            if self.is_video_in_playlist(video_id, playlist_id):
                self.logger.info(f"Video {video_id} already in playlist {playlist_id}")
                return playlist_id
            
            # Add to playlist
            if self.add_video_to_playlist(video_id, playlist_id):
                self.logger.info(f"Added video {video_id} to playlist {playlist_id}")
                return playlist_id
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error adding to playlist: {e}")
            return None
    
    def mark_video_uploaded(self, filename: str, video_id: str, playlist_id: str = None):
        """
        Mark a video as uploaded in progress tracking.
        
        Args:
            filename: Video filename
            video_id: YouTube video ID
            playlist_id: Optional playlist ID if added to playlist
        """
        if 'uploaded_videos' not in self.uploaded_videos:
            self.uploaded_videos['uploaded_videos'] = {}
        
        video_data = {
            'video_id': video_id,
            'upload_time': datetime.now().isoformat()
        }
        
        if playlist_id:
            video_data['playlist_id'] = playlist_id
        
        self.uploaded_videos['uploaded_videos'][filename] = video_data
        self.uploaded_videos['last_upload'] = datetime.now().isoformat()
        self.uploaded_videos['total_uploaded'] = len(self.uploaded_videos['uploaded_videos'])
        self._save_progress()
        self.logger.info(f"Marked {filename} as uploaded: {video_id}")

