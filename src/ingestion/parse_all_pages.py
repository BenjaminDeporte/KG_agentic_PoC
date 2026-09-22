#!/usr/bin/env python3
"""
Batch parser for all 59 .docx files.

Parses all page_*.docx files from docs/full_2908_docx/
and outputs a single JSON file indexed by page number.
"""

import sys
import json
import os
import glob
from collections import OrderedDict

# Import the parser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_word_xml import parse_docx


def main():
    # Input directory
    input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                          'docs', 'full_2908_docx')
    
    # Output file
    output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                            'data', 'parsed', 'A320_2010_2026_all_pages.json')
    
    # Get all page files
    page_files = sorted(glob.glob(os.path.join(input_dir, 'page_*.docx')))
    
    print(f"Found {len(page_files)} .docx files")
    
    # Parse all pages
    all_pages = OrderedDict()
    total_records = 0
    issues = []
    
    for i, file_path in enumerate(page_files, 1):
        print(f"\nProcessing page {i}: {os.path.basename(file_path)}")
        
        try:
            records = parse_docx(file_path)
            print(f"  Parsed {len(records)} records")
            
            if records:
                # Store with page number as key
                all_pages[str(i)] = records
                total_records += len(records)
            else:
                issues.append(f"Page {i}: No records parsed")
                
        except Exception as e:
            issues.append(f"Page {i}: Error - {str(e)}")
            print(f"  ERROR: {e}")
    
    # Save output
    output = {
        "total_pages": len(all_pages),
        "total_records": total_records,
        "pages": all_pages,
        "issues": issues
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"COMPLETE")
    print(f"{'='*60}")
    print(f"Total pages processed: {len(all_pages)}")
    print(f"Total records parsed: {total_records}")
    print(f"Issues found: {len(issues)}")
    if issues:
        for issue in issues:
            print(f"  - {issue}")
    print(f"\nOutput saved to: {output_file}")


if __name__ == '__main__':
    main()
