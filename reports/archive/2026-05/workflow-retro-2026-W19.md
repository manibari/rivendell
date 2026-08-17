---
date: 2026-05-10
iso_week: 2026-W19
period: 2026-05-04 to 2026-05-10 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W19

## TL;DR

本週 deck-building 流程持續成熟（`slide-workflow` 6 + `pitch-deck` 3 + `iot-factory-report` 3
= 12 次觸發），但**新 skill 候選訊號明顯下降** — 7 份 harvest 中有 5 份結論為「Strong：無 / 完全在
既有 skill 軌道」，是 skill ecosystem 進入收斂期的訊號。系統健康面：W18 提的 sentinel-build 修補
已 ship 且端到端串通（含 watchdog DEEP recovery），dashboard watchdog 事件從上週 6 起降到本週
3 起（5/5 ×2、5/9 ×1，皆觸發 DEEP rebuild 復原）。新發現：`doctor` + `janitor` 兩個維運 agent
exit_code=1，且 `/api/agents/{label}/runs` 對它們回傳 `[]` —— 同時是 agent 失敗 + dashboard API
資料缺口的雙重訊號。

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+) | `crm-projection` (7)、`slide-workflow` (6) | — |
| 低頻 (2-4) | `pitch-deck` (3)、`investment-research` (3)、`iot-factory-report` (3)、`workflow-retro` (3)、`gstack-office-hours` (2)、`planning-with-files` (2)、`session-wrap` (2)、`mockup` (2)、`subsidy-scraper` (2)、`slide-office-hours` (2) | 12/14 已 loaded、exit 0；2 個 exit 1（doctor、janitor） |
| 沉寂 (30+ days) | 48 個（同上週數量；含 `knowledge-graph` 56 天、`ui-ux-pro-max` 61 天、`telegram-bot`/`claude-to-telegram` 56 天、`gstack-plan-ceo-review` 32 天、`dev-process-gate` 30 天） | 7 個 project-side agent（news_stock + sales-assistant 系列）顯示為 unloaded — 排程未啟動，非失敗 |

**值得注意**：
- `crm-projection` 7 次 = 每天觸發一次的排程模式，是健康的 agent-driven 高頻。
- `slide-office-hours`（W18 新建）本週仍只 2 次觸發 — 仍處 dogfood 期，下週若 ≤2 次需檢查 trigger 詞。
- `dev-process-gate` 從 32 天前最後一次觸發進入沉寂區 — 上週還是「30 天內仍活躍」，本週越界。需觀察是否因 W18 的 deck-building flow 已 codify 而功能性被取代。
- `knowledge-graph` 仍未動（W18 action 3 未完成，從 49 天 → 56 天）。連兩週標記為 candidate for retirement。

## 重複痛點

### Theme 1: Dashboard API 回傳 `[]` for failing agents
- **頻率**: 2 個 agents（`com.sk.agent.rivendell.doctor` exit_code=1、`com.sk.agent.rivendell.janitor` exit_code=1）。`GET /api/agents/{label}/runs` 對兩者皆回傳 `[]`。
- **類別**: **Architectural** — 這是 agent 失敗 + dashboard API 觀測缺口的雙重訊號：retro 自己依賴的工具，無法回答「這個 agent 為什麼失敗、上次哪天 fail」。
- **代表性事件**: doctor 排程 7:00、janitor 排程週日 3:00；兩者都已執行（有 exit_code），但 runs 端點查不到歷史。
- **建議**: 先看 plist `StandardOutPath` 找 doctor / janitor 真正的 log 位置（`reports/doctor-stderr.log` 與 `reports/janitor.log` 都已存在）→ 直接讀 log 找 root cause；再修 `/runs` API 為什麼漏這兩個 agent。

### Theme 2: Harvest 報告連續呈現低訊號
- **頻率**: 5 份 / 7 份本週 harvest 結論為「Strong: 無」或「session 完全在既有 skill 軌道，無新 pattern」（5/04、5/06、5/06-followup、5/07、5/10）。
- **類別**: **Editorial** — 不是 harvest 壞掉，是 skill ecosystem 進入「夠用」階段；harvest 每 8 小時跑一次的成本/產出比下降。
- **代表性事件**: 5/10 報告：「4 個 session 中有 3 個直接呼叫既有 skill，可萃取的『新模式』訊號偏弱」。
- **建議**: 暫不調 harvest 排程（每天 1 個 strong 候選價值高 — 5/8 的 `couple-life-planning` 就是這樣抓到的）。但若再連續 14 天「Strong: 無」，可考慮從每 8 小時放寬到每日，把成本降三分之二。下週繼續觀察。

> Theme 3 候選（skill audit 描述錯置 — W18 提過）本週仍存在但**未升級為 action**：影響純讀者層、修法 effort > 1 hr、無新證據顯示傷害擴大。維持 W18 判斷。

## 集中度

- **Token 集中（每日累計，5/4–5/10 共 $4548）**: 5/5 $1059（峰值）、5/7 $1017、5/8 $846、5/4 $763 — 工作日均 ~$930；5/9–5/10 週末降至 $35/天（10× 降幅，是健康的 cadence）。**Per-project 7 日切片無法精準計算** — `/api/tokens/filtered?days=7` 回傳的 `projects` 欄位是全期累計而非 7 日切片，這本身是 dashboard 觀測缺口（與 Theme 1 的 `/runs` 缺口同源 — API 的時間視窗 filter 不一致）。
- **失敗集中**: 2 個 rivendell 內部 agent 同時 exit_code=1（doctor、janitor）。News-stock + sales-assistant 系列 agent 全部 exit 0。
- **Dashboard 健康**: 本週 watchdog log 紀錄 23 行事件，**3 個 incident**（5/5 17:03、5/5 17:45、5/9 01:00）— 上週 6 起的一半。W18 action 1（sentinel-build pattern）已 ship，且 watchdog 的 DEEP recovery handler 也有 `touch .next/.build-complete`，端到端串通。剩下 3 起是其他 class 的失敗（kickstart 後 web 預熱期 watchdog 過早 probe？— 證據不足，僅推測，列為下週 action 3 調查）。

## 下週 Actions (max 3, prioritized)

1. **修 `doctor` + `janitor` agent** — Why now: 兩個維運 agent 都 exit 1，且本週才被 retro 機制偵測到（上週沒列）；`reports/doctor-stderr.log` 與 `reports/janitor.log` 已存在可直接讀。Est. effort: 30 min（讀 log → 找 root cause → 修）。Expected impact: 兩支維運 agent 重回綠燈，順手釐清為什麼 `/api/agents/{label}/runs` 對它們回傳 `[]`（API 本身可能還有 bug）。

2. **退休或重寫 `knowledge-graph` skill description** — Why now: 連兩週列入 actions 都未動，第 56 天無觸發；W18 已說「三選一不再放著佔空間」。本週直接做決定，不再延期。Est. effort: 15 min。Expected impact: 證明 retro 的 actions 是真會被執行的（連兩週同 action 不執行會侵蝕 retro 自身的信任度）。

3. **檢查 watchdog 在 kickstart 後的 grace period** — Why now: W18 sentinel 修好之後仍有 3 次 incident，模式都是「DEEP rebuild 完成 → kickstart → 馬上又 1-3 次 FAIL → RESTART」（5/5 17:20→17:21、5/9 01:17→01:21）。看起來 web 預熱還沒完成 watchdog 就 probe 了。Est. effort: 30 min（讀 `bin/sk-watchdog` 的 GRACE_SECONDS 與 deep-recovery handler 之間的銜接）。Expected impact: 消除剩下 watchdog 噪音的最後一個 class。

## 對照上週

W18 的 3 個 actions 完成度：

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | 修 `start-web.sh` 的 sentinel build 偵測 | ✅ DONE | `dashboard-next/start-web.sh` 已使用 `.next/.build-complete` sentinel；`bin/sk-watchdog` 的 `deep_recovery_web` 也 `touch` 同 sentinel；watchdog 事件數 6→3 起。 |
| 2 | `presales-pipeline` README 補「通路媒介客戶」段落 | ❌ NOT DONE | `grep` `skills/workflow/presales-pipeline/SKILL.md` 無 `通路` / `channel` 命中。 |
| 3 | 檢查 `knowledge-graph` skill description 對齊度 | ❌ NOT DONE | knowledge-graph 最後觸發仍是 2026-03-15，沉寂從 49 → 56 天。 |

完成率 1/3。Action 1（系統面、明確 spec、有 .learnings 教科書級的解法）執行；Action 2/3（編輯 / 盤點類，無剛性 trigger）擱置。**這是個小 pattern：retro 的 mechanical action 會 ship，editorial action 容易延期。** 下週 action 1 是 mechanical（修 agent）預期會做；action 2 把延期的 editorial 強制截止本週交差。

指標變化：watchdog incidents 6 → 3（−50%）、deck-building 觸發 17 → 12（−29%、合理收斂）、harvest「Strong: 無」比例 ~33% → 71%（skill ecosystem 收斂訊號）。
