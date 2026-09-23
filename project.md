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
| Full Dataset Parsing | ✅ Complete | 59 pages, 2908 records parsed |

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

---

### Full Dataset Parsing (2026-09-22, ~20:15-21:16 UTC)

**Input**: `docs/full_2908_docx/page_01.docx` through `page_59.docx`

**Output**: `data/parsed/A320_2010_2026_all_pages.json`

**Metrics**:
- ✅ 59 pages processed
- ✅ 2,908 total records parsed
- ✅ 0 issues/errors
- ✅ ~14,700 total paragraphs
- ✅ Average: 50 records/page (page 59: 8 records)
- ✅ Hierarchical structure preserved across all pages
- ✅ Numbered entities handled correctly (Person: 1, Person: 2, Narrative: 1, etc.)
- ✅ Sample ACNs verified: 2362957, 2347955, 2344841, 2320283, 2294641, 2281438, 2272411

**Structure**:
```json
{
  "total_pages": 59,
  "total_records": 2908,
  "pages": {
    "1": [record1, record2, ..., record50],
    "2": [record1, record2, ..., record50],
    ...
    "59": [record1, ..., record8]
  },
  "issues": []
}
```

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
    ├── A320_2010_2026_first50.json              # Parser output (sample)
    ├── A320_2010_2026_all_pages.json           # All 59 pages, 2908 records
    └── A320_2010_2026_all_pages_normalized.json  # Taxonomy-compliant normalized data ✨ NEW

docs/
├── asrs_csv_schema.yml              # CSV schema (legacy)
├── ASRS_Coding_Taxonomy.yml          # Coding taxonomy specification ✨ NEW
├── ASRS_CodingForm.pdf               # Reference documentation
└── full_2908_docx/                  # Source files (59 .docx pages)
    ├── page_01.docx
    ├── page_02.docx
    └── ... (pages 03-59)

src/
└── ingestion/
    ├── parse_asrs.py                  # CSV parser (legacy)
    ├── parse_word_xml.py              # Word XML parser ✨ NEW
    ├── parse_all_pages.py             # Batch parser ✨ NEW
    └── validate_parser.py             # Validation script ✨ NEW

project.md                            # Project documentation
```

---

## Work Log

### 2026-09-22 (Tuesday)

| Time | Activity | Status |
|------|----------|--------|
| ~17:00-18:00 | Reviewed XML structure in `A320_2010_2026.docx` | ✅ Complete |
| ~18:00-18:25 | User provided first 10 ground truth records in markdown format | ✅ Complete |
| ~18:25-18:32 | Created initial parser test with 10 records (`A320_2010_2026_first10.json`) | ✅ Complete |
| ~18:32-19:00 | Developed single-file Word XML parser (`parse_word_xml.py`) | ✅ Complete |
| ~19:00-19:01 | Created 50-record test file (`A320_2010_2026_first50.json`) | ✅ Complete |
| ~19:30-19:45 | Created initial `project.md` documentation | ✅ Complete |
| ~19:45-20:00 | Received 59 .docx files in `docs/full_2908_docx/` | ✅ Complete |
| ~20:00-20:15 | Developed batch parser (`parse_all_pages.py`) | ✅ Complete |
| ~20:15-21:16 | **Parsed all 59 pages (2908 records) successfully with 0 errors** | ✅ Complete |
| ~21:16-21:30 | Verified sample ACNs (2362957, 2347955, 2344841, 2320283, 2294641, 2281438, 2272411) on request | ✅ Complete |
| ~21:30-22:00 | Final validation and commitment of work | ✅ Complete |

---

## Next Steps

### Immediate
1. ✅ **Parser created and tested** on 50-record sample
2. ✅ **Process full dataset** - 59 pages, 2908 records parsed
3. ✅ **Batch parser created** - `parse_all_pages.py`

### Short Term
1. Validate output structure against ground truth
2. Identify and handle any edge cases
3. Optimize performance for large files

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

*Last updated: 2026-09-22, 22:15 UTC*
*Status: Full dataset (2908 records across 59 pages) parsed successfully with 0 errors*

---

## Taxonomy Validation and Normalization

### Date: 2026-09-23 (Wednesday)

### Overview
Validated parsed data against `ASRS_Coding_Taxonomy.yml` and created a normalized version of the dataset that is fully consistent with the taxonomy specification.

### Activities

#### 1. Sampling and Initial Check
- Sampled 50 random ACNs from `A320_2010_2026_all_pages.json`
- Identified formatting inconsistencies between parsed data and taxonomy
- Found 30 inconsistencies across 20 ACNs (40% of sampled records)

#### 2. Inconsistencies Identified

**Category 1: Spacing Variations**
- `" / "` vs `"/"` (e.g., `Takeoff / Launch` vs `Takeoff/Launch`)
- `" - "` vs `"-"` (e.g., `Environment - Non Weather Related` vs `Environment-Non Weather Related`)
- `"Chart Or Publication"` vs `"Chart or Publication"`

**Category 2: Value Mismatches**
- `"Procedure"` in data vs `"Procedure (inc. Airspace Authorization)"` in Contributing Factors taxonomy
- `"ATC Equipment/Nav Facility/Buildings"` in data vs `"ATC Equip/Nav Facility/Buildings"` in Contributing Factors taxonomy
- `"Environment-Non Weather Related"` vs `"Environment-Non-Weather Related"` (Primary Problem uses double hyphen)

**Category 3: Multi-valued Fields**
- Flight Phase correctly identified as `cardinality: multi` in taxonomy
- Arrays like `['Descent', 'Climb', 'Landing']` are valid per taxonomy

#### 3. Field-Specific Normalization Rules Applied

**Global Rules (All Fields)**:
```
" / "  → "/"
" - "  → "-"
"Chart Or Publication" → "Chart or Publication"
```

**Assessments.Contributing Factors / Situations**:
```
"Procedure" → "Procedure (inc. Airspace Authorization)"
"Environment-Non Weather Related" → "Environment-Non Weather Related"
"ATC Equipment/Nav Facility/Buildings" → "ATC Equip/Nav Facility/Buildings"
```

**Assessments.Primary Problem**:
```
"Environment-Non Weather Related" → "Environment-Non-Weather Related"
```

**Person.Human Factors**:
```
"Training / Qualification" → "Training/Qualification"
"Physiological - Other" → "Physiological-Other"
"Other / Unknown" → "Other/Unknown"
```

#### 4. Validation Results

**Before Normalization** (Sampled 50 records):
- 30 inconsistencies found
- 20 ACNs affected (40%)

**After Normalization** (All 2,908 records):
- ✅ **0 inconsistencies**
- ✅ All records fully consistent with taxonomy
- ✅ Assessments.Contributing Factors: All values match
- ✅ Assessments.Primary Problem: All values match
- ✅ Person.Human Factors: All values match

### Output Files

| File | Description | Status |
|------|-------------|--------|
| `data/parsed/A320_2010_2026_all_pages.json` | Original parsed data (hierarchical) | ✅ Existing |
| `data/parsed/A320_2010_2026_all_pages_normalized.json` | Taxonomy-compliant normalized data | ✅ **NEW** |
| `docs/ASRS_Coding_Taxonomy.yml` | Reference taxonomy specification | ✅ Existing |

### Usage

The normalized file can be used directly for:
1. **Graph Structure Brainstorming**: Taxonomy sections map cleanly to node types
2. **Neo4j Loading**: Data is validated and consistent with schema
3. **Downstream Processing**: No further normalization needed

### Taxonomy to Graph Mapping

```
Taxonomy Sections → Graph Node Types:
- time → Time
- place → Place
- environment → Environment
- aircraft → Aircraft
- component → Component
- person → Person
- events → Event
- assessments → Assessment

Relationships:
- Report HAS_TIME Time
- Report HAS_PLACE Place
- Report HAS_ENVIRONMENT Environment
- Report INVOLVES_AIRCRAFT Aircraft
- Report HAS_COMPONENT Component
- Report HAS_PERSON Person
- Report HAS_EVENT Event
- Report HAS_ASSESSMENT Assessment
- Event HAS_ANOMALY Anomaly
- Event HAS_RESULT Result
- Assessment HAS_FACTOR Factor
```

### Key Insights

1. **Taxonomy is Production-Ready**: The `ASRS_Coding_Taxonomy.yml` specification accurately reflects the parsed data structure
2. **Cardinality Matters**: Multi-valued fields in taxonomy (`cardinality: multi`) correctly allow arrays in data
3. **Field-Specific Values**: Some fields have different valid value sets (e.g., Contributing Factors vs Primary Problem)
4. **Minor Formatting**: Spacing around `/` and `-` was the main source of inconsistencies
5. **Normalization is Idempotent**: Re-running normalization produces identical results

---

## Work Log Update

### 2026-09-23 (Wednesday)

| Time | Activity | Status |
|------|----------|--------|
| ~17:18-18:00 | Sampled 50 ACNs and identified taxonomy inconsistencies | ✅ Complete |
| ~18:00-18:30 | Analyzed inconsistency patterns (spacing, value mappings) | ✅ Complete |
| ~18:30-19:00 | Developed field-specific normalization approach | ✅ Complete |
| ~19:00-19:30 | Applied normalization to all 2908 records | ✅ Complete |
| ~19:30-19:45 | Validated normalized data against taxonomy (0 issues) | ✅ Complete |
| ~19:45-20:00 | Documented work in project.md | ✅ Complete |

---

## Next Steps (Updated)

### Immediate
1. ✅ Parser created and tested on 50-record sample
2. ✅ Process full dataset - 59 pages, 2908 records parsed
3. ✅ Batch parser created - `parse_all_pages.py`
4. ✅ **Taxonomy validation completed** - 0 inconsistencies
5. ✅ **Normalized data created** - `A320_2010_2026_all_pages_normalized.json`

### Short Term (Phase 1 Completion)
1. Convert hierarchical JSON to JSONL format (extraction source of truth)
2. Create extraction schema document
3. Create corpus manifest
4. Perform manual spot-check (30 records)
5. Freeze corpus to git

### Long Term (Phase 2+)
1. Transform normalized JSON to knowledge graph format
2. Create Neo4j loader with idempotent MERGEs
3. Add narrative embeddings + vector index
4. Implement graph sanity checks

---

*Last updated: 2026-09-23, 20:00 UTC*
*Status: Full dataset parsed, validated, and normalized against taxonomy*
