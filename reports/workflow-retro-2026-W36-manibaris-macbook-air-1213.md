---
date: 2026-09-06
iso_week: 2026-W36
period: 2026-08-31 to 2026-09-06 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W36

## TL;DR

本週最重要的發現不是新痛點，是**這份 retro 自己這次也沒跑出來**——排定 09-06 23:00 執行的 `com.sk.agent.rivendell.workflow-retro`，`stdout`/`stderr`/報告檔三個都是 0 bytes，連腳本最後一定會印的 `Retro complete` 都沒出現，代表 `claude -p` 那段在網路預檢通過之後整個沒有輸出就中止（本篇是事後手動補跑）。往回查同一支腳本的完整歷史，`Network unavailable — aborting` 這個訊息在過去 20 週裡已經出現 **6 次**（06-07、06-14、07-12、07-26、08-30、以及這次的「連訊息都沒有」），**W35（08-24～08-30）週報就是因此完全缺失**——這件事本身也是一直到本次回頭查 log 才發現，沒有任何機制會主動通知「這週沒有 retro」。次要發現：W34 提出的 5 項機械修復（DB_PATH、`bin/sk:489` 截斷、`_shared` 誤報、news_stock 環境變數、sales-assistant 遷移）本週逐項複查，4 項依然原封不動，但 1 項（sales-assistant）查出**其實已經在 `ROADMAP.md` 的 Known-Gap Register 登記為 `parked(Peter)`**——先前幾輪retro 把它當「沒空做的債」是誤判，它其實是已決策的擱置項，不需要再重複提醒。本週另外浮現一個新模式：09-03 當晚 22:00 前後的整批排程（maintain / skill-audit / token-analysis / test）全數缺席，而同一天較早的 harvest／disk-capacity／ssot-drift 都正常——加上 token-analysis 本週再中 2 次 DNS `ENOTFOUND`（08-31、09-04），累計連同 W34 的 2 次共 4 次，指向同一個尚未證實但值得查的假設：**夜間排程時段的網路/喚醒穩定性**。活動量正常（本週 46 sessions），無需跳過本次 retro。

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+ this week) | 無 | 無 |
| 低頻 (1-4 this week) | `sales-crm-projection`(3)、`requirement`(2)、`gstack-plan-eng-review`(2)、`sales-deck-design`(2)、`crm-projection`(2，改名前舊路徑殘留)，其餘 16 支各 1 次（`gov-tender-scraper`、`gov-subsidy-scraper`、`gov-subsidy-writer`、`gov-rfq-writer`、`chimesflow-design`、`frontend-design`、`mockup`、`user-flow`、`planning-with-files`、`gstack-design-consultation`、`local-media-transcribe`、`session-harvest`、`workflow-retro`、`yt-channel-scraper`、`sales-material-health` 等） | 5/19 exit≠0：`news_stock` 的 `research-agent`／`research-agent-weekly`（環境變數缺失，見下）、`doctor`、`tester`（皆為已知慢性問題）、`janitor`（**疑似假訊號**——見下方說明） |
| 沉寂 (30+ days) | `de-slopify`(08-02)、`pitch-deck`(08-02)、`gstack-review`(08-03)、`skill-scout`(08-03)；另有 `wayfinder`／`grill-me`／`grilling`／`to-tickets` 4 筆紀錄，但 `skills/` 目錄下已找不到對應資料夾——是舊 skill 改名/移除後留在 usage 追蹤表裡的殘影，非真實沉寂訊號 | — |

**值得注意**：
- 本週 55 支追蹤 skill 中僅 21 支有實際 firing，共 27 次，無任何一支達到「高頻」門檻——與 W34 的讀數量級相近（該週 47 次 firing），本週活動集中在 sales 循環的排程執行，非新工具採用潮。
- `janitor` 是新增的 agent（本次自動歸檔 40+ 份 8 月舊報告到 `reports/archive/2026-08/`，`reports/janitor.log` 逐筆記錄且無錯誤），但 `/api/agents` 快照顯示 `exit: 1`。這與 W33/W34 記錄的「`/api/agents/{label}/runs` 因 `dashboard/lib/db.py:6` 的 `DB_PATH` 指向錯誤檔案而永遠回傳 `[]`」是同一根因——`janitor`、`doctor` 的 exit=1 目前**無法信任**，因為底層資料表本身讀不到真實紀錄（本次對 `janitor`、`doctor`、`tester` 三支都手動 `curl /runs` 驗證，全部回傳 `[]`）。

## 重複痛點

### Theme 1：`workflow-retro` 排程本身在週日 23:00 反覆撞網路/執行失敗，累計 6 次，且失敗型態正在惡化

- **頻率**：查 `~/Library/Logs/sk-agent/com.sk.agent.rivendell.workflow-retro-stdout.log` 全歷史，`Network unavailable — aborting` 出現在 06-07、06-14、07-12、07-26、08-30，共 5 次有留下明確訊息的失敗；本次 09-06 是第 6 次失敗，但**升級成連這行訊息都沒有**——`bin/sk-workflow-retro-cron` 用 `> "$REPORT_FILE"` 立即建檔、`claude -p ... 2> error.log`、最後**無條件**印 `Retro complete`，三個檔案（stdout 增量、error.log、報告檔）全 0 bytes 且最後那行 echo 沒出現，代表 `claude -p` 呼叫本身卡住後被外部中止（機率最高：無 timeout 保護，`headless claude` 遇到 auth/session 卡頓時會無限等待）。
- **類別**：Mechanical——`bin/sk-workflow-retro-cron:63` 的 `claude -p "$PROMPT" ...` 沒有 `timeout` 包裹。用同樣模式 grep 全部排程腳本，`bin/sk-harvest-cron`、`bin/sk-facts-cron`、`bin/sk-token-analysis-cron` 的 `claude -p` 呼叫也**全部沒有 timeout**——這不是單一腳本的個案，是這批 headless cron 的共同缺口。
- **代表性事件**：W35（2026-08-24～08-30）整週 retro 因此完全缺失，直到本次才發現——沒有任何主動告警,「這週沒 retro」這件事是靜默的。
- **建議**：見下週 Actions #1。

### Theme 2：09-03 晚間 22:00 前後整批排程缺席 + token-analysis 本週再中 2 次 DNS ENOTFOUND，合計本輪已達 4 次，疑似同一類夜間網路/喚醒問題

- **頻率**：`reports/maintain-2026-09-03.log`、`skill-audit-2026-09-03*.md`、`token-analysis-2026-09-03*.md`、`test-2026-09-03*.md` 四個 09-03 檔案**全部不存在**（連 error.log 都沒有），但同一天較早執行的 `harvest-2026-09-03-manibaris-macbook-air-1213.md`(00:35)、`disk-capacity-2026-09-03.md`(12:41)、`ssot-drift-2026-09-03-manibaris-macbook-air-1213.md`(03:00) 都正常產出——只有 22:00 之後的批次整批消失。另外，`token-analysis-2026-08-31-manibaris-macbook-air-1213.md`、`token-analysis-2026-09-04-manibaris-macbook-air-1213.md` 內容都是同一句 `API Error: Can't reach the API server — check your internet or DNS (ENOTFOUND)`，加上 W34 記錄的 08-21、08-22 兩次，累計 **4 次**。
- **類別**：Mechanical，但根因未證實——目前只是時間點重疊（都落在晚間 22:00～23:59 這個排程密集窗口）的觀察，不是已驗證的因果關係。
- **代表性事件**：09-03 當晚同時段（18:50-18:51）watchdog 也記錄一次 1 分鐘的 `web` 服務短暫失聯自行恢復——同一天出現三種不同層次的網路相關異常，值得合併調查而非分別追。
- **建議**：見下週 Actions #3。

## 集中度

- **Token 集中**：`/api/tokens/filtered?days=7` 這次再驗證仍然忽略 `days` 參數（回傳全期 222 sessions、$11,572.61，與 W31-W34 記錄的限制一致，連續 6 個週期未修，本次不再單獨列為新 theme，僅記錄未變）。改用逐日 `token-analysis-*.md` 交叉核對本週真實窗口（08-31～09-06）：**7 天合計 $1,293.53、46 sessions**，其中 09-01 單日 $593.71（佔本週 45.9%），當天報告明確標注 PTI-ARES 佔 99.7%，主因是 PCB 規則文件化的設計方案反覆確認——與全期累計讀數 PTI-ARES 30.2%（$3,498.85 / $11,572.61）方向一致，非本週單一事件的異常放大，判斷為正常的專案週期性高峰。
- **失敗集中**：agent 快照 5/19 exit≠0，但如「使用度」章節所述，`janitor`／`doctor`／`tester` 三支的 exit_code 因 `/runs` 端點的 DB_PATH bug 無法獨立驗證真偽；唯一有具體外部證據支持「真的在失敗」的是 `news_stock` 的兩支 research-agent（環境變數 `PROJECTS_DIR` 持續缺失，狀態同 W34，見下方 Known-Gap 段落）。
- **Dashboard 健康**：`reports/watchdog.log` 本週窗口（08-31～09-06）僅 1 筆事件（09-03 18:50 `web` FAIL → 18:51 自行 `OK` 恢復，1 分鐘），乾淨。**回查時額外發現**：W35 窗口內（08-30 15:56～16:28）`com.sk.gateway` 曾連續 30+ 次被判定失聯,watchdog 嘗試 `launchctl kickstart` **每一次都失敗**（`kickstart failed for com.sk.gateway`），最終服務是自己恢復,不是 watchdog 修好的——因為 W35 沒有出過報告,這次事件從沒被任何 retro 提及過,值得記錄但不計入本週指標。
- **Known-Gap 對照**：複查 `ROADMAP.md` 的「Known-Gap Register」，發現 `sales-assistant 爬蟲遷移` 已正式登記為 `parked(Peter)`，附解除條件——W31-W34 retro 把它當成「已給修法但沒空做」的技術債持續提醒，是誤判,它其實是使用者已決策的擱置項。但同一張表裡**沒有** `dashboard/lib/db.py:6` DB_PATH、`bin/sk:489` byte 截斷、tester 的 `_shared` 誤報這三項——這三項本週複查依然全數未修（`bin/sk:489` 逐字未變；09-04/05/06 三份 skill-audit 報告用 Python `utf-8` decode 驗證全部在同一位置 `invalid continuation byte`；`test-2026-09-04~06` 的 `_shared` FAIL 目標從 `media/_shared` 隨 09-03 的 media→knowledge 改名 commit `e2fa5c2` 自動變成 `knowledge/_shared`，問題本身未變）——依 `ROADMAP.md` 自己在文末寫的規則「登記不修——每項要有去處,不能爛在文件」，這三項目前既沒修也沒登記,是本週最具體的一項落差。

## 下週 Actions (max 3, prioritized)

1. **幫 4 支 headless cron 的 `claude -p` 呼叫加 `timeout`，優先修 `bin/sk-workflow-retro-cron:63`** — Theme 1 顯示這個缺口已經讓 retro 本身連續失敗 6 次（其中 1 次整週報告消失、1 次連錯誤訊息都沒留下）。用 `timeout 600 claude -p ...`（比照該腳本自己的網路重試上限抓一個合理值）包住 `bin/sk-workflow-retro-cron`、`bin/sk-harvest-cron`、`bin/sk-facts-cron`、`bin/sk-token-analysis-cron` 四支的 `claude -p` 呼叫，逾時要讓 `run_exit` 明確非 0 並落地一行錯誤訊息，而不是留 0 bytes。預估工時 20-30 分鐘,四支模式相同可一次做完。
2. **把 DB_PATH、bin/sk:489 截斷、tester `_shared` 誤報三項按 `ROADMAP.md` 自己的規則登記或修掉，二選一，不要再讓它們無登記地拖** — 三項修法都已知（`dashboard/lib/db.py:6` 改指向 `dashboard/data/sk-dashboard.db`；`bin/sk:489` 的 `${#val}`/`${val:0:117}` 改用 UTF-8 安全的字元計數；tester 排除沒有 `SKILL.md` 天經地義的 `_shared/` 目錄），累計工時 40-50 分鐘。DB_PATH 那項優先度最高——修完可以讓下週 retro 第一次真正驗證 `janitor`/`doctor`/`tester` 的 exit_code 是否為真,而不是每週都要靠側面證據猜。若這次還是没空做,至少把三項寫進 `ROADMAP.md` 的 Known-Gap Register（比照 `sales-assistant` 的登記方式）,讓它們有名分,不要再讓 retro 逐週用同樣篇幅重複勸修。
3. **查 09-03 整批排程缺席 + token-analysis 累計 4 次 DNS ENOTFOUND 是否同一根因** — 檢查 macOS 睡眠排程(`pmset -g sched`)、Wi-Fi 是否有夜間漫遊/省電斷線設定,是否與 22:00-23:59 這個排程密集窗口重疊；如果證實是喚醒延遲,`token-analysis` 等腳本的網路重試邏輯要加大 timeout 或延後排程時間,而不是逐週把 ENOTFOUND 當隨機噪音略過。

## 對照上週

上一份**有實際內容**的可比報告是 **W34（2026-08-23）**——W35（2026-08-24～08-30）因 Theme 1 描述的排程失敗（`Network unavailable — aborting`，08-30 23:00 記錄在案）完全沒有產出,這件事本身也是本次才發現,列入 Theme 1。

W34 三個 actions 完成度：**0/5 逐項修復 + 1/5 意外達成登記式解法 = 實質 1/5**：

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1a | 修 `dashboard/lib/db.py:6` DB_PATH | ❌ 未執行 | 程式碼逐字未變（仍指向 `data/rivendell.db`）；`/api/agents/{label}/runs` 對 tester/janitor/doctor 三支驗證皆回傳 `[]` |
| 1b | 修 `bin/sk:489` byte-based 截斷 | ❌ 未執行 | 程式碼逐字未變；09-04/05/06 三份 skill-audit 報告 UTF-8 decode 全部在同一位置損毀 |
| 1c | tester `_shared` false-positive | ❌ 未執行（目標隨改名漂移） | `test-2026-09-04~06` 仍 FAIL,但對象從 `media/_shared` 變成 `knowledge/_shared`(隨 09-03 media→knowledge 改名) |
| 1d | news_stock 兩支 plist 加 `PROJECTS_DIR` | ❌ 未執行 | `PlistBuddy`/`grep` 確認兩支 plist 仍無此 key |
| 1e | sales-assistant 遷移或明確暫緩 | ✅ 已達成（用登記式解法非修復式） | `ROADMAP.md` Known-Gap Register 已列 `sales-assistant 爬蟲遷移 \| parked(Peter) \| 決策後擴充既有 import 橋...` |
| 2 | 至少先做 DB_PATH | ❌ 未執行 | 同 1a |
| 3 | 不要求下週 retro 重複整份 checklist | 部分達成 | 本輪只對 5 項中「登記已達成」的 1 項（sales-assistant）停止重複提醒；其餘 4 項因為在 `ROADMAP.md` 裡仍找不到登記,依 W34 自己訂的規則("登記不修不能爛在文件")本輪判斷需要繼續提及,但改成一次性合併陳述,不逐項展開舊證據 |

指標變化（W34 → W36，中間 W35 缺失無法列入趨勢）：
- watchdog 本週窗口內事件數：1 次極短暫（08-23 那週）→ **1 次極短暫**（同等級）；但本次額外回查發現 W35 窗口內有 1 次 30+ 分鐘、kickstart 全部失敗的 `gateway` 停機,是先前所有 retro 都沒發現的新資訊。
- exit≠0 agent 數（快照）：7/17 → **5/19**（agent 總數成長,新增 `disk-monitor`/`facts`/`janitor`/`mail-triage` 等；失敗比例下降,但當中 3 支的 exit_code 可信度仍受 DB_PATH bug 影響,無法視為真實改善）。
- skill-audit UTF-8 損毀：連續 20 天 → 本輪未逐日累計計算連續天數(W35 缺失造成中斷點難以定義),但 09-04/05/06 三天複驗全部持續存在,判斷從未間斷。
- tester `_shared` 誤報：連續 31 天 → 本輪對象改名但問題持續存在,同上無法精確算連續天數,但本週 08-31~09-06 窗口內 6/7 天可驗證天數全數命中(09-03 該支排程本身缺席,無法驗證)。
- 使用度活躍 skill 數：17 → **21**（本週窗口內有 fire 紀錄的 skill 數,量級持平,非顯著變化）。
- **本週新發現，此前所有 retro 都未提及**：(a) `workflow-retro` 自己的排程失敗史（累計 6 次,含本次）；(b) W35 整週報告缺失；(c) sales-assistant 其實是已登記的擱置項而非遺忘的債；(d) 09-03 整批排程缺席的新模式；(e) 4 支 headless cron 全數缺乏 `claude -p` 逾時保護的架構性缺口。
