# Session Harvest — 2026-07-21（20 場近期 session 摘要分析）

## 一、Session 摘要

| # | 專案 | 訊息數 | 關鍵活動 |
|---|------|--------|----------|
| 1 | MingOS-engine | 9 | 確認「引擎開發」責任範圍；用了 EnterWorktree，內容過短無法判斷完整 workflow |
| 2 | Verdandi-AutoML | 28 | 研究 JMP Essentials 文件站，10 個 Agent 子代理平行抓取 + WebFetch，彙整成 `jmp-learning-library.md`，用 SendUserFile 交付 |
| 3 | Verdandi-AutoML | 88 | 長時間除錯：Monitor 追蹤 venv 重建進度、大量 Bash/Read/Edit，修改 `CovaryChart.tsx`／`covary.py`，用截圖 `covary_check.png` 驗證 |
| 4–19 | mops-dbs-services-mops-notes | 各 1–5 | **16 場幾乎逐字重複**的請求：貼上台灣『前十大股東相互間關係表』(F17) 原始文字，要求抽成固定欄位的 JSON 陣列（name/self_shares/self_pct/…） |
| 20 | mops-dbs | 10 | 純 Bash 操作，無法從摘要判斷意圖 |

**總計**：157 訊息、4 專案、成本近乎 0（多為短互動）。最大訊號是 #4–19：同一個 prompt 被貼了 16 次，且幾乎沒有任何工具呼叫——代表這是純聊天室內完成的手動流程，尚未被自動化收斂。

---

## 二、Skill 候選

### 🟢 Strong — `mops-shareholder-relation-extract`

- **用途**：把台灣上市櫃公司『前十大股東相互間關係表』(F17) 的原始文字，穩定抽成固定 schema 的 JSON 陣列（`name` / `self_shares` / `self_pct` / `spouse_child_pct` / `nominee_pct` / `related_name` / `related_relation` / `is_representative`）。
- **觸發詞**：「抽 F17」「前十大股東相互間關係表」「股東關係表轉 JSON」，或使用者貼出含「前十大股東相互間為關係人」字樣的文字段落。
- **分類**：backend / data-extraction
- **理由**：
  - 16 場 session 用**逐字相同**的長 prompt 手動貼上，Tools 欄幾乎全空——沒有經過任何 skill 或腳本，純靠使用者每次重打/複製同一段指令，容易漏欄位或打錯字（浪費 token 且不一致）。
  - 已確認 `mops_dbs/services/mops_notes/sync/shareholder_llm.py` 存在幾乎相同的 prompt（`_PROMPT` 常數），並透過 `claude --print` 呼叫、有 code-fence 清除 + JSON 陣列擷取的容錯邏輯——代表這是**已被驗證有效、只是還沒收斂成可重複呼叫的介面**的模式。這 16 場互動很可能是在手動測試/微調同一份 prompt，而非走批次管線。
  - 收成一個 skill 的價值：(a) 統一 schema 定義，不必每次重打；(b) 內嵌現有腳本已驗證過的容錯處理（code fence 清除、JSON 陣列正則擷取）；(c) 在 skill 內註明「批次回填用 `shareholder_llm.py --limit N`，單筆/臨時驗證才用這個 skill」，避免使用者不知道已有批次工具而持續手動貼字。
  - 現有 skill 皆不覆蓋：`mops-financial-scraper` 明確 SKIP 董監事/股東查詢；`tw-company-lookup` 只查登記資料（負責人/董監事），不處理 F17 相互關係表這種特定申報格式的文字解析。

### 🟡 Moderate — `background-build-visual-verify`（暫定名，證據不足需再觀察）

- **用途**：長時間背景建置（如 venv 重建）時，用 Monitor 追蹤進度、日誌，收斂後對修改的前端元件做 headless screenshot 驗證，再繼續除錯。
- **觸發詞**：待觀察，目前僅 1 場 88 則訊息的 session 支撐，細節（實際失敗點、修法）在摘要裡看不到。
- **分類**：quality / debugging
- **理由**：Session #3 呈現「Monitor 背景任務 → Bash/Read/Edit 修正 → 截圖驗證」的組合，但這與現有 `gstack-investigate`（系統化除錯）、CLAUDE.md 全域規則裡的「截圖驗證」慣例（Diagram & Slide Output Defaults 段）高度重疊。**建議先不新增 skill**，改成下次遇到類似 venv/建置類除錯時，觀察是否真的是 gstack-investigate 涵蓋不到的獨立步驟（例如 Monitor 工具在長背景建置的特化用法）。目前證據（1 場、無失敗細節）不足以獨立成 skill。

### ⚪ Weak — 「文件站 → 知識庫 markdown」研究彙整（JMP Essentials 案例）

- **用途**：多個 Agent 子代理平行抓取文件站各分類頁面，彙整成單一 markdown 知識庫文件並交付。
- **理由**：這個模式**已被 `deep-research`／`autoresearch` 一類的既有 skill 覆蓋**（多來源 fan-out + WebFetch + 綜合成報告）。Session #2 的操作（10 個 Agent 平行、WebFetch、SendUserFile）與 `deep-research` 的設計高度吻合，不建議重複造輪子。若之後這類「特定文件站 → 結構化知識庫」的需求重複出現且有特化步驟（例如固定分類法、固定輸出格式），再評估是否值得從 `deep-research` 分裂出專用 skill。

### 不成候選

- Session #1（MingOS-engine, 9 則）、#20（mops-dbs, 10 則 Bash-only）：訊息量太少、摘要無意圖文字，無法判斷可重複的 workflow，暫不列入。

---

## 三、建議行動

1. **優先**：把 F17 股東關係表抽取邏輯收斂成 skill（或至少是 `mops_dbs` 專案內的 slash command / 固定 prompt 模板），終結「同一段長 prompt 手貼 16 次」的浪費。可直接沿用 `shareholder_llm.py` 裡 `_PROMPT` 常數與 code-fence 清除邏輯作為 skill 的核心內容，確保介面互相一致。
2. 觀察後續是否再出現長背景建置＋截圖除錯的重複模式，證據足夠再造 skill。
3. 研究彙整類任務優先導向既有 `deep-research`／`autoresearch`，不新增重複 skill。
