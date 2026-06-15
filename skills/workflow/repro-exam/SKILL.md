---
name: repro-exam
description: >
  依照專案的核心邏輯（如 backtest engine、portfolio strategy）產生一組 deterministic 測驗（input → expected output），讓對方在自己的機器跑完比對結果，快速定位差異來源（資料源 / 套件版本 / 隨機種子 / floating point）。
  TRIGGER when: 使用者說「我有沒有標準的測驗考題」「跑出來不一樣怎麼排錯」「驗證對方的計算結果」「reference output for comparison」。
when_to_use: 使用者說「我有沒有標準的測驗考題」「跑出來不一樣怎麼排錯」「驗證對方的計算結果」「reference output for comparison」。
version: 1.0.0
tags: [workflow, quality, reproducibility]
languages: all
source: harvest-auto
---

# repro-exam

## Overview

依照專案的核心邏輯（如 backtest engine、portfolio strategy）產生一組 deterministic 測驗（input → expected output），讓對方在自己的機器跑完比對結果，快速定位差異來源（資料源 / 套件版本 / 隨機種子 / floating point）。

## When to Use

使用者說「我有沒有標準的測驗考題」「跑出來不一樣怎麼排錯」「驗證對方的計算結果」「reference output for comparison」。

## Background

From session harvest analysis:

Session 1 中使用者明確要求「標準的測驗考題可以讓對方的電腦排查」，這是與 `qa-testing` 不同的問題：不是驗證程式正確性，而是驗證「兩台機器是否產生相同結果」。常見於量化研究、ML reproducibility、科學運算。
- **是否存在**：否。

## TODO

This skill was auto-generated from a harvest candidate.
Fill in the implementation details, patterns, and examples.
