---
date: 2026-05-16
session_count: 4
message_count: ~100
note: Supplementary harvest — light session batch, mostly existing-skill invocations
---

# Session Harvest Supplement — 2026-05-16

## Session 摘要

| # | 專案 | 訊息數 | 主要工具 | 重點活動 |
|---|------|--------|---------|---------|
| 1 | ChimesFlow | 24 | Bash×19, ToolSearch×2, Read×2 | 不明 CLI 流程（讀取 `.output` 檔案、ToolSearch 探索）— 缺乏 user intent 文本，無法判讀 |
| 2 | news-stock | 36 | WebSearch×10, Bash×9, TaskUpdate×7, TaskCreate×4 | 已調用 **investment-research** skill 的 Continuous Mode，產出 `daily-2026-05-16.md` + `portfolio-state.json` |
| 3 | news-stock | 25 | Bash×17, Read×3 | 效能 triage：「為什麼前端慢？資料庫問題還是後端程式問題？」「SQLite 該換 PostgreSQL 嗎？」— 讀取 `analyzer.py`, `finance_service.py`, `stock_picking.py` |
| 4 | sales-assistant | 15 | Bash×8, Read×3, Skill×1, Glob×1 | 已調用 **crm-projection** skill，產出 `INDEX.md` + `projection.md` |

**觀察**：4 個 session 中有 2 個（#2, #4）只是執行既有 skill，沒有新模式可萃取；#1 文本資訊太薄；只剩 #3 是有實質對話內容的問題排查。本批 harvest 候選稀薄是合理結果。

---

## Skill 候選評估

### 🟡 Moderate：`perf-bottleneck-triage`（效能瓶頸三層分流）

- **Purpose**：當使用者回報「前端慢」、「載入久」、「API 回應慢」時，提供系統化的分層測量決策樹，避免直接跳到「換資料庫」這種高成本結論。
- **Trigger**：「前端慢」、「載入久」、「API 卡」、「該換 PostgreSQL 嗎」、「效能優化」、「performance bottleneck」、「slow query」
- **Category**：`quality/` 或 `workflow/`
- **Rationale**：
  - Session 3 的開場是「為什麼前端慢、是資料庫還是後端的問題」+「SQLite 該換 PostgreSQL 嗎」。這是典型的「結論導向發問」陷阱 — 使用者已經猜了根因（DB），需要 agent 反過來引導實測。
  - 既有 `gstack-investigate` 是通用 debug，`gstack-benchmark` 偏向「這段 code 多快」；都沒有針對 **三層分流（前端 render / 後端處理 / DB 查詢）** 的決策模板。
  - 既有 `sqlite-to-postgres` 假設「決定已下、開始遷移」；缺一個 **前置決策** skill。CLAUDE.md 的「Right-size infra」rule 已涵蓋部分理念（≤10k rows / ≤20 users 留在 SQLite），但缺乏可操作步驟。
  - 流程建議：（1）量化端到端時間（瀏覽器 DevTools Network）；（2）拆 DB 查詢時間（EXPLAIN QUERY PLAN / `time` 包查詢）；（3）拆後端處理時間（log timestamp 或 `cProfile`）；（4）拆前端 render（React Profiler / Performance tab）；（5）對照「右尺寸基準」決定方向（加索引 / 加快取 / 拆 N+1 / 升 DB / SSR / 換框架）。
- **與既有 skill 的關係**：可作為 `gstack-investigate` 的 perf-domain 子流程；觸發後若決定遷移 DB，再交棒給 `sqlite-to-postgres`；若是查詢問題，可呼叫 `db-migration` 加索引。
- **保留意見**：n=1 occurrence，需再觀察 1–2 次同型對話確認模式存在。可先列入 watchlist，不急著建立 skill；下次再出現時直接 promote。

---

### ⚪ Weak：（無）

- Session 1（ChimesFlow）只有 Bash 工具痕跡，沒有可解讀的 user intent 或檔名語意，無法萃取模式。建議在後續 session 出現相同 project 時再回看。

---

## 既有 skill 使用驗證

- **investment-research** — Continuous Mode 在 news-stock 專案正常運轉，產出 daily report + portfolio-state，無新增需求。
- **crm-projection** — sales-assistant 中正常產生 `INDEX.md` + `projection.md`，符合設計。

兩者都不需改動，但可作為「skill 確實被使用」的證據點，下次 `workflow-retro` 可引用。

---

## 行動建議

1. **不建立新 skill**：本批訊號太薄。把 `perf-bottleneck-triage` 列為 watchlist 候選，等下次同型對話再 promote（目標：2026-05 月底前 review）。
2. **既有 CLAUDE.md「Right-size infra」rule 可強化**：考慮在該條補充「先測量再決策」的 micro-flow（end-to-end 時間 → 拆 DB / backend / frontend），讓 agent 在使用者直接問「該換 DB 嗎」時不會跳到結論。這是 **rule-level 修補** 而非新 skill。
3. **ChimesFlow 專案 instrumentation**：下次 session 啟動時若 intent 為空，主動詢問或記錄 task description，避免後續 harvest 看到黑盒。
