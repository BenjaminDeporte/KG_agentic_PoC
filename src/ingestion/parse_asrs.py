#!/usr/bin/env python3
"""
ASRS CSV Parser - Limited to first 10 records for verification
- Reads multi-level header CSV exports from NASA ASRS
- Uses asrs_csv_schema.yml for field mapping
- Outputs structured JSON for easy comparison with database records
- LIMITED: Only parses first 10 records for verification purposes
"""

import yaml
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent.parent
CSV_PATH = BASE_DIR / "data" / "raw" / "A320_2010_2026.csv"
SCHEMA_PATH = BASE_DIR / "docs" / "asrs_csv_schema.yml"
OUTPUT_PATH = BASE_DIR / "data" / "parsed"

# LIMIT TO FIRST 10 RECORDS FOR VERIFICATION
MAX_RECORDS = 10

# ---------------------------------------------------------------------------
# STRUCTURED OUTPUT DESIGN
# ---------------------------------------------------------------------------
# Each report will be a dict with:
# {
#   "acn": "866977",
#   "_source": {"file": "...", "row": N},
#   "time": {"date": "201001", "local_time_of_day": "1201-1800"},
#   "place": {"state_reference": "US", "altitude": {"msl_single_value": "34000"}},
#   "environment": {"flight_conditions": "VMC", "light": "Daylight"},
#   "aircraft": {"make_model": "A320", "flight_phase": "Descent", ...},
#   "component": {...},
#   "person": [...],  # List of person dicts
#   "events": {"anomaly": {"aircraft_equipment": "Critical", ...}, ...},
#   "assessments": {"contributing_factors": [...], "primary_problem": "..."},
#   "report": {"narrative": "...", "synopsis": "..."}
# }


class ASRSCSVParser:
    def __init__(self, csv_path: Path, schema_path: Path):
        self.csv_path = csv_path
        self.schema_path = schema_path
        self.schema = self._load_schema()
        self.df = None
        self.column_map = {}

    def _load_schema(self) -> Dict:
        """Load YAML schema into a nested dict."""
        with open(self.schema_path, 'r') as f:
            return yaml.safe_load(f)

    def _build_column_map(self) -> Dict[str, tuple]:
        """
        Map schema paths to CSV MultiIndex column names.
        Returns: {schema_path: (level1, level2)}
        """
        column_map = {}

        # Helper to convert schema field name to CSV column name
        # CSV uses Title Case for categories: "Time", "Place", "Environment", etc.
        # Schema uses lowercase: "time", "place", "environment"
        def get_csv_category(schema_cat: str) -> str:
            # Special case: root -> empty string
            if schema_cat == 'root':
                return ' '
            # Map schema category names to CSV category names
            category_map = {
                'time': 'Time',
                'place': 'Place',
                'environment': 'Environment',
                'aircraft_1': 'Aircraft 1',
                'aircraft_2': 'Aircraft 2',
                'component': 'Component',
                'person_1': 'Person 1',
                'person_2': 'Person 2',
                'events': 'Events',
                'assessments': 'Assessments',
                'report_1': 'Report 1',
                'report_2': 'Report 2',
            }
            return category_map.get(schema_cat, schema_cat.title())

        # Handle root level (ACN)
        if 'root' in self.schema:
            for field, meta in self.schema['root'].items():
                key = f"root.{field}"
                col_name = meta['source'].split(': ')[1]
                column_map[key] = (' ', col_name)

        # Handle each category
        for category, fields in self.schema.items():
            if category in ['root', 'metadata']:
                continue
            csv_category = get_csv_category(category)
            for field, meta in fields.items():
                if isinstance(meta, dict) and 'source' in meta:
                    # Simple field
                    key = f"{category}.{field}"
                    col_name = meta['source'].split(': ')[1]
                    column_map[key] = (csv_category, col_name)
                elif isinstance(meta, dict):
                    # Nested field (like maintenance_status)
                    for subfield, submeta in meta.items():
                        if isinstance(submeta, dict) and 'source' in submeta:
                            key = f"{category}.{field}.{subfield}"
                            col_name = submeta['source'].split(': ')[1]
                            column_map[key] = (csv_category, col_name)

        return column_map

    def _get_value(self, col_key: tuple, row: pd.Series) -> Any:
        """Extract value from row for a MultiIndex column."""
        try:
            idx = pd.MultiIndex.from_tuples([col_key])
            val = row[idx[0]]
            return None if pd.isna(val) or val == '' else str(val).strip()
        except (KeyError, IndexError):
            return None

    def parse(self, max_records: int = MAX_RECORDS) -> List[Dict[str, Any]]:
        """Parse CSV and return list of structured reports (limited)."""
        # Read CSV with multi-level headers
        self.df = pd.read_csv(
            self.csv_path,
            header=[0, 1],
            skiprows=[2],  # Skip the empty row
            dtype=str,
            keep_default_na=False,
            na_values=['', 'NaN', 'None']
        )

        self.column_map = self._build_column_map()
        reports = []

        # LIMIT: Only parse first max_records rows
        for idx, row in self.df.head(max_records).iterrows():
            report = self._parse_row(row, idx)
            if report:  # Only add if ACN exists
                reports.append(report)
            if len(reports) >= max_records:
                break

        return reports

    def _parse_row(self, row: pd.Series, row_idx: int) -> Dict[str, Any]:
        """Parse a single row into structured dict."""
        report = {
            "_source": {
                "file": self.csv_path.name,
                "row": row_idx + 3  # +3 because of header rows
            }
        }

        # Parse root level (ACN)
        acn_key = "root.acn"
        if acn_key in self.column_map:
            col = self.column_map[acn_key]
            acn_val = self._get_value(col, row)
            if acn_val:
                report["acn"] = acn_val
            else:
                return None  # Skip rows without ACN

        # Parse each category
        for category in self.schema:
            if category in ['root', 'metadata']:
                continue

            category_data = self._parse_category(category, row)
            if not category_data:
                continue

            # Handle special cases: aircraft_1/2, person_1/2
            if category in ['aircraft_1', 'aircraft_2']:
                key = 'aircraft' if not report.get('aircraft') else 'aircraft_2'
                report[key] = category_data
            elif category in ['person_1', 'person_2']:
                if 'person' not in report:
                    report['person'] = []
                report['person'].append(category_data)
            elif category in ['report_1', 'report_2']:
                if 'report' not in report:
                    report['report'] = {}
                report['report'].update(category_data)
            else:
                report[category] = category_data

        return report

    def _parse_category(self, category: str, row: pd.Series) -> Dict:
        """Parse all fields for a category."""
        category_data = {}
        fields = self.schema.get(category, {})

        for field, meta in fields.items():
            if isinstance(meta, dict) and 'source' in meta:
                # Simple field
                key = f"{category}.{field}"
                if key in self.column_map:
                    col = self.column_map[key]
                    val = self._get_value(col, row)
                    if val is not None:
                        category_data[field] = val
            elif isinstance(meta, dict):
                # Nested field (like maintenance_status)
                nested_data = {}
                for subfield, submeta in meta.items():
                    if isinstance(submeta, dict) and 'source' in submeta:
                        key = f"{category}.{field}.{subfield}"
                        if key in self.column_map:
                            col = self.column_map[key]
                            val = self._get_value(col, row)
                            if val is not None:
                                nested_data[subfield] = val
                if nested_data:
                    category_data[field] = nested_data

        return category_data if category_data else None


def main():
    """Parse CSV (first 10 records) and save structured output."""
    parser = ASRSCSVParser(CSV_PATH, SCHEMA_PATH)
    reports = parser.parse(max_records=MAX_RECORDS)

    print(f"✅ Parsed {len(reports)} reports from {CSV_PATH.name}")

    # Save as JSON
    output_file = OUTPUT_PATH / f"{CSV_PATH.stem}_first10.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(reports, f, indent=2, default=str, ensure_ascii=False)

    print(f"✅ Saved to: {output_file}")
    print(f"   File: {output_file.absolute()}")

    # Print each report for inspection
    for i, report in enumerate(reports, 1):
        print(f"\n{'='*60}")
        print(f"REPORT {i}: ACN = {report.get('acn', 'MISSING')}")
        print('='*60)
        print(json.dumps(report, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
