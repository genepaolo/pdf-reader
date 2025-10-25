"""
Process Manager for TTS Pipeline

This module provides process management functionality to prevent multiple
conflicting TTS processing operations from running simultaneously.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class ProcessManager:
    """Manages TTS processing operations to prevent conflicts."""
    
    def __init__(self, project_name: str, lock_dir: str = "./process_locks"):
        """
        Initialize the process manager.
        
        Args:
            project_name: Name of the project being processed
            lock_dir: Directory to store process lock files
        """
        self.project_name = project_name
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Lock file for this project
        self.lock_file = self.lock_dir / f"{project_name}.lock"
        self.process_id = os.getpid()
    
    def acquire_lock(self, operation_type: str, operation_details: Dict[str, Any]) -> bool:
        """
        Acquire a lock for processing operations.
        
        Args:
            operation_type: Type of operation (e.g., 'batch', 'single', 'next_chapters')
            operation_details: Details about the operation
            
        Returns:
            True if lock acquired successfully, False if another process is running
        """
        try:
            # Check if lock file exists and is still valid
            if self.lock_file.exists():
                if not self._is_lock_valid():
                    # Lock is stale, remove it
                    self.logger.warning(f"Removing stale lock file: {self.lock_file}")
                    self.lock_file.unlink()
                else:
                    # Another process is running
                    self.logger.error(f"Another TTS process is already running for project: {self.project_name}")
                    self._log_conflicting_process()
                    return False
            
            # Create lock file
            lock_data = {
                "project_name": self.project_name,
                "process_id": self.process_id,
                "operation_type": operation_type,
                "operation_details": operation_details,
                "started_at": datetime.now().isoformat(),
                "pid": self.process_id
            }
            
            with open(self.lock_file, 'w') as f:
                json.dump(lock_data, f, indent=2)
            
            self.logger.info(f"Acquired lock for {operation_type} operation on project: {self.project_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to acquire lock: {e}")
            return False
    
    def release_lock(self) -> bool:
        """
        Release the processing lock.
        
        Returns:
            True if lock released successfully, False otherwise
        """
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                self.logger.info(f"Released lock for project: {self.project_name}")
                return True
            else:
                self.logger.warning(f"No lock file found to release: {self.lock_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to release lock: {e}")
            return False
    
    def _is_lock_valid(self) -> bool:
        """Check if the existing lock is still valid (process is still running)."""
        try:
            with open(self.lock_file, 'r') as f:
                lock_data = json.load(f)
            
            # Check if the process is still running
            pid = lock_data.get('pid')
            if pid:
                try:
                    # Try to send signal 0 to check if process exists
                    os.kill(pid, 0)
                    return True  # Process is still running
                except (OSError, ProcessLookupError, Exception):
                    # Process is dead or any other error occurred
                    return False
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking lock validity: {e}")
            return False
    
    def _log_conflicting_process(self):
        """Log details about the conflicting process."""
        try:
            with open(self.lock_file, 'r') as f:
                lock_data = json.load(f)
            
            self.logger.error("Conflicting process details:")
            self.logger.error(f"  - Process ID: {lock_data.get('pid', 'Unknown')}")
            self.logger.error(f"  - Operation: {lock_data.get('operation_type', 'Unknown')}")
            self.logger.error(f"  - Started: {lock_data.get('started_at', 'Unknown')}")
            self.logger.error(f"  - Details: {lock_data.get('operation_details', {})}")
            
        except Exception as e:
            self.logger.error(f"Could not read conflicting process details: {e}")
    
    def get_active_processes(self) -> List[Dict[str, Any]]:
        """
        Get list of all active TTS processes.
        
        Returns:
            List of active process information
        """
        active_processes = []
        
        try:
            for lock_file in self.lock_dir.glob("*.lock"):
                try:
                    with open(lock_file, 'r') as f:
                        lock_data = json.load(f)
                    
                    if self._is_lock_valid():
                        active_processes.append({
                            "project": lock_data.get('project_name', 'Unknown'),
                            "pid": lock_data.get('pid', 'Unknown'),
                            "operation": lock_data.get('operation_type', 'Unknown'),
                            "started": lock_data.get('started_at', 'Unknown'),
                            "lock_file": str(lock_file)
                        })
                except Exception as e:
                    self.logger.warning(f"Error reading lock file {lock_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error scanning lock files: {e}")
        
        return active_processes
    
    def cleanup_stale_locks(self) -> int:
        """
        Clean up stale lock files.
        
        Returns:
            Number of stale locks removed
        """
        cleaned = 0
        
        try:
            for lock_file in self.lock_dir.glob("*.lock"):
                try:
                    with open(lock_file, 'r') as f:
                        lock_data = json.load(f)
                    
                    if not self._is_lock_valid():
                        lock_file.unlink()
                        cleaned += 1
                        self.logger.info(f"Removed stale lock: {lock_file}")
                        
                except Exception as e:
                    self.logger.warning(f"Error processing lock file {lock_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up stale locks: {e}")
        
        return cleaned


def check_and_prevent_conflicts(project_name: str, operation_type: str, 
                               operation_details: Dict[str, Any]) -> Optional[ProcessManager]:
    """
    Check for conflicts and acquire lock if possible.
    
    Args:
        project_name: Name of the project
        operation_type: Type of operation
        operation_details: Operation details
        
    Returns:
        ProcessManager instance if lock acquired, None if conflict exists
    """
    process_manager = ProcessManager(project_name)
    
    if process_manager.acquire_lock(operation_type, operation_details):
        return process_manager
    else:
        return None


def list_active_processes() -> List[Dict[str, Any]]:
    """List all active TTS processes across all projects."""
    process_manager = ProcessManager("dummy")  # Just for accessing the method
    return process_manager.get_active_processes()


if __name__ == "__main__":
    # Command line interface for process management
    import argparse
    
    parser = argparse.ArgumentParser(description="TTS Process Manager")
    parser.add_argument("--list", action="store_true", help="List active processes")
    parser.add_argument("--cleanup", action="store_true", help="Clean up stale locks")
    parser.add_argument("--project", help="Project name for cleanup")
    
    args = parser.parse_args()
    
    if args.list:
        processes = list_active_processes()
        if processes:
            print("Active TTS Processes:")
            for proc in processes:
                print(f"  Project: {proc['project']}")
                print(f"  PID: {proc['pid']}")
                print(f"  Operation: {proc['operation']}")
                print(f"  Started: {proc['started']}")
                print(f"  Lock: {proc['lock_file']}")
                print()
        else:
            print("No active TTS processes found.")
    
    elif args.cleanup:
        if args.project:
            process_manager = ProcessManager(args.project)
            cleaned = process_manager.cleanup_stale_locks()
            print(f"Cleaned up {cleaned} stale locks for project: {args.project}")
        else:
            process_manager = ProcessManager("dummy")
            cleaned = process_manager.cleanup_stale_locks()
            print(f"Cleaned up {cleaned} stale locks across all projects")
