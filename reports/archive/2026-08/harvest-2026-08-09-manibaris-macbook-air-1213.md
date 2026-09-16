# Skill Harvest 報告 — 2026-08-09（跨專案：PTI-ARES-Main / rivendell / sales-assistant）

> 補充說明：今日排程 harvest 未產出正式報告（僅留下空的
> `reports/harvest-2026-08-09-error.log`），本報告為互動 session 手動補跑，沿用
> `harvest-2026-08-07.md` 的格式。

## 一、Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|-------|---------|
| 1 | PTI-ARES-Main | 43 | `/model` 切換後，走 `chimesflow-design` + `user-flow` 產出板圖模組的 `docs/design-contract.md`（ChimesFlow SoT + mode (b) override）與 `docs/flows/intake-to-viewer-flow.md`，並留下 `findings.md`（`planning-with-files` 產物） |
| 2 | rivendell | 77 | 詢問「有沒有 YouTube 紀錄相關 skill」，確認缺「訂閱／自動追蹤頻道」後，當場建出 `skills/media/channel-scraper`（`feed_scan.py` + SKILL.md + README 更新），並跑一次 e2e 驗證 |
| 3 | rivendell | 1 | 單則 prompt：以 2026-08-07 各專案 token 花費 + 當日使用者指令取樣為輸入，產出繁體中文 token 用量日報 |
| 4 | rivendell | 1 | 同上，換成 2026-08-09 的資料 |
| 5 | sales-assistant | 18 | 正常執行既有 `material-health` skill：掃 `materials/` 缺 frontmatter、過期補助、過期公司資訊、孤兒檔，寫出 `HEALTH_REPORT.md` |
| 6 | sales-assistant | 22 | 正常執行既有 `crm-projection` skill：查 `nx_client` 活躍客戶 + `nx_deal` pipeline，比對 customer-intel，寫出 `projection.md` |
| 7 | sales-assistant | 17 | 同一 skill 再跑一次，過程中把臨時腳本固化成 `scripts/_crm_projection_run.py`（原本用完即丟，這次留在專案裡），並更新 `INDEX.md` |

工具分佈：Bash(95)、Read(17)、Edit(16)、TaskUpdate(8)、Write(7)、TaskCreate(5)、Skill(4)、AskUserQuestion(3)、ToolSearch(3)、WebSearch(1)。

已核對 `/Users/manibari/code/rivendell/skills/`（現有清單）：`chimesflow-design`、
`user-flow`、`planning-with-files`、`channel-scraper`、`material-health`、
`crm-projection` 均已存在且被正確呼叫。無與 `.learnings/FEATURE_REQUESTS.md`
重複的候選。

**結論先說：今天沒有 Strong/Moderate 候選。** 七個 session 全部落在既有 skill
覆蓋範圍內——Session 2 甚至是在本 session 內把缺口（channel-scraper）補上並已
出貨，其餘五個 session 都是既有 skill 的正常呼叫或既有自動化的重複輸出。

---

## 二、Skill 候選

### 🔴 Weak — 不建議新增

- **Session 1（PTI-ARES 架構規劃）**：走的是 `chimesflow-design`（HARD GATE）→
  `user-flow` → `planning-with-files` 既定路徑，產出的 `design-contract.md` /
  `intake-to-viewer-flow.md` 正是這兩個 skill 該產出的標準檔案，非新模式。
- **Session 2（channel-scraper 建置）**：這就是本次 harvest 週期內「發現缺口
  → 建 skill」的正常流程，缺口已經補上（`skills/media/channel-scraper`），
  不需要再開一張候選單。
- **Session 3、4（token 用量日報）**：單則 prompt、n=1，且已有 `bin/sk-harvest-summarize`
  / `bin/sk-token-analysis-cron` 產出同類每日 token 花費報告（見
  `reports/token-analysis-*.md`），今天出現兩次只是同一個排程輸出被跑了兩天
  份，屬既有覆蓋範圍，非新模式。
- **Session 5（material-health）／Session 6、7（crm-projection）**：都是既有
  skill 的正常呼叫。唯一值得記一筆的訊號是 Session 7 把原本用完即丟的臨時腳本
  固化成 `sales-assistant/scripts/_crm_projection_run.py`——這代表 `crm-projection`
  skill 本身可能該把這支 runner 收進 skill 的 `scripts/` 資產、而不是讓消費端
  repo 每次重造一次；這是「改善既有 skill」的維護項，不是新 skill 候選。

---

## 三、建議下一步

1. 無新 skill 需求。
2. （選做）檢查 `~/.claude/skills/crm-projection` 是否該內建
   `scripts/crm_projection_run.py`，取代目前由消費端 `sales-assistant/scripts/`
   自行維護的作法，避免同一支腳本在不同 repo 各自漂移。
3. 排查今天 `sk-harvest-cron` 為何只留空的 error log、沒有產出正式報告（同一問題
   `harvest-2026-08-07.md` 也記過一次，若連續發生建議直接修排程而非每次手動補跑）。
