---
name: tender-scraper
description: "Automated government tender scraper — fetches public tender listings from Taiwan's government procurement portal (via g0v API), filters by data-driven keywords (keywords.yml with auto-discovery), writes/archives case files, and regenerates INDEX.md. Includes network resilience (retry with exponential backoff), keyword analysis for candidate discovery, and dashboard observability. Fully local, no DB dependency."
tags: [automation, tenders, scraping, sales-enablement, local, keyword-discovery, resilience]
version: 2.0.0
source: manual
user_invocable: true
when_to_use: "TRIGGER when: user says /tender-scraper, 'scrape tenders', '更新標案', '爬標案', or this skill is invoked by a headless agent on schedule. DO NOT TRIGGER when: user is manually researching a single tender."
allowed-tools:
  - WebFetch
  - WebSearch
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Tender Scraper

Automated scraper that fetches government tender listings and maintains `materials/tenders/` as a local knowledge base. **No DB dependency** — markdown files are the single source of truth.

## Architecture

```
g0v API → Filter 公開徵求 → Dedup vs existing .md files → Write/Archive → Regenerate INDEX
```

### Data Flow

```
WebFetch pcc-api.openfun.app
    ↓
Filter brief.type = 公開徵求
    ↓
Read materials/tenders/cases/*.md frontmatter (dedup)
    ↓
New → Write cases/{job_number}-{slug}.md
Deadline passed → Move to cases/archived/
    ↓
Regenerate INDEX.md + by-category/*.md
```

## Data Source

| Source | URL | Frequency | source_id |
|--------|-----|-----------|-----------|
| g0v 政府採購 API | https://pcc-api.openfun.app | daily | pcc_g0v |
| 政府電子採購網 (fallback) | https://web.pcc.gov.tw | fallback only | pcc_web |

### API Endpoints

- `GET /api/listbydate?date=YYYYMMDD` — list all announcements for a date (100-200/page, `page` param)
- `GET /api/tender?unit_id=XXX&job_number=YYY` — tender detail (contains 招標方式, 截止投標, 預算金額)

### Important: Filtering

`brief.type` is always `"公開招標公告"` for all public tenders — **cannot** filter by 招標方式 at listing level. Must fetch detail and check `招標資料.招標方式 == "公開徵求"`.

## Workflow

Read [scraper.md](scraper.md) for the complete scraping workflow.

### Pipeline Overview (6+1 Steps)

| Step | Name | Description |
|------|------|-------------|
| 1 | **Wait for network** | DNS resolution check; block until connectivity confirmed |
| 2 | **Fetch listings** | WebFetch g0v API for today's listings (paginate all pages); retry with exponential backoff on 429 |
| 3 | **Filter by keywords** | Match listings against active keyword categories loaded from `keywords.yml` |
| 4 | **Fetch detail + create case files** | For matching tenders, fetch detail API → write `cases/{job_number}-{slug}.md` with frontmatter + parsed detail |
| 5 | **Auto-enrich** | Playwright screenshots + AI vision extract scope, qualification, evaluation method for matching tenders |
| 6 | **Archive + regenerate** | Move past-deadline tenders to `cases/archived/`, regenerate `INDEX.md` and `by-category/*.md` |
| 7 (post-scrape) | **Keyword analysis** | Analyze unmatched tenders to discover new keyword candidates; populate `candidates:` in `keywords.yml` |

```
[Step 1] Network wait
    ↓
[Step 2] Fetch listings (g0v API, retry/backoff)
    ↓
[Step 3] Filter by keywords (keywords.yml)
    ↓
[Step 4] Fetch detail + create case files
    ↓
[Step 5] Auto-enrich matching tenders
    ↓
[Step 6] Archive past-deadline + regenerate INDEX.md
    ↓
[Step 7] Keyword analysis → discover new candidates
```

## Keyword Management

Keyword matching is **data-driven** via `keywords.yml` — no hardcoded keyword lists in code.

### keywords.yml Structure

```yaml
active:
  資訊服務:
    - 資訊系統
    - 軟體開發
  auto_discovered:          # promoted from candidates
    - 資料治理
candidates:                 # auto-populated by analyzer
  數位轉型:
    count: 12
    days: 4
    sample_titles:
      - "XX機關數位轉型計畫"
rejected:                   # won't be suggested again
  - AR
  - VR
```

### Matching Rules

- **`active:`** — categories and their keywords used for tender matching in Step 3
- **`candidates:`** — auto-populated by the keyword analyzer (Step 7) with `count` and `sample_titles`
- **`rejected:`** — keywords that will never be suggested again

### Auto-Promotion

When a candidate meets **both** thresholds, it is automatically promoted to the `auto_discovered` category under `active:`:
- Appearance count >= 10
- Seen across >= 3 distinct days

### False Positive Avoidance

Short English abbreviations (`AR`, `VR`, `BI`, `API`) are auto-rejected — they generate too many false positives in Chinese tender titles. Use compound forms instead (e.g., `API介接`, `VR體驗`).

## Observability

- **exec-lib** writes run metadata to the dashboard DB on each execution
- Progress logging uses **`[step N/5]`** prefix format for structured parsing
- Dashboard renders a timeline view from plain Python log output — no special log framework needed

## Resilience

| Mechanism | Detail |
|-----------|--------|
| **Network wait** | Step 1 performs DNS resolution check; scraper blocks until connectivity is confirmed |
| **Retry with backoff** | HTTP 429 (rate limit) triggers exponential backoff with jitter; configurable max retries |
| **DNS check** | Resolves `pcc-api.openfun.app` before attempting API calls to fail fast on network issues |

## Case File Format

Each tender is a markdown file at `materials/tenders/cases/{job_number}-{slug}.md`:

```yaml
---
name: "OO機關XX系統建置案"
job_number: "LP5-114001"
agency: "經濟部"
category: "勞務"
tender_type: "公開徵求"
publish_date: "2026-03-17"
deadline: "2026-03-31"
budget_amount: "5,000,000"
reference_url: "https://web.pcc.gov.tw/..."
source_id: pcc_g0v
last_scraped: "2026-03-17"
status: active
---
```

## Category Mapping

Classify each tender based on procurement category:

| API category | category tag | by-category file |
|-------------|-------------|------------------|
| 勞務 | 勞務 | services.md |
| 財物 | 財物 | goods.md |
| 工程 | 工程 | engineering.md |

## Date Handling

- Deadline determines active/archived status
- `deadline >= today` → active
- `deadline < today` → archived (move to `cases/archived/`)

Taiwan government sites use ROC calendar (民國):
- 民國年 + 1911 = 西元年
- Example: 115年3月 = 2026年3月

## Headless Execution

Runs as headless agent via LaunchAgent `com.sk.agent.sales.tender-scraper`.
Schedule: Daily 08:30.
Runner: `scripts/tender-scraper.sh`

## Screenshot Detail Parsing

For each new tender, Playwright captures the detail page and AI vision extracts:
- Scope/requirements summary (需求規格)
- Qualification requirements (資格條件)
- Evaluation method (評選方式)
- Contract period (履約期限)

**Tool**: `services/nexus/tender_detail_parser.py`
- `capture_tender_screenshots(unit_id, job_number)` → list of PNG paths
- `build_vision_prompt()` → prompt for AI vision parsing
- Screenshots stored in `materials/tenders/screenshots/` (ephemeral)

See [scraper.md](scraper.md) Phase 3.5 for detailed workflow.

## Key Paths

- `materials/tenders/cases/*.md` — Individual tender files (SSOT)
- `materials/tenders/cases/archived/*.md` — Past-deadline tenders
- `materials/tenders/screenshots/` — Ephemeral screenshots for AI parsing
- `materials/tenders/INDEX.md` — Auto-generated active summary
- `materials/tenders/by-category/*.md` — Per-category views
- `materials/tenders/keywords.yml` — Keyword configuration (active, candidates, rejected)
