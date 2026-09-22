#!/usr/bin/env python3
"""
Compare parsed CSV output with ground truth database extract.
Identifies discrepancies between the two sources.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

# ---------------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------------

# Load parsed JSON
PARSED_FILE = Path(__file__).parent.parent.parent / "data" / "parsed" / "A320_2010_2026_first10.json"
GROUNDTRUTH_FILE = Path(__file__).parent.parent.parent / "data" / "parsed" / "A320_2010_2026_first10_groundtruth.md"

with open(PARSED_FILE) as f:
    parsed_reports = json.load(f)

parsed_by_acn = {r['acn']: r for r in parsed_reports}

# Parse ground truth markdown
def parse_groundtruth_file(filepath: Path) -> Dict[str, Dict]:
    """Parse markdown ground truth file into structured dict."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Split by ACN sections
    sections = re.split(r'\n\s*ACN:\s*(\d+)\s*\n', content)
    # First element is empty, then alternating: [None, acn1, text1, acn2, text2, ...]
    
    groundtruth = {}
    for i in range(1, len(sections), 2):
        acn = sections[i]
        text = sections[i+1] if i+1 < len(sections) else ""
        groundtruth[acn] = parse_acn_section(text.strip())
    
    return groundtruth

def parse_acn_section(text: str) -> Dict:
    """Parse a single ACN section into a dict."""
    report = {}
    current_category = None
    current_subcategory = None
    
    for line in text.split('\n'):
        line = line.strip()
        if not line or line == '':
            continue
            
        # Check for category headers (uppercase words followed by colon or newline)
        # Format: "Category Name" or "Category Name:"
        category_match = re.match(r'^([A-Z][A-Z &\-/]*[A-Z]):?$', line)
        if category_match:
            current_category = category_match.group(1).replace(' / ', '_').replace(' ', '_')
            current_subcategory = None
            if current_category not in report:
                report[current_category] = {}
            continue
        
        # Check for subcategory (indented line ending with :)
        # Format: "  Subcategory : value" or "  Subcategory.Subsub: value"
        subcat_match = re.match(r'^([A-Za-z &\-/().]+):\s*(.*)', line)
        if subcat_match:
            subcat = subcat_match.group(1).strip().replace(' ', '_').replace('/', '_')
            value = subcat_match.group(2).strip()
            
            # Handle nested subcategories (e.g., "Location Of Person.Aircraft")
            parts = subcat.split('.')
            if len(parts) == 1:
                # Simple subcategory
                if current_category:
                    report[current_category][subcat] = value
                else:
                    report[subcat] = value
            else:
                # Nested subcategory
                parent = parts[0]
                child = '.'.join(parts[1:])
                if current_category:
                    if parent not in report[current_category]:
                        report[current_category][parent] = {}
                    report[current_category][parent][child] = value
                else:
                    if parent not in report:
                        report[parent] = {}
                    report[parent][child] = value
            continue
        
        # Check for simple key: value pairs
        kv_match = re.match(r'^([A-Za-z &\-/().]+):\s*(.*)', line)
        if kv_match and current_category:
            key = kv_match.group(1).strip().replace(' ', '_')
            value = kv_match.group(2).strip()
            report[current_category][key] = value
    
    return report

groundtruth = parse_groundtruth_file(GROUNDTRUTH_FILE)

# ---------------------------------------------------------------------------
# COMPARISON FUNCTIONS
# ---------------------------------------------------------------------------

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten a nested dict for comparison."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                else:
                    items.append((f"{new_key}_{i}", item))
        else:
            items.append((new_key, v))
    return dict(items)

def normalize_value(v: Any) -> str:
    """Normalize value for comparison (lowercase, strip)."""
    if v is None:
        return ''
    return str(v).lower().strip()

def compare_reports(acn: str) -> Dict:
    """Compare parsed and ground truth for a single ACN."""
    parsed = parsed_by_acn.get(acn, {})
    gt = groundtruth.get(acn, {})
    
    if not parsed and not gt:
        return {"status": "both_missing"}
    if not parsed:
        return {"status": "parsed_missing", "groundtruth_keys": list(gt.keys())}
    if not gt:
        return {"status": "groundtruth_missing", "parsed_keys": list(parsed.keys())}
    
    # Flatten both
    parsed_flat = flatten_dict(parsed)
    gt_flat = flatten_dict(gt)
    
    # Find discrepancies
    discrepancies = {
        "matches": [],
        "parsed_extra": [],
        "groundtruth_extra": [],
        "value_mismatches": []
    }
    
    all_keys = set(parsed_flat.keys()) | set(gt_flat.keys())
    
    for key in sorted(all_keys):
        p_val = parsed_flat.get(key, None)
        g_val = gt_flat.get(key, None)
        
        if p_val is None:
            discrepancies["groundtruth_extra"].append(key)
        elif g_val is None:
            discrepancies["parsed_extra"].append(key)
        elif normalize_value(p_val) != normalize_value(g_val):
            discrepancies["value_mismatches"].append({
                "key": key,
                "parsed": p_val,
                "groundtruth": g_val
            })
        else:
            discrepancies["matches"].append(key)
    
    return discrepancies

# ---------------------------------------------------------------------------
# RUN COMPARISON
# ---------------------------------------------------------------------------

print("=" * 80)
print("COMPARISON: Parsed CSV vs Ground Truth Database")
print("=" * 80)
print()

all_acns = sorted(set(list(parsed_by_acn.keys()) + list(groundtruth.keys())))

for acn in all_acns:
    print(f"\n{'='*80}")
    print(f"ACN: {acn}")
    print('='*80)
    
    comparison = compare_reports(acn)
    
    if comparison.get("status") == "both_missing":
        print("❌ Both missing")
        continue
    
    if comparison.get("status") == "parsed_missing":
        print(f"❌ Parsed MISSING (present in ground truth)")
        print(f"   Ground truth has: {', '.join(comparison['groundtruth_keys'][:10])}...")
        continue
        
    if comparison.get("status") == "groundtruth_missing":
        print(f"❌ Ground truth MISSING (present in parsed)")
        print(f"   Parsed has: {', '.join(comparison['parsed_keys'][:10])}...")
        continue
    
    # Show statistics
    print(f"✅ Both present")
    print(f"   Matches: {len(comparison['matches'])}")
    print(f"   Value mismatches: {len(comparison['value_mismatches'])}")
    print(f"   Parsed extra: {len(comparison['parsed_extra'])}")
    print(f"   Ground truth extra: {len(comparison['groundtruth_extra'])}")
    
    # Show value mismatches
    if comparison['value_mismatches']:
        print(f"\n   🔴 VALUE MISMATCHES:")
        for mismatch in comparison['value_mismatches'][:10]:  # Limit to first 10
            print(f"      {mismatch['key']}:")
            print(f"         Parsed:   {mismatch['parsed']}")
            print(f"         Ground:   {mismatch['groundtruth']}")
    
    # Show extra keys
    if comparison['parsed_extra']:
        print(f"\n   🟡 PARSED EXTRA (not in ground truth):")
        for key in comparison['parsed_extra'][:10]:
            print(f"      {key}")
    
    if comparison['groundtruth_extra']:
        print(f"\n   🟡 GROUND TRUTH EXTRA (not in parsed):")
        for key in comparison['groundtruth_extra'][:10]:
            print(f"      {key}")

print("\n" + "=" * 80)
print("COMPARISON COMPLETE")
print("=" * 80)
