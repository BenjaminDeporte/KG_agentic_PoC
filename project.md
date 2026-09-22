# ASRS ACN Data Ingestion Project

## Overview

**Goal**: Parse 2908 ASRS (Aviation Safety Reporting System) ACN records from Microsoft Word XML exports into structured data for knowledge graph construction.

**Constraint**: XML-only format from Word (Office Open XML / .docx)

---

## Project Status

| Phase | Status | Output |
|-------|--------|--------|
| Data Exploration | ✅ Complete | Schema, ground truth analysis |
| CSV Analysis | ✅ Complete | `docs/asrs_csv_schema.yml` |
| XML Structure Analysis | ✅ Complete | WordprocessingML parsing logic |
| Parser Development | ✅ Complete | `src/ingestion/parse_word_xml.py` |
| Initial Testing | ✅ Complete | 50 records parsed successfully |
| Full Dataset Parsing | ⏳ Pending | Awaiting full XML dump |

---

## Data Sources

### 1. Raw Data
- **Format**: Microsoft Word .docx (Office Open XML)
- **Location**: `data/raw/`
- **Sample**: `A320_2010_2026.docx` (50 records, 1066 paragraphs)
- **Full Dataset**: ~2908 records across 59 pages (pending)

### 2. Ground Truth
- **Format**: Markdown with hierarchical structure
- **Location**: `data/parsed/A320_2010_2026_first10_groundtruth.md`
- **Purpose**: Reference for expected data structure
- **Records**: 10 sample ACNs with complete hierarchy

### 3. Schema Definition
- **Format**: YAML
- **Location**: `docs/asrs_csv_schema.yml`
- **Content**: Field categories, cardinality, value domains

---

## Data Structure Analysis

### Hierarchical Organization

```
ACN (Record Identifier)
├── Time / Day
│   ├── Date : <value>
│   └── Local Time Of Day : <value>
│
├── Place
│   ├── Locale Reference.Airport : <value>
│   ├── State Reference : <value>
│   └── Altitude.MSL.Single Value : <value>
│
├── Environment (optional)
│   ├── Flight Conditions : <value>
│   ├── Light : <value>
│   └── Ceiling : <value>
│
├── Aircraft
│   ├── Reference : <value>
│   ├── ATC / Advisory.* : <value>
│   ├── Aircraft Operator : <value>
│   ├── Make Model Name : <value>
│   ├── Crew Size.Number Of Crew : <value>
│   └── ... (20+ fields)
│
├── Component (repeatable)
│   ├── Aircraft Component : <value>
│   ├── Aircraft Reference : <value>
│   └── Problem : <value>
│
├── Person (repeatable: Person : 1, Person : 2, ...)
│   ├── Reference : <value>
│   ├── Location Of Person.* : <value>
│   ├── Function.* : <value>
│   ├── Experience.* : <value>
│   └── ASRS Report Number.Accession Number : <value>
│
├── Events
│   ├── Anomaly.* : <value>
│   ├── Detector.* : <value>
│   ├── Were Passengers Involved In Event : <value>
│   └── Result.* : <value>
│
├── Assessments
│   ├── Contributing Factors / Situations : <value>
│   └── Primary Problem : <value>
│
├── Narrative (repeatable: Narrative: 1, Narrative: 2, ...)
│   └── [Free text]
│
└── Synopsis
    └── [Free text]
```

### Key Characteristics

1. **Multi-valued fields**: Same key can appear multiple times (e.g., `Human Factors : Workload`, `Human Factors : Time Pressure`)
2. **Repeatable sections**: `Person`, `Component`, `Narrative` can appear multiple times with numeric suffixes
3. **Nested hierarchy**: Dot notation in keys (e.g., `Experience.Flight Crew.Total`)
4. **Line break separated**: Multiple key-value pairs in a single paragraph separated by `<w:br/>`

---

## Word XML Structure

### Office Open XML Format

The .docx file is a ZIP archive containing:
```
word/
├── document.xml          # Main content
├── styles.xml           # Style definitions
├── settings.xml         # Document settings
└── ...
```

### Paragraph Styles

| Style | Purpose | Example |
|-------|---------|---------|
| `acnheading` | ACN identifier | "ACN: 2365022 (1 of 2908)" |
| `acnsection` | Section header | "Time / Day", "Person : 1", "Narrative: 1" |
| `acndata` | Key-value data | "Date : 201001\nLocal Time Of Day : 0601-1200" |

### XML Pattern

```xml
<w:p>
  <w:pPr><w:pStyle w:val="acnheading"/></w:pPr>
  <w:r><w:t>ACN: 2365022</w:t></w:r>
</w:p>
<w:p>
  <w:pPr><w:pStyle w:val="acnsection"/></w:pPr>
  <w:r><w:t>Time / Day</w:t></w:r>
</w:p>
<w:p>
  <w:pPr><w:pStyle w:val="acndata"/></w:pPr>
  <w:r><w:t>Date : 201001</w:t></w:r>
  <w:r><w:br/><w:t>Local Time Of Day : 0601-1200</w:t></w:r>
</w:p>
```

---

## Parser Implementation

### File: `src/ingestion/parse_word_xml.py`

#### Key Functions

| Function | Purpose |
|----------|---------|
| `extract_document_xml()` | Extract word/document.xml from .docx |
| `get_paragraph_style()` | Get style attribute from paragraph |
| `get_paragraph_text()` | Extract text with `<w:br/>` handling |
| `split_key_value_pairs()` | Split "Key : Value" pairs by newline |
| `parse_paragraph()` | Classify paragraph (ACN, section, data, narrative) |
| `parse_record()` | Build hierarchical record from paragraphs |
| `parse_docx()` | Main entry point - parse entire file |

#### Algorithm

1. **Extract**: Unzip .docx and read word/document.xml
2. **Parse XML**: Use ElementTree with namespace handling
3. **Classify**: Identify paragraph styles (acnheading, acnsection, acndata)
4. **Group**: Split into records at acnheading boundaries
5. **Structure**: Within each record:
   - Create sections from acnsection paragraphs
   - Parse key-value pairs from acndata paragraphs
   - Handle numbered entities (Person: 1, Narrative: 2, etc.)
   - Capture free text for narratives and synopsis
6. **Output**: JSON with hierarchical structure

### Handling Edge Cases

- **Empty paragraphs**: Skipped during grouping
- **Line breaks in data**: `<w:br/>` converted to newlines, then split
- **Multi-valued keys**: Stored as lists, converted to single values when appropriate
- **Numbered entities**: Detected via regex pattern `(.+?): (\d+)`
- **Special characters**: xml:space="preserve" artifacts cleaned

---

## Results

### Test on Sample Data

**Input**: `data/raw/A320_2010_2026.docx` (50 records)

**Output**: `data/parsed/A320_2010_2026_first50.json`

**Metrics**:
- ✅ 50 records parsed
- ✅ 1,066 paragraphs processed
- ✅ Hierarchical structure preserved
- ✅ Key-value pairs correctly split
- ✅ Numbered entities properly grouped

**Sample Output** (first record):
```json
{
  "ACN": "2365022",
  "Time / Day": {
    "Date": "202605",
    "Local Time Of Day": "1801-2400"
  },
  "Place": {
    "Locale Reference.Airport": "ZZZ.Airport",
    "State Reference": "US",
    "Altitude.MSL.Single Value": "4000"
  },
  "Aircraft": {
    "Reference": "X",
    "ATC / Advisory.TRACON": "ZZZ",
    "Make Model Name": "A320",
    "Operating Under FAR Part": "Part 121"
  },
  "Person": {
    "Location Of Person.Facility": "ZZZ.TRACON",
    "Reporter Organization": "Government",
    "Function.Air Traffic Control": ["Instructor", "Enroute"],
    "Qualification.Air Traffic Control": "Fully Certified"
  },
  "Narrative": {
    "1": {"Text": "During the time of this event..."}
  },
  "Synopsis": {
    "Narrative": "TRACON Controller reported..."
  }
}
```

---

## Validation

### File: `src/ingestion/validate_parser.py`

Compares parser output structure with ground truth markdown:
- Counts records
- Compares section keys
- Validates hierarchical structure

**Usage**:
```bash
python3 src/ingestion/validate_parser.py output.json groundtruth.md
```

---

## File Inventory

```
data/
├── raw/
│   └── A320_2010_2026.docx          # Sample Word XML (50 records)
│
└── parsed/
    ├── A320_2010_2026_first10_groundtruth.md  # Reference structure
    └── A320_2010_2026_first50.json              # Parser output

docs/
└── asrs_csv_schema.yml              # CSV schema (legacy)

src/
└── ingestion/
    ├── parse_asrs.py                  # CSV parser (legacy)
    ├── parse_word_xml.py              # Word XML parser ✨ NEW
    └── validate_parser.py             # Validation script ✨ NEW
```

---

## Next Steps

### Immediate
1. ✅ **Parser created and tested** on 50-record sample
2. ⏳ **Process full dataset** - Awaiting complete XML dump (59 pages, 2908 records)

### Short Term
1. Run parser on full 2908-record dataset
2. Validate output structure against ground truth
3. Identify and handle any edge cases
4. Optimize performance for large files

### Long Term
1. Transform parsed JSON to knowledge graph format
2. Create XML output option (if required)
3. Add validation rules for data quality
4. Integrate with existing data pipeline

---

## Technical Notes

### WordprocessingML Namespaces
```python
W_NS = 'http://purl.oclc.org/ooxml/wordprocessingml/main'
NS = {'w': W_NS, 'a': 'http://purl.oclc.org/ooxml/drawingml/main'}
```

### Line Break Handling
Word represents line breaks within paragraphs as `<w:br/>` elements. These must be:
1. Detected as separate elements within `<w:r>`
2. Inserted as newlines between text runs
3. Used to split multi-line key-value pairs

### Numbered Entity Pattern
Regex: `^(.+?)\s*:\s*(\d+)$`
- Matches: "Person : 1", "Narrative: 1", "Component : 2"
- Captures: entity type and number
- Creates: `record[entity_type][number] = {...}`

---

## Constraints & Decisions

| Decision | Rationale |
|----------|-----------|
| XML-only focus | User specified XML as sole output format from Word |
| ElementTree parser | Standard library, no external dependencies |
| Hierarchical JSON output | Matches ground truth structure, easily transformable |
| Flat paragraph processing | Word XML doesn't use nested elements for hierarchy |
| Skip empty paragraphs | Cleaner record boundaries |

---

## References

- **ASRS**: Aviation Safety Reporting System (NASA)
- **ACN**: ASRS Case Number
- **Office Open XML**: ISO/IEC 29500 standard
- **WordprocessingML**: XML schema for Word documents

---

*Last updated: 2026-09-22*
*Status: Parser ready for full dataset processing*
