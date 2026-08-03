---
date: 2026-08-02
iso_week: 2026-W31
period: 2026-07-26 to 2026-08-02 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W31

## TL;DR

本週最重要的發現是把兩支持續兩週卡在「5/17 exit≠0」快照裡的失敗 agent **真正 root-cause 了**：`news_stock` 的 `research-agent` 與 `research-agent-weekly` 天天失敗，原因是 repo 從 `~/Documents/Projects/rivendell` 搬到 `~/code/rivendell` 後，`research-agent.sh` 的 `PROJECTS_DIR` 預設值沒跟著改，`source` 一支不存在的 `sk-exec-lib` 直接掛掉——這是純機械的一行修正（見下週 Action 1）。同時，上週 Action 1「`sales-assistant` 排程遷移二選一，這次真的執行」**再次落空**：本週窗口 7 份 harvest 報告全數點名同一件事，plist 的 working directory 逐一查證仍是 `/Users/manibari/code/sales-assistant`——這是第 3 週原地踏步，本報告不再客氣地列為必須執行項目。另一個新發現：daily tester 從 07-23 起連續 9 天回報同一筆 FAIL（`media/_shared` 缺 SKILL.md），但這其實是已知的合理設計（`_shared` 是共用腳本目錄，非 skill）——測試本身沒有排除規則，天天狼來了污染「ALL PASSED」的信任訊號。上週留下的兩個懸案本週有進度但未收尾：`/api/agents/{label}/runs` 這次換 5 個不同 agent label 交叉測試，**依然全部回傳空陣列**，連續第 2 個 retro 週期確認這不是單次故障，是端點沒接線；token 花費雙資料源分裂（`/api/tokens` vs `bin/sk audit`）落差從上週 3.6x 收斂到本週 2.7x，根因也抓到了——`bin/sk audit` 的計價表還停在舊 Opus-only 費率，而 `dashboard/lib/tokens.py` 這週已經在（未 commit 的）重寫中換成完整 model-specific 費率表，只是兩邊還沒對齊。集中度本身健康：本週最高佔比專案 PTI-ARES 只有 28.5%，沒有專案破 40% 門檻。

## 使用度

本週 usage API 追蹤範圍內共 **18 個 skill、36 次 firing**（上一份可比報告 W29：22 / 43——中間 W30 未產出報告，兩者間隔 2 週而非 1 週，數字下降需搭配這個空窗解讀，不宜直接當作使用度衰退）。

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+) | `crm-projection`(7 — 排程例行，指向 deprecated 專案，見重複痛點 Theme 1) | — |
| 低頻 (1-4) | `de-slopify`(4)、`office-pptx`(3)、`gstack-plan-eng-review`(2)、`gstack-qa-only`(2)、`slide-office-hours`(2)、`material-health`(2)、`subsidy-scraper`(2)、`subsidy-writer`(2)、`pitch-deck`(2)，以及各 1 次：`requirement`、`planning-with-files`、`local-media-transcribe`、`qa-journey`、`sales-deck-design`、`dataviz`、`gstack-codex`、`workflow-retro` | 快照 17 支中 **5 支 exit≠0**：`news_stock` `research-agent`/`research-agent-weekly`（本週已 root-cause，見下週 Action 1）、`rivendell` `doctor`（stderr 顯示 `Broken pipe`，屬暫時性、報告仍正常產出）、`rivendell` `tester`（對應已知的 false-positive FAIL，見重複痛點 Theme 3）、`rivendell` `janitor`（stdout/stderr 皆 0 bytes，無法從日誌判斷根因，待查） |
| 沉寂 (30+ days) | 12 支：`rbac-permissions`(06-12)、`claude-to-telegram`(06-13)、`gstack-autoplan`/`env-doctor`/`presales-pipeline`/`repro-exam`(06-15)、`client-kickoff-docs`(06-16)、`mops-financial-scraper`(06-23)、`gstack-plan-design-review`(06-27)、`spine-schema-sync`(06-29)、`gstack-plan-ceo-review`(06-30)、`chimesflow-design`(07-02) | — |

**值得注意**：
- `crm-projection` 連續兩份報告霸榜，本質是噪音——排程仍跑在 deprecated 的 sales-assistant 專案下，見重複痛點 Theme 1。
- `disk-monitor` 未列在 exit≠0 清單（launchd 快照顯示 exit=0），但實際上**已經 7 天沒有產出報告**（`reports/disk-capacity-*.md` 最後一筆是 07-26，`disk-monitor-stdout.log` mtime 同樣停在 07-26 16:58，排程是每日 03:30）。exit=0 只代表「上次成功執行」的殘留狀態，不代表「最近有執行」——這是本週意外驗證到的監控盲點，本身沒有錯誤訊息可查，列入下週觀察而非本週 action（見集中度）。
- 沉寂清單與 W29 幾乎重疊（少了 `mops-financial-scraper` 這次新滿 30 天），沒有新增沉寂候選，不代表異常。

## 重複痛點

### Theme 1：`sales-assistant` deprecated 專案排程遷移（連續 3 週原地踏步，本週 7/7 harvest 報告全數點名）

- **頻率**: W29 起連續追蹤，W29 的下週 Action 1 明確要求「這次真的執行」二選一。本週窗口（07-26～08-02）**7 份 harvest 報告全部**再次點名同一件事：`crm-projection`/`material-health`/`subsidy-scraper`/`tender-scraper` 四支排程 agent 的 launchd plist working directory 仍是 `/Users/manibari/code/sales-assistant`（本次逐一 `cat` plist 驗證，非僅憑 harvest 轉述）。
- **類別**: Mechanical（改 4 個 plist 的 working directory 指向 chimesflow；或明確決定「暫緩遷移」並在 `sales-assistant-deprecated` memory 補上原因與重新評估時間點——二擇一，非新開發）。
- **代表性事件**: 4 個 plist（`com.sk.agent.sales.{crm-projection,material-health,subsidy-scraper,tender-scraper}.plist`）的 `ProgramArguments` 全部仍指向 `/Users/manibari/code/sales-assistant`。
- **建議**: 連續第 3 週「觀察但不執行」不再是可接受的結果，本週必須真的做出選擇，見下週 Action 2（本次語氣加重，因為上週已承諾這次執行卻沒有）。

### Theme 2：`/api/agents/{label}/runs` 端點持續回傳空陣列（連續第 2 個 retro 週期，本週跨 5 個 label 驗證仍全空）

- **頻率**: W29 首次發現「所有 agent 的 `/runs` 查詢都回傳空陣列」。本週對 `doctor`、`janitor`、`tester`、`research-agent`、`research-agent-weekly` 5 個不同 label 逐一重新測試，**結果依然全部是空陣列**，跨兩週、跨不同 agent 集合重現，排除單次故障的可能。
- **類別**: Architectural——需要工程判斷這個端點到底有沒有接資料源，不是靠重跑排程能自癒的。
- **代表性事件**: `curl http://localhost:8000/api/agents/com.sk.agent.rivendell.doctor/runs` → `[]`；`launchctl list` 卻能查到同一 agent 的 exit code，代表底層資料其實存在（launchd 自己記得），只是沒有接進這支 API。
- **建議**: 這代表過去所有 retro 報告裡引用的「exit-code 歷史」其實從未真正來自 `/runs`，全部是快照替代——用同一句話講：**這個端點目前是裝飾用的**。下週需要一次性查清楚是前端沒接、後端沒寫、還是資料源本身沒被寫入，而不是繼續繞過它用快照湊數。

### Theme 3：Token 花費雙資料源分裂（連續第 2 週，本週落差收斂但根因已查明未修）

- **頻率**: W29 首次發現 `/api/tokens`（$2,199）與 `bin/sk audit`（$7,909.91）對同一 7 天窗口落差 3.6 倍。本週用正確參數（`date_start`/`date_end`，上週誤用的 `days=` 參數其實完全被後端忽略）重新查證：`/api/tokens/filtered` 回報本週 **$2,122.37**，`bin/sk audit` 本週回報 **$5,768.42**，落差收斂到 **2.7 倍**，但仍未對齊。
- **類別**: Mechanical——根因本週已查明：`dashboard/lib/tokens.py` 目前有一份**未 commit** 的重寫（`git diff` 可見），已經把定價表換成完整 model-specific 費率（`claude-sonnet-5`、`claude-opus-4-8` 等新模型都已補上）；但 `bin/sk`（`cmd_audit`）裡的計價邏輯**仍硬編碼寫死 Opus 單一費率**（`Opus input $15/M, output $75/M...`），對新模型完全沒有對應費率，兩邊注定越差越多。
- **代表性事件**: `bin/sk:2378` 的 `L_PRICING="Pricing: Opus input \$15/M..."` 是寫死字串，不會隨模型變動；`dashboard/lib/tokens.py` 的 `PRICING` dict 這週剛加了 6 個新模型的費率。
- **建議**: 見下週觀察清單——`tokens.py` 的重寫先 commit，再回頭把 `bin/sk audit` 的計價邏輯改成呼叫同一份 `PRICING` 表（或至少把費率同步），而不是各自維護一份計價表。本週未列入強制 action，因為重寫本身還在進行中，貿然催促 commit 可能打斷使用者手上的工作。

## 集中度

- **Token 集中**: 本週最高佔比專案 **PTI-ARES $605.88 / 28.5%**，未破 40% 門檻（第二名 Vault 26.9%，兩者相近，非單一專案獨大）。這是系列開跑以來少見的「健康」集中度週——上週 PTI-ARES 單週衝到 53.2%。（此數字取自 `/api/tokens/filtered?date_start=2026-07-26&date_end=2026-08-02`，正確參數版本；上週報告誤用 `days=7` 導致讀到全期累計數字，本週已修正查詢方式，見重複痛點 Theme 3 的方法論教訓）
- **失敗集中**: agent 快照 **5/17 exit≠0**，但拆解後只有 2 支是真正未解的新問題（`news_stock` 兩支 research-agent，root-cause 已查明，見下週 Action 1），`tester` 是已知 false positive，`doctor` 是暫時性 broken pipe（報告仍正常產出），`janitor` 日誌全空、原因待查（列入下週觀察，不足以本週定案）。
- **Dashboard 健康**: watchdog 本週僅一次極短暫事件（07-31 10:06-10:07，API/web 各 1 次 FAIL，1 分鐘內自行恢復，未觸發 RESTART），是系列中最乾淨的一週。
- **新發現盲點**: `disk-monitor` 排程 agent 的 launchd exit code 顯示 `0`（成功），但實際上已經 7 天沒有產出任何報告或日誌活動（見使用度小節）——這是本週意外撞見的「exit code 對，但根本沒在跑」情境，跟 Theme 2（`/runs` 端點空白）性質相近：現有監控介面只看得到「最後一次執行的結果」，看不到「有沒有在排定時間執行」。這兩個發現放在一起看,是本次 retro 最大的 meta 訊號:監控層本身有可信度落差,建議近期一併處理,而非逐一頭痛醫頭。

## 下週 Actions (max 3, prioritized)

1. **修 `news_stock` research-agent 系列的 stale `PROJECTS_DIR`** — Why now: 本週已完整 root-cause，`research-agent.sh` 第 8 行 `PROJECTS_DIR="${PROJECTS_DIR:-$HOME/Documents/Projects}"` 是 repo 從 `~/Documents/Projects/rivendell` 搬到 `~/code/rivendell` 之前的舊預設值，沒有這個環境變數就會 `source` 一支不存在的 `sk-exec-lib`，導致兩支 agent（daily + weekly）**每次排定執行都失敗**。修法二選一：(a) 在兩個 plist 的 `EnvironmentVariables` 加 `PROJECTS_DIR=/Users/manibari/code`；(b) 直接改腳本預設值。Est. effort: 5-10 min。Expected impact: 5/17 exit≠0 直接降到 3/17，且是本季度以來這兩支 agent 第一次有機會轉綠。

2. **`sales-assistant` 排程遷移二選一，本次不得再延** — Why now: 連續第 3 週被 harvest 報告點名（本週窗口 7/7 天），且是上週明確承諾「這次真的執行」卻落空的項目，純機械操作（4 個 plist 的 working directory）。二擇一：(a) 全部指向 chimesflow 並更新 memory；(b) 明確決定「暫緩遷移」，在 `sales-assistant-deprecated` memory 補上原因與重新評估時間點，且本週起 harvest 不再逐日複述同一件事（可在 harvest 規則加排除，若選 (b)）。Est. effort: 15-20 min。Expected impact: Theme 1 三週來首次歸零，且避免 retro 連續第 4 週寫同一段話。

3. **修 tester 的 `media/_shared` false-positive FAIL** — Why now: 07-23 起連續 9 天回報同一筆 FAIL，但 `_shared/` 是共用腳本目錄本來就不該有 SKILL.md（已記錄在 2026-07-23 的 LEARNINGS 條目），測試規則本身沒排除這個模式。9 天的「1 FAILURE(S)」污染了每日測試報告的可信度——真正的新 regression 出現時會被這筆固定雜訊淹沒。Est. effort: 10-15 min（在 tester 腳本裡對 `*/\_shared/` 或已知的共用目錄清單加排除規則）。Expected impact: 測試報告恢復「ALL PASSED」作為健康基準線的意義，未來新增的 FAIL 才會是真訊號。

**本週未列入 action 但建議下週持續觀察**（避免在證據不足時倉促行動）：
- `disk-monitor` 靜默停跑 7 天 — 需要先確認是排程本身沒觸發還是執行後零輸出，才能判斷是 mechanical 還是 architectural。
- `/api/agents/{label}/runs` 端點是否本來就沒接線 — 連續兩週空陣列已經是強訊號，但診斷本身需要讀後端程式碼而非再次觀察，適合下次直接排進 action 而非再觀察一週。
- `dashboard/lib/tokens.py` 的未 commit 重寫 — 屬於使用者手上進行中的工作，不搶著催促,待其完成後再對齊 `bin/sk audit` 計價表。

## 對照上週

上一份可比報告是 **W29（2026-07-19）**，W30（07-26 當週）未產出報告，兩者間隔 2 週。

W29 三個 actions 完成度：**1 / 3 部分進展，2 / 3 未完成**

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | `sales-assistant` 排程遷移二選一 | ❌ 未執行（第 3 週原地踏步） | 4 個 plist 的 working directory 逐一查證仍是 `/Users/manibari/code/sales-assistant`；本週 harvest 7/7 天再次點名 |
| 2 | 追查 workflow-retro W28 靜默跳過 + `/runs` 端點是否接線 | ⚙️ 部分進展 | W28 本身跳過的根因本次未追查（時間久遠、launchd log 可能已輪替），但 `/runs` 端點確認連續第 2 週對所有測試過的 label 回傳空陣列——問題範圍縮小到「端點沒接線」而非「單次故障」，尚待實際查程式碼定案 |
| 3 | 對齊 `/api/tokens` 與 `bin/sk audit` 計價/聚合口徑 | ⚙️ 部分進展 | 落差從 3.6x 收斂到 2.7x；根因查明為 `bin/sk` 計價表寫死舊費率 vs `tokens.py` 未 commit 的重寫已換新費率表——尚未真正對齊，但第一次有明確的技術路徑 |

指標變化（W29 → W31，W30 缺）：
- watchdog incidents：1 起事件簇（3 FAIL/2 RESTART，已修復）→ **1 次極短暫事件**（1 FAIL/0 RESTART，1 分鐘內自癒）——本週是系列最乾淨的一週。
- exit≠0 agent 數（快照）：5/17 → **5/17**（持平，但本週把其中 2 支的根因查清楚，性質從「不明退化」轉為「已知待修」）。
- skill-audit 待處理 issue：81（07-19 前後）→ **64**（07-26 視窗起點 62 → 08-02 終點 64，本週窗口內小幅回升 +2，非上週回報的 W27→W29 大幅上升趨勢延續）。
- skill 總數：109 → **116**（新增 `context-journal`、`media/` 分類等，符合本週 skill 上新的觀察）。
- usage 總 firing：43 → **36**，活躍 skill 數 22 → **18**（兩週間隔導致基期不同，不當作衰退解讀，見使用度小節說明）。
- 7 日 token 花費：`/api/tokens` 路徑 $2,199 → **$2,122.37**（持平，方法論已修正為正確查詢參數）；`bin/sk audit` 路徑 $7,909.91 → **$5,768.42**（下降，兩份都是各自資料源內部的真實下降，非彼此收斂到位）。
- 集中度：PTI-ARES 53.2%（單週最高紀錄）→ **28.5%**（本季度最健康的一週）。
