#!/usr/bin/env python3
"""
Test script to examine the volume structure specifically.
This script focuses on identifying and analyzing the volume-level items in the PDF outline.

This is particularly useful for verifying that the PDF has the expected structure:
- 8 main volumes (VOLUME 1-8)
- 1 Cover (should be skipped)
- 1 Side Stories (should be included)
- Total: 10 level-0 items, 9 processable volumes
"""

import PyPDF2
from pathlib import Path
import sys
import os

# Add parent directory to path to import pdf_converter_clean
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_volume_structure():
    """Test the volume structure of lotm_book1.pdf"""
    pdf_path = "../../pdfs/lotm_book1.pdf"
    
    print("Examining PDF VOLUME structure...")
    print("=" * 60)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"PDF has {len(pdf_reader.pages)} pages")
            print(f"PDF has outline: {pdf_reader.outline is not None}")
            print()
            
            if pdf_reader.outline:
                print("VOLUME STRUCTURE (Level 0 items):")
                print("-" * 40)
                
                # Get all level 0 items (volumes)
                level0_items = []
                parse_outline_for_volumes(pdf_reader.outline, pdf_reader, level=0, level0_items=level0_items)
                
                print(f"\nFound {len(level0_items)} VOLUMES:")
                for i, item in enumerate(level0_items):
                    try:
                        print(f"  {i+1}. {item['title']} (Page {item['page']})")
                    except UnicodeEncodeError:
                        safe_title = item['title'].encode('ascii', 'replace').decode('ascii')
                        print(f"  {i+1}. {safe_title} (Page {item['page']})")
                
                print(f"\nExpected: 8 volumes + Cover + Sidestories = 10 total")
                print(f"Actual: {len(level0_items)} volumes")
                
                # Analyze which volumes should be processed
                processable_volumes = []
                skipped_volumes = []
                
                for item in level0_items:
                    title = item['title'].lower()
                    if 'cover' in title:
                        skipped_volumes.append(item)
                    else:
                        processable_volumes.append(item)
                
                print(f"\nProcessable volumes (skip Cover): {len(processable_volumes)}")
                print(f"Skipped volumes: {len(skipped_volumes)}")
                
                if len(processable_volumes) == 9:
                    print("CORRECT: Found exactly 9 processable volumes (8 main + 1 side stories)")
                else:
                    print(f"ISSUE: Expected 9 processable volumes, found {len(processable_volumes)}")
                
            else:
                print("No outline found in PDF")
                
    except Exception as e:
        print(f"Error reading PDF: {e}")

def parse_outline_for_volumes(outline, pdf_reader, level=0, level0_items=None):
    """Parse outline and collect level 0 items (volumes)"""
    if level0_items is None:
        level0_items = []
    
    for item in outline:
        if isinstance(item, list):
            # This is a nested list of items
            parse_outline_for_volumes(item, pdf_reader, level + 1, level0_items)
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
                
                # Only collect level 0 items (volumes)
                if level == 0:
                    level0_items.append({
                        'title': title,
                        'page': page_num,
                        'level': level
                    })
                
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue

if __name__ == "__main__":
    test_volume_structure()
