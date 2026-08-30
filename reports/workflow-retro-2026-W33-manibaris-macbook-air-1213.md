---
date: 2026-08-16
iso_week: 2026-W33
period: 2026-08-10 to 2026-08-16 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W33

## TL;DR

W32 的三個 action 本週查證**再次 0/3 完成**——這是連續第 2 個週期全數落空（累計 6 個已給精確修法的 action，0 個被執行）。三個舊痛點原封不動：`bin/sk:489` 的 byte-based 截斷仍在讓 `skill-audit` 報告損毀（本週窗口再中 7/7 天，累計已連續 13 天，自 08-03 起從未間斷）；`sales-assistant` 4 支排程 plist 仍指向已宣告 deprecated 的專案（本週 6 份 harvest 報告再次確認 `crm-projection`/`subsidy-scraper`/`material-health` 跑在 `sales-assistant` 底下）；`tester` 的 `media/_shared` false-positive FAIL 已連續 24 天汙染每日測試報告。本週唯一的實質進展，是把連續 4 個 retro 週期只停留在「觀察」的 `/api/agents/{label}/runs` 空陣列疑案**查出根因**：`dashboard/lib/db.py:6` 的 `DB_PATH` 指向 `dashboard/data/rivendell.db`（0 筆資料），但實際寫入 agent 執行紀錄的是 `bin/sk-exec-lib:751` 寫的 `dashboard/data/sk-dashboard.db`（1121 筆、寫到今晚 22:00 都還在更新）——兩個檔名在同一個資料夾裡分裂，API 讀錯檔案，這是本次才第一次真正翻程式碼查清楚，過去三次都只是「再觀察一週」。此外本次撰寫期間**再度**（連續第 2 週、同一個 Sunday 23:00 觸發點）偵測到排程版 `workflow-retro` agent 與本次手動執行併發寫入同一個檔案的競態，記錄於集中度章節。集中度本身持穩，watchdog 是乾淨的一週。

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+ this week) | `crm-projection`(7 — 仍指向 deprecated 專案，見重複痛點)、`requirement`(5) | — |
| 低頻 (1-4 this week) | `user-flow`(2)、`planning-with-files`(2)、`gstack-plan-eng-review`(2)、`excalidraw-diagram`(2)、`artifact-design`(2)、`chimesflow-design`(2)、`qa-dataflow`(2)、`task-brief`(2)、`material-health`(2)、`workflow-retro`(2)、`skill-creator`(2)，各 1 次的 13 支（`odb-dfm-reference`、`mockup`、`frontend-design`、`iot-factory-report`、`subsidy-scraper`、`gstack-codex`、`gstack-careful`、`run`、`session-harvest`、`subsidy-writer`、`video-transcript`、`writing-great-skills` 等） | 快照 17 支中 **6 支 exit≠0**：`research-agent`/`research-agent-weekly`（news_stock，見重複痛點）、`doctor`（已知暫時性 broken pipe，非新問題）、`tester`（已知 false-positive，見重複痛點）、`material-health`（08-16 09:02 執行 hit `max_turns`，單次、非慣性問題）、`subsidy-scraper`（08-13 08:03 執行 DNS 解析失敗 `ENOTFOUND`，單次、疑似當下網路瞬斷） |
| 沉寂 (30+ days) | 8 支：`claude-to-telegram`(06-13)、`env-doctor`/`presales-pipeline`/`repro-exam`(06-15)、`mops-financial-scraper`/`client-kickoff-docs`(06-16)、`office-xlsx`(07-06)、`gstack-design-consultation`(07-13) | — |

**值得注意**：
- 本週追蹤範圍內共 **68 支 skill、26 支活躍、47 次 firing**（W32：68 / 25 / 59）——活躍面持平，總 firing 數略降，樣本量無明顯異常。
- `material-health`／`subsidy-scraper` 的 exit=1 是**本週新出現、且看起來是單次事件**（分別是 agent 跑到 turn 上限、以及觸發當下 DNS 連不上），跟 Theme 2（sales-assistant 路徑問題）是不同的失敗模式，不建議合併討論——下週若同一支 agent 再次出現同款失敗，才需要升級成獨立追蹤項目。
- 沉寂清單較 W32（11 支）減少 3 支，主因是本週窗口內部分邊緣 skill（如 `mockup`、`odb-dfm-reference`）重新被觸發，不代表系統性改善。

## 重複痛點

### Theme 1：`skill-audit` 報告 UTF-8 損毀，累計已連續 13 天未修（08-03 起）

- **頻率**: 本週窗口 `reports/skill-audit-2026-08-{10,11,12,13,14,15,16}.md` 逐一用 Python `utf-8` decode 驗證，**7/7 天全部損毀**，錯誤位置與型態與 W32 記錄的完全一致（`invalid continuation byte`，落在 ~23,700-23,850 bytes 附近）。加上 W32 記錄的 08-03~08-09 六天，**累計連續 13 天**未間斷。
- **類別**: Mechanical——修法在 W32 已給出且未變。
- **代表性事件**: `bin/sk:489`（W32 記錄為 474 行，本週因中間有其他改動位移到 489 行，程式碼本身**逐字未變**）：
  ```bash
  [ "${#val}" -gt 120 ] && val="${val:0:117}..."
  ```
  在非 UTF-8 aware 的 locale 下（launchd/cron 環境常見未設 `LANG`/`LC_ALL`），`${#val}`/`${val:0:117}` 以位元組而非字元計數，砍在中文描述的多位元組字元中間。
- **建議**: 見下週 Action 2——這是**第 3 次**給出同一個一行修法，繼续「建議」邊際效益已經很低，本次直接建議由下一個 rivendell 維運 session 動手改，不再只是提醒。

### Theme 2：`sales-assistant` deprecated 專案排程遷移，本週 6 份 harvest 報告再次確認未動

- **頻率**: 本週窗口（08-10~08-16）**六份** harvest 報告（08-10/11/12/13/14/16）逐一記錄 `crm-projection`／`subsidy-scraper`／`material-health` 正常執行於 `/Users/manibari/code/sales-assistant` 底下；重新 `grep` 四支 plist（`crm-projection`/`material-health`/`subsidy-scraper`/`tender-scraper`）的 `ProgramArguments`，**working directory 依然全部**是 `/Users/manibari/code/sales-assistant`，無任何變更痕跡。
- **類別**: Mechanical（純粹是還沒做）。
- **代表性事件**: `sales-assistant-deprecated` memory 檔仍停在 2026-06-13 的宣告，未記錄任何遷移進度或「暫緩」決定。
- **建議**: 見下週 Action 3。

### Theme 3：`news_stock` research-agent stale `PROJECTS_DIR`，root cause 已知兩週仍未套用

- **頻率**: 兩支 plist（`research-agent`／`research-agent-weekly`）的 `EnvironmentVariables` 區塊本週逐一重新檢查，**依然只有 `PATH`，沒有 `PROJECTS_DIR`**；agent 快照本週仍是 `exit=1`。
- **類別**: Mechanical——修法（plist 加一行 env var）已知兩週。
- **建議**: 併入下週 Action 3（與 Theme 2 同批處理，兩者都是「已給精確修法，純粹沒空做」）。

### Theme 4：tester 的 `media/_shared` false-positive FAIL，累計 24 天（07-23 起）

- **頻率**: `test-2026-08-{10,11,12,13,14,15,16}.md` 逐一確認同一筆 `media/_shared | SKILL.md missing | FAIL` 依然存在，本週窗口 7/7 天全中，累計自 07-23 起 **24 天**連續出現。
- **類別**: Mechanical——`_shared/` 是共用腳本目錄，本就不該有 `SKILL.md`（已記錄於 2026-07-23 LEARNINGS）。
- **建議**: 見下週 Action 3。

### （本次查清，非新增痛點）`/api/agents/{label}/runs` 端點連續 4 個 retro 週期回傳空陣列 — 根因已找到

- 連續第 4 個 retro 週期（W29、W31、W32、W33）確認同一結果 `[]`，過去三次都只停在「這是裝飾用端點」的猜測，本次直接翻程式碼查清：
  - `dashboard-next/api/server.py:20` 把 `sys.path` 指向 `dashboard/lib`（沿用舊 dashboard 的程式碼，非重複維護）。
  - `dashboard/lib/db.py:6`：`DB_PATH = Path(__file__).parent.parent / "data" / "rivendell.db"` → 實際路徑 `dashboard/data/rivendell.db`，用 `sqlite3` 直接查 `agent_runs` 表，**0 筆資料**。
  - 但真正在寫入的是 `bin/sk-exec-lib:751`：`local db_path="${SK_EXEC_REPO_DIR}/dashboard/data/sk-dashboard.db"`——同一個資料夾下**檔名不同**的另一個 sqlite 檔，`agent_runs` 表有 **1121 筆**，最新一筆是今晚 22:00 的 `maintain` 執行紀錄，資料完全健康、持續在寫。
  - 這不是「端點沒接線」，是**兩個檔名在同一個目錄裡分裂**——API 永遠讀空的那個。
- **類別**: Mechanical，一行路徑修正（或建一個 symlink）即可讓端點立刻生效。
- **建議**: 見下週 Action 1。

## 集中度

- **Token 集中**: `/api/tokens/filtered` 依然不支援真正的每週期間篩選（`days=7` 被忽略，回傳仍是全期累計）——與 W31、W32 記錄的限制完全相同，連續第 3 個週期未修。用全期累計數字看：**PTI-ARES $5,242.34 / 36.5%**（W32 讀數是 $4,141.67 / 27.8%），漲幅明顯但因為 API 限制無法拆出真正的「本週」數字做同基準比較，不宜直接解讀為「PTI-ARES 本週爆量」——比較合理的讀法是全期累計持續成長，且該專案的佔比正在逼近但仍未達 40% 門檻。本週（08-10~08-16）daily 加總可算出整體花費約 **$3,336.97 / 76 sessions**，但 API 不支援拆分到專案層級，無法確認是否由 PTI-ARES 貢獻。
- **失敗集中**: agent 快照 **6/17 exit≠0**（W32 是 4/17）。其中 4 支是重複痛點 Theme 2-3 的舊病（`research-agent`/`research-agent-weekly`/`doctor`/`tester`），另外 2 支（`material-health`/`subsidy-scraper`）是本週新出現的單次事件（max_turns、DNS 瞬斷），非結構性退化。
- **Dashboard 健康**: watchdog 本週僅 2 行紀錄，皆為同一次極短暫事件（今晚 17:26-17:27，api 端點 1 次 FAIL、1 分鐘內自行恢復，0 次 RESTART）——與 W32 同等乾淨。
- **本次撰寫期間偵測到的併發風險（連續第 2 週、同一觸發點）**：`launchctl print` 確認排程版 `com.sk.agent.rivendell.workflow-retro`（pid 99771，`bin/sk-workflow-retro-cron`）於今晚 23:00 準時自動啟動，與本次使用者手動觸發的 `/workflow-retro` **同一週、同一輸出檔路徑** `reports/workflow-retro-2026-W33.md`——這是 W32 報告記錄的同一個競態，**這次不是巧合，是同一個 Sunday 23:00 觸發窗口第 2 次撞期**，代表只要有人在週日晚上 11 點前後手動跑這個 skill，就會穩定觸發。本報告完成後檔案可能被排程版覆蓋或反過來覆蓋排程版的輸出，建議完成後覆核。這已經是可預測的模式，不再是單次觀察,值得排入下週 action 徹底解決(而非每次撞期才記錄)。

## 下週 Actions (max 3, prioritized)

1. **修 `dashboard/lib/db.py:6` 的 `DB_PATH` 檔名不一致，讓 `/api/agents/{label}/runs` 端點恢復正常** — Why now: 這是本次才第一次真正查清根因的新發現（過去 3 個週期只在「觀察」），修法非常明確：把 `DB_PATH` 從 `rivendell.db` 改成 `sk-dashboard.db`（或建 symlink `rivendell.db -> sk-dashboard.db`），資料本身完全健康（1121 筆、持續寫入到今晚），純粹是讀錯檔名。Est. effort: 5 min 改檔名 + 重啟 `com.sk.dashboard.api`（`launchctl bootout`/`bootstrap`，不可直接 `kill`）驗證 `curl localhost:8000/api/agents/com.sk.agent.rivendell.tester/runs` 不再是 `[]`。Expected impact: 往後每份 retro 的「失敗集中」章節可以直接引用真實 exit-code 歷史，不用再靠 launchd 快照猜測。

2. **修 `bin/sk:489` 的 byte-based 字串截斷，止住 skill-audit 報告的 UTF-8 損毀（第 3 次提出同一個修法）** — Why now: 累計已連續 13 天損毀，且這份報告本身是 workflow-retro 的資料來源之一。前兩次「建議」都沒有被執行，這次不再只是重複提醒——如果下週還是 0/3，代表口頭建議這個管道本身對這類一行修法無效，需要考慮的不是「再提醒」而是「直接找一個 session 動手」。Est. effort: 5-15 min（`export LC_ALL=en_US.UTF-8` 或改用 `cut -c` / `awk substr`），驗證方式跟 W32 一致：對含中文長描述的 skill 跑一次 `bin/sk audit`，`python3 -c "open(f,encoding='utf-8').read()"` 確認可解碼。

3. **一次處理兩個「已給精確修法、連續數週沒空做」的項目**（Theme 2 + Theme 3）— Why now: sales-assistant 遷移本週被 6 份 harvest 報告再次點名,news_stock PROJECTS_DIR 已知兩週未套用,繼續逐週複述邊際效益趨近於零:
   - **news_stock PROJECTS_DIR**：兩個 plist 的 `EnvironmentVariables` dict 內各加一行 `<key>PROJECTS_DIR</key><string>/Users/manibari/code</string>`，`launchctl bootout`/`bootstrap` 重載生效。Est. effort: 5-10 min。
   - **sales-assistant 遷移二選一**：(a) 把 4 支 plist 的 working directory 改指到 chimesflow 對應路徑並更新 `sales-assistant-deprecated` memory；或 (b) 明確決定「暫緩遷移」並把原因、下次評估時間點寫進該 memory，讓 harvest 未來不再逐日複述同一件事。Est. effort: 15-20 min。
   Expected impact: 兩支 agent 從連續每日失敗轉綠；harvest 報告未來不再重複點名同一組項目。

**本週未列入 action 但下次應該處理**：workflow-retro 排程版與手動觸發在 Sunday 23:00 前後的併發覆寫風險，已連續 2 週在同一個觸發窗口重現——建議在 `bin/sk-workflow-retro-cron` 加一個簡單的檔案鎖（`flock` 或檢查同名 lockfile），避免下次又在寫入中途被另一個程序覆蓋。

## 對照上週

上一份可比報告是 **W32（2026-08-09）**。

W32 三個 actions 完成度：**0 / 3 全數未完成**（與 W31→W32 的「0/3」相同，這是連續第 2 個週期三項全部落空，累計 6 個已給精確修法的 action 中 0 個被執行）：

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | 修 `bin/sk:474`（現 489 行）的 byte-based 字串截斷 | ❌ 未執行 | 程式碼逐字比對未變；本週 7/7 天 skill-audit 報告仍損毀在同一位置附近 |
| 2 | news_stock PROJECTS_DIR + sales-assistant 遷移二選一 | ❌ 未執行 | 兩個 plist 的 `EnvironmentVariables` 仍無 `PROJECTS_DIR`；4 個 sales plist working directory 仍是 `sales-assistant`；本週 6 份 harvest 報告再次點名 |
| 3 | 修 tester 的 `media/_shared` false-positive FAIL | ❌ 未執行 | `test-2026-08-{10~16}.md` 確認同一筆 FAIL 依然存在，累計已 24 天 |

指標變化（W32 → W33）：
- watchdog incidents：1 次極短暫事件 → **1 次極短暫事件**（同等級，1 FAIL/0 RESTART，1 分鐘內自癒）——連續第 3 週維持系列最乾淨紀錄。
- exit≠0 agent 數（快照）：4/17 → **6/17**（表面惡化，但 2 支新增是本週單次事件，非結構性退化；4 支舊病依然原封不動）。
- skill-audit 損毀連續天數：6 天 → **13 天**（本週再累加 7 天，未間斷）。
- tester false-positive 連續天數：18 天 → **24 天**（再累加 6 天）。
- usage 活躍 skill 數：25 → **26**（持平），總 firing：59 → **47**（略降）。
- 集中度：PTI-ARES 27.8%（W32 讀數）→ **36.5%**（本次讀數，因 API 每週篩選持續失效，兩者皆為全期累計，非同一週期的同基準比較，僅供方向參考）。
- **本週實質進展（W32 沒有的）**：`/api/agents/{label}/runs` 端點空陣列疑案連續 4 個週期後**首次查出根因**（`dashboard/lib/db.py` DB 檔名與實際寫入檔名不一致），從「觀察」升級為「可執行的一行修法」。
- **本週重現（W32 出現過一次，本週是第 2 次同一觸發點）**：workflow-retro 排程版與手動執行在 Sunday 23:00 併發寫入同一檔案的競態，兩週都在同一個時間窗口發生，已足以視為可預測模式。
