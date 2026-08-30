# Session Harvest 報告（5 sessions, 2026-08）

## Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|--------|----------|
| 1 | PTI-ARES | 154 | Canvas 渲染除錯（GeometryCanvas.tsx / canvas-renderer.ts），用 chrome-devtools 反覆截圖檢查 Soldermask 異常反白 |
| 2 | PTI-ARES | 1 | 單訊息，無實質內容 |
| 3 | PTI-ARES | 39 | 四件事組合：pull commit → 盤點進度範圍 → 產資料串接架構圖（.mmd/.png）→ 列規則定義（rule-library-v7） |
| 4 | rivendell | 1 | 給定跨專案 token 花費 + 抽樣指令，寫成繁中日報 markdown |
| 5 | sales-assistant | 18 | 執行既有 `crm-projection` skill，query CRM pipeline 資料 |

Session 5 是既有 skill 正常呼叫，非候選。Session 2 訊息量不足以分析。

## Skill 候選

### 1. token-cost-digest（Strong）
- **目的**：把「每專案 token 花費數字 + 當日 session 指令抽樣」轉成一份結論先行的繁中日報，說明錢花在哪、對應到什麼實際工作。
- **觸發**：使用者貼上多專案 token/cost 統計 + session 抽樣，要求寫日報；或排程 agent 每日產出。
- **分類**：meta / observability
- **理由**：查過 `agent-observability`（做 agent 執行可見度，非成本）、`workflow-retro`（週回顧 skill/agent 瓶頸，非逐日成本），兩者都不覆蓋「原始 token 花費→人話日報」這個轉譯步驟。Session 4 雖只有 1 則訊息，但格式（資料表→中文摘要）明確可重複，值得抽成 skill 而非每次現寫 prompt。

### 2. project-catchup-briefing（Moderate）
- **目的**：回到一個擱置一段時間的專案時，一次跑完「pull 最新 commit → 盤點進度/範圍 → 產資料串接架構圖 → 列出目前規則定義」四步驟，輸出成一份可讀的現況簡報。
- **觸發**：使用者說「這是 XXX 專案」「幫我看一下目前進度跟架構」「回顧一下這包的規則」等重新接手/久違回訪的訊號。
- **分類**：workflow（orchestrator，不重造輪子）
- **理由**：這是一個「組合既有能力」的 recipe，不是全新能力——架構圖該轉呼 `mermaid-diagram`，規則盤點某種程度上跟 `context-recovery`（自動觸發、偏 session compaction 情境）功能相鄰但目的不同：`context-recovery` 答「上次做到哪」，這個候選答「這包東西現在整體長怎樣」，且是使用者主動明確要求四件事、非自動偵測。因為與既有 skill 有邊界重疊需要抓清楚，且僅一次樣本，評 Moderate 而非 Strong。

### 3. canvas-visual-verify-loop（Weak）
- **目的**：改動 canvas/geometry 渲染程式碼後，用 chrome devtools computer 工具反覆截圖比對異常反白效果。
- **觸發**：canvas 渲染相關程式碼變更後要肉眼驗證視覺結果。
- **分類**：quality / QA
- **理由**：只有一個樣本（session 1，23 次 chrome computer 呼叫但屬即興除錯，非固定步驟），且與既有 `gstack-qa` / `gstack-browse`（headless browser QA）功能相近，尚未看出獨立於一般 QA skill 之外的專屬步驟。建議先觀察是否再出現類似模式，暫不建立新 skill。

## 未建議事項
- Session 5（crm-projection）正確呼叫既有 skill，無需新增。
- Session 2 資料量不足以判斷模式。
