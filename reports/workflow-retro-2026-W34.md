---
date: 2026-08-23
iso_week: 2026-W34
period: 2026-08-17 to 2026-08-23 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W34

## TL;DR

W33 的三個 action **再次 0/3 完成** —— 這是連續第 3 個週期全數落空，累計 9 個已給精確修法的 action 中 0 個被執行。五個舊痛點原封不動：`dashboard/lib/db.py:6` 的 `DB_PATH` 檔名不一致（`/api/agents/{label}/runs` 仍回傳 `[]`，這是連續第 5 個週期同一發現）、`bin/sk:489` 的 byte-based 截斷讓 `skill-audit` 報告損毀（本週 7/7 天再中，累計連續 **20 天**未間斷，自 08-03 起從未修復）、`tester` 的 `media/_shared` false-positive（累計連續 **31 天**，自 07-23 起）、`sales-assistant` deprecated 專案的 4 支排程 plist 仍未遷移（`crm-projection` 本週 5 次執行全部跑在 `/Users/manibari/code/sales-assistant` 底下）、`news_stock` 兩支 plist 仍缺 `PROJECTS_DIR` 環境變數。本週新發現：`/api/agents` 快照的 `exit_code` 欄位很可能與 `/runs` 端點共用同一個壞掉的 `rivendell.db`（本週 `harvest` 標記 exit=1，但同期產出的三份 harvest 報告內容完整、無對應 stderr）——代表修 Action 1 的 DB_PATH 不只修 `/runs`，連 `/api/agents` 列表本身顯示的失敗狀態都可能是假的。另外 `/api/tokens/filtered` 對 PTI-ARES 的佔比讀數從 W33 記錄的 36.5%（$5,242.34）跌回本週的 29.7%（$4,020.04）——同一個全期累計欄位理論上只增不減，這個倒退本身就是資料品質問題，已併入集中度章節。本週活動量正常（69 sessions），watchdog 乾淨。**本週最重要的發現不是新增痛點，而是「重複提醒不再有效」這件事本身**——見下週 Actions 前的說明。

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+ this week) | `requirement`(5)、`crm-projection`(5 — 仍指向 deprecated 專案，見重複痛點) | — |
| 低頻 (1-4 this week) | `chimesflow-design`(3)、`mockup`(2)、`qa-dataflow`(2)、`task-brief`(2)、`material-health`(2)、`subsidy-scraper`(2)、`workflow-retro`(2)，各 1 次的 8 支（`odb-dfm-reference`、`mermaid-diagram`、`user-flow`、`gstack-plan-eng-review`、`spine-versioning`、`claude-api`、`gstack-careful`、`resolving-merge-conflicts`） | 快照 17 支中 **7 支 exit≠0**：`research-agent`/`research-agent-weekly`（news_stock，見重複痛點）、`doctor`（已知間歇性，非新問題）、`tester`（已知 false-positive，見重複痛點）、`material-health`（連續第 2 週出現非 0，見下方說明）、`harvest`（本週新出現，疑似假訊號——見 TL;DR）、`token-analysis`（08-21、08-22 兩天 error log 確認 `ENOTFOUND` DNS 失敗） |
| 沉寂 (30+ days) | 5 支：`gstack-qa`(07-20)、`youtube-transcript`(07-22)、`sales-material`/`repo-rename`/`sow-writer`(07-23) | — |

**值得注意**：
- 本週追蹤範圍 **55 支 skill、17 支活躍、33 次 firing**（W33 讀數是 68/26/47——skill 總數的落差推測是 API 統計窗口變動，非本週新增痛點，暫不深究）。
- `material-health` 的 exit=1 上週被判定為「單次事件」（max_turns），本週再次出現在快照裡。因為 `/runs` 端點壞掉，無法確認這是**同一次舊紀錄殘留**還是**本週新的一次失敗**——這正是 Action 1（修 DB_PATH）會直接解決的盲區,不單獨升級為新主題。
- `harvest` 首次出現在 exit≠0 清單，但本週三份 harvest 報告（08-20/21/22）內容完整、對應 error log 皆為 0 bytes，判斷是快照顯示問題而非真實失敗，進一步佐證 TL;DR 提到的「`/api/agents` 的 exit_code 欄位也可能讀到壞掉的 db」。

## 重複痛點

### Theme 1：`skill-audit` 報告 UTF-8 損毀，累計連續 20 天未修（08-03 起）

- **頻率**: 本週窗口 `skill-audit-2026-08-{17~23}.md` 逐一用 Python `utf-8` decode 驗證，**7/7 天全部損毀**，錯誤位置與型態與前兩週記錄完全一致（`invalid continuation byte`，落在 ~23,840-23,880 bytes 附近）。加上 W32、W33 記錄的 08-03~08-16，**累計連續 20 天**。
- **類別**: Mechanical——修法已知，第 4 次提出同一行修法。
- **代表性事件**: `bin/sk:489`（逐字未變）：
  ```bash
  [ "${#val}" -gt 120 ] && val="${val:0:117}..."
  ```
  非 UTF-8 aware locale 下用位元組計數／截斷，砍在多位元組中文字元中間。
- **建議**: 見下週 Actions。

### Theme 2：`sales-assistant` deprecated 專案排程遷移，5 週未動

- **頻率**: 本週 `crm-projection`(5 次)、`material-health`(2 次) 執行紀錄仍在 dashboard 顯示；重新 `grep` 4 支 plist（`com.sk.agent.sales.*`）的 `ProgramArguments`，working directory 依然全部是 `/Users/manibari/code/sales-assistant`。
- **類別**: Mechanical（純粹沒空做）。
- **建議**: 見下週 Actions。

### Theme 3：`news_stock` research-agent 缺 `PROJECTS_DIR`，3 週未套用

- **頻率**: 兩支 plist（`research-agent`／`research-agent-weekly`）的 `EnvironmentVariables` 本週再次確認**只有 `PATH`**；agent 快照仍是 `exit=1`。
- **類別**: Mechanical——修法（plist 加一行 env var）已知 3 週。
- **建議**: 見下週 Actions。

### Theme 4：tester 的 `media/_shared` false-positive FAIL，累計 31 天（07-23 起）

- **頻率**: `test-2026-08-{17~23}.md` 逐一確認同一筆 `media/_shared | SKILL.md missing | FAIL` 依然存在，本週 7/7 天全中，累計 **31 天**連續出現。
- **類別**: Mechanical——`_shared/` 是共用腳本目錄，本就不該有 `SKILL.md`。
- **建議**: 見下週 Actions。

### Theme 5：`/api/agents/{label}/runs` 端點連續 5 個 retro 週期回傳空陣列，根因已知未修

- **頻率**: 連續第 5 個週期（W29、W31、W32、W33、W34）`curl localhost:8000/api/agents/com.sk.agent.rivendell.tester/runs` 回傳 `[]`。W33 已查出根因：`dashboard/lib/db.py:6` 的 `DB_PATH` 指向空的 `rivendell.db`，實際寫入的是 `sk-dashboard.db`（本週再次確認 db.py 第 6 行逐字未變）。
- **類別**: Mechanical——一行路徑修正。
- **建議**: 見下週 Actions。

### Theme 6：`/api/tokens/filtered` 忽略 `days=` 參數，連續 4 個週期未修

- **頻率**: 本週 `?days=7` 回傳仍是全期 144 天累計（W31、W32、W33 記錄同一限制）。
- **類別**: Mechanical/Architectural 邊界——需要後端加真正的日期篩選邏輯，非一行修法，可能是這批問題裡唯一不是「順手就能修」的一項。
- **代表性事件**: 本週用同一個全期累計欄位算出 PTI-ARES $4,020.04 / 29.7%，與 W33 記錄的 $5,242.34 / 36.5% 不一致——理論上只增不減的累計數字倒退，這不只是「不支援週篩選」，更像是底層資料本身在兩次讀取之間發生了變動（清理／回填／去重都有可能），已併入集中度章節，暫不歸因。
- **建議**: 本週不排入 action（範疇比其他 5 項大），但下次有 rivendell 維運時間應優先於「已知修法沒空做」的幾項。

## 集中度

- **Token 集中**: 全期累計讀數 PTI-ARES **$4,020.04 / 29.7%**（total $13,515.19）。與 W33 讀數 $5,242.34 / 36.5% 不一致，見 Theme 6——本週用同一份 `/api/tokens` 與 `/api/tokens/filtered` 交叉驗證,兩端點數字一致（互相印證非單一端點的抓取錯誤,但無法排除底層資料本身在週期間變動)。本週窗口（08-17~08-23）加總可算出：**$2,118.97 / 69 sessions**，逐日分布集中在 08-17（$389）、08-20（$811）、08-21（$701）三天，但無法拆分到專案層級確認佔比。
- **失敗集中**: agent 快照 **7/17 exit≠0**（W33 是 6/17，表面惡化）。其中 5 支是舊病（Theme 2、3、4 對應的 4 支 + `doctor`），另外 2 支（`harvest`、`token-analysis`）本週首次出現：`harvest` 判斷為假訊號（見使用度說明）；`token-analysis` 有明確 error log 佐證（08-21、08-22 兩天 `ENOTFOUND`），屬單次網路瞬斷，非結構性問題。
- **Dashboard 健康**: watchdog 本週窗口內僅 1 筆事件（08-20 23:36，api + web 各 1 次 FAIL，1 分鐘內自行恢復，0 次 RESTART）——連續第 4 週維持乾淨紀錄。
- **併發風險複核**: 本次執行時同步確認排程版 `com.sk.agent.rivendell.workflow-retro`（`bin/sk-workflow-retro-cron`）於今晚 23:00 啟動的行程（pid 86638/86656）**就是本次撰寫這份報告的行程本身**——不是 W32、W33 記錄的「手動觸發與排程版撞期」，本週沒有出現雙寫競態。上週懷疑的「Sunday 23:00 撞期模式」這次沒有重現,可能是巧合而非固定模式,不再視為已確認的週期性問題。

## 下週 Actions (max 3, prioritized)

**先說明**：Theme 1、2、3、4、5 全部是「已給精確修法、純粹沒空做」，累計已提出 9 次、完成 0 次。繼續逐週重複同樣的建議文字邊際效益已經趨近於零——與其再寫第 4、5、6 次「請修這一行」，這裡改成**把 5 項壓縮成一次性的維運 checklist**，供下一個有時間做 rivendell 維運的 session 直接照做，而不是要求 retro 自己再產生新的說服力：

1. **一次性清償 checklist（5 項，預估總工時 40-60 分鐘）** — 全部是已知修法、獨立不互相依賴，建議同一個 session 一次做完，不要再拆成「下週再看」：
   - `dashboard/lib/db.py:6` `DB_PATH` 改成指向 `sk-dashboard.db`（或建 symlink），`launchctl bootout`/`bootstrap` `com.sk.dashboard.api` 後驗證 `curl localhost:8000/api/agents/com.sk.agent.rivendell.tester/runs` 不再是 `[]`。**優先度最高**——這是唯一會讓後續每週的「失敗集中」判讀從猜測變成事實的一項，且可能連帶修正 `harvest`/`material-health` 的假陽性 exit_code。
   - `bin/sk:489` 的 `${#val}`/`${val:0:117}` 改用 `LC_ALL=en_US.UTF-8` 或 `awk`/`cut -c` 做字元計數，驗證含中文長描述的 `sk audit` 輸出可被 `utf-8` decode。
   - `test-*.md` 裡 `media/_shared` 的 FAIL：讓 tester 腳本排除沒有 `SKILL.md` 天經地義的 `_shared/` 目錄。
   - `news_stock` 兩支 plist 各加一行 `<key>PROJECTS_DIR</key><string>/Users/manibari/code</string>`，reload 生效。
   - `sales-assistant` 遷移二選一並寫回 memory：(a) 4 支 plist working directory 改到新專案；或 (b) 明確記錄「暫緩」+ 下次評估時間點，讓 harvest 未來不再逐日複述。

2. **（若上面 5 項本週仍然沒空做）至少先做 DB_PATH 一項** — 這是 5 項裡投資報酬率最高的單一動作：5 分鐘工時，解開連續 5 週的資料盲區，且可能順帶證實/推翻本週對 `harvest`/`material-health` 假陽性的猜測。

3. **不要求下週 retro 再次重複這份 checklist** — 若下週執行完仍是 0/5，代表問題不在「retro 沒講清楚」，值得考慮的是把這 5 項直接轉成 GitHub issue / TODO 檔案，脫離 retro 週期,由使用者自己排入行事曆,而不是繼續讓 retro 每週產生同一份清單造成閱讀疲乏。

## 對照上週

上一份可比報告是 **W33（2026-08-16）**。

W33 三個 actions 完成度：**0 / 3 全數未完成**（連續第 3 個週期全部落空，累計 9 個已給精確修法的 action 中 0 個被執行）：

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | 修 `dashboard/lib/db.py:6` DB_PATH 檔名不一致 | ❌ 未執行 | 程式碼逐字未變；`/api/agents/{label}/runs` 本週仍回傳 `[]` |
| 2 | 修 `bin/sk:489` byte-based 字串截斷 | ❌ 未執行 | 程式碼逐字未變；本週 7/7 天 skill-audit 報告仍損毀在同一位置附近 |
| 3 | news_stock PROJECTS_DIR + sales-assistant 遷移二選一 | ❌ 未執行 | 兩個 plist 仍無 `PROJECTS_DIR`；4 個 sales plist working directory 仍是 `sales-assistant` |

指標變化（W33 → W34）：
- watchdog incidents：1 次極短暫事件 → **1 次極短暫事件**（同等級，連續第 4 週維持系列最乾淨紀錄）。
- exit≠0 agent 數（快照）：6/17 → **7/17**（表面惡化，但新增的 2 支中 1 支疑似假訊號、1 支是單次 DNS 瞬斷，非結構性退化）。
- skill-audit 損毀連續天數：13 天 → **20 天**（再累加 7 天，未間斷）。
- tester false-positive 連續天數：24 天 → **31 天**（再累加 7 天）。
- usage 活躍 skill 數：26 → **17**（API 統計窗口疑似變動，見使用度章節，非確認的真實下滑）。
- 集中度：PTI-ARES 讀數從 36.5%（$5,242.34）→ **29.7%**（$4,020.04）——同一累計欄位不應該倒退，判斷為資料品質問題而非真實下降,見 Theme 6。
- **本週未重現（W32、W33 出現過的）**：Sunday 23:00 手動觸發與排程版併發覆寫的競態，本次確認執行行程本身就是排程版，沒有第二個寫入者，暫不視為已確認的固定模式。
- **本週新發現**：`/api/agents` 快照的 `exit_code` 欄位可能與 `/runs` 端點共用同一個壞掉的 db（`harvest` 本週的假陽性 exit=1 是佐證）——強化了 Action 1 的優先度，這不只是修一個裝飾性端點,而是可能連帶修正整份「失敗集中」章節的可信度。
