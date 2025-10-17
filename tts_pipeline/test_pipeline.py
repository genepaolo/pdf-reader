#!/usr/bin/env python3
"""
TTS Pipeline Test Script

Demonstrates the complete TTS pipeline workflow:
1. List available files
2. Copy files to input
3. Process batch
4. Track progress
5. Generate report
"""

import os
import sys
import time
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from file_organizer import TTSFileOrganizer
from batch_processor import TTSBatchProcessor
from progress_tracker import TTSProgressTracker


def test_file_organizer():
    """Test the file organizer functionality."""
    print("\n" + "="*60)
    print("TESTING FILE ORGANIZER")
    print("="*60)
    
    organizer = TTSFileOrganizer()
    
    # List available files
    print("\n1. Listing available files...")
    organizer.list_available_files()
    
    # Copy 3 files for testing
    print("\n2. Copying 3 files for testing...")
    copied_files = organizer.copy_files_by_count(3)
    
    if copied_files:
        print(f"\nSuccessfully copied {len(copied_files)} files:")
        for filename in copied_files:
            print(f"   - {filename}")
    else:
        print("\nNo files copied")
    
    return len(copied_files) > 0


def test_batch_processor():
    """Test the batch processor functionality."""
    print("\n" + "="*60)
    print("TESTING BATCH PROCESSOR")
    print("="*60)
    
    processor = TTSBatchProcessor()
    
    # Check status
    print("\n1. Checking initial status...")
    processor.print_status()
    
    # Process a small batch
    print("\n2. Processing batch of 2 files...")
    result = processor.process_batch(count=2, service="simulated")
    
    if result.get("success"):
        print(f"\nBatch completed successfully")
        print(f"   Successful conversions: {result.get('successful_conversions', 0)}")
        print(f"   Failed conversions: {result.get('failed_conversions', 0)}")
        print(f"   Duration: {result.get('duration', 0):.1f}s")
    else:
        print(f"\nBatch failed: {result.get('error', 'Unknown error')}")
    
    return result.get("success", False)


def test_progress_tracker():
    """Test the progress tracker functionality."""
    print("\n" + "="*60)
    print("TESTING PROGRESS TRACKER")
    print("="*60)
    
    tracker = TTSProgressTracker()
    
    # Show comprehensive status
    print("\n1. Showing comprehensive status...")
    tracker.print_summary()
    tracker.print_batch_history(3)
    tracker.print_failed_summary()
    tracker.print_timeline()
    
    # Export report
    print("\n2. Exporting test report...")
    tracker.export_report("test_report.json")
    
    return True


def cleanup_test_files():
    """Clean up test files."""
    print("\n" + "="*60)
    print("CLEANING UP TEST FILES")
    print("="*60)
    
    # Clear input directory
    input_dir = Path("input")
    if input_dir.exists():
        for file in input_dir.iterdir():
            if file.is_file():
                file.unlink()
        print(f"Cleared {input_dir} directory")
    
    # Clear output directory
    output_dir = Path("output")
    if output_dir.exists():
        for file in output_dir.iterdir():
            if file.is_file():
                file.unlink()
        print(f"Cleared {output_dir} directory")
    
    # Remove test report
    test_report = Path("test_report.json")
    if test_report.exists():
        test_report.unlink()
        print(f"Removed test report")


def main():
    """Run complete TTS pipeline test."""
    print("TTS PIPELINE COMPREHENSIVE TEST")
    print("="*60)
    print("This test will demonstrate:")
    print("1. File organization and copying")
    print("2. Batch processing with simulated TTS")
    print("3. Progress tracking and reporting")
    print("4. Cleanup of test files")
    
    print("\nStarting test automatically...")
    
    try:
        # Test 1: File Organizer
        organizer_success = test_file_organizer()
        
        if not organizer_success:
            print("\nFile organizer test failed - stopping")
            return
        
        # Test 2: Batch Processor
        processor_success = test_batch_processor()
        
        if not processor_success:
            print("\nBatch processor test failed - stopping")
            return
        
        # Test 3: Progress Tracker
        tracker_success = test_progress_tracker()
        
        if not tracker_success:
            print("\nProgress tracker test failed - stopping")
            return
        
        # Cleanup
        cleanup_test_files()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nThe TTS pipeline is ready for use!")
        print("\nNext steps:")
        print("1. Copy your actual text files to input/")
        print("2. Configure your TTS service credentials")
        print("3. Run batch processing with real TTS service")
        print("4. Monitor progress and generate reports")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        cleanup_test_files()
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        cleanup_test_files()


if __name__ == "__main__":
    main()
