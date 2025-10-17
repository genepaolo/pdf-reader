#!/usr/bin/env python3
"""
TTS File Organizer

Copies selected text files from extracted_text to tts_pipeline/input/
for TTS processing. Supports various selection methods:
- By volume
- By chapter range
- By count
- By specific chapter numbers
"""

import os
import json
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import re


class TTSFileOrganizer:
    """Organizes text files for TTS processing."""
    
    def __init__(self, source_dir: str = "../extracted_text", target_dir: str = "input"):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.target_dir.mkdir(exist_ok=True)
        
        # Load tracking data
        self.tracking_dir = Path("tracking")
        self.converted_file = self.tracking_dir / "converted.json"
        self.metadata_file = self.tracking_dir / "metadata.json"
        
        self.converted_files = self._load_converted_files()
        self.metadata = self._load_metadata()
    
    def _load_converted_files(self) -> Dict:
        """Load list of already converted files."""
        if self.converted_file.exists():
            with open(self.converted_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"converted_files": [], "total_converted": 0}
    
    def _load_metadata(self) -> Dict:
        """Load file metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"file_metadata": {}, "statistics": {}}
    
    def _save_metadata(self):
        """Save updated metadata."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)
    
    def scan_source_files(self) -> Dict[str, List[str]]:
        """Scan source directory and return organized file structure."""
        file_structure = {}
        
        if not self.source_dir.exists():
            print(f"ERROR: Source directory {self.source_dir} does not exist")
            return file_structure
        
        # Look for PDF folders (e.g., lotm_book1)
        for pdf_folder in self.source_dir.iterdir():
            if pdf_folder.is_dir():
                pdf_name = pdf_folder.name
                file_structure[pdf_name] = {}
                
                # Look for volume folders
                for volume_folder in pdf_folder.iterdir():
                    if volume_folder.is_dir() and not volume_folder.name.startswith('Volume_'):
                        volume_name = volume_folder.name
                        file_structure[pdf_name][volume_name] = []
                        
                        # Get all chapter files
                        for chapter_file in volume_folder.glob("Chapter_*.txt"):
                            file_structure[pdf_name][volume_name].append(chapter_file.name)
        
        return file_structure
    
    def get_file_info(self, file_path: Path) -> Dict:
        """Get metadata for a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract chapter number and title from filename
            filename = file_path.name
            chapter_match = re.search(r'Chapter_(\d+)_(.+)\.txt', filename)
            
            info = {
                "filename": filename,
                "file_path": str(file_path),
                "size_bytes": file_path.stat().st_size,
                "word_count": len(content.split()),
                "line_count": len(content.splitlines()),
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
            
            if chapter_match:
                info["chapter_number"] = int(chapter_match.group(1))
                info["chapter_title"] = chapter_match.group(2).replace('_', ' ')
            
            return info
            
        except Exception as e:
            print(f"ERROR: Could not read file {file_path}: {e}")
            return {"filename": file_path.name, "error": str(e)}
    
    def copy_files_by_count(self, count: int, volume: Optional[str] = None, 
                           exclude_converted: bool = True) -> List[str]:
        """Copy N files to input directory."""
        copied_files = []
        file_structure = self.scan_source_files()
        
        if not file_structure:
            print("No source files found")
            return copied_files
        
        # Get all available files
        all_files = []
        for pdf_name, volumes in file_structure.items():
            for vol_name, chapters in volumes.items():
                if volume and vol_name != volume:
                    continue
                
                for chapter_file in chapters:
                    file_path = self.source_dir / pdf_name / vol_name / chapter_file
                    file_info = self.get_file_info(file_path)
                    
                    # Skip if already converted
                    if exclude_converted and file_info["filename"] in self.converted_files["converted_files"]:
                        continue
                    
                    all_files.append((file_path, file_info))
        
        # Sort by chapter number if available
        all_files.sort(key=lambda x: x[1].get("chapter_number", 999999))
        
        # Copy first N files
        for i, (file_path, file_info) in enumerate(all_files[:count]):
            try:
                target_path = self.target_dir / file_info["filename"]
                shutil.copy2(file_path, target_path)
                copied_files.append(file_info["filename"])
                
                # Update metadata
                self.metadata["file_metadata"][file_info["filename"]] = file_info
                
                print(f"Copied: {file_info['filename']} ({file_info['word_count']} words)")
                
            except Exception as e:
                print(f"ERROR: Failed to copy {file_info['filename']}: {e}")
        
        self._save_metadata()
        return copied_files
    
    def copy_files_by_chapters(self, chapters: List[int], volume: str) -> List[str]:
        """Copy specific chapter numbers from a volume."""
        copied_files = []
        
        volume_path = None
        for pdf_folder in self.source_dir.iterdir():
            if pdf_folder.is_dir():
                vol_path = pdf_folder / volume
                if vol_path.exists():
                    volume_path = vol_path
                    break
        
        if not volume_path:
            print(f"ERROR: Volume {volume} not found")
            return copied_files
        
        for chapter_num in chapters:
            # Find chapter file
            chapter_files = list(volume_path.glob(f"Chapter_{chapter_num}_*.txt"))
            if not chapter_files:
                print(f"WARNING: Chapter {chapter_num} not found in {volume}")
                continue
            
            chapter_file = chapter_files[0]
            file_info = self.get_file_info(chapter_file)
            
            try:
                target_path = self.target_dir / file_info["filename"]
                shutil.copy2(chapter_file, target_path)
                copied_files.append(file_info["filename"])
                
                self.metadata["file_metadata"][file_info["filename"]] = file_info
                print(f"Copied: {file_info['filename']} ({file_info['word_count']} words)")
                
            except Exception as e:
                print(f"ERROR: Failed to copy {file_info['filename']}: {e}")
        
        self._save_metadata()
        return copied_files
    
    def copy_files_by_volume(self, volume: str, exclude_converted: bool = True) -> List[str]:
        """Copy all files from a specific volume."""
        copied_files = []
        file_structure = self.scan_source_files()
        
        for pdf_name, volumes in file_structure.items():
            if volume in volumes:
                for chapter_file in volumes[volume]:
                    file_path = self.source_dir / pdf_name / volume / chapter_file
                    file_info = self.get_file_info(file_path)
                    
                    # Skip if already converted
                    if exclude_converted and file_info["filename"] in self.converted_files["converted_files"]:
                        print(f"Skipped (already converted): {file_info['filename']}")
                        continue
                    
                    try:
                        target_path = self.target_dir / file_info["filename"]
                        shutil.copy2(file_path, target_path)
                        copied_files.append(file_info["filename"])
                        
                        self.metadata["file_metadata"][file_info["filename"]] = file_info
                        print(f"Copied: {file_info['filename']} ({file_info['word_count']} words)")
                        
                    except Exception as e:
                        print(f"ERROR: Failed to copy {file_info['filename']}: {e}")
        
        self._save_metadata()
        return copied_files
    
    def list_available_files(self, volume: Optional[str] = None):
        """List all available files for copying."""
        file_structure = self.scan_source_files()
        
        print("\n=== Available Files ===")
        total_files = 0
        converted_count = 0
        
        for pdf_name, volumes in file_structure.items():
            print(f"\n{pdf_name}")
            
            for vol_name, chapters in volumes.items():
                if volume and vol_name != volume:
                    continue
                
                print(f"  {vol_name} ({len(chapters)} chapters)")
                
                for chapter_file in chapters:
                    file_path = self.source_dir / pdf_name / vol_name / chapter_file
                    file_info = self.get_file_info(file_path)
                    
                    status = "[CONVERTED]" if chapter_file in self.converted_files["converted_files"] else "[PENDING]"
                    if status == "[CONVERTED]":
                        converted_count += 1
                    
                    print(f"    {status} {chapter_file} ({file_info['word_count']} words)")
                    total_files += 1
        
        print(f"\nSummary:")
        print(f"  Total files: {total_files}")
        print(f"  Already converted: {converted_count}")
        print(f"  Available for conversion: {total_files - converted_count}")
    
    def clear_input_directory(self):
        """Clear the input directory."""
        if self.target_dir.exists():
            for file in self.target_dir.iterdir():
                if file.is_file():
                    file.unlink()
            print(f"Cleared {self.target_dir} directory")


def main():
    parser = argparse.ArgumentParser(description="Organize text files for TTS processing")
    parser.add_argument("--source", default="../extracted_text", help="Source directory")
    parser.add_argument("--target", default="input", help="Target directory")
    
    # Selection methods
    parser.add_argument("--count", type=int, help="Copy N files")
    parser.add_argument("--volume", help="Copy all files from a volume")
    parser.add_argument("--chapters", help="Copy specific chapters (e.g., '1,5,10' or '1-10')")
    
    # Options
    parser.add_argument("--list", action="store_true", help="List available files")
    parser.add_argument("--clear", action="store_true", help="Clear input directory")
    parser.add_argument("--include-converted", action="store_true", help="Include already converted files")
    
    args = parser.parse_args()
    
    organizer = TTSFileOrganizer(args.source, args.target)
    
    if args.clear:
        organizer.clear_input_directory()
        return
    
    if args.list:
        organizer.list_available_files(args.volume)
        return
    
    copied_files = []
    
    if args.count:
        print(f"Copying {args.count} files...")
        copied_files = organizer.copy_files_by_count(
            args.count, 
            args.volume, 
            exclude_converted=not args.include_converted
        )
    
    elif args.volume and args.chapters:
        # Parse chapter numbers
        chapters = []
        if ',' in args.chapters:
            chapters = [int(x.strip()) for x in args.chapters.split(',')]
        elif '-' in args.chapters:
            start, end = map(int, args.chapters.split('-'))
            chapters = list(range(start, end + 1))
        else:
            chapters = [int(args.chapters)]
        
        print(f"Copying chapters {chapters} from volume {args.volume}...")
        copied_files = organizer.copy_files_by_chapters(chapters, args.volume)
    
    elif args.volume:
        print(f"Copying all files from volume {args.volume}...")
        copied_files = organizer.copy_files_by_volume(
            args.volume, 
            exclude_converted=not args.include_converted
        )
    
    else:
        print("Please specify --count, --volume, or --chapters")
        return
    
    print(f"\nSuccessfully copied {len(copied_files)} files to {args.target}/")
    
    if copied_files:
        print("\nCopied files:")
        for filename in copied_files:
            print(f"  - {filename}")


if __name__ == "__main__":
    main()
