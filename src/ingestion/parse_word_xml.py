#!/usr/bin/env python3
"""
ASRS ACN Parser for Word XML (.docx) files

Parses Office Open XML format from Word documents containing ASRS ACN records.
Structure:
- Records delimited by 'acnheading' style paragraphs
- Sections within records marked by 'acnsection' style paragraphs  
- Data lines use 'acndata' style with key-value pairs separated by <w:br/>
- Key-value pairs separated by ' : '

Usage:
    python parse_word_xml.py /path/to/input.docx /path/to/output.json
"""

import sys
import json
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
import re

# WordprocessingML namespace
W_NS = 'http://purl.oclc.org/ooxml/wordprocessingml/main'
NS = {'w': W_NS, 'a': 'http://purl.oclc.org/ooxml/drawingml/main'}


def extract_document_xml(docx_path):
    """Extract word/document.xml from a .docx file."""
    with zipfile.ZipFile(docx_path, 'r') as z:
        with z.open('word/document.xml') as f:
            return f.read()
    return None


def get_paragraph_style(p):
    """Get the style value of a paragraph, or None if no style."""
    pstyle = p.find('w:pPr/w:pStyle', NS)
    if pstyle is not None:
        return pstyle.get(f'{{{W_NS}}}val')
    return None


def get_paragraph_text(p):
    """Extract all text content from a paragraph, handling line breaks."""
    # Get all text runs and line breaks from the paragraph
    parts = []
    
    for child in p:
        if child.tag == f'{{{W_NS}}}r':
            # Check if this run contains a line break
            br = child.find('w:br', NS)
            t = child.find('w:t', NS)
            
            if br is not None:
                # This run has a line break - insert marker BEFORE the text of this run
                parts.append('<BR>')
                if t is not None:
                    parts.append(t.text or '')
            else:
                # Regular text run without line break
                if t is not None:
                    parts.append(t.text or '')
        elif child.tag == f'{{{W_NS}}}br':
            # Standalone line break
            parts.append('<BR>')
    
    # Join and clean
    full_text = ''.join(parts)
    # Replace xml:space="preserve" artifacts
    full_text = full_text.replace('\u200b', '').replace('\xa0', ' ')
    # Replace our line break marker with actual newline
    full_text = full_text.replace('<BR>', '\n')
    # Clean up multiple spaces but preserve newlines
    # Split by newlines, clean each line, then rejoin
    lines = full_text.split('\n')
    cleaned_lines = [re.sub(r'\s+', ' ', line).strip() for line in lines]
    full_text = '\n'.join(cleaned_lines)
    return full_text.strip()


def split_key_value_pairs(text):
    """
    Split text into key-value pairs.
    
    Handles:
    - Multiple pairs separated by newlines (from <w:br/> elements)
    - Keys and values separated by ' : '
    - Keys containing dots (e.g., 'Aircraft.Component', 'Experience.Flight Crew.Total')
    """
    pairs = []
    
    # Split by newlines first to get individual key-value lines
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Split each line by ' : ' to get key and value
        # Only split on the first occurrence in case value contains ' : '
        if ' : ' in line:
            # Split on first occurrence of ' : '
            first_sep = line.find(' : ')
            key = line[:first_sep].strip()
            value = line[first_sep + 3:].strip()  # 3 = len(' : ')
            if key and value:
                pairs.append((key, value))
        else:
            # No separator found, treat as key with no value
            if line:
                pairs.append((line, None))
    
    return pairs


def parse_paragraph(p):
    """
    Parse a paragraph and return its type and content.
    
    Returns:
        tuple: (style, text, is_narrative)
        where is_narrative is True if this is a free-text narrative/synopsis paragraph
    """
    style = get_paragraph_style(p)
    text = get_paragraph_text(p)
    
    # Check if it's a special section
    if style == 'acnheading':
        # Extract ACN number
        match = re.search(r'ACN:\s*(\d+)', text)
        if match:
            return ('acn', match.group(1), False)
    elif style == 'acnsection':
        # This is a section header
        return ('section', text, False)
    elif style == 'acndata':
        # Check if this looks like free text (narrative/synopsis)
        # Free text paragraphs typically don't have " : " pattern
        if ' : ' not in text and len(text) > 10:
            return ('narrative', text, True)
        return ('data', text, False)
    
    return (style, text, False)


def parse_record(paragraphs):
    """
    Parse a list of paragraphs into a structured record.
    
    Args:
        paragraphs: List of (style, text, is_narrative) tuples
    
    Returns:
        dict: Structured record
    """
    if not paragraphs:
        return None
    
    # First paragraph should be the ACN
    acn = None
    if paragraphs[0][0] == 'acn':
        acn = paragraphs[0][1]
        paragraphs = paragraphs[1:]  # Skip ACN line
    
    record = {
        'ACN': acn,
    }
    
    current_section = None
    current_entity = None
    
    for style, text, is_narrative in paragraphs:
        if style == 'section':
            # New section
            section_name = text.strip()
            
            # Check if this is a numbered entity (e.g., "Person : 1", "Narrative: 2")
            # Actually, looking at the ground truth, it's "Person : 1" or "Narrative: 1"
            # Let's check the pattern
            entity_match = re.match(r'^(.+?)\s*:\s*(\d+)$', section_name)
            
            if entity_match:
                # This is a numbered entity like "Person : 1" or "Narrative: 1"
                entity_type = entity_match.group(1).strip()
                entity_num = entity_match.group(2)
                
                # Create the entity if it doesn't exist
                if entity_type not in record:
                    record[entity_type] = {}
                
                # Initialize the numbered entity
                if entity_num not in record[entity_type]:
                    record[entity_type][entity_num] = OrderedDict()
                
                current_section = entity_type
                current_entity = entity_num
                
            else:
                # Regular section
                current_section = section_name
                current_entity = None
                
                # Initialize section if it doesn't exist
                if current_section not in record:
                    record[current_section] = OrderedDict()
                    
        elif style == 'data' and text:
            # Parse key-value pairs
            pairs = split_key_value_pairs(text)
            
            if current_entity:
                # Add to numbered entity
                for key, value in pairs:
                    if key not in record[current_section][current_entity]:
                        record[current_section][current_entity][key] = []
                    record[current_section][current_entity][key].append(value)
            else:
                # Add to current section
                for key, value in pairs:
                    if key not in record[current_section]:
                        record[current_section][key] = []
                    record[current_section][key].append(value)
                    
        elif is_narrative and current_section:
            # Free text narrative
            if current_entity:
                # Add to numbered entity
                narrative_key = f"Text"
                if narrative_key not in record[current_section][current_entity]:
                    record[current_section][current_entity][narrative_key] = []
                record[current_section][current_entity][narrative_key].append(text)
            else:
                # Add to current section
                if "Narrative" not in record[current_section]:
                    record[current_section]["Narrative"] = []
                record[current_section]["Narrative"].append(text)
    
    # Clean up: convert single-item lists to single values
    def clean_lists(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, list) and len(v) == 1:
                    obj[k] = v[0]
                elif isinstance(v, (dict, list)):
                    clean_lists(v)
        elif isinstance(obj, list):
            for item in obj:
                clean_lists(item)
    
    clean_lists(record)
    
    return record


def parse_docx(docx_path):
    """
    Parse a .docx file containing ASRS ACN records.
    
    Args:
        docx_path: Path to the .docx file
    
    Returns:
        list: List of parsed record dictionaries
    """
    # Extract XML
    xml_content = extract_document_xml(docx_path)
    if xml_content is None:
        print(f"Error: Could not extract document.xml from {docx_path}")
        return []
    
    # Parse XML
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return []
    
    # Find all paragraphs in the body
    body = root.find('w:body', NS)
    if body is None:
        print("Error: No body found in document")
        return []
    
    paragraphs = body.findall('w:p', NS)
    print(f"Found {len(paragraphs)} paragraphs")
    
    # Parse all paragraphs
    parsed_paragraphs = []
    for p in paragraphs:
        parsed = parse_paragraph(p)
        parsed_paragraphs.append(parsed)
    
    # Group into records (separated by 'acn' type paragraphs)
    records = []
    current_record_paragraphs = []
    
    for p in parsed_paragraphs:
        style, text, _ = p
        if style == 'acn':
            # Start new record
            if current_record_paragraphs:
                record = parse_record(current_record_paragraphs)
                if record:
                    records.append(record)
            current_record_paragraphs = [p]
        else:
            # Skip empty paragraphs (style=None, text='')
            if style is None and not text:
                continue
            current_record_paragraphs.append(p)
    
    # Don't forget the last record
    if current_record_paragraphs:
        record = parse_record(current_record_paragraphs)
        if record:
            records.append(record)
    
    return records


def convert_to_groundtruth_format(record):
    """
    Convert parsed record to format matching the ground truth markdown.
    
    This transforms the internal structure to match the expected output format.
    """
    output = OrderedDict()
    output['ACN'] = record.get('ACN')
    
    # Copy other sections
    for section_name, section_data in record.items():
        if section_name == 'ACN':
            continue
        
        if isinstance(section_data, dict):
            output[section_name] = section_data
    
    return output


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python parse_word_xml.py <input.docx> <output.json>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    print(f"Parsing {input_path}...")
    records = parse_docx(input_path)
    
    print(f"Parsed {len(records)} records")
    
    # Convert to ground truth format
    formatted_records = [convert_to_groundtruth_format(r) for r in records]
    
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_records, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(formatted_records)} records to {output_path}")


if __name__ == '__main__':
    main()
