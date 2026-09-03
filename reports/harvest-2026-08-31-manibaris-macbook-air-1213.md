# Session Harvest Report — 2026-08-31

## Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|--------|----------|
| 1 | Vault-Peter-Work | 24 | 光泉地端 vs 部署模型健康度比對（ToolSearch→Bash 查台帳/對照表→Chrome 開部署站→寫結論） |
| 2 | Vault-Peter-Work | 74 | 冰水系統節能 SI 檢查表 deck（讀既有簡報→列條件/資料需求→寫 checklist md→截圖驗證） |
| 3 | ChimesFlow | 17 | SSH 進 CRM/SEP server 盤點內容，寫成 `crm_sep_server_ssh.md` |
| 4 | ChimesFlow | 66 | 8/24–9/4 工作日誌：使用者口述時段→AI 結構化→Chrome 自動化填入 ChimesFlow 工作日誌頁面 |
| 5 | sales-assistant | 1 | 觸發 `crm-projection` skill（既有 skill，非候選） |
| 6 | sales-assistant | 1 | 觸發 `subsidy-scraper` skill（既有 skill，非候選） |

---

## Skill 候選

### 🟢 Strong — `worklog-entry`（暫名）

- **用途**：把使用者口述的「幾點到幾點做什麼」時間表，轉成結構化日誌條目，並透過瀏覽器自動化填入 ChimesFlow 工作日誌頁面（`page.tsx` 對應的表單）。
- **觸發**：「我要寫 8/24~9/4 的日誌」「幫我補工作紀錄」「填工作日誌」等，使用者接著會逐日口述時段。
- **分類**：workflow（也可能落在 ChimesFlow repo 自己的 `.claude/skills/`，而非 rivendell — 需依「Skills domain boundaries」規則判斷歸屬）。
- **理由**：
  - Session 4 佔了本批次最多訊息（66則）與最多 Bash 呼叫（35），且明確重複同一序列：解析口述時段 → 寫暫存結構（`worklogs.jsonl`）→ Chrome computer 操作逐筆填表（9次）。這是典型「同序列重複出現」訊號。
  - 現有 `context-journal` skill 記錄的是 **Claude 工作階段** 的日誌，跟這裡「使用者本人的行事曆式活動日誌」是不同對象，不衝突、不重疊。
  - 檢查過 rivendell/skills 全庫，找不到現成的 worklog/日誌填寫 skill。
  - ⚠️ 落地前建議先確認：這個模式未來還會重複幾次？如果只是本次補記過去兩週日誌的一次性任務，價值會下降到 Moderate。

### 🟡 Moderate — `server-recon`（暫名，SSH 伺服器盤點）

- **用途**：SSH 進一台不熟悉的伺服器，系統性盤點上面跑什麼服務/設定/用途，輸出成一份 markdown 文件（如本次的 `crm_sep_server_ssh.md`）。
- **觸發**：「你可以 ssh 連到 X」「上面有什麼」「幫我盤點這台機器」。
- **分類**：workflow / meta。
- **理由**：
  - 這類「接手陌生基礎設施、先摸清楚再動手」的需求在 solo-dev + 多產品線（Fleet infra spine）情境下有機會重複發生，且產出格式（服務清單、config 路徑、用途說明）具備可模板化的骨架。
  - 但本次只出現 1 次（17 則訊息、12 次 Bash），樣本數不足以確認是穩定重複模式，先列 Moderate、待下次同類任務出現再確認要不要真的建立 skill。
  - 現有 skill 中沒有對應項目（`repo-rename`、`env-doctor` 都是相近但目標不同的基礎設施類 skill）。

### 🔴 Weak — 光泉地端/部署模型健康度比對

- **理由不建 skill**：這是特定客戶（光泉 / kuangchuan-bi）、特定模型部署平台的一次性診斷，資料格式（`對照表_同尺.csv`、`模型台帳.csv`）綁死在該客戶專案裡，通用性低。若未來同類需求（比對本地 vs 雲端部署健康度）重複出現在**其他客戶**身上，才有必要抽象成 skill；現階段屬於 `ml-model-registry` skill 或客戶專案自己的文件範疇即可涵蓋。

### 🔴 Weak — 冰水系統節能 SI 檢查表

- **理由不建 skill**：這是領域知識（冰機效率監控、溫濕度條件、水質/濾網檢查項目）+ 既有 skill 組合（`iot-factory-report` 提供 IoT 分析能力、`sales-deck-design`/`chart-design` 提供 deck 產出能力），流程本身沒有新的工具序列可抽出。真正有價值沉澱的是「檢查表內容」本身，這類領域知識更適合存成 reference 文件（例如 `knowledge/` 或該客戶素材庫），而不是新增流程型 skill。

---

## 小結

本批次唯一明確達到「重複多步驟工具序列」門檻的是 **工作日誌填寫（worklog-entry）**；伺服器盤點列為觀察中的 Moderate 候選，其餘兩個屬於一次性客戶任務或既有 skill 已覆蓋，不建議新增。
