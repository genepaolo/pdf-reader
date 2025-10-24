#!/usr/bin/env python3
"""
FFmpeg Path Setup Utility

This script automatically detects and sets up FFmpeg PATH for the current session.
It can be imported by other scripts to ensure FFmpeg is available.
"""

import os
import subprocess
import sys
from pathlib import Path
import logging

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def find_ffmpeg_in_project() -> Path:
    """
    Find FFmpeg executable in the project directory.
    
    Returns:
        Path to FFmpeg executable, or None if not found
    """
    # Common FFmpeg locations in the project
    possible_paths = [
        Path(__file__).parent.parent.parent / "ffmpeg" / "ffmpeg-master-latest-win64-gpl" / "bin" / "ffmpeg.exe",
        Path(__file__).parent.parent.parent / "ffmpeg" / "bin" / "ffmpeg.exe",
        Path(__file__).parent.parent.parent / "ffmpeg.exe",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

def check_ffmpeg_available() -> bool:
    """
    Check if FFmpeg is available in the current PATH.
    
    Returns:
        True if FFmpeg is available, False otherwise
    """
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False

def setup_ffmpeg_path() -> bool:
    """
    Set up FFmpeg PATH for the current session.
    
    Returns:
        True if FFmpeg is now available, False otherwise
    """
    # Check if FFmpeg is already available
    if check_ffmpeg_available():
        return True
    
    # Try to find FFmpeg in the project
    ffmpeg_path = find_ffmpeg_in_project()
    if ffmpeg_path and ffmpeg_path.exists():
        # Add FFmpeg directory to PATH
        ffmpeg_dir = ffmpeg_path.parent
        current_path = os.environ.get('PATH', '')
        if str(ffmpeg_dir) not in current_path:
            os.environ['PATH'] = str(ffmpeg_dir) + os.pathsep + current_path
            logging.info(f"Added FFmpeg to PATH: {ffmpeg_dir}")
        
        # Verify it's now available
        if check_ffmpeg_available():
            logging.info("FFmpeg is now available")
            return True
        else:
            logging.error("Failed to make FFmpeg available")
            return False
    else:
        logging.error("FFmpeg not found in project directory")
        return False

def ensure_ffmpeg_available() -> bool:
    """
    Ensure FFmpeg is available, setting it up if necessary.
    
    Returns:
        True if FFmpeg is available, False otherwise
    """
    if check_ffmpeg_available():
        return True
    
    logging.warning("FFmpeg not found in PATH, attempting to set up...")
    return setup_ffmpeg_path()

def main():
    """Main function for testing FFmpeg setup."""
    setup_logging()
    
    print("FFmpeg Path Setup Utility")
    print("=" * 40)
    
    if ensure_ffmpeg_available():
        print("[OK] FFmpeg is available!")
        
        # Test FFmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"Video: {version_line}")
            else:
                print("[ERROR] FFmpeg test failed")
        except Exception as e:
            print(f"[ERROR] Error testing FFmpeg: {e}")
    else:
        print("[ERROR] FFmpeg is not available")
        print("\nTo fix this permanently:")
        print("1. Add FFmpeg to your system PATH")
        print("2. Or place FFmpeg in the project directory")
        print("3. Or run: python tts_pipeline/scripts/setup_ffmpeg_path.py")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
