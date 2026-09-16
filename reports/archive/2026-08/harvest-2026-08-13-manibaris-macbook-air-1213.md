# Skill Harvest 報告 — 2026-08-13（跨專案：3 個 project，4 個 session）

**結論先說：本輪沒有 Strong/Moderate 候選。** 4 個 session 全部對應到既有 skill／排程
agent 的正常執行（`mockup` + 截圖交付、token 用量日報 agent、`subsidy-scraper`、
`crm-projection`），沒有出現新的重複模式。

## 一、Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|-------|---------|
| 1 | Urd-ETL | 13 | 查專案進度（規劃已完成、程式碼未動），並將 `mockups/process-flow-canvas.html`（深色 SAS EG 風格 DAG 畫布 mockup）headless 截圖成 `canvas-drawer.png`／`canvas.png`，用 `SendUserFile` 交付給使用者 |
| 2 | rivendell | 1 | Token 用量分析日報生成——對應既有 `agents/registry/token-analysis.md` 排程 agent（已連續數日在 08-06～08-12 報告中確認為既有流程），非新模式 |
| 3 | sales-assistant | 1 | 執行既有 `subsidy-scraper` skill：爬 grants.nat.gov.tw / SBIR / SIIR，比對既有 `nx_` 資料去重 |
| 4 | sales-assistant | 12 | 執行既有 `crm-projection` skill：查 `nx_client`／`nx_deal` pipeline，比對 customer-intel 報告，寫出 `projection.md`（`Skill` 工具明確呼叫，base directory 對應 `/Users/manibari/.claude/skills/crm-projection`） |

已核對 `/Users/manibari/code/rivendell/skills/`：`crm-projection`、`subsidy-scraper`
均已存在且對應正確；`mockup` skill 涵蓋 session 1 的截圖產出行為；token 用量日報
連續多日已確認是 `agents/registry/token-analysis.md` 的例行輸出。

## 二、Skill 候選

### 🔴 Weak（記錄觀察，不立案）

- **Session 1（進度查詢 + mockup 截圖交付）**：使用者請求「看一下進度」，AI 回報
  規劃完成度後主動截圖 mockup 並用 `SendUserFile` 送出。這個「查狀態 → 順手截圖
  交付」的組合，本質是 `mockup` skill（產出 + 自我截圖檢查，CLAUDE.md 已有規則）
  加上一般性的進度回報，沒有超出既有工具組合。單次發生（n=1），不構成新 skill
  的證據。

## 三、建議下一步

1. 無新 skill 需求，本輪不建立任何新 skill。
2. 本輪樣本量偏小（4 個 session、~27 訊息、成本 $0），訊號不足，維持觀察即可，
   不需要額外行動。

**Trigger to revisit**：若「查進度時順手截圖 mockup 並主動推送檔案給使用者」這個
組合再出現 1-2 次，可考慮把「截圖後用 SendUserFile 主動交付」寫進 `mockup` skill
的結尾步驟，而非獨立成新 skill。
