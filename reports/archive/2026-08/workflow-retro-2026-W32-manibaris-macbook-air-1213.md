---
date: 2026-08-09
iso_week: 2026-W32
period: 2026-08-03 to 2026-08-09 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W32

## TL;DR

本週最重要的發現是新的、系統性的資料損毀：`reports/skill-audit-*.md` 從 08-03 起連續 **6/6 天全部損毀**（08-03/04/05/06/07/09），每份都在幾乎相同的位元位置（~23,600–23,900 bytes）出現無效 UTF-8 續位元組。根因已查明並非資料本身壞掉，是 `bin/sk:474` 的描述欄位截斷邏輯 `${val:0:117}` 在非 UTF-8 locale 下以「位元組」而非「字元」切字串，砍在某支 skill 中文描述的多位元組字元中間——這是一行修法（下週 Action 1）。同時，上週三個 action **全部 0/3 完成**：`sales-assistant` 排程遷移連續第 4 週原地踏步（本週窗口 3 份 harvest 報告再次點名同一組 plist）；`news_stock` research-agent 的 stale `PROJECTS_DIR` 修法本週再次確認完全未套用（stderr 逐日重現同一行錯誤）；tester 的 `media/_shared` false-positive FAIL 已連續 18 天汙染每日測試報告。這是本季度第一次三項全部落空,值得點名為 meta 訊號:同一組已經給出精確修法（檔案/行號/預估工時）的建議,連續數週沒有人執行——問題不是分析不夠,是沒有人在做執行這一步。好消息是上週懸而未決的 `disk-monitor` 疑慮本週已徹底查清：不是監控盲點,而是設計如此（"silent when fine"）,磁碟使用率已從 07-26 的 96% 危急降到本週的 14%,沒有異常。集中度本身依然健康,沒有專案單週佔比破 40% 門檻,watchdog 是系列中最乾淨的一週。另需提醒:本次 retro 撰寫過程中,發現**排程版 workflow-retro agent（pid 87292，23:00 觸發，與本次手動執行同一週期）正在背景執行中**,兩者會寫入同一份 `reports/workflow-retro-2026-W32.md`,存在檔案覆寫競態——已在集中度章節記錄,建議完成後覆核檔案內容是否被排程版覆蓋。

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+ this week) | `crm-projection`(7 — 仍指向 deprecated 專案，見重複痛點 Theme 2)、`odb-dfm-reference`(6)、`excalidraw-diagram`(5)、`requirement`(5) | — |
| 低頻 (1-4 this week) | `gstack-plan-eng-review`(3)、`local-media-transcribe`(3)、`video-transcript`(3)、`task-brief`(2)、`gstack-office-hours`(2)、`mermaid-diagram`(2)、`planning-with-files`(2)、`de-slopify`(2)、`material-health`(2)、`subsidy-scraper`(2)、`workflow-retro`(2)、`pitch-deck`(2)，各 1 次：`user-flow`、`gstack-design-shotgun`、`wayfinder`、`office-pptx`、`grill-me`、`grilling`、`to-tickets`、`gstack-review`、`skill-scout` | 快照 17 支中 **4 支 exit≠0**：`news_stock` `research-agent`/`research-agent-weekly`（本週再次確認 root cause 未修，見重複痛點 Theme 3）、`rivendell` `doctor`（stderr 仍是同一個暫時性 `Broken pipe`，報告產出正常，非新問題）、`rivendell` `tester`（對應已知 false-positive FAIL，見重複痛點 Theme 4） |
| 沉寂 (30+ days) | 11 支：`rbac-permissions`(06-12)、`claude-to-telegram`(06-13)、`gstack-autoplan`/`env-doctor`/`presales-pipeline`/`repro-exam`(06-15)、`mops-financial-scraper`(06-16)、`client-kickoff-docs`(06-16)、`gstack-plan-design-review`(06-27)、`chimesflow-design`(07-02)、`office-xlsx`(07-06) | — |

**值得注意**：
- 本週使用度追蹤範圍內共 **25 個 skill、59 次 firing**（上一份 W31：18 / 36）——成長明顯，但兩份報告的追蹤基期不完全可比（W31 未列出追蹤總數，本次 API 回報追蹤範圍內共 68 支 skill），不宜過度解讀為「使用度翻倍」，較合理的讀法是「活躍面擴大」。
- `crm-projection` 連續第 3 份報告霸榜高頻，本質仍是噪音——排程仍跑在 deprecated 的 sales-assistant 專案下，見重複痛點 Theme 2。
- **`rivendell.janitor` 快照本週 exit=0，且 `reports/janitor.log` 08-09 03:00 有正常歸檔紀錄** — 上週「stdout/stderr 皆 0 bytes，待查」的懸案本次查清：janitor 本來就寫到 `reports/janitor.log`（非 launchd 的 stdout 檔），launchd 那兩個 log 檔本來就該是空的。這是誤報，非問題。
- **`rivendell.disk-monitor` 快照 exit=0，且本週確認並非監控盲點**：讀 `bin/sk-disk-monitor-cron` 原始碼確認其設計是「usage < 90% 時完全不寫報告、不輸出」（"noisy when broken, silent when fine"）。實測 `df -h /` 目前使用率僅 **14%**（07-26 最後一筆報告是 96% 危急），代表使用者已在 07-26 之後大幅清理磁碟，`disk-monitor` 沒有報告是正確行為，不是卡住。上週列為「觀察中」的懸案本週正式結案：非 bug。
- 沉寂清單與上週幾乎重疊，無新增沉寂候選，不代表異常。

## 重複痛點

### Theme 1（新發現）：`skill-audit` 報告系統性 UTF-8 損毀，本週窗口 6/6 天全部中招

- **頻率**: `reports/skill-audit-2026-08-{03,04,05,06,07,09}.md` 全部檔案，用 Python `utf-8` decode 逐一驗證，**6/6 皆在幾乎相同的位元位置（23,600～23,900 bytes 之間）拋出 `invalid continuation byte`**。同時每天都留下一個 0 bytes 的同名 `.md.tmp` 檔案（`08-03` 起每天，含今天）。
- **類別**: Mechanical — 已定位到確切一行。
- **代表性事件**: 檢查損毀位置前後 bytes，看到 `\x80\x81` 這種孤立續位元組緊接在下一支 skill（`sales-deck-design`）的表格列之前，符合「多位元組字元被從中間切斷」的典型特徵。追到 `bin/sk:474`：
  ```bash
  [ "${#val}" -gt 120 ] && val="${val:0:117}..."
  ```
  `${#val}` / `${val:0:117}` 在 bash 裡，若執行環境的 locale 不是 UTF-8 aware（launchd/cron 環境常見未設定 `LANG`/`LC_ALL`），會退化成「以位元組計數」而非「以字元計數」——當某支 skill 的中文 description 長度剛好讓第 117 個位元組落在一個多位元組字元中間時，截斷後的字串就是無效 UTF-8。
- **建議**: 兩個修法擇一（皆為單行改動）：(a) 在 `bin/sk` 呼叫 `cmd_audit` 前明確 `export LC_ALL=en_US.UTF-8`（或 `C.UTF-8`），讓 bash 的字串運算變成字元感知；(b) 改用不依賴 locale 的截斷方式，例如 `echo "$val" | cut -c1-117`（`cut -c` 在多數系統仍受 locale 影響，需搭配 (a)）或改用 `awk` 的 `substr` + 顯式 UTF-8 模式。兩者都應在下次執行前驗證：對含中文長描述的 skill（如 `sales-deck-design`）跑一次 `bin/sk audit`，再用 `python3 -c "open(f,encoding='utf-8').read()"` 驗證輸出檔可正常解碼。**這份報告本身是 workflow-retro 的資料來源之一，損毀會連帶影響未來幾週 retro 對 skill 健康度的判讀，優先度拉高。**

### Theme 2：`sales-assistant` deprecated 專案排程遷移，連續第 4 週原地踏步（W29→W31→W32，中間 W30 缺）

- **頻率**: 本週窗口（08-03～08-09）harvest 報告 `08-03`、`08-07`、`08-09` 三份**再次**明確記錄 `crm-projection`/`material-health` 在 `/Users/manibari/code/sales-assistant` 底下正常執行；逐一重新 `grep` 四支相關 plist（`crm-projection`、`material-health`、`subsidy-scraper`、`tender-scraper`）確認 `WorkingDirectory`/`ProgramArguments` **依然全部**指向 `sales-assistant`，無任何變更痕跡。
- **類別**: Mechanical（純粹是還沒做，不是技術障礙）。
- **代表性事件**: W31 報告的下週 Action 2 原文是「連續第 3 週『觀察但不執行』不再是可接受的結果，本週必須真的做出選擇」——本週查證後，**依然是原地踏步，這是第 4 週**。
- **建議**: 見下週 Action 2。本次不再只複述「快做」，而是把兩個選項的具體指令直接列出，降低「知道要做但沒空展開」的門檻。

### Theme 3：`news_stock` research-agent stale `PROJECTS_DIR`，root cause 已知一週仍未套用

- **頻率**: `research-agent-stderr.log` 本週連續多筆（逐日累積）皆是同一行：`scripts/research-agent.sh: line 10: /Users/manibari/Documents/Projects/rivendell/bin/sk-exec-lib: No such file or directory`，與 W31 報告記錄的錯誤一字不差。
- **類別**: Mechanical——W31 已給出具體修法（兩個 plist 加 `PROJECTS_DIR` 環境變數，或改腳本預設值），本週逐一檢查兩個 plist 的 `EnvironmentVariables` 區塊，**確認未套用任何修改**。
- **代表性事件**: `research-agent` 與 `research-agent-weekly` 兩支 agent 本週快照仍是 `exit=1`。
- **建議**: 見下週 Action 2（與 Theme 2 併案處理，兩者都是「上週已給精確修法、純粹沒空/沒做」的同類問題）。

### Theme 4：tester 的 `media/_shared` false-positive FAIL，連續 18 天汙染測試報告（07-23 起）

- **頻率**: `test-2026-08-09.md` 確認同一筆 FAIL 依然存在（`media/_shared | SKILL.md missing | FAIL`），累計自 07-23 起至今 **18 天**連續出現，本週 6 份 test 報告未逐一重新核對，但每日排程規則本身未變，可合理推定持續存在。
- **類別**: Mechanical——`_shared/` 是共用腳本目錄，本就不該有 `SKILL.md`（已記錄於 2026-07-23 LEARNINGS 條目），測試規則本身沒排除這個已知模式。
- **建議**: 見下週 Action 3。

### （持續追蹤，非本週新增）`/api/agents/{label}/runs` 端點持續回傳空陣列

- 本次對 `com.sk.agent.rivendell.tester` 重新測試，依然是 `[]`，是連續第 3 個 retro 週期（W29、W31、W32）確認同一結果——維持 W31 的結論：這是裝飾用端點，過去所有 retro 引用的「exit-code 歷史」實際上都來自 launchd 快照，不是這支 API。本週未再花時間深挖後端程式碼（時間分配給新發現的 skill-audit 損毀問題），下週如果還要繼續用這份報告佐證「失敗集中」，建議直接排入 action 一次查清楚，而不是連續第 4 次觀察。

## 集中度

- **Token 集中**: `/api/tokens/filtered` 目前不支援真正的每週期間篩選（`days=`/隱含參數皆被後端忽略，回傳仍是全期累計），此限制與 W31 記錄的一致，本週未見改善。用全期累計數字看：**PTI-ARES $4,141.67 / 27.8%**，未破 40% 門檻，第二名是 `tukey-automl`（11.8%，但僅 1 個 session、單次代價異常高，屬單一大型 session 而非持續性專案，不列入集中度風險）。本週（08-02～08-09）僅能從 daily 總額算出整體花費 **$3,966.18 / 89 sessions**，無法拆分到專案層級。
- **失敗集中**: agent 快照 **4/17 exit≠0**（`research-agent`、`research-agent-weekly`、`doctor`、`tester`），較上週 5/17 少一支——但這是因為 `janitor` 本週查清是誤報（見使用度小節），不是真的修好了什麼。4 支中，`doctor` 是已知暫時性 broken pipe，其餘 3 支都是 Theme 2-4 的重複痛點，非新退化。
- **Dashboard 健康**: watchdog 本週僅一次極短暫事件（08-09 01:44-01:45，web 1 次 FAIL，1 分鐘內自行恢復，未觸發 RESTART），與 W31 同等乾淨，是系列中最穩定的兩週之一。
- **新發現：本次 retro 撰寫期間偵測到排程版 agent 併發執行**：`launchctl print` 顯示 `com.sk.agent.rivendell.workflow-retro`（pid 87292，state=running）於今晚 23:00 依排程自動啟動，與本次使用者手動觸發的 `/workflow-retro` **屬同一週期、同一輸出檔** `reports/workflow-retro-2026-W32.md`——目前該檔案在寫入前是空檔（0 bytes），代表排程版尚未完成或正在執行中。兩個程序若都寫入同一路徑，存在後寫入者覆蓋先寫入者的競態風險。本報告完成後建議覆核檔案內容，確認最終落地的版本是預期的分析內容，而非被排程版的（可能較淺的）輸出覆蓋，或反過來被截斷。這不是本週的「痛點」而是本次執行過程中的即時觀察，記錄於此供覆核。

## 下週 Actions (max 3, prioritized)

1. **修 `bin/sk:474` 的 byte-based 字串截斷，止住 skill-audit 報告的 UTF-8 損毀** — Why now: 本週 6/6 天報告全部損毀，且損毀的是 retro 自己依賴的資料來源之一，拖越久，越多下游（下週 retro、任何讀取這份報告的工具）會吃到壞資料。Est. effort: 5-15 min（改一行 + 在 cron 呼叫前 export `LC_ALL=en_US.UTF-8`，或改用 locale-independent 的截斷方式）。Expected impact: skill-audit 報告從本次起可正常被 `utf-8` decode，且 6 天損毀視窗不再擴大。

2. **一次清掉兩個「上週已給精確修法、純粹沒空做」的項目**（Theme 2 + Theme 3）— Why now: 這是連續第 4 週 / 連續第 2 週被同一份報告點名同一個修法，繼續只是「再提醒一次」邊際效益已經很低，這次直接列出可複製貼上的指令：
   - **news_stock PROJECTS_DIR**：在 `com.sk.agent.news_stock.research-agent.plist` 與 `.research-agent-weekly.plist` 的 `EnvironmentVariables` dict 內各加一行 `<key>PROJECTS_DIR</key><string>/Users/manibari/code</string>`，`launchctl bootout`/`bootstrap` 重載即可生效。Est. effort: 5-10 min。
   - **sales-assistant 遷移二選一**：(a) 把 4 支 plist（`crm-projection`/`material-health`/`subsidy-scraper`/`tender-scraper`）的 working directory 從 `/Users/manibari/code/sales-assistant` 改成 chimesflow 對應路徑並更新 memory；或 (b) 明確決定「暫緩遷移」，把原因和下次評估時間點寫進 `sales-assistant-deprecated` memory，讓 harvest 未來不再逐日複述同一件事。Est. effort: 15-20 min。
   Expected impact: 兩支 agent 從連續每日失敗轉綠；harvest 報告未來不再重複點名同一組項目（無論選哪個選項，都是「終結重複」而非「再拖一週」）。

3. **修 tester 的 `media/_shared` false-positive FAIL** — Why now: 連續 18 天（07-23 起）汙染每日測試報告，讓「ALL PASSED」這個健康基準線失去意義——真正的新 regression 出現時會被這筆固定雜訊淹沒。Est. effort: 10-15 min（在 tester 腳本對 `_shared/` 之類已知的共用目錄模式加排除規則）。Expected impact: 測試報告恢復其作為健康基準線的可信度。

**本週未列入 action 但建議下次真的排進去（連續第 3 次觀察，不宜再拖）**：
- `/api/agents/{label}/runs` 端點是否本來就沒接線——連續 3 個 retro 週期空陣列已是極強訊號，下次直接排 action 查程式碼，而非再觀察一週。

## 對照上週

上一份可比報告是 **W31（2026-08-02）**。

W31 三個 actions 完成度：**0 / 3 全數未完成**（比 W29→W31 的「1/3 部分進展」更差，這是本季度第一次三項全部落空）：

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | 修 `news_stock` research-agent 系列的 stale `PROJECTS_DIR` | ❌ 未執行 | 兩個 plist 的 `EnvironmentVariables` 逐一查證未變更；`research-agent-stderr.log` 本週仍逐日重現同一行錯誤 |
| 2 | `sales-assistant` 排程遷移二選一，本次不得再延 | ❌ 未執行（第 4 週原地踏步） | 4 個 plist 的 working directory 逐一查證仍是 `/Users/manibari/code/sales-assistant`；本週 harvest 08-03/08-07/08-09 三份再次點名 |
| 3 | 修 tester 的 `media/_shared` false-positive FAIL | ❌ 未執行 | `test-2026-08-09.md` 確認同一筆 FAIL 依然存在，累計已 18 天 |

指標變化（W31 → W32）：
- watchdog incidents：1 次極短暫事件（1 FAIL/0 RESTART，1 分鐘內自癒）→ **1 次極短暫事件**（同等級，1 FAIL/0 RESTART，08-09 01:44-01:45）——連續兩週維持系列最乾淨紀錄。
- exit≠0 agent 數（快照）：5/17 → **4/17**（表面改善，但實質是 `janitor` 本週查清為誤報，非真的修好一支；Theme 2-4 三支真正的失敗依然原封不動）。
- skill 總數：116 → **122**（+6，符合近期持續有新 skill 上架的觀察）。
- usage 總 firing：36 → **59**，活躍 skill 數 18 → **25**（成長，但追蹤基期不完全可比，見使用度小節）。
- 集中度：PTI-ARES 28.5%（W31，正確每週查詢）→ **27.8%**（本次因 API 每週篩選失效，只能用全期累計數字，非同基準比較，但方向一致——PTI-ARES 持續是最大但未破 40% 的專案）。
- **新增（W31 沒有的問題）**：`skill-audit` 報告 UTF-8 損毀，本週 6/6 天中招，上週同一份報告是正常的。
- **結案（W31 列為觀察，本週查清非問題）**：`disk-monitor` 靜默 7 天的疑慮——本週延長到 14 天靜默，但已確認是設計如此（磁碟使用率從 96% 降到 14%），不是監控盲點。
