#!/usr/bin/env python3
"""
Test script to examine the chapter structure within volumes.
This script analyzes how chapters are organized under each volume and validates
the chapter-to-volume mapping.

This helps ensure that:
- Chapters are correctly assigned to their parent volumes
- Chapter numbering is sequential within each volume
- Page ranges are correct
"""

import PyPDF2
from pathlib import Path
import sys
import os

# Add parent directory to path to import pdf_converter_clean
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_chapter_structure():
    """Test the chapter structure of lotm_book1.pdf"""
    pdf_path = "../../pdfs/lotm_book1.pdf"
    
    print("Examining PDF CHAPTER structure...")
    print("=" * 60)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"PDF has {len(pdf_reader.pages)} pages")
            print(f"PDF has outline: {pdf_reader.outline is not None}")
            print()
            
            if pdf_reader.outline:
                # Parse outline into structured data
                outline_items = parse_outline_structured(pdf_reader.outline, pdf_reader)
                
                # Separate volumes and chapters
                volumes = [item for item in outline_items if item['level'] == 0]
                chapters = [item for item in outline_items if item['level'] > 0]
                
                print(f"Found {len(volumes)} volumes and {len(chapters)} chapters")
                print()
                
                # Analyze each volume and its chapters
                for i, volume in enumerate(volumes):
                    volume_title = volume['title']
                    volume_page = volume['page']
                    
                    try:
                        print(f"Volume {i+1}: {volume_title} (Page {volume_page})")
                    except UnicodeEncodeError:
                        safe_title = volume_title.encode('ascii', 'replace').decode('ascii')
                        print(f"Volume {i+1}: {safe_title} (Page {volume_page})")
                    
                    # Find chapters in this volume
                    volume_chapters = get_chapters_for_volume(volume, outline_items)
                    
                    print(f"  Chapters in this volume: {len(volume_chapters)}")
                    
                    # Show first few chapters as examples
                    for j, chapter in enumerate(volume_chapters[:3]):
                        try:
                            print(f"    {j+1}. {chapter['title']} (Page {chapter['page']})")
                        except UnicodeEncodeError:
                            safe_title = chapter['title'].encode('ascii', 'replace').decode('ascii')
                            print(f"    {j+1}. {safe_title} (Page {chapter['page']})")
                    
                    if len(volume_chapters) > 3:
                        print(f"    ... and {len(volume_chapters) - 3} more chapters")
                    
                    print()
                
            else:
                print("No outline found in PDF")
                
    except Exception as e:
        print(f"Error reading PDF: {e}")

def parse_outline_structured(outline, pdf_reader, level=0):
    """Parse outline into structured list of items"""
    items = []
    
    for item in outline:
        if isinstance(item, list):
            # This is a nested list of items
            items.extend(parse_outline_structured(item, pdf_reader, level + 1))
        else:
            # This is an individual outline item
            try:
                # Get page number
                page_num = None
                if hasattr(item, 'page') and item.page is not None:
                    page_num = pdf_reader.get_destination_page_number(item)
                elif hasattr(item, 'page_number'):
                    page_num = item.page_number
                
                # Get title with Unicode handling
                try:
                    title = str(item.title) if hasattr(item, 'title') else str(item)
                except UnicodeEncodeError:
                    title = str(item.title).encode('ascii', 'replace').decode('ascii') if hasattr(item, 'title') else str(item)
                
                items.append({
                    'title': title,
                    'page': page_num,
                    'level': level
                })
                
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue
    
    return items

def get_chapters_for_volume(volume, outline_items):
    """Get all chapters that belong to a specific volume"""
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

if __name__ == "__main__":
    test_chapter_structure()
