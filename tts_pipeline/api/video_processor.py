#!/usr/bin/env python3
"""
Video Processor for TTS Pipeline

This module handles video creation by combining audio files with background visuals
for YouTube-ready content. Supports both manual and automatic video generation.

Features:
- Multiple video types (still image, animated background, slideshow)
- FFmpeg integration for high-quality video processing
- YouTube-optimized output settings
- Batch processing capabilities
- Progress tracking integration
- Error handling and retry logic

Usage:
    from api.video_processor import VideoProcessor
    
    processor = VideoProcessor(project_config)
    success = processor.create_video(audio_path, output_path, video_type="still_image")
"""

import os
import subprocess
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json

# Import FFmpeg setup utility
try:
    from scripts.setup_ffmpeg_path import ensure_ffmpeg_available
except ImportError:
    # Fallback if import fails
    def ensure_ffmpeg_available():
        return True
import shutil


class VideoProcessor:
    """Handles video creation from audio files and background visuals."""
    
    def __init__(self, project_config: Dict[str, Any]):
        """
        Initialize the video processor.
        
        Args:
            project_config: Project configuration containing video settings
        """
        self.config = project_config
        self.logger = logging.getLogger(__name__)
        
        # Extract video configuration
        self.video_config = self.config.get('video', {})
        self.enabled = self.video_config.get('enabled', False)
        
        if not self.enabled:
            self.logger.warning("Video processing is disabled in configuration")
            return
        
        # Video settings
        self.output_dir = Path(self.video_config.get('output_directory', './video_output'))
        self.temp_dir = Path(self.video_config.get('temp_directory', './temp_video'))
        self.video_type = self.video_config.get('video_type', 'still_image')
        
        # Resolve default image path relative to project
        default_image_path = self.video_config.get('default_image', './assets/images/default_cover.jpg')
        if not Path(default_image_path).is_absolute():
            # Try to resolve relative to project root
            project_root = Path(__file__).parent.parent.parent  # Go up to project root
            self.default_image = project_root / default_image_path
        else:
            self.default_image = default_image_path
        
        # Format settings
        self.format_config = self.video_config.get('format', {})
        self.resolution = self.format_config.get('resolution', '1920x1080')
        self.video_codec = self.format_config.get('video_codec', 'libx264')
        self.audio_codec = self.format_config.get('audio_codec', 'aac')
        self.audio_bitrate = self.format_config.get('audio_bitrate', '128k')
        self.pixel_format = self.format_config.get('pixel_format', 'yuv420p')
        
        # Compression settings
        self.compression_config = self.video_config.get('compression', {})
        self.compression_enabled = self.compression_config.get('enabled', True)
        self.crf = self.compression_config.get('crf', 23)
        self.preset = self.compression_config.get('preset', 'fast')
        self.optimize_streaming = self.compression_config.get('optimize_streaming', True)
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Check FFmpeg availability
        self._check_ffmpeg()
        
        self.logger.info(f"Video processor initialized for project: {self.config.get('project_name', 'unknown')}")
        self.logger.info(f"Video type: {self.video_type}, Output: {self.output_dir}")
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available and working."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.info("FFmpeg is available and working")
                return True
            else:
                self.logger.error("FFmpeg is not working properly")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"FFmpeg not found or not working: {e}")
            self.logger.info("Attempting to set up FFmpeg automatically...")
            
            # Try to set up FFmpeg automatically
            if ensure_ffmpeg_available():
                self.logger.info("FFmpeg setup successful, retrying...")
                # Retry the check
                try:
                    result = subprocess.run(['ffmpeg', '-version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.logger.info("FFmpeg is now available and working")
                        return True
                except Exception as retry_error:
                    self.logger.error(f"FFmpeg still not working after setup: {retry_error}")
            else:
                self.logger.error("Failed to set up FFmpeg automatically")
                self.logger.error("Please install FFmpeg and ensure it's in your PATH")
            return False
    
    def create_video(self, audio_path: str, output_path: str, 
                    video_type: Optional[str] = None,
                    background_image: Optional[str] = None,
                    chapter_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a video from audio file and background visuals.
        
        Args:
            audio_path: Path to the audio file
            output_path: Path for the output video file
            video_type: Type of video to create (overrides config)
            background_image: Custom background image path
            chapter_info: Chapter metadata for dynamic content
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            self.logger.warning("Video processing is disabled")
            return False
        
        try:
            audio_file = Path(audio_path)
            output_file = Path(output_path)
            
            if not audio_file.exists():
                self.logger.error(f"Audio file not found: {audio_path}")
                return False
            
            # Determine video type
            video_type = video_type or self.video_type
            
            # Create output directory
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Creating {video_type} video: {audio_file.name} -> {output_file.name}")
            
            # Route to appropriate video creation method
            if video_type == "still_image":
                success = self._create_still_image_video(audio_file, output_file, background_image, chapter_info)
            elif video_type == "animated_background":
                success = self._create_animated_background_video(audio_file, output_file, background_image, chapter_info)
            elif video_type == "slideshow":
                success = self._create_slideshow_video(audio_file, output_file, chapter_info)
            else:
                self.logger.error(f"Unsupported video type: {video_type}")
                return False
            
            if success:
                self.logger.info(f"Successfully created video: {output_file}")
                return True
            else:
                self.logger.error(f"Failed to create video: {output_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating video: {e}")
            return False
    
    def _create_still_image_video(self, audio_file: Path, output_file: Path, 
                                background_image: Optional[str] = None,
                                chapter_info: Optional[Dict[str, Any]] = None) -> bool:
        """Create a video with a still background image."""
        try:
            # Determine background image
            if background_image and Path(background_image).exists():
                image_path = background_image
            else:
                # Try to get portrait image based on chapter info
                portrait_image = self._get_portrait_for_chapter(chapter_info)
                if portrait_image and Path(portrait_image).exists():
                    image_path = portrait_image
                    self.logger.info(f"Using portrait image: {Path(portrait_image).name}")
                elif Path(self.default_image).exists():
                    image_path = self.default_image
                else:
                    self.logger.error(f"No background image found: {self.default_image}")
                    return False
            
            # Get audio duration
            duration = self._get_audio_duration(audio_file)
            if duration is None:
                return False
            
            # Build FFmpeg command with GPU hardware acceleration (optimized for pre-resized images)
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-loop', '1',  # Loop the image
                '-i', str(image_path),  # Input image (already 1920x1080)
                '-i', str(audio_file),  # Input audio
                '-c:v', 'h264_nvenc',  # NVIDIA GPU hardware acceleration
                '-preset', 'p1',  # Fastest NVENC preset
                '-rc', 'vbr',  # Variable bitrate for efficiency
                '-cq', '18',  # Constant quality (18 = high quality)
                '-c:a', 'copy',  # Copy audio without re-encoding (preserves quality)
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                '-shortest',  # End when shortest input ends
                '-r', '1',  # Low frame rate for still images (much faster)
                '-g', '1',  # Keyframe every frame (for still images)
            ]
            
            # Add streaming optimization
            if self.optimize_streaming:
                cmd.extend(['-movflags', '+faststart'])
            
            cmd.append(str(output_file))
            
            self.logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            # Execute FFmpeg with longer timeout (20 minutes)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
            
            if result.returncode == 0:
                self.logger.info(f"Still image video created successfully: {output_file}")
                return True
            else:
                self.logger.error(f"FFmpeg failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("FFmpeg command timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error creating still image video: {e}")
            return False
    
    def _create_animated_background_video(self, audio_file: Path, output_file: Path,
                                        background_image: Optional[str] = None,
                                        chapter_info: Optional[Dict[str, Any]] = None) -> bool:
        """Create a video with animated background video (looping)."""
        try:
            # Check for video background first
            video_background_path = self._find_video_background()
            
            if video_background_path:
                return self._create_video_with_video_background(audio_file, output_file, video_background_path)
            
            # Fallback to image with zoom effect
            if background_image and Path(background_image).exists():
                image_path = background_image
            elif Path(self.default_image).exists():
                image_path = self.default_image
            else:
                self.logger.error(f"No background image or video found")
                return False
            
            # Get audio duration
            duration = self._get_audio_duration(audio_file)
            if duration is None:
                return False
            
            # Create animated background with zoom effect
            cmd = [
                'ffmpeg',
                '-y',
                '-loop', '1',
                '-i', str(image_path),
                '-i', str(audio_file),
                '-c:v', self.video_codec,
                '-c:a', self.audio_codec,
                '-b:a', self.audio_bitrate,
                '-pix_fmt', self.pixel_format,
                '-shortest',
                '-vf', f'scale={self.resolution},zoompan=z=1.1:d={int(duration * 30)}:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2)',
            ]
            
            # Add compression
            if self.compression_enabled:
                cmd.extend([
                    '-crf', str(self.crf),
                    '-preset', self.preset,
                ])
                
                if self.optimize_streaming:
                    cmd.extend(['-movflags', '+faststart'])
            
            cmd.append(str(output_file))
            
            self.logger.debug(f"FFmpeg animated command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"Animated background video created: {output_file}")
                return True
            else:
                self.logger.error(f"FFmpeg animated failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating animated background video: {e}")
            return False
    
    def _find_video_background(self) -> Optional[Path]:
        """Find a video file to use as animated background."""
        # Look for video files in assets/videos directory
        project_root = Path(__file__).parent.parent.parent  # Go up to project root
        video_dirs = [
            project_root / 'assets' / 'videos',
            project_root / 'tts_pipeline' / 'assets' / 'videos',
            Path(self.default_image).parent.parent / 'videos',
        ]
        
        for video_dir in video_dirs:
            if video_dir.exists():
                # Look for common video formats
                for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv']:
                    video_files = list(video_dir.glob(ext))
                    if video_files:
                        # Use the first video file found
                        video_path = video_files[0]
                        self.logger.info(f"Found video background: {video_path}")
                        return video_path
        
        self.logger.debug("No video background found, will use image fallback")
        return None
    
    def _create_video_with_video_background(self, audio_file: Path, output_file: Path, 
                                          video_background: Path) -> bool:
        """Create video using a looping video background."""
        try:
            # Get audio duration
            duration = self._get_audio_duration(audio_file)
            if duration is None:
                return False
            
            self.logger.info(f"Creating video with looping background: {video_background.name}")
            self.logger.info(f"Audio duration: {duration:.2f} seconds")
            
            # Create video with looping background (no audio from background video)
            cmd = [
                'ffmpeg',
                '-y',
                '-stream_loop', '-1',  # Loop the video indefinitely
                '-i', str(video_background),  # Background video (no audio)
                '-i', str(audio_file),  # TTS audio
                '-c:v', self.video_codec,
                '-c:a', self.audio_codec,
                '-b:a', self.audio_bitrate,
                '-pix_fmt', self.pixel_format,
                '-shortest',  # End when audio ends
                '-map', '0:v:0',  # Use video from first input (background)
                '-map', '1:a:0',  # Use audio from second input (TTS)
                '-vf', f'scale={self.resolution}',  # Scale to target resolution
            ]
            
            # Add compression
            if self.compression_enabled:
                cmd.extend([
                    '-crf', str(self.crf),
                    '-preset', self.preset,
                ])
                
                if self.optimize_streaming:
                    cmd.extend(['-movflags', '+faststart'])
            
            cmd.append(str(output_file))
            
            self.logger.debug(f"FFmpeg video background command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                self.logger.info(f"Video with looping background created: {output_file}")
                return True
            else:
                self.logger.error(f"FFmpeg video background failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("FFmpeg video background command timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error creating video with video background: {e}")
            return False
    
    def _create_slideshow_video(self, audio_file: Path, output_file: Path,
                              chapter_info: Optional[Dict[str, Any]] = None) -> bool:
        """Create a slideshow video with multiple images."""
        try:
            # This is a placeholder for slideshow functionality
            # Would require multiple images and timing configuration
            
            self.logger.warning("Slideshow video type not yet implemented, falling back to still image")
            return self._create_still_image_video(audio_file, output_file, None, chapter_info)
            
        except Exception as e:
            self.logger.error(f"Error creating slideshow video: {e}")
            return False
    
    def _get_audio_duration(self, audio_file: Path) -> Optional[float]:
        """Get the duration of an audio file in seconds."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                str(audio_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                self.logger.debug(f"Audio duration: {duration:.2f} seconds")
                return duration
            else:
                self.logger.error(f"Failed to get audio duration: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting audio duration: {e}")
            return None
    
    def batch_create_videos(self, audio_files: List[str], 
                          output_dir: Optional[str] = None,
                          video_type: Optional[str] = None) -> Dict[str, bool]:
        """
        Create videos for multiple audio files.
        
        Args:
            audio_files: List of audio file paths
            output_dir: Output directory (overrides config)
            video_type: Video type (overrides config)
            
        Returns:
            Dictionary mapping audio file paths to success status
        """
        results = {}
        
        if not self.enabled:
            self.logger.warning("Video processing is disabled")
            return {file: False for file in audio_files}
        
        output_directory = Path(output_dir) if output_dir else self.output_dir
        
        self.logger.info(f"Starting batch video creation for {len(audio_files)} files")
        
        for i, audio_file in enumerate(audio_files, 1):
            try:
                audio_path = Path(audio_file)
                
                # Generate output filename
                output_filename = audio_path.stem + '.mp4'
                output_path = output_directory / output_filename
                
                self.logger.info(f"Processing {i}/{len(audio_files)}: {audio_path.name}")
                
                success = self.create_video(
                    str(audio_path), 
                    str(output_path),
                    video_type=video_type
                )
                
                results[audio_file] = success
                
                if success:
                    self.logger.info(f"✓ Success: {output_filename}")
                else:
                    self.logger.error(f"✗ Failed: {output_filename}")
                
            except Exception as e:
                self.logger.error(f"Error processing {audio_file}: {e}")
                results[audio_file] = False
        
        successful = sum(1 for success in results.values() if success)
        self.logger.info(f"Batch video creation completed: {successful}/{len(audio_files)} successful")
        
        return results
    
    def validate_video(self, video_path: str) -> bool:
        """
        Validate that a video file is properly created and playable.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            True if video is valid, False otherwise
        """
        try:
            video_file = Path(video_path)
            
            if not video_file.exists():
                self.logger.error(f"Video file not found: {video_path}")
                return False
            
            if video_file.stat().st_size == 0:
                self.logger.error(f"Video file is empty: {video_path}")
                return False
            
            # Use ffprobe to validate the video
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                str(video_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                if duration > 0:
                    self.logger.info(f"Video validation passed: {video_file.name} ({duration:.2f}s)")
                    return True
                else:
                    self.logger.error(f"Video has zero duration: {video_path}")
                    return False
            else:
                self.logger.error(f"Video validation failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error validating video: {e}")
            return False
    
    def _get_portrait_for_chapter(self, chapter_info: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Get the appropriate portrait image for a chapter based on chapter number.
        
        Args:
            chapter_info: Chapter metadata containing chapter number
            
        Returns:
            Path to the portrait image, or None if not found
        """
        if not chapter_info:
            return None
            
        try:
            # Extract chapter number from filename or chapter_info
            chapter_number = self._extract_chapter_number(chapter_info)
            if chapter_number is None:
                self.logger.warning("Could not extract chapter number from chapter info")
                return None
            
            # Load portrait mapping configuration
            portrait_mapping = self._load_portrait_mapping()
            if not portrait_mapping:
                self.logger.debug("No portrait mapping configuration found")
                return None
            
            # Find the appropriate portrait for this chapter
            portrait_image = self._find_portrait_for_chapter(chapter_number, portrait_mapping)
            if portrait_image:
                # Try pre-resized image first (much faster)
                project_root = Path(__file__).parent.parent.parent  # Go up to project root
                resized_dir = project_root / 'tts_pipeline' / 'assets' / 'images' / 'resized'
                resized_filename = f"{Path(portrait_image).stem}_1920x1080{Path(portrait_image).suffix}"
                resized_path = resized_dir / resized_filename
                
                if resized_path.exists():
                    self.logger.debug(f"Using pre-resized portrait: {resized_filename}")
                    return str(resized_path)
                
                # Fallback to original image
                assets_dir = project_root / 'tts_pipeline' / 'assets' / 'images'
                full_path = assets_dir / portrait_image
                if full_path.exists():
                    self.logger.warning(f"Using original portrait (not pre-resized): {portrait_image}")
                    return str(full_path)
                else:
                    self.logger.warning(f"Portrait image not found: {full_path}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting portrait for chapter: {e}")
            return None
    
    def _extract_chapter_number(self, chapter_info: Dict[str, Any]) -> Optional[int]:
        """Extract chapter number from chapter info."""
        try:
            # Try to extract from filename (e.g., "Chapter_1_Crimson.txt" -> 1)
            filename = chapter_info.get('filename', '')
            if filename:
                import re
                match = re.search(r'Chapter_(\d+)_', filename)
                if match:
                    return int(match.group(1))
            
            # Try to extract from chapter_number if available
            if 'chapter_number' in chapter_info:
                return int(chapter_info['chapter_number'])
                
            return None
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error extracting chapter number: {e}")
            return None
    
    def _load_portrait_mapping(self) -> Optional[Dict[str, Any]]:
        """Load portrait mapping configuration from JSON file."""
        try:
            # Look for portrait mapping in project config directory
            project_root = Path(__file__).parent.parent.parent  # Go up to project root
            
            # Try to get project name from config if available
            project_name = self.config.get('project_name', 'lotm_book1')
            
            config_paths = [
                project_root / 'tts_pipeline' / 'config' / 'projects' / project_name / 'portrait_mapping.json',
                project_root / 'config' / 'projects' / project_name / 'portrait_mapping.json',
                project_root / 'portrait_mapping.json'
            ]
            
            for config_path in config_paths:
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        mapping = json.load(f)
                        self.logger.debug(f"Loaded portrait mapping from: {config_path}")
                        return mapping
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading portrait mapping: {e}")
            return None
    
    def _find_portrait_for_chapter(self, chapter_number: int, portrait_mapping: Dict[str, Any]) -> Optional[str]:
        """Find the appropriate portrait image for a given chapter number."""
        try:
            mapping = portrait_mapping.get('portrait_mapping', {})
            
            for range_str, config in mapping.items():
                if self._is_chapter_in_range(chapter_number, range_str):
                    portrait_image = config.get('image')
                    if portrait_image:
                        self.logger.debug(f"Chapter {chapter_number} maps to {portrait_image} (range: {range_str})")
                        return portrait_image
            
            # Fallback to default image
            fallback = portrait_mapping.get('fallback_image')
            if fallback:
                self.logger.debug(f"Using fallback portrait: {fallback}")
                return fallback
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding portrait for chapter {chapter_number}: {e}")
            return None
    
    def _is_chapter_in_range(self, chapter_number: int, range_str: str) -> bool:
        """Check if a chapter number falls within a given range string."""
        try:
            if '-' in range_str:
                start, end = map(int, range_str.split('-'))
                return start <= chapter_number <= end
            else:
                # Single number
                return chapter_number == int(range_str)
                
        except (ValueError, TypeError):
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during video processing."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
                self.logger.info("Temporary files cleaned up")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp files: {e}")


def main():
    """Test the video processor with sample files."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test video processor")
    parser.add_argument('--audio', required=True, help='Audio file path')
    parser.add_argument('--output', required=True, help='Output video path')
    parser.add_argument('--config', help='Project config file')
    parser.add_argument('--type', default='still_image', 
                      choices=['still_image', 'animated_background', 'slideshow'],
                      help='Video type')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        # Default configuration
        project_root = Path(__file__).parent.parent.parent  # Go up to project root
        config = {
            'project_name': 'test',
            'video': {
                'enabled': True,
                'video_type': args.type,
                'output_directory': str(project_root / 'test_video_output'),
                'temp_directory': str(project_root / 'test_video_temp'),
                'format': {
                    'resolution': '1920x1080',
                    'video_codec': 'libx264',
                    'audio_codec': 'aac',
                    'audio_bitrate': '128k',
                    'pixel_format': 'yuv420p'
                },
                'compression': {
                    'enabled': True,
                    'crf': 23,
                    'preset': 'fast',
                    'optimize_streaming': True
                }
            }
        }
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create video processor
    processor = VideoProcessor(config)
    
    # Create video
    success = processor.create_video(args.audio, args.output, video_type=args.type)
    
    if success:
        print(f"✓ Video created successfully: {args.output}")
        
        # Validate video
        if processor.validate_video(args.output):
            print("✓ Video validation passed")
        else:
            print("✗ Video validation failed")
    else:
        print(f"✗ Failed to create video: {args.output}")


if __name__ == "__main__":
    main()

