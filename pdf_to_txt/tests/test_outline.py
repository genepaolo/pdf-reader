#!/usr/bin/env python3
"""
Test script to examine the PDF outline structure for Lord of the Mysteries.
This will help us understand the correct hierarchy before fixing the parser.

This script provides detailed analysis of the PDF's document outline (bookmarks)
to understand the structure and identify any parsing issues.
"""

import PyPDF2
from pathlib import Path
import sys
import os

# Add parent directory to path to import pdf_converter_clean
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_outline_structure():
    """Test the outline structure of lotm_book1.pdf"""
    pdf_path = "../../pdfs/lotm_book1.pdf"
    
    print("Examining PDF outline structure...")
    print("=" * 60)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"PDF has {len(pdf_reader.pages)} pages")
            print(f"PDF has outline: {pdf_reader.outline is not None}")
            print()
            
            if pdf_reader.outline:
                print("OUTLINE STRUCTURE:")
                print("-" * 40)
                parse_outline_recursive(pdf_reader.outline, pdf_reader, level=0)
            else:
                print("No outline found in PDF")
                
    except Exception as e:
        print(f"Error reading PDF: {e}")

def parse_outline_recursive(outline, pdf_reader, level=0):
    """Recursively parse and display outline structure"""
    indent = "  " * level
    
    for item in outline:
        if isinstance(item, list):
            # This is a nested list of items
            parse_outline_recursive(item, pdf_reader, level + 1)
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
                
                # Display the item
                page_info = f" (Page {page_num})" if page_num is not None else " (No page)"
                print(f"{indent}Level {level}: {title}{page_info}")
                
                # Show first 10 items at each level to avoid spam
                if level == 0:
                    print(f"{indent}  -> This appears to be a VOLUME")
                elif level == 1:
                    print(f"{indent}  -> This appears to be a CHAPTER")
                elif level >= 2:
                    print(f"{indent}  -> This appears to be a SUB-SECTION")
                
            except Exception as e:
                print(f"{indent}Error parsing item: {e}")
                continue

if __name__ == "__main__":
    test_outline_structure()
