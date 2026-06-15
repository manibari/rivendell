---
name: env-doctor
description: >
  為專案產生 `doctor.sh`（或 `doctor.py`），檢查 Python/Node 版本、依賴鎖定檔 hash、模型/資料下載狀態、key env vars、外部服務連線；輸出彩色 PASS/FAIL 報告供跨機器一鍵診斷。
  TRIGGER when: 使用者說「為什麼我在另一台機器跑出來不一樣」「環境排錯」「reproducibility」「寫一個 doctor 腳本」「跨機器 setup 驗證」。
when_to_use: 使用者說「為什麼我在另一台機器跑出來不一樣」「環境排錯」「reproducibility」「寫一個 doctor 腳本」「跨機器 setup 驗證」。
version: 1.0.0
tags: [workflow, environment, reproducibility, diagnostics]
languages: all
source: harvest-auto
---

# env-doctor

## Overview

為專案產生 `doctor.sh`（或 `doctor.py`），檢查 Python/Node 版本、依賴鎖定檔 hash、模型/資料下載狀態、key env vars、外部服務連線；輸出彩色 PASS/FAIL 報告供跨機器一鍵診斷。

## When to Use

使用者說「為什麼我在另一台機器跑出來不一樣」「環境排錯」「reproducibility」「寫一個 doctor 腳本」「跨機器 setup 驗證」。

## Background

From session harvest analysis:

Session 1 花了大量時間建立 `doctor.sh`，這是任何多人/多機器專案的通用痛點。現有 `qa-testing`、`qa-auto` 處理的是測試，不是環境一致性；`init-project` 只負責初始化，不做 runtime health。值得獨立 skill。
- **是否存在**：否（已檢查 `skills/` 全部子目錄）。

## TODO

This skill was auto-generated from a harvest candidate.
Fill in the implementation details, patterns, and examples.
