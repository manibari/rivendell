---
date: 2026-07-19
iso_week: 2026-W29
period: 2026-07-13 to 2026-07-19 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W29

## TL;DR

本週最大的事件是**上週的治理懸案自己到期了**：W27 幫 `knowledge-graph`／`demo-anonymize` 設下「W28 無決定即套用預設」的終結條款，但 **W28（07-12）workflow-retro 本身靜默跳過**——沒有報告檔、沒有 error log，`/api/agents/{label}/runs` 對所有 agent 都回傳空陣列，查不出原因。本週是條款第一次可執行的週期，本報告依約定**正式關閉這兩項**（詳見重複痛點）。基礎設施面則是一次「壞了又自己修好」的健康案例：07-18 晚間 dashboard API 死亡螺旋復發（3 次 FAIL→RESTART），但使用者同晚 23:13 就 root-cause 並發版 0.2.1，此後零事件——agent 快照因此從上週全綠的 0/17 exit≠0 倒退到 5/17，但那筆最大的（API 本身）已經修完，不是累積中的問題。另一個新發現：**同一週兩個 token 資料源對同一 7 天窗口打架**——`/api/tokens` 報 $2,199，`bin/sk audit` 報 $7,909.91，落差 3.6 倍——巧的是使用者這週才剛修過 `/tokens` 頁面的「誠實計價」（commit `2ce76e7`），但只動到前端，後端聚合口徑還沒對齊。真正持續未解的痛點只剩一個：`sales-assistant` deprecated 專案的排程殘留，本週窗口內**連續 4 份 harvest 報告**（07-13/17/18/19）都點名同一件事,用語逐次升溫,卻仍未執行。

## 使用度

本週 usage API 追蹤範圍內共 **22 個 skill、43 次 firing**（W27：19 / 43 — 總量持平，活躍 skill 數上升）。

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+) | `crm-projection`(5，排程例行，見 Theme 2) | — |
| 低頻 (1-4) | `requirement`(4)、`planning-with-files`(4)、`mockup`(3)、`user-flow`(3)、`gstack-plan-eng-review`(3)、`office-hours`(3)、`gstack-qa`(2)、`context-recovery`(2)、`gstack-design-consultation`(2)，以及各 1 次：`task-brief`、`gstack-office-hours`、`gstack-ship`、`spine-auth`、`office-docx`、`material-health`、`repo-rename`、`spine-versioning`、`workflow-retro`、`session-harvest`、`gstack-context-save`、`gstack-context-restore` | 快照 17 支中 **5 支 exit≠0**（news_stock `research-agent`/`research-agent-weekly`、rivendell `doctor`/`janitor`、sales `subsidy-scraper`）——較 W27 的 0/17 全綠倒退，詳見集中度 |
| 沉寂 (30+ days) | usage API 只追蹤「曾 fire 過」的 47 支，其中 8 支 30+ 天未動：`rbac-permissions`(06-12)、`skill-creator`/`claude-to-telegram`(06-13)、`gstack-autoplan`/`env-doctor`/`presales-pipeline`/`repro-exam`(06-15)、`client-kickoff-docs`(06-16)。真正的沉寂訊號在 skill-audit 的 **61 支「可能棄用」**（90+ 天 mtime，W27: 44，依 W26 判例視為債務水位計、不逐條追蹤） | — |

**值得注意**：
- `crm-projection` 連續霸榜且是噪音——它排程仍跑在 deprecated 的 sales-assistant 專案下（見 Theme 2）。
- `gstack-context-save`／`gstack-context-restore` 本週首次出現 firing 紀錄，與同週新建（尚未 commit）的 `workflow/context-journal` skill 時間點吻合，屬預期中的新功能採用訊號，非異常。
- `requirement`(3→4)、`planning-with-files`(3→4) 續熱，`user-flow`(4→3)略降——與 token 集中度顯示的 PTI-ARES/mops-dbs 產品打磨期一致（見集中度）。

## 重複痛點

### Theme 1：`knowledge-graph` 二選一決策鏈（連續 7 次未動 → 本週依預設條款關閉）

- **頻率**: W19/W20/W22/W25/W26/W27 連續 6 次 retro 追蹤，W27 設下「W28 無決定即視為選項 (b)」的終結條款。W28（07-12）workflow-retro **未產出報告**，條款延後一週才第一次有機會執行。
- **類別**: Architectural → 本週執行預設，**正式關閉**。
- **代表性事件**: `skills/meta/knowledge-graph` 仍存在、usage API 仍 0 紀錄、git log 全歷史查無相關 commit。
- **建議**: 依 W27 Action 1 的預設條款——本報告即為「W28 無人決定」後的執行點，正式視為選項 (b)：**保留該 skill，但從此不再於 workflow-retro 逐週追蹤**。Theme 1 到此為止，不應再出現在未來 retro。

### Theme 2：`sales-assistant` deprecated 專案排程殘留（本週窗口內 4/4 份 harvest 連續點名，語氣逐次升溫）

- **頻率**: 本週窗口 07-13、07-17、07-18、07-19 **四份 harvest 報告全部**重複同一觀察——`crm-projection`/`material-health`/`subsidy-scraper`/`tender-scraper` 四支排程 agent 仍全部掛在已標記 deprecated 的 `sales-assistant` 專案下。07-17 起用語從「觀察」升級為「應提高優先度」，07-18 再強調「連續兩輪」，07-19 仍在發生。API 交叉驗證：`com.sk.agent.sales.*` 四支 `working_directory` 目前確實仍是 `/Users/manibari/code/sales-assistant`，`loaded=true` 持續產出。
- **類別**: Mechanical（改 4 個 plist 的 working directory 指到 chimesflow，或明確決定「暫緩遷移」並在 memory 註記原因——二擇一，非新開發）。
- **代表性事件**: 07-19 harvest：「Session 3 直接對 sales-assistant 專案下的 `crm-projection` skill 下指令」——deprecated 專案不只排程還在跑，連互動操作都還在對著它。
- **建議**: 本週必須二選一執行，不再留第 5 次觀察，見下週 Action 1。

### Theme 3：`demo-anonymize` 候選懸案（跨 6+ 週 n≥2 未建 → 本週依預設條款關閉）

- **頻率**: W25 起連續提及，W27 Action 3 設下「W28 無動作即除名」。W28 未執行（同 Theme 1 的通道空窗），本週為首次可執行的週期。
- **類別**: Architectural → 本週執行預設，**正式除名**。
- **代表性事件**: `find skills -iname '*anonymize*'` 查無結果；git log 全歷史查無相關 commit；07-13~07-19 七份 harvest 報告完全未再提及此候選（需求自然消退，而非主動決策）。
- **建議**: 依預設條款除名，不再列入候選追蹤清單。

## 集中度

- **Token 集中**: skill-audit 7 日視窗顯示 **PTI-ARES $4,203.75 / 53.2%**（總計 $7,909.91，>40% 門檻，且是本系列首次由單一產品衝破 50%；W27 最高集中專案 mops-dbs 僅 22.7%）。但**同一週兩個資料源對「7 天總花費」打架**：`/api/tokens` 回報 **$2,199 / 103 sessions / 5.5M 輸出 tokens（+1550.7M cache）**，`bin/sk audit` 回報 **$7,909.91 / 3010.9M tokens**——$ 落差 3.6 倍、token 落差近 2 倍。使用者本週才剛修過 `/tokens` 頁面的「誠實計價」（commit `2ce76e7`：拆產出/context 重讀/估算花費三軸，標記舊 `$total_cost_usd` 為虛構），但目前只動到前端呈現層，`/api/tokens` 聚合欄位與 `bin/sk audit` 的計價/聚合邏輯都還沒跟上同一套口徑。**在兩個資料源對齊之前，「PTI-ARES 是否過度集中」這個判斷本身建立在不可信的分母上**，建議先修資料源、再評估是否要真的採取行動。
- **失敗集中**: agent 快照 **5/17 exit≠0**（`news_stock/research-agent`、`news_stock/research-agent-weekly`、`rivendell/doctor`、`rivendell/janitor`、`sales/subsidy-scraper`）——較 W27 的 0/17 全綠倒退。其中最重大的一筆其實已經解決：**dashboard API 自身的死亡螺旋復發**——07-18 22:33-23:10 watchdog 記錄 3 次 FAIL→RESTART 循環，但使用者同晚 23:13 即 root-cause 完成並發版 **0.2.1**（`d3f2877`：per-file JSONL cache + 單次 launchctl dump，取代舊有每 agent 逐一 launchctl 的 18 秒開銷），此後**零事件**——是「觀測到→修復」的健康循環，不是累積中的退化。其餘 4 支（news_stock ×2、doctor、janitor）為間歇性問題，尚待下週快照確認是否持續。
- **Dashboard 健康**: watchdog 本週僅這一起事件簇（3 FAIL / 2 RESTART，07-18 22:33-23:10），事發後已根治並發版，週其餘時間 0 FAIL / 0 RESTART。
- **Meta（新發現）**: workflow-retro 自己在 **W28（07-12，週日）靜默跳過**——沒有報告檔、沒有 error log；`/api/agents/{label}/runs` 對本次檢查的所有 agent（harvest、doctor、janitor、workflow-retro）都回傳空陣列，無法從 API 端佐證原因，只能靠快照/`launchctl list` 推測。這正是「捕捉可靠性缺口的工具，自己出現了一次未被偵測的可靠性缺口」——值得下週追查根因，見 Action 2。

## 下週 Actions (max 3, prioritized)

1. **`sales-assistant` 排程遷移二選一，這次真的執行** — Why now: 本週窗口內連續 4 份 harvest 報告點名同一件事、語氣逐次升溫，且是純機械改動（4 個 launchd plist 的 working directory）。二擇一：(a) 全部指向 chimesflow 並更新 memory；(b) 明確決定「暫緩遷移」，在 `sales-assistant-deprecated` memory 補上原因與重新評估時間點。Est. effort: 15-20 min。Expected impact: Theme 2 歸零，且避免持續有新資料寫進判定為死專案的目錄。

2. **追查 workflow-retro 為何 W28（07-12）靜默跳過，並確認 `/api/agents/{label}/runs` 是否本來就沒接線** — Why now: 這兩個問題疊在一起，代表 retro 系列自己的可靠性目前**無法從資料驗證**——如果 `/runs` endpoint 從未真正回傳過資料，那麼過去 7 週 retro 報告裡引用的「exit-code 歷史」其實一直只來自快照，需要在文件裡誠實標注這個限制；如果 W28 是真的排程/launchd 故障，需要知道是否也影響了同日的 `janitor`（同為週日排程，快照也顯示 exit=1）。Est. effort: 30-45 min（查 launchd log、`agents.conf`、`launchctl list` 歷史）。

3. **對齊 `/api/tokens` 與 `bin/sk audit` 的計價/聚合口徑** — Why now: 使用者本週才做完 `/tokens` 頁面的誠實化重構，趁勢把後端聚合欄位與 skill-audit 報表產生器一併對齊，避免兩個資料源永久分裂成「兩套各自為政的假帳」。目前 3.6x（$）與 ~2x（token）的落差已經大到會誤導集中度判斷（見上）。Est. effort: 30-60 min。Expected impact: 下週起集中度分析可信任同一組數字，`>40%` 這類門檻判斷才有意義。

## 對照上週

W27 三個 actions 完成度（原機制直接完成）：**0 / 3**——但本週依 W27 自訂的「W28 無動作即套用預設」條款，把其中 2 項正式終結（非經主動執行，而是條款到期生效）。

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | `knowledge-graph` 二選一 | ⚙️ 依 DEFAULT 關閉為 (b) | W28 未產出報告，本週為條款第一次可執行週期，已依約定關閉，未來不再追蹤 |
| 2 | harvest wrapper 兩修一次做 | ❌ NOT DONE（第 3 週） | git log 查無 `session-harvest`/`sk-harvest-cron` 相關 commit；07-13~07-19 harvest 報告仍需手動點名 sales-assistant 殘留，佐證過濾機制未修 |
| 3 | `demo-anonymize` 建掉或除名 | ⚙️ 依 DEFAULT 除名 | `find` 查無此 skill；07-13~07-19 七份 harvest 完全未再提及（需求消退）；依條款除名 |

指標變化（W27 → W29，W28 缺）：
- watchdog incidents：0 FAIL/0 RESTART → **1 起事件簇**（3 FAIL/2 RESTART，07-18）但同日根治並發版 0.2.1，此後 0——單一污點已修，非累積退化。
- exit≠0 agent 數（快照）：0/17 → **5/17**——倒退（news_stock ×2、doctor、janitor、subsidy-scraper）。
- skill-audit 待處理 issue：63 → **81**（+29%），其中「可能棄用」44→61；依 W26 判例，視為債務水位計，不逐條列為獨立缺陷。
- skill 總數：108 → **109**（新增尚未 commit 的 `context-journal`）。
- usage 總 firing：43 → **43**（持平），活躍 skill 數 19→**22**。
- 7 日 token 花費：資料源分裂，見集中度——兩個系統本週互相打架（$2,199 vs $7,909.91），無法給出可信的單一數字對比 W27 的 $15.1k。
- retro action 完成率：0/3 → **0/3 直接完成，2/3 經預設條款終結**——長期懸案（Theme 1、Theme 3）本週淨減少，是系列開跑以來的第一次。
