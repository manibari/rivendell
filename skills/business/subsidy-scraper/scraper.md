# Subsidy Scraper — Detailed Workflow

All data lives in `materials/subsidies/` as markdown files. No database dependency.

## Phase 1: Fetch Listings

For each scrape source, fetch the listing page and extract program entries.

### grants.nat.gov.tw (政府補助一站通)

```
1. WebFetch https://grants.nat.gov.tw/Portal/SiteMap
2. Look for active grant listings in the response
3. Extract for each listing:
   - Program name (計畫名稱)
   - Agency (主辦機關)
   - Deadline (截止日期) — convert from 民國
   - URL (reference_url)
```

### SBIR (www.sbir.org.tw)

```
1. WebFetch https://www.sbir.org.tw/information/show/1
2. Extract active call-for-proposals
3. Fields: name, agency (經濟部中小及新創企業署), deadline, eligibility, funding_amount
```

### SIIR (www.siir.org.tw)

```
1. WebFetch https://www.siir.org.tw/information/show/1
2. Extract active programs
3. Fields: name, agency (經濟部商業發展署), deadline, eligibility, funding_amount
```

## Phase 2: Deduplication (File-Based)

Read all existing program files and build a lookup:

```
1. Glob materials/subsidies/programs/*.md
2. For each file, read YAML frontmatter
3. Build sets:
   - existing_urls = { frontmatter.reference_url }
   - existing_names = { frontmatter.name }
4. For each scraped program:
   - If url in existing_urls OR name in existing_names → skip (or update last_scraped)
   - Else → new program, proceed to create
```

## Phase 3: Write New Program Files

For each new program, create a markdown file:

**Filename**: `materials/subsidies/programs/{slug}.md`
- slug = lowercase, hyphens, e.g. `sbir-phase2-2026`, `siir-service-innovation-2026`

**Content**:
```markdown
---
name: {program name}
agency: {agency}
program_type: {sbir|siir|government|other}
deadline: "{ISO date}"
deadline_text: "{original 民國 text}"
funding_amount: "{amount text}"
eligibility: "{eligibility text}"
scope: "{scope description}"
industry_tags: [{classified tags}]
company_size: {sme|micro|startup|all}
reference_url: "{url}"
source_id: {grants_nat|sbir|siir}
last_scraped: "{today ISO date}"
status: active
---

# {program name}

## 基本資訊

| 項目 | 內容 |
|------|------|
| 主辦機關 | {agency} |
| 補助金額 | {funding_amount} |
| 申請資格 | {eligibility} |
| 截止日期 | {deadline_text} ({ISO date}) |
| 申請連結 | {reference_url} |

## 補助範圍

{scope}

## 適用場景

- {根據 industry_tags 和 scope 描述適合什麼樣的客戶}
```

## Phase 4: Archive Expired

```
1. Glob materials/subsidies/programs/*.md (not archived/)
2. For each file, read frontmatter
3. If deadline < today AND name not in current scrape results:
   - Change frontmatter status: active → expired
   - Move file to materials/subsidies/programs/archived/
```

Ensure archived directory exists:
```
mkdir -p materials/subsidies/programs/archived/
```

## Phase 5: Regenerate Index Files

After all sources are processed, regenerate from the program files.

### INDEX.md

```
1. Glob materials/subsidies/programs/*.md (active only, not archived/)
2. Read each frontmatter
3. Sort by deadline ASC
4. Write materials/subsidies/INDEX.md as markdown table:
   | 補助名稱 | 主辦機關 | 截止日期 | 適用產業 | 詳情 |
```

### by-industry/*.md

For each industry tag found across active programs:

```
1. Collect all programs with that industry_tag
2. Write materials/subsidies/by-industry/{industry-slug}.md
   - manufacturing.md (製造業)
   - technology.md (科技業)
   - services.md (服務業)
   - retail.md (零售業)
   - agriculture.md (農業)
   - healthcare.md (醫療業)
   - all-industries.md (全產業)
```

Each file is a filtered table of programs matching that industry.

## Error Handling

- If WebFetch fails (anti-scraping), fall back to WebSearch for the same information
- If WebSearch also fails, try the web-scraper skill (Playwright-based) as last resort
- Log errors but continue with other sources
- Never crash the entire scraper for one source failure

## Output Summary

At the end of each run, output:

```
=== Subsidy Scraper Summary ===
Date: {today}
Sources checked: {N}
New programs written: {N} files
Programs archived: {N} files
Active programs total: {N}
INDEX.md regenerated: Yes
by-industry files updated: {N} files
```
