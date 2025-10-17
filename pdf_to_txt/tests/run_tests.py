#!/usr/bin/env python3
"""
Test runner script for PDF converter tests.
Runs all tests in sequence and provides a summary.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test(test_name, test_file):
    """Run a single test and return success status"""
    print(f"\n{'='*60}")
    print(f"Running {test_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, 
                              text=True, 
                              cwd=Path(__file__).parent)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_name}: {e}")
        return False

def main():
    """Run all tests and provide summary"""
    print("PDF Converter Test Suite")
    print("Running all tests...")
    
    tests = [
        ("Outline Structure Analysis", "test_outline.py"),
        ("Volume Structure Analysis", "test_volumes.py"),
        ("Chapter Structure Analysis", "test_chapters.py")
    ]
    
    results = []
    
    for test_name, test_file in tests:
        success = run_test(test_name, test_file)
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\nAll tests passed! PDF structure is valid.")
        return 0
    else:
        print(f"\n{failed} test(s) failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
