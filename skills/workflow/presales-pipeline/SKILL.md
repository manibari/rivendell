---
name: presales-pipeline
description: >
  以檔案系統（`01_presales/<client-slug>/`）管理 B2B 售前 pipeline：`new-client.sh` 建立標準資料夾（`client-readme.md` + `company-overview.md` + 狀態 frontmatter），支援 `active` / `won` / `lost` / `archive` 狀態轉移，整合既有 `customer-
  TRIGGER when: 使用者說「新 client」「presales」「這個可以 archive / lost 了」「宸祿科技」這類公司級 prospect 命名、或 `cd` 進入 `01_presales` 目錄時。
when_to_use: 使用者說「新 client」「presales」「這個可以 archive / lost 了」「宸祿科技」這類公司級 prospect 命名、或 `cd` 進入 `01_presales` 目錄時。
version: 1.0.0
tags: [workflow, sales, presales]
languages: all
source: harvest-auto
---

# presales-pipeline

## Overview

以檔案系統（`01_presales/<client-slug>/`）管理 B2B 售前 pipeline：`new-client.sh` 建立標準資料夾（`client-readme.md` + `company-overview.md` + 狀態 frontmatter），支援 `active` / `won` / `lost` / `archive` 狀態轉移，整合既有 `customer-intel` 做 one-shot research、以及 `crm-projection` 做 CRM 回填。產出 `INDEX.md` 彙總所有 prospect 現況。

## When to Use

使用者說「新 client」「presales」「這個可以 archive / lost 了」「宸祿科技」這類公司級 prospect 命名、或 `cd` 進入 `01_presales` 目錄時。

## Background

From session harvest analysis:

Session 5 展現的工作模式跟 `customer-intel`（單次深度研究）、`crm-projection`（DB → markdown 投影）都不同——這是 prospect 的**生命週期**管理：新增 → 研究 → 判定 active/lost/archive → 歸檔。使用者已自建 `new-client.sh`，但分類語意（archive vs lost）與 INDEX 規則需要 codify。與 `material-health` 的「素材健康檢查」可進一步形成 pipeline 閉環。
- **是否存在**：否。`customer-intel`、`crm-projec...

## TODO

This skill was auto-generated from a harvest candidate.
Fill in the implementation details, patterns, and examples.
