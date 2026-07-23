---
name: subsidy-scraper
description: "Automated government subsidy scraper — fetches grant listings from Taiwan government portals, deduplicates against existing markdown files, writes/archives program files, and regenerates INDEX.md. Fully local, no DB dependency."
tags: [automation, subsidies, scraping, sales-enablement, local]
version: 1
source: manual
user_invocable: true
when_to_use: "TRIGGER when: user says /subsidy-scraper, 'scrape subsidies', '更新補助', '爬補助', or this skill is invoked by a headless agent on schedule. DO NOT TRIGGER when: user is manually researching a single subsidy (use subsidy-research command instead)."
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

# Subsidy Scraper

Automated scraper that fetches government subsidy/grant listings and maintains `materials/subsidies/` as a local knowledge base. **No DB dependency** — markdown files are the single source of truth.

## Architecture

```
Scrape Sources → Extract Listings → Dedup vs existing .md files → Write/Archive → Regenerate INDEX
```

### Data Flow

```
WebFetch / WebSearch
    ↓
Parse program listings
    ↓
Read materials/subsidies/programs/*.md frontmatter (dedup)
    ↓
New → Write programs/{slug}.md
Expired → Move to programs/archived/
    ↓
Regenerate INDEX.md + by-industry/*.md
```

## Scrape Sources

| Source | URL | Frequency | source_id |
|--------|-----|-----------|-----------|
| 政府補助一站通 | https://grants.nat.gov.tw | 2x/week | grants_nat |
| SBIR 小型企業創新研發 | https://www.sbir.org.tw | weekly | sbir |
| SIIR 服務業創新研發 | https://www.siir.org.tw | weekly | siir |

## Workflow

Read [scraper.md](scraper.md) for the complete scraping workflow.

### Quick Reference

1. **Fetch** — WebFetch each source's listing page
2. **Parse** — Extract program name, agency, deadline, eligibility, URL
3. **Dedup** — Glob `materials/subsidies/programs/*.md`, read frontmatter, match by `reference_url` or `name`
4. **Create** — New programs → write `programs/{slug}.md` with frontmatter
5. **Archive** — Past deadline + no longer listed → move to `programs/archived/`
6. **Regenerate** — Rebuild `INDEX.md` and `by-industry/*.md` from all active program files

## Program File Format

Each subsidy is a markdown file at `materials/subsidies/programs/{slug}.md`:

```yaml
---
name: SBIR 小型企業創新研發計畫 第 N 梯次
agency: 經濟部中小及新創企業署
program_type: sbir
deadline: "2026-06-30"
deadline_text: "115年6月30日"
funding_amount: "個別申請最高 1,000 萬元"
eligibility: "依法登記之中小企業"
industry_tags: [全產業]
company_size: sme
reference_url: "https://www.sbir.org.tw/..."
source_id: sbir
last_scraped: "2026-03-16"
status: active
---
```

## Industry Tag Mapping

Classify each subsidy based on keywords in eligibility/scope:

| Keywords | industry_tag |
|----------|-------------|
| 製造, 工廠, 生產 | 製造業 |
| 軟體, 資訊, 數位, AI | 科技業 |
| 服務, 餐飲, 觀光 | 服務業 |
| 零售, 通路, 電商 | 零售業 |
| 農業, 農漁 | 農業 |
| 醫療, 生技, 長照 | 醫療業 |
| 全產業, 不限 | 全產業 |

## Date Handling

Taiwan government sites use ROC calendar (民國):
- 民國年 + 1911 = 西元年
- Example: 115年3月 = 2026年3月

## Headless Execution

Runs as headless agent via LaunchAgent `com.sk.agent.sales.subsidy-scraper`.
Schedule: Monday & Thursday 08:00.
Runner: `scripts/subsidy-scraper.sh`

## Key Paths

- `materials/subsidies/programs/*.md` — Individual program files (SSOT)
- `materials/subsidies/programs/archived/*.md` — Expired programs
- `materials/subsidies/INDEX.md` — Auto-generated active summary
- `materials/subsidies/by-industry/*.md` — Per-industry views
