"""
Clean PDF to Text Converter with Document Outline Support

This module extracts text from PDF files and organizes content using the PDF's
document outline (bookmarks) for TTS-friendly output with volume-by-volume processing.

Key Features:
- Volume-by-volume processing for memory efficiency
- Real-time progress tracking with dual progress bars
- TTS-optimized output format with proper headers
- Comprehensive error handling and validation
- Smart folder organization and safe filename generation

Author: PDF-to-Audio Pipeline Team
Version: 2.0 (Cleaned and Optimized)
"""

import os
import re
import time
from pathlib import Path
from typing import List, Dict, Tuple
import PyPDF2
import pdfplumber


class PDFConverter:
    """
    Clean PDF converter that uses document outline for TTS-friendly organization.
    
    This converter processes PDF files by extracting their document outline (bookmarks)
    and organizing content into volume and chapter structures. It processes one volume
    at a time to manage memory efficiently and provides real-time progress tracking.
    
    Key Features:
    - Uses PDF document outline for accurate structure detection
    - Processes volumes sequentially to prevent memory issues
    - Generates TTS-friendly output with proper headers
    - Creates organized folder structure for downstream processing
    - Provides real-time progress bars with ETA calculations
    
    Attributes:
        output_dir (Path): Directory where converted text files will be saved
        pdf_name (str): Name of the PDF file being processed (without extension)
    
    Example:
        >>> converter = PDFConverter("my_output_folder")
        >>> converter.convert_pdf("my_book.pdf")
    """
    
    def __init__(self, output_dir: str = "extracted_text", chunk_size: int = 100):
        """
        Initialize the PDF converter with output directory.
        
        Args:
            output_dir (str): Directory where converted text files will be saved.
                            Defaults to "extracted_text".
            chunk_size (int): Chunk size for processing (currently unused but kept
                            for compatibility). Defaults to 100.
        
        Creates the output directory if it doesn't exist.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.pdf_name = None
    
    def extract_outline(self, pdf_path: str) -> List[Dict]:
        """
        Extract document outline/bookmarks from PDF file.
        
        This method reads the PDF's document outline (table of contents/bookmarks)
        and converts it into a structured list of dictionaries containing title,
        page number, and hierarchy level information.
        
        Args:
            pdf_path (str): Path to the PDF file to extract outline from
            
        Returns:
            List[Dict]: List of outline items, where each item contains:
                - 'title': The outline item title (str)
                - 'page': Page number where the item starts (int or None)
                - 'level': Hierarchy level (0 for volumes, >0 for chapters) (int)
        
        Example:
            >>> outline = converter.extract_outline("book.pdf")
            >>> print(outline[0])
            {'title': 'Volume 1', 'page': 1, 'level': 0}
        """
        outline_items = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if pdf_reader.outline:
                    outline_items = self._parse_outline(pdf_reader.outline, pdf_reader)
                else:
                    print("No document outline found in PDF")
                    
        except Exception as e:
            print(f"Error extracting outline: {e}")
            
        return outline_items
    
    def _parse_outline(self, outline, pdf_reader, level=0) -> List[Dict]:
        """Recursively parse outline items."""
        items = []
        
        for item in outline:
            if isinstance(item, list):
                items.extend(self._parse_outline(item, pdf_reader, level + 1))
            else:
                try:
                    page_num = None
                    if hasattr(item, 'page') and item.page is not None:
                        page_num = pdf_reader.get_destination_page_number(item)
                    elif hasattr(item, 'page_number'):
                        page_num = item.page_number
                    
                    outline_item = {
                        'title': str(item.title) if hasattr(item, 'title') else str(item),
                        'page': page_num,
                        'level': level
                    }
                    items.append(outline_item)
                    
                except Exception as e:
                    print(f"Error parsing outline item: {e}")
                    continue
        
        return items
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """Extract text from PDF file page by page."""
        pages_text = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        pages_text.append(text.strip())
                    else:
                        pages_text.append("")
                        
        except Exception as e:
            print(f"Error extracting text with pdfplumber: {e}")
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text:
                            pages_text.append(text.strip())
                        else:
                            pages_text.append("")
            except Exception as e2:
                print(f"Error with PyPDF2 fallback: {e2}")
                return []
        
        return pages_text
    
    def extract_text_chunked(self, pdf_path: str, chunk_size: int = 100) -> Tuple[int, List[Dict]]:
        """Extract text from PDF in chunks and return total pages and outline items."""
        total_pages = 0
        outline_items = self.extract_outline(pdf_path)
        
        if not outline_items:
            return 0, []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
        except Exception as e:
            print(f"Error getting page count: {e}")
            return 0, []
        
        return total_pages, outline_items
    
    def process_pdf_by_volumes(self, pdf_path: str, outline_items: List[Dict], total_pages: int, start_time: float) -> None:
        """Process PDF by volumes with progress tracking."""
        # Create main PDF folder
        main_dir = self.output_dir / self.pdf_name
        main_dir.mkdir(exist_ok=True)
        
        # Check if we have volume hierarchy (at least 2 levels)
        # Filter out "Cover" and only include actual volumes and side stories
        all_level0_items = [item for item in outline_items if item['level'] == 0]
        volumes = []
        
        for item in all_level0_items:
            title = item['title'].lower()
            # Skip cover, include actual volumes and side stories
            if 'cover' not in title:
                volumes.append(item)
        
        chapters = [item for item in outline_items if item['level'] > 0]
        
        if len(volumes) > 1 and len(chapters) > 0:
            print(f"Processing by volumes: {len(volumes)} volumes found")
            self._process_volumes(pdf_path, outline_items, volumes, chapters, main_dir, start_time)
        else:
            print("No volume hierarchy detected, creating single file with all content")
            pages_text = self.extract_text_from_pdf(pdf_path)
            if pages_text:
                all_content = '\n\n'.join(pages_text)
                with open(self.output_dir / "full_content.txt", 'w', encoding='utf-8') as f:
                    f.write("Lord of the Mysteries\n\n")
                    f.write(all_content)
                print(f"Created full_content.txt with {len(pages_text)} pages")
    
    def _process_volumes(self, pdf_path: str, outline_items: List[Dict], volumes: List[Dict], chapters: List[Dict], main_dir: Path, start_time: float) -> None:
        """Process PDF volume by volume with comprehensive error handling."""
        total_chapters = len(chapters)
        completed_chapters = 0
        failed_chapters = []
        processed_volumes = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pdf_pages = len(pdf.pages)
                print(f"PDF loaded: {total_pdf_pages} pages total")
                
                for vol_idx, volume in enumerate(volumes):
                    # Extract volume number from title
                    volume_num = self._extract_volume_number(volume['title'])
                    try:
                        print(f"\nProcessing Volume {volume_num}/{len(volumes)}: {volume['title']}")
                    except UnicodeEncodeError:
                        safe_title = volume['title'].encode('ascii', 'replace').decode('ascii')
                        print(f"\nProcessing Volume {volume_num}/{len(volumes)}: {safe_title}")
                    
                    try:
                        # Find chapters in this volume
                        volume_chapters = self._get_volume_chapters(volume, outline_items)
                        
                        if not volume_chapters:
                            print(f"  WARNING: No chapters found for volume: {volume['title']}")
                            continue
                        
                        print(f"  Found {len(volume_chapters)} chapters in this volume")
                        
                        # Extract volume content with validation
                        volume_start = volume['page'] if volume['page'] is not None else 0
                        volume_end = self._get_volume_end_page(volume, volumes, vol_idx)
                        
                        # Validate page boundaries
                        if volume_start >= total_pdf_pages:
                            print(f"  ERROR: Volume start page {volume_start} exceeds PDF pages {total_pdf_pages}")
                            continue
                        
                        volume_end = min(volume_end, total_pdf_pages - 1)
                        print(f"  Extracting pages {volume_start} to {volume_end}")
                        
                        # Extract pages for this volume with error handling
                        volume_pages = []
                        failed_pages = []
                        
                        for page_num in range(volume_start, volume_end + 1):
                            try:
                                page = pdf.pages[page_num]
                                text = page.extract_text()
                                if text:
                                    volume_pages.append(text.strip())
                                else:
                                    volume_pages.append("")
                                    print(f"    WARNING: Page {page_num} extracted empty text")
                            except Exception as e:
                                print(f"    ERROR: Failed to extract page {page_num}: {e}")
                                volume_pages.append("")
                                failed_pages.append(page_num)
                        
                        if failed_pages:
                            print(f"  WARNING: {len(failed_pages)} pages failed to extract: {failed_pages}")
                        
                        # Process volume file
                        volume_filename = self._create_filename(volume['title'], 0, volume_num)
                        volume_file_path = main_dir / volume_filename
                        
                        try:
                            with open(volume_file_path, 'w', encoding='utf-8') as f:
                                f.write(f"Lord of the Mysteries\n")
                                # Clean volume title for header
                                clean_vol_title = self._clean_title(volume['title'])
                                f.write(f"Volume {volume_num}: {clean_vol_title}\n\n")
                                f.write('\n\n'.join(volume_pages))
                            print(f"  Volume file created: {volume_filename}")
                        except Exception as e:
                            print(f"  ERROR: Failed to write volume file: {e}")
                            continue
                        
                        # Process chapters in this volume
                        volume_folder = self._create_volume_folder_name(volume['title'], volume_num)
                        volume_dir = main_dir / volume_folder
                        volume_dir.mkdir(exist_ok=True)
                        
                        volume_chapter_count = 0
                        
                        for chapter in volume_chapters:
                            try:
                                chapter_num = self._extract_chapter_number(chapter['title'])
                                chapter_filename = self._create_filename(chapter['title'], 1, chapter_num)
                                chapter_file_path = volume_dir / chapter_filename
                                
                                # Extract chapter content with validation
                                chapter_start = chapter['page'] if chapter['page'] is not None else volume_start
                                chapter_end = self._get_chapter_end_page(chapter, outline_items)
                                
                                # Validate chapter boundaries
                                if chapter_start < volume_start or chapter_start > volume_end:
                                    print(f"    WARNING: Chapter {chapter_num} start page {chapter_start} outside volume range")
                                    chapter_start = volume_start
                                
                                if chapter_end > volume_end:
                                    chapter_end = volume_end
                                
                                # Get chapter pages relative to volume start
                                chapter_start_rel = chapter_start - volume_start
                                chapter_end_rel = chapter_end - volume_start
                                
                                chapter_start_rel = max(0, chapter_start_rel)
                                chapter_end_rel = min(len(volume_pages) - 1, chapter_end_rel)
                                
                                if chapter_start_rel > chapter_end_rel:
                                    print(f"    ERROR: Invalid chapter boundaries for {chapter['title']}")
                                    failed_chapters.append(chapter['title'])
                                    continue
                                
                                chapter_content = '\n\n'.join(volume_pages[chapter_start_rel:chapter_end_rel + 1])
                                
                                # Validate chapter content
                                if not chapter_content.strip():
                                    print(f"    WARNING: Chapter {chapter_num} has no content")
                                
                                # Write chapter file
                                with open(chapter_file_path, 'w', encoding='utf-8') as f:
                                    clean_title = self._clean_title(chapter['title'])
                                    f.write(f"Lord of the Mysteries\n")
                                    f.write(f"Chapter {chapter_num}\n")
                                    f.write(f"{clean_title}\n\n")
                                    f.write(chapter_content)
                                
                                completed_chapters += 1
                                volume_chapter_count += 1
                                
                            except Exception as e:
                                print(f"    ERROR: Failed to process chapter {chapter['title']}: {e}")
                                failed_chapters.append(chapter['title'])
                                continue
                        
                        print(f"  Completed {volume_chapter_count}/{len(volume_chapters)} chapters in this volume")
                        processed_volumes.append(volume['title'])
                        
                        # Show progress
                        self.show_dual_progress(
                            volume_end, total_pdf_pages,
                            completed_chapters, total_chapters,
                            f"Processing Volume {vol_idx + 1}", start_time
                        )
                        
                    except Exception as e:
                        print(f"  ERROR: Failed to process volume {volume['title']}: {e}")
                        continue
        
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to open PDF: {e}")
            return
        
        # Final validation report
        print(f"\n=== PROCESSING COMPLETE ===")
        print(f"Processed volumes: {len(processed_volumes)}/{len(volumes)}")
        print(f"Completed chapters: {completed_chapters}/{total_chapters}")
        
        if failed_chapters:
            print(f"Failed chapters ({len(failed_chapters)}):")
            for chapter in failed_chapters[:10]:  # Show first 10
                print(f"  - {chapter}")
            if len(failed_chapters) > 10:
                print(f"  ... and {len(failed_chapters) - 10} more")
        
        if completed_chapters < total_chapters:
            print(f"WARNING: {total_chapters - completed_chapters} chapters were not processed!")
        else:
            print("SUCCESS: All chapters processed successfully!")
    
    def _get_volume_chapters(self, volume: Dict, outline_items: List[Dict]) -> List[Dict]:
        """Get all chapters belonging to a volume."""
        volume_index = outline_items.index(volume)
        chapters = []
        
        # Look for chapters after this volume
        for i in range(volume_index + 1, len(outline_items)):
            item = outline_items[i]
            if item['level'] == 0:  # Next volume found
                break
            elif item['level'] > 0:  # Chapter found
                chapters.append(item)
        
        return chapters
    
    def _get_volume_end_page(self, volume: Dict, volumes: List[Dict], vol_index: int) -> int:
        """Get the end page of a volume."""
        if vol_index + 1 < len(volumes):
            next_volume = volumes[vol_index + 1]
            return next_volume['page'] - 1 if next_volume['page'] is not None else 0
        else:
            # Last volume - go to end of document
            return 999999
    
    def _get_chapter_end_page(self, chapter: Dict, outline_items: List[Dict]) -> int:
        """Get the end page of a chapter."""
        chapter_index = outline_items.index(chapter)
        
        # Look for next chapter or volume
        for i in range(chapter_index + 1, len(outline_items)):
            if outline_items[i]['level'] <= chapter['level']:
                return outline_items[i]['page'] - 1 if outline_items[i]['page'] is not None else 0
        
        # If no next chapter found, assume it goes to end
        return 999999
    
    def _clean_title(self, title: str) -> str:
        """Clean and normalize outline title."""
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title.strip())
        
        # Remove common prefixes and chapter numbers
        title = re.sub(r'^(Chapter|Ch\.?|Vol\.?|Volume|Book|Part)\s+\d+\s*', '', title, flags=re.IGNORECASE)
        
        return title
    
    def _extract_chapter_number(self, title: str) -> str:
        """Extract chapter number from title."""
        # Look for chapter number pattern
        match = re.search(r'Chapter\s+(\d+)', title, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Fallback: look for any number at the start
        match = re.search(r'^(\d+)', title.strip())
        if match:
            return match.group(1)
        
        return "1"  # Default fallback
    
    def _extract_volume_number(self, title: str) -> str:
        """Extract volume number from title."""
        # Look for volume number pattern like "VOLUME 1" or "Volume 1"
        match = re.search(r'VOLUME\s+(\d+)', title, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Look for side stories
        if 'side' in title.lower() and 'stories' in title.lower():
            return "Side Stories"
        
        # Fallback: look for any number at the start
        match = re.search(r'^(\d+)', title.strip())
        if match:
            return match.group(1)
        
        return "1"  # Default fallback
    
    def _create_filename(self, title: str, level: int, chapter_num: str = None) -> str:
        """Create a safe filename from title with chapter/volume number."""
        # Convert to ASCII, replacing Unicode characters
        safe_title = title.encode('ascii', 'replace').decode('ascii')
        
        # Remove common prefixes to avoid duplication
        safe_title = re.sub(r'^(Chapter|Ch\.?|Vol\.?|Volume|Book|Part)\s+\d+\s*', '', safe_title, flags=re.IGNORECASE)
        
        # Remove or replace invalid filename characters
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', safe_title)
        safe_title = re.sub(r'\s+', '_', safe_title)
        safe_title = re.sub(r'[^\w\-_.]', '_', safe_title)
        
        # Limit length
        if len(safe_title) > 30:
            safe_title = safe_title[:30]
        
        # Use appropriate prefix with chapter/volume number
        if level == 0:
            # For volumes, use the volume number and clean title
            if chapter_num and chapter_num != "Side Stories":
                filename = f"Volume_{chapter_num}_{safe_title}.txt"
            elif chapter_num == "Side Stories":
                filename = f"Side_Stories.txt"
            else:
            filename = f"Volume_{safe_title}.txt"
        else:
            filename = f"Chapter_{chapter_num}_{safe_title}.txt"
        
        return filename
    
    def _create_volume_folder_name(self, volume_title: str, volume_num: str) -> str:
        """Create a safe folder name from volume title with volume number."""
        # Convert to ASCII, replacing Unicode characters
        safe_title = volume_title.encode('ascii', 'replace').decode('ascii')
        
        # Remove common prefixes
        safe_title = re.sub(r'^(Volume|Vol\.?|Book|Part)\s+', '', safe_title, flags=re.IGNORECASE)
        
        # Remove or replace invalid filename characters
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', safe_title)
        safe_title = re.sub(r'\s+', '_', safe_title)
        safe_title = re.sub(r'[^\w\-_.]', '_', safe_title)
        
        # Limit length
        if len(safe_title) > 30:
            safe_title = safe_title[:30]
        
        # Add volume number prefix
        if volume_num == "Side Stories":
            return "Side_Stories"
        else:
            return f"{volume_num}_{safe_title}"
    
    def display_outline_summary(self, outline_items: List[Dict]) -> None:
        """Display a summary of the document outline."""
        volumes = [item for item in outline_items if item['level'] == 0]
        chapters = [item for item in outline_items if item['level'] > 0]
        
        print(f"\nDocument Summary:")
        print(f"- Total outline items: {len(outline_items)}")
        print(f"- Volumes: {len(volumes)}")
        print(f"- Chapters: {len(chapters)}")
        
        if volumes:
            print(f"\nVolumes found:")
            for vol in volumes[:5]:  # Show first 5 volumes only
                try:
                    print(f"  - {vol['title']}")
                except UnicodeEncodeError:
                    safe_title = vol['title'].encode('ascii', 'replace').decode('ascii')
                    print(f"  - {safe_title}")
            if len(volumes) > 5:
                print(f"  ... and {len(volumes) - 5} more volumes")
    
    def show_dual_progress(self, pages_completed: int, total_pages: int, chapters_completed: int, total_chapters: int, operation: str, start_time: float) -> None:
        """
        Display dual progress bars for pages and chapters with ETA calculation.
        
        This method creates a visual progress display showing both page and chapter
        completion progress with estimated time remaining. It's designed to provide
        real-time feedback during long conversion processes.
        
        Args:
            pages_completed (int): Number of pages processed so far
            total_pages (int): Total number of pages in the PDF
            chapters_completed (int): Number of chapters processed so far
            total_chapters (int): Total number of chapters in the PDF
            operation (str): Description of current operation (e.g., "Processing Volume 1")
            start_time (float): Timestamp when conversion started (for ETA calculation)
        
        Example Output:
            Processing Volume 1:
              Pages:   [##########----------] 50.0% (125/250)
              Chapters: [#######-------------] 35.0% (7/20) ETA: 45s
        """
        # Calculate progress percentages
        pages_progress = pages_completed / total_pages if total_pages > 0 else 0
        chapters_progress = chapters_completed / total_chapters if total_chapters > 0 else 0
        
        # Create visual progress bars
        pages_bar_length = 20
        pages_filled = int(pages_bar_length * pages_progress)
        pages_bar = '#' * pages_filled + '-' * (pages_bar_length - pages_filled)
        
        chapters_bar_length = 20
        chapters_filled = int(chapters_bar_length * chapters_progress)
        chapters_bar = '#' * chapters_filled + '-' * (chapters_bar_length - chapters_filled)
        
        # Calculate estimated time remaining
        elapsed_time = time.time() - start_time
        if pages_completed > 0:
            estimated_total = elapsed_time * total_pages / pages_completed
            remaining_time = estimated_total - elapsed_time
            eta_str = f"ETA: {remaining_time:.0f}s"
        else:
            eta_str = "ETA: calculating..."
        
        # Convert to percentages for display
        pages_pct = pages_progress * 100
        chapters_pct = chapters_progress * 100
        
        # Display progress bars with error handling for Unicode
        try:
            print(f"\r{operation}:")
            print(f"  Pages:   [{pages_bar}] {pages_pct:.1f}% ({pages_completed}/{total_pages})")
            print(f"  Chapters: [{chapters_bar}] {chapters_pct:.1f}% ({chapters_completed}/{total_chapters}) {eta_str}", end='', flush=True)
        except UnicodeEncodeError:
            # Fallback to ASCII-only display for systems that don't support Unicode
            print(f"\r{operation}: Pages {pages_pct:.1f}% ({pages_completed}/{total_pages}) | Chapters {chapters_pct:.1f}% ({chapters_completed}/{total_chapters}) {eta_str}", end='', flush=True)
        
        # Add newline when conversion is complete
        if pages_completed == total_pages and chapters_completed == total_chapters:
            print()  # New line when complete
    
    def convert_pdf(self, pdf_path: str) -> None:
        """
        Main method to convert PDF using volume-by-volume processing.
        
        This is the primary entry point for converting a PDF file into organized
        text files. It handles the entire conversion process including:
        - Document outline extraction
        - Volume and chapter structure detection
        - Volume-by-volume text extraction with progress tracking
        - TTS-friendly file generation with proper headers
        
        Args:
            pdf_path (str): Path to the PDF file to convert
            
        Output:
            Creates organized text files in the output directory with structure:
            - PDF_Name/Volume_Folders/Chapter_Files
            - Each file includes TTS-friendly headers
            
        Example:
            >>> converter = PDFConverter("output_folder")
            >>> converter.convert_pdf("my_book.pdf")
            Converting PDF: my_book.pdf
            Extracting document outline...
            Processing by volumes: 3 volumes found
            ...
        """
        start_time = time.time()
        print(f"Converting PDF: {pdf_path}")
        
        # Set PDF name for folder naming
        pdf_file = Path(pdf_path)
        self.pdf_name = pdf_file.stem
        
        # Extract document outline and get page count
        print("Extracting document outline...")
        total_pages, outline_items = self.extract_text_chunked(pdf_path)
        
        if not outline_items:
            print("No outline found. Creating single file.")
            pages_text = self.extract_text_from_pdf(pdf_path)
            if pages_text:
                all_content = '\n\n'.join(pages_text)
                with open(self.output_dir / "full_content.txt", 'w', encoding='utf-8') as f:
                    f.write("Lord of the Mysteries\n\n")
                    f.write(all_content)
                print(f"Created full_content.txt with {len(pages_text)} pages")
            return
        
        # Display summary instead of full outline
        self.display_outline_summary(outline_items)
        
        # Process PDF by volumes (if hierarchy exists) or chunks (fallback)
        print(f"\nTotal pages: {total_pages}, Total chapters: {len([item for item in outline_items if item['level'] > 0])}")
        
        self.process_pdf_by_volumes(pdf_path, outline_items, total_pages, start_time)
        
        total_time = time.time() - start_time
        print(f"\nConversion complete! Files saved to: {self.output_dir}")
        print(f"Total processing time: {total_time:.1f} seconds")

        print(f"Completed chapters: {completed_chapters}/{total_chapters}")

        

        if failed_chapters:

            print(f"Failed chapters ({len(failed_chapters)}):")

            for chapter in failed_chapters[:10]:  # Show first 10

                print(f"  - {chapter}")

            if len(failed_chapters) > 10:

                print(f"  ... and {len(failed_chapters) - 10} more")

        

        if completed_chapters < total_chapters:

            print(f"WARNING: {total_chapters - completed_chapters} chapters were not processed!")

        else:

            print("SUCCESS: All chapters processed successfully!")

    

    def _get_volume_chapters(self, volume: Dict, outline_items: List[Dict]) -> List[Dict]:

        """Get all chapters belonging to a volume."""

        volume_index = outline_items.index(volume)

        chapters = []

        

        # Look for chapters after this volume

        for i in range(volume_index + 1, len(outline_items)):

            item = outline_items[i]

            if item['level'] == 0:  # Next volume found

                break

            elif item['level'] > 0:  # Chapter found

                chapters.append(item)

        

        return chapters

    

    def _get_volume_end_page(self, volume: Dict, volumes: List[Dict], vol_index: int) -> int:

        """Get the end page of a volume."""

        if vol_index + 1 < len(volumes):

            next_volume = volumes[vol_index + 1]

            return next_volume['page'] - 1 if next_volume['page'] is not None else 0

        else:

            # Last volume - go to end of document

            return 999999

    

    def _get_chapter_end_page(self, chapter: Dict, outline_items: List[Dict]) -> int:

        """Get the end page of a chapter."""

        chapter_index = outline_items.index(chapter)

        

        # Look for next chapter or volume

        for i in range(chapter_index + 1, len(outline_items)):

            if outline_items[i]['level'] <= chapter['level']:

                return outline_items[i]['page'] - 1 if outline_items[i]['page'] is not None else 0

        

        # If no next chapter found, assume it goes to end

        return 999999

    

    def _clean_title(self, title: str) -> str:

        """Clean and normalize outline title."""

        # Remove extra whitespace

        title = re.sub(r'\s+', ' ', title.strip())

        

        # Remove common prefixes and chapter numbers

        title = re.sub(r'^(Chapter|Ch\.?|Vol\.?|Volume|Book|Part)\s+\d+\s*', '', title, flags=re.IGNORECASE)

        

        return title

    

    def _extract_chapter_number(self, title: str) -> str:

        """Extract chapter number from title."""

        # Look for chapter number pattern

        match = re.search(r'Chapter\s+(\d+)', title, re.IGNORECASE)

        if match:

            return match.group(1)

        

        # Fallback: look for any number at the start

        match = re.search(r'^(\d+)', title.strip())

        if match:

            return match.group(1)

        

        return "1"  # Default fallback

    

    def _create_filename(self, title: str, level: int, chapter_num: str = None) -> str:

        """Create a safe filename from title with chapter number."""

        # Convert to ASCII, replacing Unicode characters

        safe_title = title.encode('ascii', 'replace').decode('ascii')

        

        # Remove common prefixes to avoid duplication

        safe_title = re.sub(r'^(Chapter|Ch\.?|Vol\.?|Volume|Book|Part)\s+\d+\s*', '', safe_title, flags=re.IGNORECASE)

        

        # Remove or replace invalid filename characters

        safe_title = re.sub(r'[<>:"/\\|?*]', '_', safe_title)

        safe_title = re.sub(r'\s+', '_', safe_title)

        safe_title = re.sub(r'[^\w\-_.]', '_', safe_title)

        

        # Limit length

        if len(safe_title) > 30:

            safe_title = safe_title[:30]

        

        # Use appropriate prefix with chapter number

        if level == 0:

            filename = f"Volume_{safe_title}.txt"

        else:

            filename = f"Chapter_{chapter_num}_{safe_title}.txt"

        

        return filename

    

    def _create_volume_folder_name(self, volume_title: str) -> str:

        """Create a safe folder name from volume title."""

        # Convert to ASCII, replacing Unicode characters

        safe_title = volume_title.encode('ascii', 'replace').decode('ascii')

        

        # Remove common prefixes

        safe_title = re.sub(r'^(Volume|Vol\.?|Book|Part)\s+', '', safe_title, flags=re.IGNORECASE)

        

        # Remove or replace invalid filename characters

        safe_title = re.sub(r'[<>:"/\\|?*]', '_', safe_title)

        safe_title = re.sub(r'\s+', '_', safe_title)

        safe_title = re.sub(r'[^\w\-_.]', '_', safe_title)

        

        # Limit length

        if len(safe_title) > 30:

            safe_title = safe_title[:30]

        

        return safe_title

    

    def display_outline_summary(self, outline_items: List[Dict]) -> None:

        """Display a summary of the document outline."""

        volumes = [item for item in outline_items if item['level'] == 0]

        chapters = [item for item in outline_items if item['level'] > 0]

        

        print(f"\nDocument Summary:")

        print(f"- Total outline items: {len(outline_items)}")

        print(f"- Volumes: {len(volumes)}")

        print(f"- Chapters: {len(chapters)}")

        

        if volumes:

            print(f"\nVolumes found:")

            for vol in volumes[:5]:  # Show first 5 volumes only

                try:

                    print(f"  - {vol['title']}")

                except UnicodeEncodeError:

                    safe_title = vol['title'].encode('ascii', 'replace').decode('ascii')

                    print(f"  - {safe_title}")

            if len(volumes) > 5:

                print(f"  ... and {len(volumes) - 5} more volumes")

    

    def show_dual_progress(self, pages_completed: int, total_pages: int, chapters_completed: int, total_chapters: int, operation: str, start_time: float) -> None:

        """
        Display dual progress bars for pages and chapters with ETA calculation.
        
        This method creates a visual progress display showing both page and chapter
        completion progress with estimated time remaining. It's designed to provide
        real-time feedback during long conversion processes.
        
        Args:
            pages_completed (int): Number of pages processed so far
            total_pages (int): Total number of pages in the PDF
            chapters_completed (int): Number of chapters processed so far
            total_chapters (int): Total number of chapters in the PDF
            operation (str): Description of current operation (e.g., "Processing Volume 1")
            start_time (float): Timestamp when conversion started (for ETA calculation)
        
        Example Output:
            Processing Volume 1:
              Pages:   [##########----------] 50.0% (125/250)
              Chapters: [#######-------------] 35.0% (7/20) ETA: 45s
        """
        # Calculate progress percentages
        pages_progress = pages_completed / total_pages if total_pages > 0 else 0

        chapters_progress = chapters_completed / total_chapters if total_chapters > 0 else 0
        
        # Create visual progress bars
        pages_bar_length = 20

        pages_filled = int(pages_bar_length * pages_progress)

        pages_bar = '#' * pages_filled + '-' * (pages_bar_length - pages_filled)

        

        chapters_bar_length = 20

        chapters_filled = int(chapters_bar_length * chapters_progress)

        chapters_bar = '#' * chapters_filled + '-' * (chapters_bar_length - chapters_filled)

        

        # Calculate estimated time remaining
        elapsed_time = time.time() - start_time

        if pages_completed > 0:

            estimated_total = elapsed_time * total_pages / pages_completed

            remaining_time = estimated_total - elapsed_time

            eta_str = f"ETA: {remaining_time:.0f}s"

        else:

            eta_str = "ETA: calculating..."

        

        # Convert to percentages for display
        pages_pct = pages_progress * 100

        chapters_pct = chapters_progress * 100

        

        # Display progress bars with error handling for Unicode
        try:

            print(f"\r{operation}:")

            print(f"  Pages:   [{pages_bar}] {pages_pct:.1f}% ({pages_completed}/{total_pages})")

            print(f"  Chapters: [{chapters_bar}] {chapters_pct:.1f}% ({chapters_completed}/{total_chapters}) {eta_str}", end='', flush=True)

        except UnicodeEncodeError:

            # Fallback to ASCII-only display for systems that don't support Unicode
            print(f"\r{operation}: Pages {pages_pct:.1f}% ({pages_completed}/{total_pages}) | Chapters {chapters_pct:.1f}% ({chapters_completed}/{total_chapters}) {eta_str}", end='', flush=True)

        

        # Add newline when conversion is complete
        if pages_completed == total_pages and chapters_completed == total_chapters:

            print()  # New line when complete

    

    def convert_pdf(self, pdf_path: str) -> None:

        """
        Main method to convert PDF using volume-by-volume processing.
        
        This is the primary entry point for converting a PDF file into organized
        text files. It handles the entire conversion process including:
        - Document outline extraction
        - Volume and chapter structure detection
        - Volume-by-volume text extraction with progress tracking
        - TTS-friendly file generation with proper headers
        
        Args:
            pdf_path (str): Path to the PDF file to convert
            
        Output:
            Creates organized text files in the output directory with structure:
            - PDF_Name/Volume_Folders/Chapter_Files
            - Each file includes TTS-friendly headers
            
        Example:
            >>> converter = PDFConverter("output_folder")
            >>> converter.convert_pdf("my_book.pdf")
            Converting PDF: my_book.pdf
            Extracting document outline...
            Processing by volumes: 3 volumes found
            ...
        """
        start_time = time.time()

        print(f"Converting PDF: {pdf_path}")

        

        # Set PDF name for folder naming

        pdf_file = Path(pdf_path)

        self.pdf_name = pdf_file.stem

        

        # Extract document outline and get page count

        print("Extracting document outline...")

        total_pages, outline_items = self.extract_text_chunked(pdf_path)

        

        if not outline_items:

            print("No outline found. Creating single file.")

            pages_text = self.extract_text_from_pdf(pdf_path)

            if pages_text:

                all_content = '\n\n'.join(pages_text)

                with open(self.output_dir / "full_content.txt", 'w', encoding='utf-8') as f:

                    f.write("Lord of the Mysteries\n\n")

                    f.write(all_content)

                print(f"Created full_content.txt with {len(pages_text)} pages")

            return

        

        # Display summary instead of full outline

        self.display_outline_summary(outline_items)

        

        # Process PDF by volumes (if hierarchy exists) or chunks (fallback)

        print(f"\nTotal pages: {total_pages}, Total chapters: {len([item for item in outline_items if item['level'] > 0])}")
        

        self.process_pdf_by_volumes(pdf_path, outline_items, total_pages, start_time)

        

        total_time = time.time() - start_time

        print(f"\nConversion complete! Files saved to: {self.output_dir}")

        print(f"Total processing time: {total_time:.1f} seconds")

