# PDF Converter Test Suite

This directory contains test scripts to analyze and validate the PDF structure before running the main conversion process. These tests help ensure the converter correctly understands the document outline and can properly organize content into volumes and chapters.

## Test Files

### 1. `test_outline.py` - Full Outline Analysis
**Purpose**: Comprehensive analysis of the entire PDF outline structure

**What it does**:
- Displays the complete hierarchy of the PDF's document outline
- Shows all levels (volumes, chapters, sub-sections)
- Identifies the structure and organization of content
- Handles Unicode characters properly for display

**Usage**:
```bash
cd tests
python test_outline.py
```

**Expected Output**:
- Shows all 1,442 outline items
- Displays volumes at level 0
- Shows chapters at level 1
- Identifies any sub-sections at level 2+

### 2. `test_volumes.py` - Volume Structure Analysis
**Purpose**: Focused analysis of volume-level items only

**What it does**:
- Extracts and displays only level 0 items (volumes)
- Validates the expected volume count (10 total, 9 processable)
- Identifies which volumes should be processed vs skipped
- Verifies the correct structure for Lord of the Mysteries

**Usage**:
```bash
cd tests
python test_volumes.py
```

**Expected Output**:
- 10 total volumes found
- 9 processable volumes (skips Cover)
- Lists: Cover, VOLUME 1-8, SIDE STORIES

### 3. `test_chapters.py` - Chapter Structure Analysis
**Purpose**: Detailed analysis of chapter organization within volumes

**What it does**:
- Shows how chapters are organized under each volume
- Displays chapter counts per volume
- Validates chapter-to-volume mapping
- Shows sample chapters from each volume

**Usage**:
```bash
cd tests
python test_chapters.py
```

**Expected Output**:
- Shows 8 main volumes + Side Stories
- Displays chapter counts for each volume
- Shows sample chapter titles and page numbers

## Running All Tests

To run all tests in sequence:

```bash
cd tests
python test_outline.py
echo "---"
python test_volumes.py
echo "---"
python test_chapters.py
```

## Test Results Validation

### ✅ Successful Test Results Should Show:

1. **PDF Structure**:
   - 9,575 total pages
   - 1,442 outline items total
   - 10 volumes (including Cover)
   - 1,432 chapters

2. **Volume Structure**:
   - Cover (Page 0) - should be skipped
   - VOLUME 1 - CLOWN (Page 3)
   - VOLUME 2 - FACELESS (Page 1479)
   - VOLUME 3 - TRAVELER (Page 3326)
   - VOLUME 4 - UNDYING (Page 5010)
   - VOLUME 5 - RED PRIEST (Page 6380)
   - VOLUME 6 - LIGHTSEEKER (Page 7703)
   - VOLUME 7 - THE HANGED MAN (Page 8489)
   - VOLUME 8 - FOOL (Page 9075)
   - SIDE STORIES (Page 9358)

3. **Chapter Distribution**:
   - Volume 1: ~213 chapters
   - Volume 2: ~269 chapters
   - Volume 3: ~250 chapters
   - Volume 4: ~214 chapters
   - Volume 5: ~204 chapters
   - Volume 6: ~116 chapters
   - Volume 7: ~87 chapters
   - Volume 8: ~41 chapters
   - Side Stories: ~38 chapters

### ❌ Common Issues to Watch For:

1. **Unicode Encoding Errors**:
   - Error: `'charmap' codec can't encode character`
   - Fix: Tests handle Unicode properly with fallback encoding

2. **Missing Outline**:
   - Error: "No outline found in PDF"
   - Cause: PDF doesn't have bookmarks/outline structure

3. **Wrong Volume Count**:
   - Expected: 10 total volumes (9 processable)
   - Actual: Different count indicates parsing issues

4. **Missing Chapters**:
   - Expected: 1,432 chapters total
   - Actual: Significantly different count

## Troubleshooting

### If Tests Fail:

1. **Check PDF Path**:
   - Ensure `lotm_book1.pdf` is in `../../pdfs/` relative to tests folder
   - Verify the PDF file exists and is readable

2. **Check Dependencies**:
   - Ensure PyPDF2 is installed: `pip install PyPDF2`
   - Python 3.6+ required

3. **Unicode Issues**:
   - Tests include Unicode handling
   - If still failing, check system locale settings

4. **Permission Issues**:
   - Ensure read access to PDF file
   - Check file isn't locked by another process

## Integration with Main Converter

These tests validate the same logic used by the main converter:

- `test_volumes.py` validates the volume filtering logic in `process_pdf_by_volumes()`
- `test_chapters.py` validates the chapter mapping logic in `_get_volume_chapters()`
- `test_outline.py` validates the outline parsing logic in `_parse_outline()`

If these tests pass but the main converter fails, the issue is likely in the text extraction or file writing logic, not the outline parsing.

## Adding New Tests

To add new tests:

1. Create a new `test_*.py` file in this directory
2. Follow the same pattern as existing tests
3. Include proper Unicode handling
4. Add documentation to this README
5. Test with the Lord of the Mysteries PDF structure

## Notes

- Tests are designed for the specific structure of `lotm_book1.pdf`
- Unicode handling is built-in for Chinese characters in volume titles
- Tests provide detailed output for debugging and validation
- All tests can be run independently or in sequence
