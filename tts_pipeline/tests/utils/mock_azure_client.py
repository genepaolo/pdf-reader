"""
Mock Azure TTS client for testing purposes.
"""

import time
import os
from typing import Dict, Any, Optional
from pathlib import Path


class MockAzureTTSClient:
    """Mock Azure TTS client that simulates API behavior without making real calls."""
    
    def __init__(self, subscription_key: str, region: str):
        self.subscription_key = subscription_key
        self.region = region
        self.call_count = 0
        self.failure_rate = 0.0  # 0.0 = no failures, 1.0 = always fails
        self.response_delay = 0.1  # Simulate API response time
    
    def set_failure_rate(self, rate: float):
        """Set the failure rate for testing error scenarios."""
        self.failure_rate = max(0.0, min(1.0, rate))
    
    def set_response_delay(self, delay: float):
        """Set the response delay to simulate network latency."""
        self.response_delay = delay
    
    def synthesize_speech(self, text: str, voice_name: str = "en-US-JennyNeural", 
                         output_format: str = "audio-24khz-160kbitrate-mono-mp3") -> bytes:
        """Mock speech synthesis."""
        self.call_count += 1
        
        # Simulate response delay
        time.sleep(self.response_delay)
        
        # Simulate random failures
        if self.failure_rate > 0 and (self.call_count % int(1/self.failure_rate)) == 0:
            raise Exception(f"Mock API failure (call #{self.call_count})")
        
        # Return mock audio data (just a small binary string)
        mock_audio_data = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00"
        
        # Add some variation based on text length to simulate realistic audio
        text_length = len(text)
        additional_data = b"\x00" * min(text_length // 10, 1000)  # Simulate longer audio for longer text
        
        return mock_audio_data + additional_data
    
    def save_audio_to_file(self, audio_data: bytes, file_path: str) -> str:
        """Save mock audio data to file."""
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(audio_data)
        
        return str(output_path)
    
    def get_audio_duration(self, audio_file_path: str) -> float:
        """Mock audio duration calculation based on file size."""
        if not os.path.exists(audio_file_path):
            return 0.0
        
        file_size = os.path.getsize(audio_file_path)
        # Mock calculation: larger files = longer duration
        # This is not realistic but works for testing
        duration = max(60.0, file_size / 1000)  # Minimum 1 minute
        return duration
    
    def validate_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """Mock audio file validation."""
        result = {
            "valid": False,
            "duration_seconds": 0.0,
            "file_size_bytes": 0,
            "error": None
        }
        
        try:
            if not os.path.exists(audio_file_path):
                result["error"] = "File does not exist"
                return result
            
            file_size = os.path.getsize(audio_file_path)
            duration = self.get_audio_duration(audio_file_path)
            
            result["file_size_bytes"] = file_size
            result["duration_seconds"] = duration
            result["valid"] = file_size > 0 and duration > 0
            
            if file_size == 0:
                result["error"] = "Empty file"
            elif duration < 60:  # Less than 1 minute
                result["error"] = "Audio too short"
                
        except Exception as e:
            result["error"] = str(e)
        
        return result


class MockProgressTracker:
    """Mock progress tracker for testing."""
    
    def __init__(self, tracking_file: str):
        self.tracking_file = tracking_file
        self.progress_data = {
            "current_volume": None,
            "current_chapter": None,
            "last_processed": None,
            "total_chapters_found": 0,
            "chapters_processed": 0,
            "chapters_failed": 0,
            "estimated_remaining": "Unknown"
        }
        self.completed_chapters = {}
        self.failed_chapters = {}
    
    def load_progress(self) -> Dict[str, Any]:
        """Load progress from file (mock implementation)."""
        return self.progress_data.copy()
    
    def save_progress(self, progress_data: Dict[str, Any]) -> None:
        """Save progress to file (mock implementation)."""
        self.progress_data.update(progress_data)
    
    def mark_chapter_completed(self, chapter_name: str, audio_file: str, 
                              duration: float, volume: str) -> None:
        """Mark a chapter as completed."""
        self.completed_chapters[chapter_name] = {
            "audio_file": audio_file,
            "duration_seconds": duration,
            "volume": volume,
            "processed_date": "2024-01-01T00:00:00Z"
        }
        self.progress_data["chapters_processed"] += 1
    
    def mark_chapter_failed(self, chapter_name: str, error: str) -> None:
        """Mark a chapter as failed."""
        self.failed_chapters[chapter_name] = {
            "error": error,
            "failed_date": "2024-01-01T00:00:00Z"
        }
        self.progress_data["chapters_failed"] += 1
    
    def get_next_chapter(self, available_chapters: list) -> Optional[str]:
        """Get the next chapter to process."""
        if not available_chapters:
            return None
        
        # Simple logic: find first chapter not in completed or failed
        for chapter in available_chapters:
            if chapter not in self.completed_chapters and chapter not in self.failed_chapters:
                return chapter
        
        return None
