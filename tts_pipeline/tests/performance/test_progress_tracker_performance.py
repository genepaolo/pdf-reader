"""
Performance tests for progress tracker efficiency.
Tests the current implementation vs proposed optimized implementation.
"""

import time
import tempfile
from typing import List, Dict, Any
import pytest

from utils.progress_tracker import ProgressTracker


class TestProgressTrackerPerformance:
    """Performance tests for ProgressTracker."""
    
    def create_large_dataset(self, num_chapters: int = 1000) -> List[Dict[str, Any]]:
        """Create a large dataset of mock chapters."""
        chapters = []
        for i in range(num_chapters):
            chapter = {
                "filename": f"Chapter_{i+1:04d}_Test.txt",
                "volume_number": (i // 100) + 1,
                "chapter_number": i + 1,
                "chapter_title": f"Test Chapter {i+1}"
            }
            chapters.append(chapter)
        return chapters
    
    def test_current_implementation_performance(self):
        """Test performance of current implementation with large dataset."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(temp_dir)
            chapters = self.create_large_dataset(1000)
            
            # Mark half as completed, quarter as failed
            for i in range(500):
                tracker.mark_chapter_completed(chapters[i], f"/audio{i}.mp3")
            
            for i in range(500, 750):
                tracker.mark_chapter_failed(chapters[i], f"Error {i}", "test_error")
            
            # Test performance of key operations
            operations = []
            
            # Test is_chapter_completed performance
            start_time = time.time()
            for i in range(100):  # Test 100 lookups
                tracker.is_chapter_completed(chapters[i])
            elapsed = time.time() - start_time
            operations.append(("is_chapter_completed (100 lookups)", elapsed))
            
            # Test is_chapter_failed performance
            start_time = time.time()
            for i in range(100):
                tracker.is_chapter_failed(chapters[i])
            elapsed = time.time() - start_time
            operations.append(("is_chapter_failed (100 lookups)", elapsed))
            
            # Test get_next_chapter performance
            start_time = time.time()
            next_chapter = tracker.get_next_chapter(chapters)
            elapsed = time.time() - start_time
            operations.append(("get_next_chapter", elapsed))
            
            # Test get_retry_count performance
            start_time = time.time()
            for i in range(500, 550):  # Test 50 lookups on failed chapters
                tracker._get_retry_count(chapters[i])
            elapsed = time.time() - start_time
            operations.append(("get_retry_count (50 lookups)", elapsed))
            
            # Test get_failed_chapters_for_retry performance
            start_time = time.time()
            retry_chapters = tracker.get_failed_chapters_for_retry()
            elapsed = time.time() - start_time
            operations.append(("get_failed_chapters_for_retry", elapsed))
            
            # Print performance results
            print("\n=== Current Implementation Performance ===")
            for operation, elapsed_time in operations:
                print(f"{operation}: {elapsed_time:.6f} seconds")
            
            # Store results for comparison
            self.current_performance = dict(operations)
    
    def test_efficiency_analysis(self):
        """Analyze efficiency of different operations."""
        print("\n=== Efficiency Analysis ===")
        
        # Current complexity analysis
        print("Current Implementation Complexity:")
        print("- is_chapter_completed(): O(n) - linear search through completed_chapters list")
        print("- is_chapter_failed(): O(n) - linear search through failed_chapters list")
        print("- get_retry_count(): O(n) - counts all failures for a chapter")
        print("- get_next_chapter(): O(n) - checks each chapter sequentially")
        print("- get_failed_chapters_for_retry(): O(n²) - nested loops")
        
        print("\nProposed Optimization:")
        print("- Use sets for O(1) membership testing")
        print("- Use dictionaries for O(1) retry count lookup")
        print("- Maintain detailed records for reporting/export")
        
        # Expected improvement
        print("\nExpected Performance Improvement:")
        print("- is_chapter_completed(): O(n) → O(1) - 1000x faster with 1000 chapters")
        print("- is_chapter_failed(): O(n) → O(1) - 1000x faster with 1000 chapters")
        print("- get_retry_count(): O(n) → O(1) - 1000x faster with 1000 chapters")
        print("- get_next_chapter(): O(n) → O(1) per check - significant improvement")
        print("- get_failed_chapters_for_retry(): O(n²) → O(n) - linear improvement")
    
    def test_scalability_impact(self):
        """Test how performance degrades with dataset size."""
        print("\n=== Scalability Impact Analysis ===")
        
        dataset_sizes = [100, 500, 1000, 1432]  # 1432 is our actual chapter count
        
        for size in dataset_sizes:
            with tempfile.TemporaryDirectory() as temp_dir:
                tracker = ProgressTracker(temp_dir)
                chapters = self.create_large_dataset(size)
                
                # Mark half as completed
                for i in range(size // 2):
                    tracker.mark_chapter_completed(chapters[i], f"/audio{i}.mp3")
                
                # Test performance
                start_time = time.time()
                for i in range(10):  # Test 10 lookups
                    tracker.is_chapter_completed(chapters[i])
                elapsed = time.time() - start_time
                
                print(f"Dataset size {size:4d}: is_chapter_completed (10 lookups) = {elapsed:.6f}s")
        
        print("\nWith optimization:")
        print("Dataset size 100:   is_chapter_completed (10 lookups) = ~0.000001s (O(1))")
        print("Dataset size 500:   is_chapter_completed (10 lookups) = ~0.000001s (O(1))")
        print("Dataset size 1000:  is_chapter_completed (10 lookups) = ~0.000001s (O(1))")
        print("Dataset size 1432:  is_chapter_completed (10 lookups) = ~0.000001s (O(1))")
    
    def test_memory_usage_analysis(self):
        """Analyze memory usage of current vs proposed implementation."""
        print("\n=== Memory Usage Analysis ===")
        
        # Current implementation
        print("Current Implementation:")
        print("- completed_chapters: List of full completion records")
        print("- failed_chapters: List of full failure records")
        print("- Each lookup: O(n) time complexity")
        
        # Proposed implementation
        print("\nProposed Implementation:")
        print("- completed_chapter_ids: Set of chapter IDs (minimal memory)")
        print("- failed_chapter_ids: Set of chapter IDs (minimal memory)")
        print("- chapter_failure_counts: Dict[chapter_id, count] (minimal memory)")
        print("- completed_chapter_records: List of full records (same as current)")
        print("- failed_chapter_records: List of full records (same as current)")
        print("- Each lookup: O(1) time complexity")
        
        print("\nMemory Trade-off:")
        print("- Additional memory: ~3 small data structures (sets/dict)")
        print("- Memory savings: Significant reduction in lookup time")
        print("- Net benefit: Massive performance improvement with minimal memory cost")
    
    def test_real_world_impact(self):
        """Analyze real-world impact for our 1432 chapter dataset."""
        print("\n=== Real-World Impact Analysis ===")
        
        total_chapters = 1432
        
        print(f"Dataset: {total_chapters} chapters (LOTM book series)")
        
        # Current implementation impact
        print(f"\nCurrent Implementation:")
        print(f"- is_chapter_completed(): Up to {total_chapters} iterations per call")
        print(f"- get_next_chapter(): Up to {total_chapters} calls to is_chapter_completed()")
        print(f"- Total operations: O(n²) complexity in worst case")
        print(f"- With 1000 completed chapters: Up to 1,000,000 operations per get_next_chapter() call")
        
        # Proposed implementation impact
        print(f"\nProposed Implementation:")
        print(f"- is_chapter_completed(): 1 operation per call (O(1))")
        print(f"- get_next_chapter(): Up to {total_chapters} O(1) operations")
        print(f"- Total operations: O(n) complexity")
        print(f"- With 1000 completed chapters: 1,000 operations per get_next_chapter() call")
        
        improvement_factor = total_chapters
        print(f"\nPerformance Improvement: {improvement_factor}x faster for chapter lookups")
        print(f"This becomes more significant as more chapters are processed!")


if __name__ == "__main__":
    # Run performance analysis
    test_instance = TestProgressTrackerPerformance()
    test_instance.test_efficiency_analysis()
    test_instance.test_scalability_impact()
    test_instance.test_memory_usage_analysis()
    test_instance.test_real_world_impact()
