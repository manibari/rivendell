---
date: 2026-05-31
iso_week: 2026-W22
period: 2026-05-24 to 2026-05-31 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W22

## TL;DR

本週 **infra 健康度明顯回升**：watchdog log 整週只有 1 次 FAIL、0 次 RESTART/ESCALATE（W20 是 80+ 行、8 RESTART），W20 最擔心的 5/12 API outage 那一類事件**沒有重演**；`crm-projection` agent 也從 exit 1 修回 exit 0。本週工作量本身很大（7 天 ~$10.5k token、約 64 sessions，是 W20 的 3.6×），但系統穩穩接住了。

真正的問題不在系統、在 **retro 機制自己**：W20 把「退休 `knowledge-graph`」設成最低成本、最高象徵性的 dogfooding 測試，明文寫「下週若仍未動就暫停 retro」——W21 確實被跳過（無檔案），而本週 `skills/meta/knowledge-graph` **依然在原地、依然 0 觸發**。最便宜的那個 action 已經連續 3+ 次 retro 沒被執行。這是本週最重要的 finding，比任何 infra 數字都重要。

## 使用度

本週共 18 個 skill 觸發（usage API 追蹤範圍內）。

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+) | `crm-projection` (5) | — |
| 中頻 (3-4) | `requirement` (4)、`planning-with-files` (3)、`gstack-plan-eng-review` (3) | — |
| 低頻 (1-2) | `workflow-retro` (2)、`session-harvest` (2)、`ship` (2)、`office-pptx`、`session-wrap`、`repo-rename`、`candidate-analysis`、`subsidy-scraper`、`material-health`、`office-docx`、`slide-office-hours`、`gstack-codex`、`gstack-spec`、`rbac-permissions` (各 1) | 10/16 exit 0；6 exit 1（`research-agent`、`research-agent-weekly`、`doctor`、`harvest`、`janitor`、`material-health`） |
| 沉寂 (30+ days) | `auto-stage` (33d, **誤報**)、`agent-fungibility` (33d)、`sales-material` (32d)、`slide-template-extractor` (32d) | — |

**值得注意**：
- **`crm-projection` (5)** 維持 daily agent 節奏，且對應 launchd agent 本週 **exit_code=0**——W20 Action 3 的這一半已修好（見對照上週）。
- **沉寂清單只有 4 個，但這個數字不可信**：usage API 只追蹤「自 ~2026-04-26 起至少觸發過 1 次」的 53 個 skill，整個 catalog 的真實沉寂面（如 `knowledge-graph` 連 1 次都沒進過資料集）在這個 endpoint 看不到。**`auto-stage` 是 PostToolUse hook、不是 slash skill**，它靜默觸發、不寫 usage log → 列在沉寂區是誤報，忽略。`sales-material` / `slide-template-extractor` 沉寂是本週 deck 工作量低的自然結果，非 routing 問題。
- **新出現的觸發**：`ship`(2)、`repo-rename`(1)、`gstack-spec`(1)、`rbac-permissions`(1)——`repo-rename` 觸發與本週 iCloud detach 收尾一致（見重複痛點 Theme 1）。`slide-office-hours`(1) 表示 storyline gate 有被走到。
- **agent exit-1 雙態問題持續**：`harvest` exit=1，但 `harvest-2026-05-24`～`05-30` 每天都產出報告、且 `-error.log` 全為 0-byte；`material-health` exit=1，但本週 skill 有跑、`HEALTH_REPORT.md` 有產出。**skill 成功、agent wrapper 回報失敗**——這是 W19/W20 已點名、連 3 週未解的訊號，且它直接污染本 retro 的使用度資料源（見 Action 2）。

## 重複痛點

### Theme 1: iCloud detach 遷移餘震 — 寫死舊路徑 / symlink drift

- **頻率**: `.learnings/LEARNINGS.md` 本週新增 4 條同源 entry——2026-05-23 `sk-setup-agents` PROJECTS_DIR 寫死 `~/Documents/Projects`、2026-05-23 `_sk_exec_record_run` 11-arg vs cron 3-arg、2026-05-23 `bin/sk undeploy` 只認 current REPO_DIR symlink（舊路徑成 orphan）、2026-05-26 搬 symlink-deployed skill repo 要跑自己的 relink。全部回溯到同一根因：5/22 把 17 個 repo 從 `~/Documents/Projects` 搬到 `~/code`，但工具本體仍假設舊 layout。
- **類別**: **Mechanical**（且**大致已修**）。git log top 兩筆 commit 正是修這條線：`8007c6d fix(agents): defuse sk-setup-agents PROJECTS_DIR landmine + ssot-drift cron 11-arg`、`389eacb fix(bin/sk): cmd_check_ssot derives project from PROJECT_REL_PATH not label`。
- **代表性事件**: `ssot-drift` plist 自 2026-05-20 加入後一直沒被載入——根因是「跑 `sk-setup-agents` 會把全部 plist 倒回壞路徑，所以沒人敢跑」。一個寫死路徑癱瘓了整條 agent 重建流程。
- **建議**: 已落地修復，本週**不需新 action**。唯一殘留追蹤項：確認 `~/.claude/skills/*` 不再有指向 `~/Documents/Projects/...` 的 dangling symlink（5/23 entry 提到曾有 94 個）——可併入既有 `symlink-fix` agent（本週 exit 0，正常）日常掃描，不另開 action。

### Theme 2: harvest 持續產出「PoC/售前 domain」候選，皆 n=1 被正確遞延

- **頻率**: 最近 7 天 harvest 報告共 4 個 Moderate 候選——`dashboard-health-panel`(05-24)、`poc-to-product-audit`(05-27)、`data-poc-scoping`(05-29)、`cv-poc-acceptance-criteria`(05-30)。後三者都是「B2B 售前 PoC 驗收/規劃」同一母題的不同 domain 切片（產品化盤點、資料 PoC、CV/AOI 驗收）。
- **類別**: **Editorial**（觀察，非痛點）。每份 harvest 都正確判斷 n=1、與 `.claude/CLAUDE.md` 既有 domain-gap 追蹤合流、明文「第 2 案出現即抽」。機制按設計運作，**不是 gap**。
- **代表性事件**: 05-29 `data-poc-scoping` 與 05-30 `cv-poc-acceptance-criteria` 連兩天出現、結構幾乎相同（風險分層門檻、provisional labeling、domain-gap framing），只差 domain。
- **建議**: 暫不抽 skill。但提報一個 watch item：這三者共享的「售前 PoC 驗收標準 scoping 方法學」其實**跨 domain 的 n 已 ≥3**。若 6 月再出現第 4 個 PoC 售前案，考慮抽一個 domain-agnostic 的 `presales-poc-scoping` 母 skill（共用方法、domain 知識當參數），而不是繼續累積 3-4 個各自 n=1 的子候選。**此為 6 月觀察項，非本週 action。**

## 集中度

- **Token 集中**: 本週 7 天 ~**$10,549**（05-26 $2047、05-29 $2080 為峰值），是 W20 weekday 總額（$2,901）的 ~3.6×——本週工作量本身大增。**但 per-project 7-day 切片仍取不到**：`/api/tokens/filtered?days=7` 回傳內容與 `/api/tokens` **byte-for-byte 相同**（days 參數被忽略），`projects` 陣列是 all-time 累計（總額 $25,908），無法歸因本週。累計榜首已換成 `ChimesFlow`($5.6k) + `odb-dfm`($3.1k) 這兩個 W20 還不顯著的新專案——強烈暗示它們是本週 spike 來源，但**無法證實**。這是連 **3 週**（W19/W20/W22）卡在同一個觀測缺口。
- **失敗集中**: 6/16 agent exit 1（`research-agent`、`research-agent-weekly`、`doctor`、`harvest`、`janitor`、`material-health`）。其中 `harvest`、`material-health` 確定是「skill 成功、wrapper exit 1」的假失敗（有產出、error log 0-byte）。真實失敗面被假陽性淹沒、無法區分——這讓「失敗集中」這個指標本身失去意義。
- **Dashboard 健康**: 本週 watchdog log **1 FAIL、0 RESTART、0 ESCALATE**（W20 是 80+ 行、8 RESTART）。dashboard API **全程在線**（本 retro 三個 endpoint 都正常回應，無需 fallback）。**這是 W19 以來最健康的一週。**

## 下週 Actions (max 3, prioritized)

1. **退休 `knowledge-graph` skill — 這次真的刪** — Why now: W20 Action 2 把它設成 retro 的 dogfooding 測試（「證明 retro action 會被執行」），結果 W21 被跳過、W22 它**還在 `skills/meta/knowledge-graph`、仍 0 觸發**。連 3+ 次 retro 沒動最便宜的 action，是 retro 信任度的直接威脅。Est. effort: 10 min（`rm -rf skills/meta/knowledge-graph` → `bin/sk audit` → README skill count -1）。Expected impact: 終結這條延期鏈；若本週仍不執行，**應正式暫停 workflow-retro 至少兩週**，停止生產沒人消化的報告。

2. **Root-cause agent exit-1 雙態（先打 `harvest` + `material-health`）** — Why now: 這兩個 agent 明明有產出、error log 卻 0-byte，wrapper 仍 exit 1。它讓本 retro 的「使用度」與「失敗集中」兩個軸的資料源失真——6/16「失敗」裡有幾個是假的，沒人能分。連 3 週點名未解。Est. effort: 30 min（讀 wrapper 結尾 exit-code 邏輯，多半是 last-command 殘留 exit、或 git push no-op 被當失敗）。Expected impact: agent 健康儀表回到可信；後續 retro 不必每週手動辨識假失敗。

3. **修 `/api/tokens/filtered` 讓 `days` 參數生效（或補 per-project 7d 切片）** — Why now: 集中度軸連 3 週（W19/W20/W22）無法歸因週度成本，偏偏本週 $10.5k spike（3.6×）正是最需要歸因的一週，卻只能猜「大概是 ChimesFlow/odb-dfm」。Est. effort: 30-45 min（endpoint 目前無視 days、回傳 all-time；加日期過濾 + 按 project group-by）。Expected impact: 集中度軸從「猜」變「測」；>40% 單一專案的告警才有資料基礎。

> **不再列 W20 Action 1（拿掉 DEEP recovery）為本週 action**：本週 watchdog 0 incident，該風險未實體化，cleanup 價值仍在但不急（dead code、無害）。降為 backlog，待下次 watchdog 事故或順手重構時處理。

## 對照上週

> 註：W21 無 retro 檔案（被跳過，與 W20 結尾「Action 2 未動則暫停兩週」的建議一致）。以下對照 **W20**。

W20 三個 actions 完成度：

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | 拿掉 `sk-watchdog` DEEP recovery | ❌ NOT DONE | `grep deep_recovery\|ESCALATE\|Resource deadlock bin/sk-watchdog` 仍 9 處。但本週 watchdog 0 incident，風險未觸發。 |
| 2 | 退休 `knowledge-graph` | ❌ NOT DONE | `skills/meta/knowledge-graph` 仍存在、usage 資料集內 0 紀錄。**連 3+ 次未動。** |
| 3 | 修 `crm-projection`（+ 兩個 research agent）的 exit 1 | 🟡 PARTIAL | `crm-projection` 本週 **exit 0**（已修）；`research-agent` / `research-agent-weekly` 仍 exit 1。 |

完成率 **1/3**（Action 3 半成）。W18→W19→W20→W22 的 action 完成率是 1/3 → 0/3 → 0/3 → 1/3——略有回升，但回升全靠那個「修 crm-projection」這類 **mechanical** action；**editorial/cleanup** action（退休 skill、刪 dead code）依舊一條都沒動，與 W19 的預判完全一致。

指標變化：
- watchdog incidents：W20 8 RESTART → W22 **0 RESTART / 1 FAIL** —— **-100%**，回到 W19 之前的平靜水準。
- exit-1 agent 數：W20 5 → W22 6 —— +1（但 `crm-projection` 修好、其他項目組成略變；且至少 2 個確認是假失敗）。
- 週度 token：W20 weekday ~$2.9k → W22 7d ~$10.5k —— **+3.6×**（工作量驅動，非異常）。
- per-project 7d 歸因能力：W19/W20/W22 連 3 週缺口，**無變化**。
- retro action 完成率：W20 0/3 → W22 1/3。
