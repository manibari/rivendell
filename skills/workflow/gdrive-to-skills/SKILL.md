---
name: gdrive-to-skills
description: >
  Read Google Drive documents via MCP, categorize them, and create structured knowledge skills.
  Use when: user wants to import Google Drive files into the skills library, or says /gdrive-to-skills.
tags: [workflow]
version: 1
imported_at: 2026-06-13
user_invocable: true
---

# Google Drive to Skills

Read documents from Google Drive, classify their content, and generate knowledge skills automatically.

## Prerequisites

- Google Drive MCP must be configured and accessible
- Skills library repo with `./bin/sk` available

## Workflow

### Step 1: Verify Google Drive MCP Access & Warm Up Permissions

Before starting, confirm Google Drive MCP tools are available:

1. Use ToolSearch to find Google Drive MCP tools (search for "google", "drive", "gdrive")
2. If no tools found, STOP and tell the user:
   - "Google Drive MCP is not configured in this session."
   - Suggest: add it via `claude mcp add` or project `.mcp.json`
3. If tools found, list available operations (search, read, list files, etc.)

**IMPORTANT — Permission warm-up:** MCP tool permissions must be approved in the **main conversation** before delegating to background Agents. In Step 1, call at least one of each MCP tool type you plan to use (e.g. `listFolder`, `downloadFile`, `readGoogleDoc`) so the user can approve them. Background agents inherit approved permissions but CANNOT trigger new approval prompts.

### Step 2: Discover Documents

Ask the user which documents to import. Support these modes:

- **By folder**: List files in a specific Google Drive folder
- **By search**: Search for documents by keyword
- **By URL/ID**: User provides specific document links or IDs
- **All in folder**: Process every document in a given folder

For each discovered document, collect:
- File name
- File type (Google Docs, Sheets, PDF, etc.)
- Last modified date

Present the list to the user for confirmation before proceeding.

### Step 3: Read and Analyze Each Document

**IMPORTANT — File type detection before reading:**
Google Drive `listFolder` does NOT reliably distinguish Google Docs from Google Sheets from the icon alone. Before reading/downloading, detect the actual MIME type using one of:
- `getDocumentInfo` (works for Docs)
- `getSpreadsheetInfo` (works for Sheets)
- Or attempt `downloadFile` — the error message reveals the actual MIME type

**MIME type → download strategy:**

| MIME Type | Tool / Export Format |
|-----------|---------------------|
| `application/vnd.google-apps.document` | `downloadFile` with `text/plain` or `readGoogleDoc` with `format=markdown` |
| `application/vnd.google-apps.spreadsheet` | `downloadFile` with `text/csv` or `getGoogleSheetContent` |
| `application/vnd.google-apps.presentation` | `downloadFile` with `text/plain` or `getGoogleSlidesContent` |
| `.docx` (uploaded file) | `downloadFile` (no exportMimeType needed), then `textutil -convert txt` on macOS |
| `.pdf` (uploaded file) | `downloadFile`, then read with Read tool |
| `.pptx` (uploaded file) | `downloadFile`, then `textutil -convert txt` on macOS |

**IMPORTANT — Avoid parallel MCP call cascading failures:**
When one MCP tool call fails in a parallel batch, ALL sibling calls get cancelled. To prevent this:
- Download/read files **one at a time** or in **small batches of 2-3** where you are confident of the file type
- Never mix different file types (Doc vs Sheet) in the same parallel batch
- If using Agents for parallel reads, ensure permissions are already approved (see Step 1)

For each confirmed document:

1. Detect file type, then read the full content via the appropriate method
2. Analyze the content to determine:
   - **Topic**: What is this document about?
   - **Type**: SOP, reference, guide, checklist, architecture doc, meeting notes, etc.
   - **Category**: Map to existing skills categories or suggest new ones:

| Document Type | Suggested Category | Skill Name Pattern |
|--------------|-------------------|-------------------|
| Development SOP / process | `workflow/` | `sop-{topic}` |
| Coding standards / style guide | `quality/` | `standards-{topic}` |
| Architecture / design doc | `docs/` | `arch-{topic}` |
| Deploy / DevOps procedure | `workflow/` | `deploy-{topic}` |
| API reference / integration | `docs/` | `ref-{topic}` |
| Business rules / domain knowledge | `knowledge/` | `domain-{topic}` |
| Checklist / review process | `quality/` | `checklist-{topic}` |
| Onboarding / how-to guide | `docs/` | `guide-{topic}` |
| Meeting notes / decisions | `knowledge/` | `decisions-{topic}` |
| Other | `knowledge/` | `{topic}` |

3. If a new category (e.g. `knowledge/`) is needed, create it

### Step 4: Generate Skills

For each document, create a skill with this structure:

```
skills/{category}/{skill-name}/
├── SKILL.md           # Main skill file with frontmatter + instructions
└── references/        # Optional: split large documents
    └── source.md      # Original content, restructured
```

#### SKILL.md Template

```markdown
---
name: {skill-name}
description: "{One-line description}. Auto-imported from Google Drive: {original filename}."
tags: [{category}]
source: "gdrive:{document_id}"
imported_at: "{YYYY-MM-DD}"
---

# {Title}

{Restructured content from the Google Drive document.}

## Key Points
{Summarized key takeaways — only if the document is long.}
```

#### Content Restructuring Rules

- Convert Google Docs formatting to clean Markdown
- Preserve all substantive content — do NOT summarize away details
- Add clear headings if the original lacks structure
- Remove formatting artifacts, redundant whitespace, page breaks
- Keep tables, lists, and code blocks intact
- If the document exceeds 500 lines, split into `SKILL.md` (overview + instructions) and `references/` (detailed content)

### Step 5: Deploy and Report

After generating all skills:

1. Run `./bin/sk deploy` to symlink new skills
2. Present a summary table:

```
| # | Source Document | Created Skill | Category |
|---|----------------|---------------|----------|
| 1 | Design Guide.gdoc | arch-design-guide | docs/ |
| 2 | Deploy SOP.gdoc | sop-deploy | workflow/ |
```

3. Remind the user to restart Claude Code to pick up new skills

## Error Handling

- If a document fails to read, log it and continue with the rest
- If a document is empty or too short (< 50 chars), skip it and note in the report
- If a skill name conflicts with an existing skill, append `-v2` and warn the user
- Never overwrite existing skills without explicit user confirmation
- If a MIME type detection fails, try downloading with `text/plain` first; if that fails, the error will reveal the correct MIME type — retry with the correct format
- If an Agent reports permission denied, fall back to reading in the main conversation where permission prompts can be triggered
