#!/usr/bin/env python3
"""
TTS Batch Processor

Converts text files to audio using various TTS services.
Supports batch processing with progress tracking and resume capability.
"""

import os
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import threading
from datetime import datetime, timedelta
import uuid


class TTSBatchProcessor:
    """Processes text files in batches for TTS conversion."""
    
    def __init__(self, input_dir: str = "input", output_dir: str = "output", config_dir: str = "config"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.config_dir = Path(config_dir)
        
        # Create directories
        self.output_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # Tracking files
        self.tracking_dir = Path("tracking")
        self.tracking_dir.mkdir(exist_ok=True)
        
        self.converted_file = self.tracking_dir / "converted.json"
        self.failed_file = self.tracking_dir / "failed.json"
        self.progress_file = self.tracking_dir / "progress.json"
        self.metadata_file = self.tracking_dir / "metadata.json"
        
        # Load tracking data
        self.converted_data = self._load_json(self.converted_file, {"converted_files": [], "total_converted": 0})
        self.failed_data = self._load_json(self.failed_file, {"failed_files": [], "total_failed": 0})
        self.progress_data = self._load_json(self.progress_file, {"current_batch": {}, "batch_history": []})
        self.metadata = self._load_json(self.metadata_file, {"file_metadata": {}, "statistics": {}})
        
        # Processing state
        self.is_processing = False
        self.current_batch_id = None
        self.start_time = None
        
    def _load_json(self, file_path: Path, default: Dict) -> Dict:
        """Load JSON file with default fallback."""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"WARNING: Could not load {file_path}: {e}")
        return default
    
    def _save_json(self, file_path: Path, data: Dict):
        """Save data to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def get_input_files(self) -> List[Path]:
        """Get all text files in input directory."""
        if not self.input_dir.exists():
            return []
        
        return list(self.input_dir.glob("*.txt"))
    
    def load_tts_config(self, service: str) -> Dict:
        """Load TTS service configuration."""
        config_file = self.config_dir / f"{service}_config.json"
        
        if not config_file.exists():
            print(f"ERROR: Configuration file {config_file} not found")
            print(f"Please create {config_file} with your {service} credentials")
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR: Could not load {service} config: {e}")
            return {}
    
    def simulate_tts_conversion(self, text_file: Path, config: Dict) -> Tuple[bool, str, Dict]:
        """
        Simulate TTS conversion (placeholder for actual TTS service integration).
        Returns: (success, output_file_path, metadata)
        """
        try:
            # Read text file
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simulate processing time based on content length
            word_count = len(content.split())
            processing_time = max(1, word_count // 100)  # ~1 second per 100 words
            
            print(f"  Processing {text_file.name} ({word_count} words)...")
            time.sleep(min(processing_time, 5))  # Cap at 5 seconds for demo
            
            # Create output filename
            output_filename = text_file.stem + ".mp3"
            output_path = self.output_dir / output_filename
            
            # Simulate file creation (in real implementation, this would be the actual audio file)
            with open(output_path, 'w') as f:
                f.write(f"# Simulated audio file for {text_file.name}\n")
                f.write(f"# Word count: {word_count}\n")
                f.write(f"# Generated at: {datetime.now()}\n")
            
            # Calculate metadata
            metadata = {
                "input_file": str(text_file),
                "output_file": str(output_path),
                "word_count": word_count,
                "processing_time": processing_time,
                "file_size": len(content),
                "timestamp": datetime.now().isoformat(),
                "service": config.get("service", "simulated"),
                "voice": config.get("voice", "default")
            }
            
            return True, str(output_path), metadata
            
        except Exception as e:
            return False, "", {"error": str(e)}
    
    def process_batch(self, count: int, service: str = "simulated", 
                     voice: Optional[str] = None, resume: bool = False) -> Dict:
        """Process a batch of files."""
        if self.is_processing:
            print("ERROR: Already processing a batch")
            return {"success": False, "error": "Already processing"}
        
        # Load configuration
        config = self.load_tts_config(service)
        if not config:
            return {"success": False, "error": "Invalid configuration"}
        
        if voice:
            config["voice"] = voice
        
        # Get input files
        input_files = self.get_input_files()
        if not input_files:
            print("ERROR: No input files found")
            return {"success": False, "error": "No input files"}
        
        # Filter out already converted files
        if not resume:
            unconverted_files = [f for f in input_files 
                               if f.name not in self.converted_data["converted_files"]]
        else:
            unconverted_files = input_files
        
        if not unconverted_files:
            print("All files have been converted")
            return {"success": True, "message": "All files converted"}
        
        # Limit batch size
        files_to_process = unconverted_files[:count]
        
        # Initialize batch
        self.current_batch_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        
        batch_info = {
            "batch_id": self.current_batch_id,
            "start_time": self.start_time.isoformat(),
            "files_to_process": [f.name for f in files_to_process],
            "files_completed": [],
            "files_failed": [],
            "current_file": None,
            "progress_percentage": 0,
            "service": service,
            "voice": voice
        }
        
        self.progress_data["current_batch"] = batch_info
        self._save_json(self.progress_file, self.progress_data)
        
        print(f"\nStarting batch conversion")
        print(f"   Batch ID: {self.current_batch_id}")
        print(f"   Service: {service}")
        print(f"   Voice: {voice or 'default'}")
        print(f"   Files to process: {len(files_to_process)}")
        print(f"   Start time: {self.start_time.strftime('%H:%M:%S')}")
        
        # Process files
        self.is_processing = True
        successful_conversions = 0
        failed_conversions = 0
        
        try:
            for i, text_file in enumerate(files_to_process):
                # Update progress
                batch_info["current_file"] = text_file.name
                batch_info["progress_percentage"] = (i / len(files_to_process)) * 100
                self._save_json(self.progress_file, self.progress_data)
                
                print(f"\n[{i+1}/{len(files_to_process)}] {text_file.name}")
                
                # Convert file
                success, output_path, metadata = self.simulate_tts_conversion(text_file, config)
                
                if success:
                    # Update converted files
                    self.converted_data["converted_files"].append(text_file.name)
                    self.converted_data["total_converted"] += 1
                    batch_info["files_completed"].append(text_file.name)
                    successful_conversions += 1
                    
                    # Update metadata
                    self.metadata["file_metadata"][text_file.name] = metadata
                    
                    print(f"  Success: {output_path}")
                    
                else:
                    # Update failed files
                    failed_entry = {
                        "filename": text_file.name,
                        "error": metadata.get("error", "Unknown error"),
                        "timestamp": datetime.now().isoformat(),
                        "batch_id": self.current_batch_id
                    }
                    self.failed_data["failed_files"].append(failed_entry)
                    self.failed_data["total_failed"] += 1
                    batch_info["files_failed"].append(text_file.name)
                    failed_conversions += 1
                    
                    print(f"  Failed: {metadata.get('error', 'Unknown error')}")
                
                # Save progress
                self._save_json(self.converted_file, self.converted_data)
                self._save_json(self.failed_file, self.failed_data)
                self._save_json(self.metadata_file, self.metadata)
                self._save_json(self.progress_file, self.progress_data)
        
        except KeyboardInterrupt:
            print(f"\nBatch interrupted by user")
            batch_info["status"] = "interrupted"
        
        except Exception as e:
            print(f"\nBatch error: {e}")
            batch_info["status"] = "error"
            batch_info["error"] = str(e)
        
        finally:
            # Finalize batch
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            batch_info["end_time"] = end_time.isoformat()
            batch_info["duration_seconds"] = duration.total_seconds()
            batch_info["status"] = "completed"
            batch_info["successful_conversions"] = successful_conversions
            batch_info["failed_conversions"] = failed_conversions
            
            # Move to history
            self.progress_data["batch_history"].append(batch_info)
            self.progress_data["current_batch"] = {}
            self._save_json(self.progress_file, self.progress_data)
            
            self.is_processing = False
            
            # Print summary
            print(f"\nBatch Summary:")
            print(f"   Duration: {duration}")
            print(f"   Successful: {successful_conversions}")
            print(f"   Failed: {failed_conversions}")
            print(f"   Success rate: {(successful_conversions/len(files_to_process)*100):.1f}%")
            
            return {
                "success": True,
                "batch_id": self.current_batch_id,
                "successful_conversions": successful_conversions,
                "failed_conversions": failed_conversions,
                "duration": duration.total_seconds()
            }
    
    def retry_failed_files(self, service: str = "simulated", voice: Optional[str] = None) -> Dict:
        """Retry all failed conversions."""
        failed_files = self.failed_data["failed_files"]
        if not failed_files:
            print("No failed files to retry")
            return {"success": True, "message": "No failed files"}
        
        print(f"Retrying {len(failed_files)} failed files...")
        
        # Clear failed files list
        self.failed_data["failed_files"] = []
        self.failed_data["total_failed"] = 0
        
        # Copy failed files to input directory
        retry_files = []
        for failed_entry in failed_files:
            filename = failed_entry["filename"]
            input_file = self.input_dir / filename
            if input_file.exists():
                retry_files.append(input_file)
        
        if not retry_files:
            print("No failed files found in input directory")
            return {"success": False, "error": "No failed files found"}
        
        # Process retry batch
        return self.process_batch(len(retry_files), service, voice, resume=True)
    
    def get_status(self) -> Dict:
        """Get current processing status."""
        input_files = self.get_input_files()
        converted_count = len(self.converted_data["converted_files"])
        failed_count = len(self.failed_data["failed_files"])
        
        status = {
            "is_processing": self.is_processing,
            "input_files": len(input_files),
            "converted_files": converted_count,
            "failed_files": failed_count,
            "available_for_conversion": len(input_files) - converted_count,
            "current_batch": self.progress_data["current_batch"],
            "last_batch": self.progress_data["batch_history"][-1] if self.progress_data["batch_history"] else None
        }
        
        return status
    
    def print_status(self):
        """Print current status."""
        status = self.get_status()
        
        print("\n=== TTS Processing Status ===")
        print(f"Processing: {'Yes' if status['is_processing'] else 'No'}")
        print(f"Input files: {status['input_files']}")
        print(f"Converted: {status['converted_files']}")
        print(f"Failed: {status['failed_files']}")
        print(f"Available: {status['available_for_conversion']}")
        
        if status['current_batch'] and status['current_batch'].get('batch_id'):
            batch = status['current_batch']
            print(f"\nCurrent Batch:")
            print(f"  ID: {batch['batch_id']}")
            print(f"  Progress: {batch['progress_percentage']:.1f}%")
            print(f"  Current file: {batch.get('current_file', 'None')}")
            print(f"  Completed: {len(batch.get('files_completed', []))}")
            print(f"  Failed: {len(batch.get('files_failed', []))}")
        
        if status['last_batch']:
            batch = status['last_batch']
            print(f"\nLast Batch:")
            print(f"  Status: {batch.get('status', 'unknown')}")
            print(f"  Duration: {batch.get('duration_seconds', 0):.1f}s")
            print(f"  Successful: {batch.get('successful_conversions', 0)}")
            print(f"  Failed: {batch.get('failed_conversions', 0)}")


def main():
    parser = argparse.ArgumentParser(description="TTS Batch Processor")
    parser.add_argument("--count", type=int, default=5, help="Number of files to process")
    parser.add_argument("--service", default="simulated", help="TTS service (simulated, azure, google)")
    parser.add_argument("--voice", help="Voice to use")
    parser.add_argument("--resume", action="store_true", help="Resume interrupted batch")
    parser.add_argument("--retry-failed", action="store_true", help="Retry failed conversions")
    parser.add_argument("--status", action="store_true", help="Show current status")
    
    args = parser.parse_args()
    
    processor = TTSBatchProcessor()
    
    if args.status:
        processor.print_status()
        return
    
    if args.retry_failed:
        result = processor.retry_failed_files(args.service, args.voice)
    else:
        result = processor.process_batch(args.count, args.service, args.voice, args.resume)
    
    if result.get("success"):
        print(f"\nBatch completed successfully")
    else:
        print(f"\nBatch failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
