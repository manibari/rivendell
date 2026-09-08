# Session Harvest — 2026-09-05

## 摘要

11 個 session、約 285 則訊息、涉及 5 個專案（PTI-ARES、Verdandi-AutoML、rivendell、sales-assistant、無專案根目錄）。掃過一輪後**沒有找到值得新建 skill 的強訊號**——多數活動不是已有對應 skill 在跑（`sales-crm-projection`、`gov-subsidy-scraper`、`chimesflow-design`+`frontend-design` 組合），就是單次出現、樣本不足以判斷是否會重複。以下列出觀察與候選，誠實標註信心等級。

## Session 摘要

| # | 日期* | 專案 | 訊息數 | 主要活動 |
|---|------|------|-------|---------|
| 1 | 2026-09-04 | PTI-ARES | 70 | 啟動前後端 dev server，用 Chrome DevTools 現場查系統日誌頁面的分頁上限與跨使用者可視範圍（RBAC 邊界問答） |
| 2 | 2026-09-04 | Verdandi-AutoML | 71 | agentic-driver Phase 4 設計討論：domain template 要不要當 MCP resource、多租戶使用者怎麼上傳知識庫 |
| 3 | 2026-09-04 | rivendell | 1 | 產生 token 用量分析日報（已有排程 agent 產出，見 `reports/token-analysis-*.md`） |
| 4 | 2026-09-04→05 | rivendell | 6 | 從近期 session 摘要更新實體知識庫（人物/公司/專案事實）— knowledge-graph 既有流程 |
| 5 | 2026-09-04 | rivendell | 1 | 同上，另一批 session 摘要的知識庫更新 |
| 6 | 2026-09-04 | rivendell | 1 | token 用量日報（同 #3 的重複觸發） |
| 7 | 2026-09-04 | sales-assistant | 15 | 執行 `crm-projection`（改名前）：查 `nx_client`/deal pipeline 交叉比對 |
| 8 | 2026-09-04 | sales-assistant | 20 | 執行 `sales-crm-projection`（改名後同一支 skill） |
| 9 | 2026-09-04 | sales-assistant | 36 | 執行 `subsidy-scraper`（= `gov-subsidy-scraper`）：爬 grants.nat.gov.tw / SBIR / SIIR 並去重 |
| 10 | 2026-09-04 | (無專案根) | 25 | 從 Google Drive 抓設計參考圖，跟現有儀表板（立特冰機）畫面截圖比對差異 |
| 11 | 2026-09-04 | (無專案根) | 39 | 人流疏散應用架構討論 + 用 `chimesflow-design`→`frontend-design` 產出聯絡頁面 mockup |

\* 日期為原始摘要中的相對敘述，已盡量對齊 2026-09-04/05；session 本身未附精確時間戳。

## Skill 候選

### 1. （無新建議 — Weak）Live-app 行為問答（PTI-ARES session #1）
- **觀察**：啟動 dev server → Chrome DevTools 現場操作 → 回答「日誌只能看六頁嗎」「能看到其他使用者的操作紀錄嗎」這類**唯讀行為查證**問題，不是在修 bug、也不是在做 UI 視覺 QA。
- **是否新建**：**不建議**。這個模式跟既有 `gstack-investigate`（bug root cause）、`gstack-browse`（headless QA）、`qa-dataflow`（資料流驗證含權限閘門是否擋得住）都有重疊，且只出現 1 次，看不出穩定的工具序列（40 次 Bash + 12 次 chrome js_tool，步驟隨問題即興變化）。**評級：Weak**——先觀察是否再出現同型態問題（"這個功能實際上限制到哪" 類），出現 2 次以上再考慮是否要包成 `qa-dataflow` 的一個子模式，而非獨立 skill。

### 2. 參考設計圖 vs 現有畫面比對（session #10）
- **名稱**：`design-reference-diff`（暫名，若成案）
- **目的**：從 Google Drive 抓設計參考圖／guide sheet，跟目前實作的畫面截圖並排比對，抓出落差（缺元件、配色不符、佈局跑掉）。
- **觸發**：使用者丟一個 Drive 連結當「這是設計稿/guide」，同時要求跟目前的頁面比對。
- **類別**：`docs` 或 `frontend`
- **評級：Weak**——只出現這一次，且和既有 `gstack-design-review`（比對 design system tokens）、`ui-ux-pro-max` 有功能重疊，差異只在「參考來源是 Drive 上的截圖而非 design system 文件」。單一樣本不足以判斷這是穩定需求還是一次性任務，**建議先觀察，不建新 skill**。

### 3. （無新建議）CRM projection / subsidy scraper 重複執行
- Session #7、#8、#9 都是**既有 skill 的正常排程/手動執行**（`sales-crm-projection`、`gov-subsidy-scraper`），不是新模式。唯一值得記的觀察：#7 用的路徑是 `/Users/manibari/.claude/skills/crm-projection`，#8 是 `/Users/manibari/.claude/skills/sales-crm-projection`——兩者是改名前後的同一支 skill，非重複建設，符合 `.claude/CLAUDE.md` 的 skill naming v2 收斂工作（sales loop 已完成該次 rename）。

### 4. （無新建議）token 用量日報、entity 知識庫更新
- Session #3/#6（token 分析）與 #4/#5（entity 知識庫）都是 rivendell 既有排程 agent 的產出過程，本身就是自動化基礎設施在跑，不是「手動重複做的事」，不構成 skill 候選。

## 結論

這批 11 個 session **沒有 Strong 候選**，Moderate 也沒有——最接近的兩個觀察（live-app 行為問答、參考圖 vs 實作比對）都只出現 1 次，且與既有 skill（`gstack-investigate`/`qa-dataflow`/`gstack-design-review`）功能重疊，貿然新建只會增加維護負擔而非填補真空。建議：不新建 skill，把這兩個觀察記下來，等下次出現同型態任務時再評估是否要收斂成既有 skill 的子模式，而非獨立 skill。
