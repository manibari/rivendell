---
name: doc-to-structured-data
loop: shared
pdca: do
description: Parse unstructured technical documents (.doc, .pdf, .xlsx) into structured CSV/JSON — handles format detection, extraction strategy selection, domain-specific field recognition, and multi-table output with validation.
tags: [backend, data-extraction, document-processing]
version: 1
source: harvest-2026-03-19
user_invocable: true
---

# doc-to-structured-data

TRIGGER when: user asks to "extract data from document", "parse this spec", "convert to CSV/JSON", "把這份文件結構化", or has a technical document (.doc/.pdf/.xlsx) that needs tabular extraction.
DO NOT TRIGGER when: simple PDF text reading (use office-pdf), creating documents (use office-docx/pptx), or working with already-structured data.

## When This Skill Adds Value

- Technical specs, test plans, datasheets with semi-structured tables
- Government forms, RFP documents with fixed but complex layouts
- Legacy .doc files that need modern structured output
- Multi-section documents that produce multiple output tables

## Workflow

### Step 1: Format Detection

Determine extraction strategy by file type:

| Format | Strategy | Tool |
|--------|----------|------|
| `.pdf` | Read tool (native PDF support) | Read with `pages` parameter |
| `.docx` | Read tool or python-docx | Preserves tables, headings |
| `.doc` (legacy) | `textutil -convert html` (macOS) → parse HTML | Fallback: `antiword` or `catdoc` |
| `.xlsx` | openpyxl or Read tool | Direct table access |
| `.html` | BeautifulSoup | Table extraction |

For `.doc` files on macOS:
```bash
textutil -convert html input.doc -output /tmp/converted.html
```

### Step 2: Document Structure Analysis

Before extracting, understand the document's structure:

1. **Identify sections** — headings, page breaks, horizontal rules
2. **Identify tables** — markdown tables, HTML tables, tab-delimited blocks
3. **Identify repeated patterns** — forms, test cases, spec rows
4. **Map domain fields** — what each column/section means in context

Present structure summary to user:
```
Document structure:
- Section 1: Overview (text, skip)
- Section 2: Test Items (table, 45 rows × 6 cols)
- Section 3: Pin Definitions (table, 128 rows × 4 cols)
- Section 4: Test Flow (diagram, extract as sequence)
```

### Step 3: Field Mapping

Map document fields to output schema. Common domain patterns:

**IC Test Plans:**
- Test item name, test conditions, limits (min/typ/max), units
- Pin name, pin number, function, direction, voltage level

**Government RFPs:**
- Project name, budget, deadline, requirements, evaluation criteria

**Product Datasheets:**
- Parameter, conditions, min, typical, max, unit

Ask user to confirm or adjust the mapping before extraction.

### Step 4: Extract & Transform

1. Parse each identified table/section
2. Apply field mapping
3. Handle edge cases:
   - Merged cells → expand to all covered rows
   - Multi-line cells → join with ` | ` or newline
   - Missing values → empty string (not "N/A")
   - Units embedded in values → separate into own column
4. Type inference: numbers, dates, enums

### Step 5: Output

Produce structured files:

```
output/
├── {document_name}_table1.csv
├── {document_name}_table2.csv
├── {document_name}_all.json       # Combined JSON with metadata
└── {document_name}_summary.md     # Human-readable extraction report
```

JSON format:
```json
{
  "source": "filename.pdf",
  "extracted_at": "2026-03-19T10:00:00",
  "tables": [
    {
      "name": "Test Items",
      "rows": 45,
      "columns": ["item", "condition", "min", "typ", "max", "unit"],
      "data": [...]
    }
  ]
}
```

### Step 6: Validate

- Row count matches expected (from structure analysis)
- No empty required fields
- Numeric fields are actually numeric
- Duplicate detection (same item appearing twice)

Report validation results before finalizing.

## Comparison with Existing Skills

- **office-pdf**: reads/creates PDFs, no domain-aware extraction
- **office-xlsx**: reads/creates spreadsheets, no document-to-table parsing
- **office-docx**: reads/creates Word docs, no structured extraction pipeline
- **web-scraper**: scrapes web pages, not local documents
