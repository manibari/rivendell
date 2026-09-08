# Session Harvest — 2026-09-06

## 摘要

| # | 日期 | 專案 | 訊息數 | 花費 | 主要活動 |
|---|------|------|--------|------|----------|
| 1 | 2026-09-05 | rivendell | 1 | $0.00 | 依 token 花費 + session 指令取樣，寫每日 token 用量分析日報（繁中） |
| 2 | (近期) | sales-assistant | 11 | $0.00 | 執行 `sales-crm-projection` skill：查 nx_client + nx_deal，交叉比對 sales-customer-intel |
| 3 | (近期) | sales-assistant | 12 | $0.00 | 同上，`sales-crm-projection` 第二次執行 |

樣本量小（3 場、共 ~24 則訊息），且工具使用集中在 Bash + Skill，訊號有限。

## 逐場分析

### Session 1 — token 用量分析日報
Intent 是「你是 token 用量分析師，寫繁中日報」。這個模式**已經有專責自動化**：`bin/sk-token-analysis-cron`（nightly launchd 排程，輸出 `reports/token-analysis-YYYY-MM-DD-<host>.md`，用 haiku 模型做每日「錢花去哪＋做了什麼」摘要，含 Telegram 推播）。這場很可能就是該 cron 腳本背後的 claude -p 呼叫，不是使用者手動重新發明的流程。**不是新 skill 候選**。

### Session 2 & 3 — sales-crm-projection 重複執行
兩場都是呼叫既有 skill `/Users/manibari/.claude/skills/sales-crm-projection`（同時也在 rivendell repo 有對應版本 `skills/sales/sales-crm-projection`，`loop: sales`, `pdca: act`，frontmatter 已寫明 daily headless agent 觸發）。查 nx_client + nx_deal pipeline → 交叉比對 customer-intel → 寫入 `materials/clients/`。這正是該 skill 設計時要覆蓋的重複性工作，**行為符合預期，非新模式**。

## Skill 候選評估

本次沒有發現尚未被涵蓋的重複工作流程或領域知識。

| 候選 | 評級 | 說明 |
|------|------|------|
| （無） | — | 兩個觀察到的模式（token 日報、CRM projection）皆已有對應自動化（`sk-token-analysis-cron`、`sales-crm-projection` skill），重複執行是既有機制在正常運作，不構成新 skill 訊號。 |

## 建議

- 樣本量過小（僅 3 場、多為既有自動化的正常重跑），此次無需採取行動。
- 若要提高下次 harvest 的訊號密度，可以待 session 數量回升、或聚焦在非排程性的互動 session（目前 3 場中有 2 場疑似排程/headless 觸發，訊號本身就會偏低）。
