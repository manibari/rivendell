# Session Harvest Report — 2026-08-03（跨專案：ChimesFlow / sales-assistant / code）

## Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|-------|---------|
| 1 | ChimesFlow | 24 | `quote-export.ts` 報表匯出對齊問題除錯，用 repro.png/repro-fixed.png 前後截圖驗證修復 |
| 2 | sales-assistant | 54 | 執行既有 `subsidy-scraper` skill，爬 grants.nat.gov.tw / SBIR / SIIR，dedupe 後寫入補助項目 md |
| 3 | sales-assistant | 19 | 執行既有 `crm-projection` skill，投影 `nx_client`/`nx_deal` 到 `materials/clients/` |
| 4 | code | 34 | 看完 Matt Pocock「grill-me」skill 解析影片後，反思是否自建 RBAC / 監控 / roadmap 系統，並討論是否該精簡 gstack 邏輯 |
| 5 | code | 9 | 同一支 Matt Pocock 影片的逐字稿摘要說明 |
| 6 | code | 190 | 讀一遍 `github.com/manibari/matt-skills` → 套用其 skill 評估 ChimesFlow 架構 → 產出 `architecture-review-chimesflow.html` + 重構順序計畫 |
| 7 | code | 22 | 類 excalidraw 架構圖工具的需求發想，走 `requirement` + `gstack-office-hours` |

工具分佈：Bash(260)、Read(23)、Edit(14)、Write(11)、AskUserQuestion(6)、Skill(4)。

## 跨 Session 觀察

1. **Session 2、3、7 都是既有 skill 的正常執行**（subsidy-scraper、crm-projection、requirement/gstack-office-hours），沒有新 pattern。
2. **Session 4、5 是同一素材的兩階段消費**：先轉錄摘要（video-transcript 範疇），後續在另一個 session 拿摘要做策略反思（office-hours 範疇）。兩端都有既有 skill 覆蓋，只是分屬不同 session，非缺口。
3. **Session 6 是本輪唯一有新意的模式**：匯入外部 skill repo 後，沒有停在「介紹/評估這些 skill 好不好」，而是**直接拿它的評估邏輯來審自己的專案**，產出 HTML 報告 + 重構優先順序清單。這一步目前落在 `skill-scout`（discover/evaluate/port，描述停在「匯入」）與 `github-repo-audit`（審自己的 repo，但用的是 rivendell 自己的評分邏輯，不是「套用剛匯入的外部 skill」）的中間地帶。
4. **Session 1 的截圖前後對照除錯**，已經是 CLAUDE.md「生成圖後自我截圖檢查」規則的既有實踐，只是這次用在 debug 而非畫圖，單次 24 msgs，不構成新 skill 的證據量。

## Skill 候選

### 🟡 Moderate — `skill-import-and-apply`（匯入即套用）

- **目的**：把 `skill-scout` 匯入的外部 skill（尤其是審查/評估類）在同一輪立刻套用到當前專案，產出評分報告 + 優先順序行動清單，把「匯入」到「拿來用在自己身上」的斷點接起來。
- **觸發**：「這個 skill 拿來評我的專案」「用剛匯入的 skill 看一下 X 專案」，或 `skill-scout` 匯入完成後緊接著的評估請求。
- **類別**：meta（與 skill-scout 同層，銜接而非取代）
- **理由**：Session 6（190 msgs，本輪最大量）完整走過一次，且產出具體交付物（architecture-review-chimesflow.html、重構順序 md）。但目前只有 1 個資料點，且與 `skill-scout` + `github-repo-audit` 有職責重疊——建議先觀察下次是否再出現同型任務（匯入外部 skill → 立即套用評估自己），若再發生一次再決定是獨立成 skill，還是把「匯入後追加套用」寫進 `skill-scout` 的流程步驟即可（後者成本更低）。

### 🔴 Weak — `visual-repro-diff`（截圖前後對照除錯）

- **目的**：UI/報表匯出類 bug 修復時，固定用 repro 前後截圖對照確認修復生效。
- **觸發**：畫面/匯出對齊類 bug 修復。
- **理由**：Session 1 只有 24 msgs、單次發生，且本質上已被 CLAUDE.md「生成圖後自我截圖檢查」規則覆蓋，只是應用場景從畫圖延伸到 debug。**建議不成立新 skill**，維持現有規則涵蓋即可。

## 結論

本輪 7 個 sessions 中，4 個是既有 skill 的正常重跑（無新 pattern）、2 個是同素材的既有 skill 分段消費、1 個（Session 6）產生了唯一有新意但證據量不足的候選。**沒有 Strong 候選**，1 個 Moderate（`skill-import-and-apply`，建議再等一次同型實例）、1 個降級為既有規則覆蓋（不建議新增 skill）。無與現有 138 個 skills 重複的新建議。

未寫入 `reports/`：依專案規則，`reports/*` 由排程 agent 專屬產出，互動 session 中的即席分析以對話回覆呈現即可。
