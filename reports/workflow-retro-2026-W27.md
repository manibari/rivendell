---
date: 2026-07-05
iso_week: 2026-W27
period: 2026-06-29 to 2026-07-05 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W27

## TL;DR

Infra 面是 retro 系列開跑以來**最乾淨的一週**：watchdog **0 FAIL / 0 RESTART**（W26: 4 FAIL），**17/17 agent 快照全 exit 0**——news_stock 兩支 `research-agent` 七週來首次轉綠，W26 點名的 `doctor`/`janitor` 也在快照轉綠（`doctor` 週中仍有一次 exit 1，屬間歇未根治）。使用度 43 firing / 24 skill，firing 總量與 W26 持平但更分散；新建的 `spine-versioning`/`spine-schema-sync` 當週就有實戰 firing，對照 audit 44 支 90 天沒動的長尾，再次驗證 demand-driven 抽取的命中率。

兩個結構性訊號：**(1)** 連 5 週卡住的「per-project token 歸因」缺口，本週被大幅收窄——但**不是經由 retro 清單**，是使用者自己的 flow（`token-analysis` 每日 agent + per-project SQLite 持久化 + dashboard /tokens 頁，commit 46cb94e/02c8bae/a88f647）。**(2)** W26 的二選一最後通牒（退 `knowledge-graph` 或停 retro agent）**無人回應**，三個 action 完成 **0/3**，`knowledge-graph` 連續**第 6 週**未動。兩件事拼起來，meta-結論已經不是「內容不對」而是「**通道失效**」：寫在報告裡的決策請求沒有被讀到/回應的路徑，落在使用者 flow 裡的事才會動。本週 Action 1 不再重寫通牒，而是**換通道**（下個互動 session 直接提問 + 無回應即自動除名的 default），讓這條延期鏈無論如何在 W28 終結。

## 使用度

本週 usage API 追蹤範圍內共 **24 個 skill、43 次 firing**（W26：19 / 43 — 總量持平、分散度上升）。

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+) | `crm-projection`(6，排程例行) | — |
| 低頻 (1-4) | `user-flow`(4)、`gstack-office-hours`(3)、`planning-with-files`(3)、`gstack-plan-eng-review`(3)、`office-pptx`(3)、`requirement`(3)、`chimesflow-design`(2)，以及各 1 次：`task-brief`、`gstack-browse`、`mermaid-diagram`、`gstack-plan-ceo-review`、`mockup`、`office-docx`、`gstack-qa`、`subsidy-scraper`、`material-health`、`gstack-design-consultation`、`context-recovery`、`spine-schema-sync`、`spine-versioning`、`repo-rename`、`sow-writer`、`workflow-retro` | 17 支全部 exit 0 快照（W26：16 中 4 支 exit 1）；本週新增 `token-analysis`(23:45)、`token-snapshot`(2:30) 兩支 |
| 沉寂 (30+ days) | usage API 結構限制同 W26（只追蹤曾 fire 過的 42 支，42 支近 30 天全有紀錄）；真沉寂訊號在 skill-audit 的 **44 支「可能棄用」**（90+ 天 mtime，W26: 41）。`knowledge-graph` usage 依舊 **0 紀錄** | — |

**值得注意**：
- **`requirement`(5→3)、`user-flow`(5→4)、`mockup`(4→1) 同步降溫**——ChimesFlow UI 建構潮退峰，工作重心轉到 PTI-ARES / IC-YMS / tukey-bi / mops_dbs 的產品打磨（harvest session 分佈同樣指向此）。
- **`spine-versioning`（06-28 才建）與 `spine-schema-sync` 當週即實戰 firing**，且 rivendell 自己也吃了 spine-versioning 的藥（本週 repo 新增 `VERSION`/`CHANGELOG.md`）。demand-driven 抽出來的 skill 立刻被用，對照 44 支 90 天長尾——抽取紀律有效的直接證據。
- 榜首 `crm-projection` 是排程例行，且 sales-assistant 已標 deprecated（遷移 chimesflow 中）——它霸榜是噪音不是訊號。

## 重複痛點

### Theme 1：retro 決策類 action 的「通道」失效（第 6 次，升級為 meta-finding）

- **頻率**: W19/W20/W22/W25/W26/W27 連續 6 次 retro。W26 已把它設計成二選一最後通牒，本週 `skills/meta/knowledge-graph` 仍在原地（usage 0 紀錄）、retro agent 也照常排程執行——**兩個選項都沒被選**。
- **類別**: Architectural（不是內容問題，是 delivery 問題：報告裡的決策請求沒有「被回應」的路徑）。
- **代表性事件**: 同週對照組——連 5 週的 per-project token 缺口，本週被使用者**自主**建掉 80%（見集中度）。落在使用者 flow 裡的事會動；躺在報告裡的事不動。
- **建議**: 換通道 + 自動終結 default，見 Action 1。**W28 起本項不得再以相同形式出現在 retro 裡**。

### Theme 2：排程 session 污染 harvest 取樣（W26 Action 2 未執行，痛點如期重現）

- **頻率**: 本週 **5/5 份** harvest 報告（06-29、07-01、07-02、07-03、07-05）都得先花篇幅排除 `crm-projection`/`subsidy-scraper`/`material-health` 的排程執行——合計 **8/24 個取樣 session 是排程重跑**（06-29 最嚴重：4 個 session 有 3 個）。加上 W26 已點名，跨兩週 11+ 次。
- **類別**: Mechanical（取樣前置過濾，做法 W26 已寫明：session cwd 比對 `com.sk.agent.*` plist 的 `working_directory`）。
- **代表性事件**: 07-05 harvest 4 個 session 只有 1 個（mops-dbs 建庫，172 msgs）是真正可收割的人類工作流。
- **建議**: 見 Action 2。另外本週新增一個同源小病：**07-05 的 harvest 報告以對話式收尾**（「要不要我把這份報告寫進 reports/…先問你」）——headless agent 的 prompt 滲漏出互動行為，報告開頭還留著「我已比對現有 skills，可以產出報告了」的對話語氣。n=1 不獨立成 theme，但修 wrapper 時應同批處理（prompt 明示：直接落檔、不反問）。

### Theme 3：harvest→build 鏈——問題已收斂成「只欠 n≥2 的那兩支」（第 6 週）

- **頻率**: W19 起連續母題。本週 5 份 harvest 產出 **6 支 Moderate 候選、0 Strong**（`api-key-auth`、`canvas-render-fidelity`、`double-entry-ledger`、`retail-replenishment-dashboard`、`ic-yms-solution-narrative`、`postgres-multidb-bootstrap`），**全數自律標 n=1 → 觀察**，引用的都是「第二實例才驗證抽象」紀律。
- **類別**: Architectural，但範圍已收窄——本週的「0 build」是紀律的**正確輸出**，不是斷鏈；真正斷的只剩「達到 n≥2 門檻卻不建」：`demo-anonymize`（W25 起）與 `phm-soft-sensor`（n=2，跨 06-10/06-26）。
- **代表性事件**: W26 Action 3 明文把 `demo-anonymize` 當「鏈會不會動」的測試——第 2 次流標。
- **建議**: 見 Action 3——建掉或除名，二擇一，讓 Theme 3 歸零。

## 集中度

- **Token 集中**: 本週 7 天 **$15,121 / 101 sessions / 25.1M tokens**（W26 報告值 $16,306 / 71 → 成本 **−7%**、session **+42%**）——更多、更輕的 session，與多產品並行打磨 + 排程 agent 增多一致。峰值 06-29 $2,908。**per-project 7 天切片**：`/api/tokens/filtered` 日期參數**仍然無效**（第 6 週，本次 `start/end` 實測仍回 all-time 全量），**但缺口性質已改變**——本週上線的 `token-analysis` 每日 agent + per-project 日用量 SQLite 持久化，從 07-05 起提供日級歸因（07-05：mops_dbs $676 / **53%**，台股新聞情緒分析迭代；Vault $373 / 29%）。缺口從「無資料」降級為「API 未接線」，下週起 retro 可直接用日報加總出 7 天切片。
- **失敗集中**: 快照 **0/17 exit-1**（W26: 4/16）——retro 系列首次全綠。保留一筆：`doctor` 週中仍有一次 exit 1（tester 07-05 報告 WARN），間歇性未根治；news_stock 兩支 `research-agent` 七週來首次轉綠，是否恢復成功 commit 待下週驗證。
- **Dashboard 健康**: watchdog 本週 **0 FAIL / 0 RESTART / 0 ESCALATE**（W26: 4 FAIL）——W26 記錄的「單點瞬斷輕微抬頭」趨勢本週歸零。

## 下週 Actions (max 3, prioritized)

1. **`knowledge-graph` 二選一：換通道，並掛上自動終結 default** — Why now: 第 6 次未動已證明「寫在報告裡」這個通道是死的。做法：下個**互動** session 開場（或 away flag 開啟時由 agent 經 Telegram `ask_user`）直接問一次三選項：(a) 退休 `knowledge-graph`（10 分鐘 mechanical，AI 代執行：rm → `bin/sk audit` → README 同步）；(b) 保留，並從 retro 追蹤**永久除名**；(c) 暫停 `workflow-retro` agent。**Default 條款：若 W28 retro 執行時仍無任何決定，自動視為 (b)，本項從此不再出現**——延期鏈無論如何在 W28 終結。Est. effort: 提問 1 分鐘 + 最多 10 分鐘執行。本次排程 run 已檢查 away flag（不存在），依規則不越權代決。
2. **harvest wrapper 兩修一次做（Theme 2）** — Why now: 唯一純機械、且直接抬高收割訊號密度的修法，W26 已寫明做法但沒人執行，本週 8/24 樣本仍是排程重跑。內容：(a) 取樣前置過濾——session cwd 命中 `com.sk.agent.*` plist `working_directory` 即排除；(b) headless prompt 補「直接寫入 `reports/harvest-YYYY-MM-DD.md`，不得以問句收尾」（07-05 報告即病例）。Est. effort: ~45 min。Expected impact: harvest 訊號密度回升、報告格式穩定，Theme 2 下週應歸零。
3. **`demo-anonymize` 建掉或除名（Theme 3 收尾）** — Why now: harvest 端紀律已收斂，全庫達 n≥2 未建的只剩 `demo-anonymize` 與 `phm-soft-sensor` 兩支；`demo-anonymize` 已兩度流標。二擇一：用 `skill-creator` 落地（1-1.5 hr，五週來第一個候選→產出閉環），或正式從候選清單除名（結論=需求已過期）。**不允許第三次「下週再說」**——與 Action 1 同邏輯，掛 default：W28 無動作即除名。

> 不重列的 backlog：`/api/tokens/filtered` 日期參數修復——價值已被 token-analysis + SQLite 路線大幅稀釋，等日報加總跑一週後再評估是否還值得修 API；`doctor` 間歇 exit 1 root-cause——已非集中失敗（全綠快照），降級觀察。

## 對照上週

W26 三個 actions 完成度：**0 / 3**（系列新低；W22→W25→W26 皆為 1/3）

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | `knowledge-graph` 二選一（退休 or 停 retro agent） | ❌ NOT DONE | `skills/meta/knowledge-graph` 仍存在、usage 0 紀錄；retro agent 本週日 23:00 照常執行。兩個選項都沒被選，**升級為連 6 次未動**。 |
| 2 | harvest 過濾排程 session | ❌ NOT DONE | 本週 git log 無相關 commit、`bin/` 無過濾邏輯；5/5 份 harvest 報告仍被排程執行稀釋（8/24 sessions）。 |
| 3 | 建 `demo-anonymize` 跑通 harvest→build | ❌ NOT DONE | `find skills -iname '*anonymize*'` 無結果，第 2 次流標。 |

**但要誠實記一筆在帳的另一邊**：retro backlog 掛了 5 週的「per-project token 歸因」缺口，本週被使用者**自主**收窄 80%（`token-analysis` 每日 agent、per-project SQLite 持久化、dashboard /tokens 30 天視圖，commit 46cb94e/02c8bae/a88f647）——沒有經過 retro 清單。這一正一反正是本週 meta-finding 的完整證據：**方向判斷（retro 的 what）多次被事後驗證是對的，執行通道（retro 的 how）是死的**。Action 1 的換通道設計即由此而來。

指標變化（W26 → W27）：
- watchdog incidents：4 FAIL/0 RESTART → **0/0** —— 歸零，系列最佳。
- exit-1 agent 數：4 → **0**（快照）—— 首次全綠；agent 總數 16→17（本週新增 `token-analysis`/`token-snapshot`；與 W26 名冊的逐支差異未盤點）。
- 週度 token：$16.3k / 71 sessions → **$15.1k / 101 sessions** —— 成本 −7%、session +42%（更多更輕）。
- skill-audit 待處理 issue：62 → **63** —— 持平；skill 總數 108（06-15 audit 時 96），可能棄用 41→**44**。
- per-project 7d 歸因：連 5 週「無資料」→ **「API 未接線但日報可加總」** —— 6 週來首次實質推進（使用者自建）。
- retro action 完成率：1/3 → **0/3** —— 新低，觸發 Action 1 的通道改革 + 自動終結 default。
