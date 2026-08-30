# Session Harvest 報告 — 2026-08-28

## Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|--------|----------|
| 1 | Vault-Peter-Work（立積電子交付案） | 104 | 對話收集 PAD/RPA 客戶技術現況（版本、觸發機制）→ 寫需求評估與方案說明 v0.2 → 產出觸發鏈路架構圖 → 產生簡報素材（contact sheet、design-system.css） |
| 2 | rivendell | 1 | 讀每日 token 花費資料 → 產出繁中日報 |
| 3 | sales-assistant | 19 | 執行既有 `crm-projection` skill：查 nx_client/deal → 交叉比對 customer-intel → 寫 projection.md、重建 INDEX.md |
| 4 | sales-assistant | 33 | 執行既有 `subsidy-scraper` skill：爬三個政府補助來源 → 去重 → 寫/歸檔補助檔 → 重建 INDEX.md |

**先排除 3、4**：兩者都是既有 skill（`crm-projection`、`subsidy-scraper`）依 SOP 執行，沒有偏離腳本的新模式，是「skill 用得對」的證據，不是新候選。

**先排除 2**：查了 `rivendell/reports/token-analysis-*.md`，這個每日 token 用量分析**已經是排程 headless agent 在跑**（2026-07-05 至今每天一份，含 error log），session 2 只是那次執行的其中一筆記錄。不是新模式。

真正有新模式的只有 **Session 1**。

---

## Skill 候選

### 1. 〔Strong〕`rpa-chat-trigger-spec`

- **用途**：為「對話機器人（AI Agent）收集意圖關鍵字 → 觸發客戶既有 RPA（Power Automate Desktop 等）流程」這類整合案，提供一份可重複套用的**架構設計骨架 + 三條硬性設計原則**，而不是每次重新想。從 Session 1 實際交付內容（`需求評估與方案說明_v0.2.md`）萃取出的骨架：
  ```
  對話式前端 → AI Agent（關鍵字擷取→依權限列候選 flow）
    → 【人】選定 flow（人在迴圈，不自動觸發）
    → AI Agent 補齊參數→摘要確認
    → Workflow API（權限檢查／Catalog／Run History／Approval／Audit）
    → 觸發通道 → 客戶 RPA 主機（CLI 或 HTTP trigger）→ 既有 flow
  ```
  三條設計原則：(a) 權限矩陣在主鏈路上（角色 × flow）(b) 人選定，AI 不代為觸發 (c) 排程與對話觸發共用 run history/audit。
- **觸發時機**："RPA 整合"、"串接 Power Automate/PAD/UiPath"、"對話觸發流程"、"AI agent 觸發既有系統"、客戶来信只給「現有 RPA 現況」要求評估整合方案時。
- **分類**：business（domain reference，同 `odb-dfm-reference` 的性質 — 領域知識骨架，不是通用程式碼庫）。
- **理由**：
  - 這不是一次性需求。用 `grep -rl "RPA\|Power Automate\|PAD"` 掃 Vault 發現至少 3–4 個案子（立積電子、光泉、上旺）都摸到 RPA/PAD 整合，代表這類 presales/scoping 場景會重複出現。
  - Session 1 花了 104 則訊息、6 次 SendUserFile 才把「我方只做這一段、其他不碰」的邊界劃清楚 —— 這正是最容易在下一個案子重新繞一次彎路的地方。把邊界宣告 + 三條原則 + 架構骨架固化成 skill，下次可以直接套用再依客戶現況微調，省掉重新 negotiate scope 的來回。
  - 與既有 `rbac-permissions`（通用全端 RBAC 實作）不重疊：那個是給工程師寫 decorator/AuthGuard 的實作骨架；這個是給業務/顧問畫 **presales 方案邊界**與**人在迴圈設計原則**的骨架，屬於不同層次。

### 2.〔Weak〕無新候選 — Session 2–4

- Session 2（token 日報）已有排程 agent 在跑，不必再造。
- Session 3、4 是既有 skill 的常規執行，工具序列（Bash 查詢 → 交叉比對 → Write → 重建 INDEX）完全符合各自 SKILL.md 定義的 SOP，沒有需要新抽的模式。

---

## 建議下一步

只有 1 個 Strong 候選（`rpa-chat-trigger-spec`）。要幫你用 `skill-creator` 建立這個 skill 嗎？
