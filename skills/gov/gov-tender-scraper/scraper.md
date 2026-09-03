# Tender Scraper — Detailed Workflow

All data lives in `materials/tenders/` as markdown files. No database dependency.

## API Structure (Verified 2026-03-17)

The g0v API (`pcc-api.openfun.app`) returns:

**Listing API** (`/api/listbydate`):
- Returns 100–200 records per page (use `page` param, 0-indexed)
- `brief.type` = always `"公開招標公告"` for all public tenders (NOT the 招標方式)
- `brief.title` = tender name
- `brief.category` = procurement category (e.g. `"財物類352-醫藥產品"`)
- `job_number`, `unit_id`, `unit_name` = identifiers

**Detail API** (`/api/tender`):
- `招標資料.招標方式` = actual procurement method (`"公開招標"`, `"公開徵求"`, etc.)
- `領投標.截止投標` = deadline in ROC format (e.g. `"115/03/24 17:00"`)
- `採購資料.預算金額` = budget (e.g. `"5,868,000元"`)
- `採購資料.預算金額是否公開` = whether budget is public (`"是"` / `"否"`)

⚠️ **Cannot filter by 招標方式 at listing level** — must fetch detail for each entry and check `招標資料.招標方式`.

## Phase 1: Fetch Listings

Fetch today's tender announcements from the g0v API. Paginate through all pages.

```
1. DATE = today in YYYYMMDD format
2. page = 0
3. Loop:
   a. WebFetch https://pcc-api.openfun.app/api/listbydate?date={DATE}&page={page}
   b. Parse JSON response → records array
   c. If empty array or no results → break
   d. Collect all entries (cannot filter by 招標方式 at this level)
   e. page += 1
   f. Continue loop
```

### Fallback: Playwright

If the g0v API is unavailable (HTTP error, timeout, or empty response when tenders are expected):

```
1. Use web-scraper skill (Playwright) to navigate web.pcc.gov.tw
2. Go to public tender search page
3. Set search criteria: 公告日期 = today, 招標方式 = 公開徵求
4. Extract listing table
5. For each row, extract: name, job_number, agency, category, deadline
```

## Phase 2: Deduplication (File-Based)

Read all existing case files and build a lookup by job_number:

```
1. Glob materials/tenders/cases/*.md
2. For each file, read YAML frontmatter
3. Build set: existing_job_numbers = { frontmatter.job_number }
4. For each scraped listing:
   - If job_number in existing_job_numbers → update last_scraped only
   - Else → new tender, proceed to fetch detail
```

## Phase 3: Fetch Detail & Filter

For each new tender, fetch the detail API. **Filter for 公開徵求 at this stage.**

```
1. WebFetch https://pcc-api.openfun.app/api/tender?unit_id={unit_id}&job_number={job_number}
2. Parse JSON response
3. Check: 招標資料.招標方式 — if NOT "公開徵求" → skip this tender
4. Extract from the LATEST record in the records array:
   - name: brief.title (標案名稱)
   - agency: unit_name (招標機關)
   - category: parse from brief.category — 勞務/財物/工程
   - tender_type: 招標資料.招標方式 (should be "公開徵求")
   - publish_date: record date (YYYYMMDD → ISO)
   - deadline: 領投標.截止投標 (ROC format "115/MM/DD HH:MM" → ISO date)
   - budget_amount: 採購資料.預算金額
   - reference_url: record.url field
```

### Category Extraction

`brief.category` format: `"勞務類XXX-描述"` or `"財物類XXX-描述"` or `"工程類XXX-描述"`

```
- starts with "勞務" → category: 勞務
- starts with "財物" → category: 財物
- starts with "工程" → category: 工程
```

### ROC Date Conversion

`領投標.截止投標` format: `"115/03/24 17:00"`
```
ROC year = 115 → Western year = 115 + 1911 = 2026
Result: 2026-03-24
```

## Phase 3.5: Screenshot-Based Detail Parsing

After fetching basic info from the g0v API, capture screenshots of the tender detail page and parse with AI vision for richer content (scope, qualification, evaluation method).

### When to Use

- Always run for new tenders that pass the 公開徵求 filter
- The g0v API provides basic metadata but lacks detailed requirements/scope
- Screenshots capture the full tender announcement including specs

### Workflow

```python
from services.nexus.tender_detail_parser import capture_tender_screenshots, build_vision_prompt

# 1. Capture screenshots
paths = capture_tender_screenshots(unit_id, job_number)

# 2. Read each screenshot with Claude's vision
for path in paths:
    # Use Read tool on the screenshot file — Claude can read images natively
    # Then apply the vision prompt to extract structured data

# 3. Parse the YAML response and merge into the case file
```

### Step-by-step

```
1. Call capture_tender_screenshots(unit_id, job_number)
   → Returns list of PNG paths in materials/tenders/screenshots/

2. For each screenshot path:
   - Read the image file (Read tool supports PNG)
   - Apply build_vision_prompt() to extract structured YAML

3. Merge parsed fields into the case file:
   - scope_summary → "## 標案說明" section
   - qualification → "## 資格條件" section
   - evaluation_method → add to "## 備註"
   - contract_period → add to frontmatter or "## 備註"
   - contact_name/phone/email → update frontmatter + "## 聯絡資訊"

4. If multiple screenshots, merge results (later sections may have specs)
```

### Screenshot Storage

```
materials/tenders/screenshots/
├── {job_number}_{date}_full.png    ← full-page screenshot
├── {job_number}_{date}_s1.png      ← section 1 (if page is long)
├── {job_number}_{date}_s2.png      ← section 2
└── ...
```

Screenshots are ephemeral — can be cleaned up after parsing. The extracted data lives in the case .md file.

### Error Handling

- If Playwright fails (site blocked, timeout) → skip screenshot enrichment, keep basic API data
- If AI vision parsing returns incomplete results → keep what was extracted, mark gaps
- Never block the main scraper flow for screenshot failures

---

## Phase 4: Write New Case Files

For each new tender, create a markdown file:

**Filename**: `materials/tenders/cases/{job_number}-{slug}.md`
- slug = first 30 chars of name, lowercased, non-alphanumeric replaced with hyphens
- Example: `LP5-114001-某機關資訊系統建置.md`

**Content**:
```markdown
---
name: "{tender name}"
job_number: "{job_number}"
agency: "{agency}"
category: "{勞務|財物|工程}"
tender_type: "公開徵求"
publish_date: "{ISO date}"
deadline: "{ISO date}"
budget_amount: "{amount}"
reference_url: "{url}"
source_id: pcc_g0v
last_scraped: "{today ISO date}"
status: active
---

# {tender name}

## 基本資訊

| 項目 | 內容 |
|------|------|
| 標案案號 | {job_number} |
| 招標機關 | {agency} |
| 採購類別 | {category} |
| 招標方式 | {tender_type} |
| 公告日期 | {publish_date} |
| 截止收件 | {deadline} |
| 預算金額 | {budget_amount} |
| 公告連結 | {reference_url} |

## 標案說明

{description from API, if available}

## 備註

- 來源：g0v 政府採購 API
- 最後更新：{last_scraped}
```

## Phase 5: Archive Past-Deadline Tenders

```
1. Glob materials/tenders/cases/*.md (not archived/)
2. For each file, read frontmatter
3. If deadline < today:
   - Change frontmatter status: active → archived
   - Move file to materials/tenders/cases/archived/
```

Ensure archived directory exists:
```
mkdir -p materials/tenders/cases/archived/
```

## Phase 6: Regenerate Index Files

After all processing, regenerate from the case files.

### INDEX.md

```
1. Glob materials/tenders/cases/*.md (active only, not archived/)
2. Read each frontmatter
3. Sort by deadline ASC
4. Write materials/tenders/INDEX.md as markdown table:
   | 標案名稱 | 招標機關 | 採購類別 | 截止日期 | 預算金額 | 詳情 |
```

### by-category/*.md

For each procurement category:

```
services.md   — 勞務類標案
goods.md      — 財物類標案
engineering.md — 工程類標案
```

Each file is a filtered table of active tenders matching that category.

## Error Handling

- If g0v API fails → use Playwright fallback (web.pcc.gov.tw)
- If Playwright also fails → log error, skip today's scrape
- Log errors but continue with processing existing data
- Never crash the entire scraper for a transient API failure

## Rate Limiting

- g0v API has no documented rate limit, but be respectful
- Add 1-second delay between paginated requests
- Add 0.5-second delay between detail API calls

## Output Summary

At the end of each run, output:

```
=== Tender Scraper Summary ===
Date: {today}
Pages fetched: {N}
Tenders found (公開徵求): {N}
New cases written: {N} files
Cases archived: {N} files
Active cases total: {N}
INDEX.md regenerated: Yes
by-category files updated: {N} files
```
