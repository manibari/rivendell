# Skill Harvest 報告 — 2026-08-04

## 一、Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|--------|----------|
| 1 | news-stock | 129 | 策略換股日調整（月初開盤日換股）：先跑方案 B 回測比對績效，確認後把 B 的口徑寫進 `portfolio_strategy.py` / `backtest_service.py`，`regression.py` 把關 |
| 2 | rivendell | 1 | 執行既有 `token-analysis` 排程 agent（`com.sk.agent.rivendell.token-analysis`），產出 2026-08-03 token 用量日報 |
| 3 | code | 1 | 單句閒聊（「沒看到你燉蹄」），無工具呼叫 |
| 4 | code | 1 | 空白訊息，無工具呼叫 |
| 5 | code | 24 | 使用者想做一個類似 Excalidraw、可直接畫架構圖並儲存的工具 → 走 `requirement` + `gstack-office-hours` 探索 |

已核對 `/Users/manibari/code/rivendell/skills/` 現有清單。本輪命中率偏低：5 個 session 中有 2 個是無實質內容的單訊息、1 個是既有排程 agent 的正常執行、1 個是既有 skill routing（`requirement` → `gstack-office-hours`）的正常運作。唯一有實質工程內容的是 session 1，但屬單一專案的一次性程式修改。

---

## 二、Skill 候選

### 🔴 Weak — 不建議新增

- **Session 1（策略換股日回測 → 寫入引擎）**：`investment-research` skill 的說明已涵蓋「backtesting、rebalancing proposals」，這次工作屬於該領域的正常執行，不是缺口。而且改動的檔案（`portfolio_strategy.py`、`backtest_service.py`、`regression.py`）是 news-stock 專案內部實作細節，只出現這一次，尚未看到跨專案或跨時間重複的模式。若要沉澱，建議寫進 **news-stock 專案自己的 `.learnings/`**（例如「方案變更前先跑 A/B 回測比較，落地時同步更新 regression 測試」這條原則），而不是拉高成 rivendell 共用 skill —— 目前證據量不足以支撐一個可攜的流程沉澱。
- **Session 2（token 用量日報）**：已經是 `com.sk.agent.rivendell.token-analysis` 排程 agent（見 `agents/agents.conf`）在跑，不是缺口，是既有自動化的正常輸出。
- **Session 3、4**：訊息內容不足以判斷任何工作模式（單句閒聊 / 空白），略過。
- **Session 5（類 Excalidraw 架構圖工具發想）**：使用者本身已經正確地被導入 `requirement` → `gstack-office-hours`（思考/探索階段），這正是 CLAUDE.md 的 Step 0 任務分流該做的事，不是缺口。若這個產品構想後續要繼續推進，屬於 `gstack-office-hours` 的既有職責，不需要新技能。

---

## 三、建議下一步

本輪沒有 Strong/Moderate 候選需要動手做。唯一值得留意的動作：

1. 若 session 1 的「A/B 回測比對 → 確認才寫入引擎」模式在 news-stock 專案未來再出現 2 次以上，回頭補一個 news-stock 專屬的 skill 或至少一條 `.learnings/LEARNINGS.md` 規則。
2. 無其他建議動作 —— 本次 harvest 判定為低命中率週期，符合機制正常運作（多數需求已被既有 skill/agent 覆蓋，不代表 harvest 流程失效）。
