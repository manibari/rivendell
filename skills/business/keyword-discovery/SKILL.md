---
name: keyword-discovery
description: >
  Automated keyword discovery for scraper filter systems. Analyzes unmatched items
  to find frequent terms, writes candidates to a YAML config for human review,
  and auto-promotes high-confidence keywords. TRIGGER when: building a scraper that
  filters by keywords, user wants to discover new filter terms, or mentions
  "關鍵字分析" / "keyword analysis" / "漏網之魚". DO NOT TRIGGER when: doing
  one-time keyword research (use web-search), or NLP/ML classification tasks.
version: 1.0.0
tags: [workflow, scraping, automation, data-quality]
languages: [python, yaml]
---

# Keyword Discovery

Automated keyword discovery for scraper/filter systems. Analyzes unmatched items to surface new filter terms, manages them through a candidate → promote/reject lifecycle, all driven by a single YAML config.

## Architecture

```
Scraper runs → unmatched items logged
    ↓
Analyzer script (post-scrape)
    ↓
Extract terms from unmatched titles/descriptions
    ↓
Update keywords.yml: new candidates + auto-promote qualifiers
    ↓
Human reviews remaining candidates → approve / reject
```

**YAML config is SSOT** — the scraper reads `active` keywords at runtime, the analyzer writes `candidates`, and the promote logic moves terms between sections. No database needed.

## YAML Config Format

File: `config/keywords.yml`

```yaml
active:
  category_name:
    - keyword1
    - keyword2
  auto_discovered:
    - keyword3  # promoted 2026-03-24

candidates:
  term:
    count: 15
    days_seen: 3
    first_seen: "2026-03-24"
    sample_titles: ["example title 1", "example title 2"]

rejected:
  - AR  # too short, ambiguous
  - 公告  # too generic
```

- **active** — grouped by category; scraper uses these for filtering
- **candidates** — terms seen in unmatched items, pending review
- **rejected** — blocklist; analyzer skips these permanently

## Term Extraction

### Chinese (n-grams)

- Extract 2–4 character n-grams from unmatched titles
- Filter out stopwords (的、是、在、了、有、和、為、與、及)
- Require at least one CJK character in the gram

### English

- Extract words with 3+ characters (lowercase, stripped of punctuation)
- Skip common stopwords (the, and, for, with, from, etc.)
- Short abbreviations (<=2 chars) go straight to `rejected`

### Counting

- Deduplicate per-item (same term in one title counts once)
- Accumulate across scrape runs; track `count` and `days_seen`

## Auto-Promote Logic

After each analyzer run, check all candidates:

```python
for term, stats in candidates.items():
    if stats["count"] >= 10 and stats["days_seen"] >= 3:
        active["auto_discovered"].append(term)
        del candidates[term]
        log(f"AUTO-PROMOTED: {term} (count={stats['count']}, days={stats['days_seen']})")
```

Thresholds: **count >= 10 AND days_seen >= 3** — both conditions must be met. This prevents one-day spikes from polluting the active list.

## False Positive Prevention

| Rule | Example | Action |
|------|---------|--------|
| Short English (<=2 chars) | AR, IT, AI | Auto-reject |
| Ambiguous single terms | API, 系統 | Use compound form: API介接, 資訊系統 |
| Rejected list match | Any term in `rejected` | Skip silently |
| Below auto-promote threshold | count=5, days=1 | Keep in `candidates` for human review |

Best practices:
- Prefer compound terms over single generic words
- Review `candidates` weekly — promote good ones, reject noise
- Add context comments to `rejected` entries explaining why

## Integration

### Post-Scrape Hook

```bash
#!/bin/bash
# run-scraper.sh
set -euo pipefail

# 1. Run the scraper
python3 scraper.py

# 2. Analyze unmatched items for new keywords
python3 keyword_analyzer.py \
  --config config/keywords.yml \
  --unmatched data/unmatched.jsonl \
  --log "logs/keyword-discovery-$(date +%Y-%m-%d).log"
```

### Analyzer Script Outline

```python
def analyze(config_path: str, unmatched_path: str) -> None:
    config = load_yaml(config_path)
    active_terms = flatten_active(config["active"])
    rejected_terms = set(config.get("rejected", []))

    for item in read_jsonl(unmatched_path):
        terms = extract_terms(item["title"])
        for term in terms:
            if term in active_terms or term in rejected_terms:
                continue
            if is_short_english(term):
                config["rejected"].append(term)
                continue
            update_candidate(config["candidates"], term, item)

    auto_promote(config)
    save_yaml(config_path, config)
```

### Dashboard Visibility

- Analyzer logs to `logs/keyword-discovery-YYYY-MM-DD.log`
- Log format: one line per action (NEW_CANDIDATE, COUNT_UPDATE, AUTO_PROMOTED, AUTO_REJECTED)
- Dashboard reads log files to show discovery activity

## Key Paths

- `config/keywords.yml` — Single source of truth for all keyword state
- `data/unmatched.jsonl` — Items that didn't match any active keyword (scraper output)
- `logs/keyword-discovery-*.log` — Dated analyzer logs
- `keyword_analyzer.py` — Analyzer script
