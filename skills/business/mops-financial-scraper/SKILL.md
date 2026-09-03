---
name: mops-financial-scraper
description: >
  Scrape listed/OTC company financials from Taiwan's MOPS (公開資訊觀測站,
  mopsov.twse.com.tw) — historical 財務三表, 月營收, 季/年度合併營收 — and
  normalize into SQLite/DuckDB with a TEJ-like query API for quant analysis.
  Covers 股票代號清單, throttling, retry, incremental update, schema versioning.
  TRIGGER: 「抓財報」「MOPS 爬蟲」「建一個像 TEJ 的資料庫」「月營收歷史」
  「公開資訊觀測站下載」「台股財務資料庫」, or building a Taiwan financial
  time-series database.
  SKIP: company-registration / 負責人 / 董監事 lookup (use tw-company-lookup);
  B2B sales research (sales-customer-intel); non-TW or stock-picking research
  (investment-research); a one-off CSV/xlsx transform (office-xlsx).
tags: [workflow, finance, scraping, taiwan, data-pipeline]
version: 1.1.0
source: manual
---

# mops-financial-scraper

Build a local, TEJ-like Taiwan financial database by scraping MOPS, normalizing,
and exposing a query API. The parsed DB — not the raw HTML/PDF — is the asset
downstream quant code reads.

## Workflow

1. **股票代號清單** — resolve the universe (上市 + 上櫃). Fix the canonical symbol
   form up front (see Gotchas — `2330` vs `2330.TW`).
2. **節流抓取** — fetch per company × report type with throttling + retry/backoff.
   Three streams: (a) 財務三表 (BS/IS/CF), (b) 月營收, (c) 季/年度合併營收.
3. **標準化落地** — parse → typed rows → SQLite/DuckDB (`finance_db.py` pattern),
   with an explicit schema + a schema-version column for migrations.
4. **增量更新** — dedup on (symbol, period, report_type); only fetch new periods;
   never re-scrape what already landed.
5. **Query API** — a thin TEJ-like accessor (by symbol, period range, statement)
   so downstream code never touches raw files.

## Gotchas (highest-signal — MOPS will burn you here)

- **Cert rejection**: requests/urllib3 reject the `mopsov.twse.com.tw` cert with
  "Missing Subject Key Identifier". `verify=False` is acceptable for this public,
  read-only gov data.
- **307 throttle disguised as success**: MOPS throttles via `307 → 200 homepage`.
  Set `allow_redirects=False` (`redirect: 'manual'`). Auto-follow silently returns
  the homepage HTML instead of data — you parse junk and never see the failure.
- **Schema-aware SQL before the first cross-table query**: run `.schema <table>`
  for each table. Don't trust column conventions across tables (`report_date` vs
  `year_month` vs `date`); don't trust symbol conventions (`2330.TW` vs `2330`).
  Normalize at the service boundary, not deep in queries.
- **合併 vs 個體**: consolidated and parent-only financials are different report
  types/endpoints — keep `report_type` explicit so they don't silently mix
  (see sibling skill mops-individual-financial-report).
- **待補**: exact MOPS download endpoints per report type — confirm from a real run
  / existing `collect_historical.py` before coding; do not guess URLs.
