#!/usr/bin/env python3
"""
TTS Progress Tracker

Monitors and reports on TTS conversion progress.
Provides detailed statistics and batch history.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta


class TTSProgressTracker:
    """Tracks and reports TTS conversion progress."""
    
    def __init__(self, tracking_dir: str = "tracking"):
        self.tracking_dir = Path(tracking_dir)
        
        # Tracking files
        self.converted_file = self.tracking_dir / "converted.json"
        self.failed_file = self.tracking_dir / "failed.json"
        self.progress_file = self.tracking_dir / "progress.json"
        self.metadata_file = self.tracking_dir / "metadata.json"
        
        # Load data
        self.converted_data = self._load_json(self.converted_file, {"converted_files": [], "total_converted": 0})
        self.failed_data = self._load_json(self.failed_file, {"failed_files": [], "total_failed": 0})
        self.progress_data = self._load_json(self.progress_file, {"current_batch": {}, "batch_history": []})
        self.metadata = self._load_json(self.metadata_file, {"file_metadata": {}, "statistics": {}})
    
    def _load_json(self, file_path: Path, default: Dict) -> Dict:
        """Load JSON file with default fallback."""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"WARNING: Could not load {file_path}: {e}")
        return default
    
    def get_overall_stats(self) -> Dict:
        """Get overall conversion statistics."""
        converted_count = len(self.converted_data["converted_files"])
        failed_count = len(self.failed_data["failed_files"])
        
        # Calculate success rate
        total_attempted = converted_count + failed_count
        success_rate = (converted_count / total_attempted * 100) if total_attempted > 0 else 0
        
        # Get batch statistics
        batch_history = self.progress_data.get("batch_history", [])
        total_batches = len(batch_history)
        
        # Calculate average batch duration
        completed_batches = [b for b in batch_history if b.get("status") == "completed"]
        avg_duration = 0
        if completed_batches:
            durations = [b.get("duration_seconds", 0) for b in completed_batches]
            avg_duration = sum(durations) / len(durations)
        
        # Calculate total processing time
        total_processing_time = sum(b.get("duration_seconds", 0) for b in completed_batches)
        
        return {
            "converted_files": converted_count,
            "failed_files": failed_count,
            "total_attempted": total_attempted,
            "success_rate": success_rate,
            "total_batches": total_batches,
            "completed_batches": len(completed_batches),
            "average_batch_duration": avg_duration,
            "total_processing_time": total_processing_time
        }
    
    def get_current_status(self) -> Dict:
        """Get current processing status."""
        current_batch = self.progress_data.get("current_batch", {})
        
        status = {
            "is_processing": bool(current_batch.get("batch_id")),
            "current_batch_id": current_batch.get("batch_id"),
            "current_file": current_batch.get("current_file"),
            "progress_percentage": current_batch.get("progress_percentage", 0),
            "files_to_process": len(current_batch.get("files_to_process", [])),
            "files_completed": len(current_batch.get("files_completed", [])),
            "files_failed": len(current_batch.get("files_failed", [])),
            "service": current_batch.get("service"),
            "voice": current_batch.get("voice")
        }
        
        return status
    
    def get_batch_history(self, limit: int = 10) -> List[Dict]:
        """Get recent batch history."""
        batch_history = self.progress_data.get("batch_history", [])
        return batch_history[-limit:] if limit else batch_history
    
    def get_failed_files_summary(self) -> Dict:
        """Get summary of failed files."""
        failed_files = self.failed_data.get("failed_files", [])
        
        # Categorize errors
        error_categories = {}
        for failed_file in failed_files:
            error = failed_file.get("error", "Unknown error")
            error_categories[error] = error_categories.get(error, 0) + 1
        
        # Get recent failures
        recent_failures = []
        for failed_file in failed_files[-10:]:  # Last 10 failures
            recent_failures.append({
                "filename": failed_file.get("filename"),
                "error": failed_file.get("error"),
                "timestamp": failed_file.get("timestamp")
            })
        
        return {
            "total_failed": len(failed_files),
            "error_categories": error_categories,
            "recent_failures": recent_failures
        }
    
    def get_conversion_timeline(self) -> List[Dict]:
        """Get conversion timeline with timestamps."""
        timeline = []
        
        # Add batch completions
        for batch in self.progress_data.get("batch_history", []):
            if batch.get("status") == "completed":
                timeline.append({
                    "timestamp": batch.get("end_time"),
                    "type": "batch_completed",
                    "description": f"Batch completed: {batch.get('successful_conversions', 0)} successful, {batch.get('failed_conversions', 0)} failed",
                    "duration": batch.get("duration_seconds", 0)
                })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.get("timestamp", ""))
        
        return timeline[-20:]  # Last 20 events
    
    def print_summary(self):
        """Print overall summary."""
        stats = self.get_overall_stats()
        status = self.get_current_status()
        
        print("\n" + "="*50)
        print("TTS CONVERSION SUMMARY")
        print("="*50)
        
        print(f"\nOverall Statistics:")
        print(f"   Converted files: {stats['converted_files']}")
        print(f"   Failed files: {stats['failed_files']}")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        print(f"   Total batches: {stats['total_batches']}")
        print(f"   Completed batches: {stats['completed_batches']}")
        
        if stats['average_batch_duration'] > 0:
            print(f"   Avg batch duration: {stats['average_batch_duration']:.1f}s")
        
        if stats['total_processing_time'] > 0:
            total_time = timedelta(seconds=int(stats['total_processing_time']))
            print(f"   Total processing time: {total_time}")
        
        print(f"\nCurrent Status:")
        if status['is_processing']:
            print(f"   Processing: YES")
            print(f"   Batch ID: {status['current_batch_id']}")
            print(f"   Progress: {status['progress_percentage']:.1f}%")
            print(f"   Current file: {status['current_file']}")
            print(f"   Service: {status['service']}")
            print(f"   Voice: {status['voice']}")
        else:
            print(f"   Processing: NO")
    
    def print_batch_history(self, limit: int = 5):
        """Print recent batch history."""
        history = self.get_batch_history(limit)
        
        if not history:
            print("\nNo batch history available")
            return
        
        print(f"\nRecent Batch History (last {len(history)} batches):")
        print("-" * 60)
        
        for i, batch in enumerate(reversed(history), 1):
            batch_id = batch.get("batch_id", "unknown")[:8]
            status = batch.get("status", "unknown")
            start_time = batch.get("start_time", "")
            duration = batch.get("duration_seconds", 0)
            successful = batch.get("successful_conversions", 0)
            failed = batch.get("failed_conversions", 0)
            
            # Format timestamp
            if start_time:
                try:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = start_time[:8]
            else:
                time_str = "unknown"
            
            # Status emoji
            status_emoji = {
                "completed": "[OK]",
                "interrupted": "[INTERRUPTED]",
                "error": "[ERROR]"
            }.get(status, "[UNKNOWN]")
            
            print(f"   {i}. {status_emoji} Batch {batch_id} - {time_str}")
            print(f"      Status: {status}")
            print(f"      Duration: {duration:.1f}s")
            print(f"      Results: {successful} successful, {failed} failed")
            print()
    
    def print_failed_summary(self):
        """Print failed files summary."""
        failed_summary = self.get_failed_files_summary()
        
        if failed_summary['total_failed'] == 0:
            print("\nNo failed conversions!")
            return
        
        print(f"\nFailed Conversions Summary:")
        print(f"   Total failed: {failed_summary['total_failed']}")
        
        if failed_summary['error_categories']:
            print(f"\n   Error Categories:")
            for error, count in failed_summary['error_categories'].items():
                print(f"     - {error}: {count}")
        
        if failed_summary['recent_failures']:
            print(f"\n   Recent Failures:")
            for failure in failed_summary['recent_failures'][-5:]:
                filename = failure['filename']
                error = failure['error']
                timestamp = failure['timestamp']
                print(f"     - {filename}: {error}")
    
    def print_timeline(self):
        """Print conversion timeline."""
        timeline = self.get_conversion_timeline()
        
        if not timeline:
            print("\nNo timeline data available")
            return
        
        print(f"\nRecent Activity Timeline:")
        print("-" * 50)
        
        for event in timeline[-10:]:  # Last 10 events
            timestamp = event.get("timestamp", "")
            event_type = event.get("type", "")
            description = event.get("description", "")
            
            # Format timestamp
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[:8]
            else:
                time_str = "unknown"
            
            print(f"   {time_str} - {description}")
    
    def export_report(self, output_file: str = "tts_report.json"):
        """Export comprehensive report to JSON file."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "overall_stats": self.get_overall_stats(),
            "current_status": self.get_current_status(),
            "batch_history": self.get_batch_history(),
            "failed_summary": self.get_failed_files_summary(),
            "timeline": self.get_conversion_timeline(),
            "converted_files": self.converted_data.get("converted_files", []),
            "failed_files": self.failed_data.get("failed_files", [])
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="TTS Progress Tracker")
    parser.add_argument("--summary", action="store_true", help="Show overall summary")
    parser.add_argument("--history", type=int, metavar="N", help="Show last N batches")
    parser.add_argument("--failed", action="store_true", help="Show failed files summary")
    parser.add_argument("--timeline", action="store_true", help="Show activity timeline")
    parser.add_argument("--export", metavar="FILE", help="Export report to JSON file")
    parser.add_argument("--all", action="store_true", help="Show all information")
    
    args = parser.parse_args()
    
    tracker = TTSProgressTracker()
    
    if args.all or not any([args.summary, args.history, args.failed, args.timeline, args.export]):
        # Default: show summary
        tracker.print_summary()
        tracker.print_batch_history(5)
        tracker.print_failed_summary()
        tracker.print_timeline()
    
    if args.summary:
        tracker.print_summary()
    
    if args.history:
        tracker.print_batch_history(args.history)
    
    if args.failed:
        tracker.print_failed_summary()
    
    if args.timeline:
        tracker.print_timeline()
    
    if args.export:
        tracker.export_report(args.export)


if __name__ == "__main__":
    main()
