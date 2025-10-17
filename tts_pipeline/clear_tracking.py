#!/usr/bin/env python3
"""
Clear TTS Tracking Data

Clears all tracking data from test runs to start fresh.
"""

import json
from pathlib import Path


def clear_tracking_data():
    """Clear all tracking data."""
    tracking_dir = Path("tracking")
    
    if not tracking_dir.exists():
        print("No tracking directory found - nothing to clear")
        return
    
    # Clear converted files
    converted_file = tracking_dir / "converted.json"
    if converted_file.exists():
        with open(converted_file, 'w', encoding='utf-8') as f:
            json.dump({"converted_files": [], "total_converted": 0}, f, indent=2)
        print("Cleared converted files tracking")
    
    # Clear failed files
    failed_file = tracking_dir / "failed.json"
    if failed_file.exists():
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump({"failed_files": [], "total_failed": 0}, f, indent=2)
        print("Cleared failed files tracking")
    
    # Clear progress data
    progress_file = tracking_dir / "progress.json"
    if progress_file.exists():
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({"current_batch": {}, "batch_history": []}, f, indent=2)
        print("Cleared progress tracking")
    
    # Clear metadata
    metadata_file = tracking_dir / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({"file_metadata": {}, "statistics": {}}, f, indent=2)
        print("Cleared metadata tracking")
    
    print("\nAll tracking data cleared! Ready for fresh start.")


if __name__ == "__main__":
    clear_tracking_data()
