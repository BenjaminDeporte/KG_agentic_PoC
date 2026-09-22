#!/usr/bin/env python3
"""
Validation script to compare parser output structure with ground truth.
"""

import json
import sys


def load_groundtruth(md_path):
    """Load ground truth from markdown file."""
    records = []
    current_record = None
    current_section = None
    current_entity = None
    
    with open(md_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Check for ACN header
            if line.startswith('ACN:'):
                if current_record:
                    records.append(current_record)
                current_record = {'ACN': line.split(':')[1].strip()}
                current_section = None
                current_entity = None
                continue
            
            # Check for section header (ends with colon or contains colon with number like "Person : 1")
            import re
            entity_match = re.match(r'^(.+?)\s*:\s*(\d+)$', line)
            
            if entity_match or line in ['Time / Day', 'Place', 'Aircraft', 'Component', 'Events', 'Assessments', 'Environment', 'Synopsis']:
                if entity_match:
                    # Numbered entity like "Person : 1" or "Narrative: 1"
                    entity_type = entity_match.group(1).strip()
                    entity_num = entity_match.group(2)
                    current_section = entity_type
                    current_entity = entity_num
                    if entity_type not in current_record:
                        current_record[entity_type] = {}
                    if entity_num not in current_record[entity_type]:
                        current_record[entity_type][entity_num] = {}
                else:
                    # Regular section
                    section_name = line.strip()
                    current_section = section_name
                    current_entity = None
                    if section_name not in current_record:
                        current_record[section_name] = {}
                continue
            
            # Parse key-value pair
            if ' : ' in line:
                key, value = line.split(' : ', 1)
                if current_entity:
                    current_record[current_section][current_entity][key] = value
                else:
                    current_record[current_section][key] = value
            elif line and current_section:
                # Free text (narrative)
                if current_entity:
                    if 'Text' not in current_record[current_section][current_entity]:
                        current_record[current_section][current_entity]['Text'] = []
                    current_record[current_section][current_entity]['Text'].append(line)
                else:
                    if 'Narrative' not in current_record[current_section]:
                        current_record[current_section]['Narrative'] = []
                    current_record[current_section]['Narrative'].append(line)
    
    if current_record:
        records.append(current_record)
    
    return records


def compare_structures(json_records, md_records):
    """Compare structures between JSON and markdown records."""
    print(f"JSON records: {len(json_records)}")
    print(f"Markdown records: {len(md_records)}")
    
    # Compare first record
    if json_records and md_records:
        j_keys = set(json_records[0].keys())
        m_keys = set(md_records[0].keys())
        
        print(f"\nFirst record comparison:")
        print(f"  JSON keys: {sorted(j_keys)}")
        print(f"  Markdown keys: {sorted(m_keys)}")
        
        # Check common sections
        common_sections = j_keys & m_keys
        print(f"  Common sections: {sorted(common_sections)}")
        
        # Check Time / Day
        if 'Time / Day' in common_sections:
            j_time = json_records[0]['Time / Day']
            m_time = md_records[0]['Time / Day']
            print(f"\n  Time / Day comparison:")
            print(f"    JSON: {j_time}")
            print(f"    Markdown: {m_time}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python validate_parser.py <json_file> <markdown_file>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    md_path = sys.argv[2]
    
    # Load JSON
    with open(json_path) as f:
        json_records = json.load(f)
    
    # Load markdown
    md_records = load_groundtruth(md_path)
    
    # Compare
    compare_structures(json_records, md_records)


if __name__ == '__main__':
    main()
