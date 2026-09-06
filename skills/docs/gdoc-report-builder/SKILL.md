---
name: gdoc-report-builder
loop: shared
pdca: do
description: >
  Build structured Google Docs / Slides via MCP — batch table editing, paragraph styling,
  find-and-replace, media insertion, share/export.
  TRIGGER: "寫進 Google Doc", "更新簡報", "把資料填進 Slides", "Google Docs 報告".
  SKIP: local .docx/.pptx (office-docx / office-pptx); single-edit Google Docs.
tags: [docs]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep, WebSearch"
---

# Google Docs/Slides Report Builder

Programmatically build structured documents in Google Docs or Slides using MCP tools.

## When to Use

- Batch-filling tables from CSV/JSON/YAML data into Google Docs or Slides
- Applying consistent paragraph styles across a document
- Variable substitution (find-and-replace) for template-based reports
- Converting structured data into formatted Google Docs reports

## Core Workflow

### Step 1: Prepare Data

Read the source data (CSV, JSON, YAML, or in-memory). Identify:
- Table structures (rows × columns)
- Template variables to replace (e.g., `{{company_name}}`, `{{date}}`)
- Paragraph style requirements (headings, body text, captions)

### Step 2: Create or Open Document

```
# Create new Google Doc
mcp__google-drive__createGoogleDoc(title, folderId?)

# Or create new Google Slides
mcp__google-drive__createGoogleSlides(title, folderId?)

# Or open existing
mcp__google-drive__getGoogleDocContent(fileId)
mcp__google-drive__getGoogleSlidesContent(fileId)
```

### Step 3: Populate Tables

For each table, use `editTableCell` to fill data cell by cell:

```
# Pattern: iterate rows × columns
for row_idx, row_data in enumerate(data):
    for col_idx, value in enumerate(row_data):
        mcp__google-drive__editTableCell(
            fileId, tableIndex, rowIndex=row_idx+1, columnIndex=col_idx,
            text=str(value)
        )
```

**Performance tip**: Group related edits. Google Docs API has rate limits — batch
edits within the same table before moving to the next.

### Step 4: Apply Styles

Use `applyParagraphStyle` for consistent formatting:

```
# Heading style
mcp__google-drive__applyParagraphStyle(
    fileId, startIndex, endIndex,
    namedStyleType="HEADING_1"
)

# Body text with specific font
mcp__google-drive__applyTextStyle(
    fileId, startIndex, endIndex,
    bold=False, fontSize=11, fontFamily="Noto Sans TC"
)
```

### Step 5: Variable Substitution

Use `findAndReplaceInDoc` for template variables:

```
mcp__google-drive__findAndReplaceInDoc(
    fileId, findText="{{company_name}}", replaceText="實際公司名稱"
)
```

### Step 6: Share or Export

```
# Share with collaborators
mcp__google-drive__shareFile(fileId, email, role="writer")

# Or export as PDF
mcp__google-drive__downloadFile(fileId, mimeType="application/pdf")
```

## Common Patterns

### Weekly Report Template
1. Duplicate a template doc (`copyFile`)
2. Replace date variables
3. Fill summary table with weekly data
4. Apply conditional formatting (red for misses, green for hits)
5. Share with team

### Data-Driven Slides
1. Create slides from template
2. For each data row: duplicate a slide, replace placeholders, insert charts
3. Reorder slides to match desired narrative
4. Add speaker notes from data annotations

## Error Handling

- **Rate limits**: Add 100ms delays between batch edits if hitting API limits
- **Table index**: Tables are 0-indexed; verify table exists with `getGoogleDocContent` first
- **Character encoding**: Google Docs handles UTF-8 natively; CJK text works without special handling
