# ASRS Database Reconnaissance

**Purpose:** Document findings from exploring NASA ASRS Database Online to inform data acquisition strategy.

**Date:** 22/09/2026

**Explorer:** Chrome

---

## 1. Query Interface

### URL
- [ASRS Database Online](https://asrs.arc.nasa.gov/search/database.html)

Use https://dbol1-prod.arc.nasa.gov/ASRSPublicQueryWizard/QueryWizard_Filter.aspx to run a query

### Query Wizard Structure

 How To Search:
Step 1:	Click  to add search items. Note: Make sure your Pop-up Blocker is off.
Step 2:	In "Current Search Items" section, select "Click Here" in a statement and choose items from lookup window.
 Date & Report Number
Envoyer	 Report Number (ACN) was [number]
Envoyer	 Date of Incident was between [date] and [date]
 Environment
Envoyer	 Flight Conditions were [conditions]
Envoyer	 Lighting was [conditions]
Envoyer	 Weather was [element]
 Aircraft
Envoyer	 Federal Aviation Regs (FAR) Part was [regulation]
Envoyer	 Flight Plan was [type]
Envoyer	 Flight Phase was [phase]
Envoyer	 Make/Model was [aircraft type]
Envoyer	 Mission was [operation]
 Place
Envoyer	 Location was [identifier]
Envoyer	 State was [abbreviation]
 Person
Envoyer	 Reporter Organization was [type]
Envoyer	 Reporter Function was [position]
 Event Assessment
Envoyer	 Event Type was [anomaly]
Envoyer	 Detector was [equipment/human]
Envoyer	 Primary Problem was [most prominent factor]
Envoyer	 Contributing Factors were [problem areas]
Envoyer	 Human Factors (since 6/09) were [factor]
Envoyer	 Result was [consequence]
 Text: Narrative / Synopsis
Envoyer Text contains [words]

 Current Search Items:   	

 	Search is empty.

Return to the previous page.Perform this search and go to the Results page.

### Query Behavior
- Can multiple filters be combined? YES
- Are there predefined query templates? YES
- Can queries be saved/bookmarked? NO

---

## 2. Available Fields

### Coded Fields (Fixed Taxonomy)
| Field Name | Data Type | Example Values | Notes |
|------------|-----------|----------------|-------|
| ACN | String | | Unique identifier |
| Date | Date | | Format: _______ |
| Aircraft Make | String | | |
| Aircraft Model | String | | |
| Flight Phase | Categorical | | Values: _______ |
| Anomaly Type | Categorical | | Values: _______ |
| Contributing Factors | Multi-value | | Separator: _______ |
| FAR References | Multi-value | | Separator: _______ |
| Location | String | | Airport codes? |

### Text Fields
| Field Name | Description | Multi-line? | Special Chars? |
|------------|-------------|------------|----------------|
| Narrative | Reporter's text | Yes/No | |
| Synopsis | Analyst summary | Yes/No | |

---

## 3. Export Constraints

| Constraint | Value | Verified? |
|------------|-------|-----------|
| Max records per export | | ⬜ |
| Export formats | CSV/XLS/DOC | ⬜ |
| Rate limit between exports | | ⬜ |
| Session timeout | | ⬜ |
| Requires login/account? | Yes/No | ⬜ |

### Export Process
1. Run query
2. Click "Export" button
3. Select format: CSV
4. Select fields: all
5. Download file

### Paging
- Can results be paged? ⬜ Yes  ⬜ No
- If yes, max per page: _______
- How to get next page: __________

---

## 4. Data Format Quirks

### CSV Specifics
| Issue | Observation | Impact |
|-------|-------------|--------|
| Multi-line fields | | |
| Field quoting | | |
| Empty values | | |
| Special characters | | |
| Encoding | UTF-8? | |
| Line endings | CRLF/LF | |

### Multi-value Fields
- Format: `value1,value2,value3` or `[value1, value2]`?
- Example: _______________

### Date Format
- Example: _______________
- Timezone: _______________

---

## 5. Recommended Acquisition Strategy

### Scope Decision
- **Option A:** Filter by aircraft family
  - Selected: _______________
  - Estimated reports: _______
  
- **Option B:** Filter by anomaly domain
  - Selected: _______________
  - Estimated reports: _______

- **Option C:** Filter by date range
  - Selected: _______________
  - Estimated reports: _______

### Target
- **Goal:** 2,000-5,000 reports
- **Selected approach:** _______________

### Field Selection
List all fields to export:
1. 
2. 
3. 
4. 
5. 

### Paging Strategy
- Batch size: _______ records per export
- Number of batches needed: _______
- Delay between batches: _______ seconds (if any)

---

## 6. Open Questions

1. 
2. 
3. 

---

## 7. Notes & Observations

(Free-form notes from exploration)

---

**Status:** ⬜ Draft  ⬜ In Progress  ✅ Complete
