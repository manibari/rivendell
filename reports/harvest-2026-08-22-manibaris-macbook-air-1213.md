## Session Harvest 報告 — 2026-08-22

**結論先講**：4 個 session 裡沒有新 skill 缺口。3 個屬於既有 skill/agent 正常運作的證據；1 個（Urd-WMS 新產品籌建，592 則訊息）抓到一個**既有 skill 的觸發飄移案例**——`spine-auth`／`spine-rbac` 明明命中觸發詞卻沒被叫到，值得記錄但不構成新 skill。

---

### 一、Session 摘要

| # | 專案 | 訊息數 | 關鍵活動 | 產出/素材 |
|---|------|--------|----------|----------|
| 1 | Peter's Work Vault | 52 | 立積電子案交付盤點：讀 `cache/data-intake-2026-08-16/盤點報告.md`、更新 `STATE.md`；被中斷後轉向調查「原廠經銷授權書」該不該併入 ChimesFlow 既有合約範本引擎（查了 `contract-templates` / `generated-documents` API 與對應 alembic migration） | 授權書 PDF、ChimesFlow API 查詢紀錄 |
| 2 | rivendell | 1 | `sk-token-analysis-cron` 排程 agent 產出 2026-08-21 token 用量日報（既有機制） | 對應 `reports/token-analysis-2026-08-21.md` |
| 3 | sales-assistant | 19 | 執行既有 `crm-projection` skill，查 `nx_client` + deal pipeline 交叉比對 | — |
| 4 | code（新專案 Urd-WMS） | 592 | 從 Norns-ERP M7 拆出獨立輕量產品「包材批次 WMS：影像辨識領用 + FIFO 稽核 + 追溯 + 提醒」。依序呼叫 `requirement` → `claude-api`（vision 查詢）→ `chimesflow-design` 三個 skill，實作 Next.js app（port 3071），用 `claude-in-chrome` 直接操作瀏覽器跑收貨建批／領用登錄／PIN 登入測試（兩個 tab 分飾 operator 角色） | 手機拍照包材照片、螢幕截圖、design-system 檔案 |

---

### 二、Skill 候選

#### Session 1（Peter's Work Vault）→ 不構成候選，證據太薄

被使用者中斷（`[Request interrupted by user for tool use]`），只留下「相關功能你要不要去 chimesflow」這句路由提問後的調查片段。N=1、且結論未定，看不出可重複的步驟序列，不下判斷。

#### Session 2（token-analysis）、Session 3（crm-projection）→ 已是既有機制，非候選

排程 agent 與既有 skill 正常運作的證據，不是缺口。

#### Session 4（Urd-WMS 新產品籌建）→ **Weak**：既有 skill 觸發飄移，非新 skill 缺口

實際翻了對話（非只看摘要）。路由大致正確：`requirement`（i=~0）→ `chimesflow-design`（「Urd-WMS 現場平板領用畫面」，符合 `.claude/CLAUDE.md` UI Feature 流程 Step 3 的 HARD GATE）→ `claude-api`（vision/結構化 JSON 輸出參考）都有照規則被叫到。

但在 i=1141 使用者說「對，做 RBAC」後（i=1146），agent 直接手刻 PIN 登入（現場共用平板、戴手套快速換人的考量），改 `backend/app/db.py`、`backend/app/main.py`，**全程沒有呼叫 `spine-auth` 或 `spine-rbac`**。核對這兩個 skill 的 SKILL.md frontmatter：

- `spine-auth` 觸發詞明寫「標配 FastAPI + Postgres 產品」「standing up a new fleet product that needs users」「登入」——Urd-WMS 正是新 fleet 產品要建使用者登入，理論上該觸發。
- `spine-rbac` 觸發詞「加角色/權限/RBAC/給人用要分權限」——「對，做 RBAC」這句話字面上就命中。

沒觸發不代表 spine-auth 的方案就是錯的：PIN 碼（共用平板快速換人）跟 spine-auth 現有的 JWT+bcrypt+Bearer 政策核心本來就是不同的落地模式，spine-auth 目前的 divergent policy 清單（single vs refresh token、tenant claim、RBAC tier）裡沒有涵蓋「現場共用裝置 PIN 登入」這個變體。這比較像是**該不該把「共用裝置 PIN 登入」補進 spine-auth 的政策選項**，而不是開一個新 skill——先記一筆，等下一次同類（IoT/廠務/現場平板類產品）出現共用裝置登入需求時，若又是繞過 spine-auth 手刻，再考慮動手擴充。

---

### 三、結論與建議

- 本次沒有新 skill 候選要開。
- 唯一值得追蹤的訊號：`spine-auth` 在「新 fleet 產品建使用者登入」這個明確命中觸發詞的情境下沒被叫到，改成手刻 PIN 登入。建議：(a) 觀察下次現場平板/共用裝置類產品是否重複這個模式；(b) 若重複出現，把「共用裝置 PIN 登入」補進 `spine-auth` 的 divergent policy 選項，而不是開新 skill。
- Session 1 因中斷而證據不足，未追蹤；Session 2、3 是既有機制正常運作。
