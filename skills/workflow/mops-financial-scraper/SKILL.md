---
name: mops-financial-scraper
description: >
  自動化從 MOPS（`mopsov.twse.com.tw/mops/web/index`）抓取上市櫃公司的 (a) 歷史財務三表、(b) 月營收、(c) 季/年度合併營收，標準化落地到 SQLite/DuckDB（`finance_db.py` 模式），並提供類似 TEJ 的查詢 API，供後續量化分析使用。包含：股票代號清單、抓取節流、錯誤重試、增量更新、schema 版本控制。
  TRIGGER when: 使用者說「抓財報」「MOPS 爬蟲」「建一個像 TEJ 的資料庫」「月營收歷史」「公開資訊觀測站下載」「台股財務資料庫」。
when_to_use: 使用者說「抓財報」「MOPS 爬蟲」「建一個像 TEJ 的資料庫」「月營收歷史」「公開資訊觀測站下載」「台股財務資料庫」。
version: 1.0.0
tags: [workflow, finance, scraping]
languages: all
source: harvest-auto
---

# mops-financial-scraper

## Overview

自動化從 MOPS（`mopsov.twse.com.tw/mops/web/index`）抓取上市櫃公司的 (a) 歷史財務三表、(b) 月營收、(c) 季/年度合併營收，標準化落地到 SQLite/DuckDB（`finance_db.py` 模式），並提供類似 TEJ 的查詢 API，供後續量化分析使用。包含：股票代號清單、抓取節流、錯誤重試、增量更新、schema 版本控制。

## When to Use

使用者說「抓財報」「MOPS 爬蟲」「建一個像 TEJ 的資料庫」「月營收歷史」「公開資訊觀測站下載」「台股財務資料庫」。

## Background

From session harvest analysis:

Session 1 長達 178 訊息、Bash(43) + Edit(30) + Write(17)，實際產出 `collect_historical.py` / `finance_db.py` / `conftest.py`，是明確成形的工作流程。現有 `tw-company-lookup` 是抓 findbiz 登記資料、`customer-intel` 是 B2B sales research，都不是財務時序資料。對走量化 / news-stock / investment-research 的人等於補齊 Taiwan 資料源這塊拼圖。
- **是否存在**：否（`skills/bac...

## TODO

This skill was auto-generated from a harvest candidate.
Fill in the implementation details, patterns, and examples.
