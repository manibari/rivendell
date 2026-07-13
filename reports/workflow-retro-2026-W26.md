---
date: 2026-06-28
iso_week: 2026-W26
period: 2026-06-21 to 2026-06-28 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W26

## TL;DR

Infra 延續 W22/W25 的平靜：**0 RESTART、0 ESCALATE**，agent 失敗面從 W25 的 5 縮到 **4**（`harvest` 假失敗本週回到 exit 0）。使用度與 W25 大致持平（43 firing / 19 skill vs 45 / 18），工作重心仍在 **ChimesFlow UI 建構**——`requirement`/`user-flow`/`mockup`/`chimesflow-design`/`planning-with-files` 五個一起高頻，是典型的「需求→流程→畫面」建構軌跡。

但**本週最重要的 finding 不是任何數字，是 retro 機制自己的存亡點已經到了**。W25 對 `knowledge-graph` 退休下了明文最後通牒：「**若本週仍不執行，下一步不是再寫一份 retro，是正式停掉 `workflow-retro` agent**」。本週 grep 確認 `skills/meta/knowledge-graph` **仍在原地、usage 資料集 0 紀錄**——這是**連續第 5 次** retro 動不了一個 10 分鐘、零風險的 cleanup。同型訊號還有兩個：W25 Action 2（建 `demo-anonymize`）未建、`/api/tokens/filtered` 日期參數連 **5 週**未修。W25 完成的唯一一項（`concurrent-session-git` 描述修復）又是 **mechanical 5-min fix**——完全複製 W18→W25「只有機械性 action 會被執行」的 pattern。

升級條件已觸發。本週 Action 1 不是再描述問題，是**逼出一個二選一決定**：現在就退掉 `knowledge-graph`（我可代執行），或正式暫停 retro agent。再寫第 6 份沒人消化的 retro 本身就是不誠實。

## 使用度

本週 usage API 追蹤範圍內共 **19 個 skill、43 次 firing**（W25：18 / 45 — 持平）。

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+) | `crm-projection`(6)、`requirement`(5)、`user-flow`(5) | — |
| 低頻 (1-4) | `mockup`(4)、`planning-with-files`(4)、`chimesflow-design`(3)、`gstack-office-hours`(3)、`subsidy-scraper`(2)，以及各 1 次：`gstack-plan-eng-review`、`gstack-plan-design-review`、`gstack-qa`、`gstack-codex`、`deep-research`、`mermaid-diagram`、`office-xlsx`、`office-pptx`、`material-health`、`mops-financial-scraper`、`workflow-retro` | 16 中 **12 exit 0 / 4 exit 1**（`research-agent`、`research-agent-weekly`[news_stock]、`doctor`、`janitor`[rivendell]） |
| 沉寂 (30+ days) | usage API **結構上測不到**（只追蹤「曾 fire 過」的 39 支）；真正沉寂訊號在 skill-audit 的 **41 支「可能棄用」（mtime 90+ 天未動）**。W25 點名的 slide/deck 群（`pitch-deck`/`slide-workflow`/`iot-factory-report`/`gdoc-report-builder`）本週仍零 firing——同 W25，無簡報工作的自然結果，非 routing 問題 | — |

**值得注意**：
- **`requirement` 從 W25 的 15 跌回 5**、`crm-projection`(6, 排程例行) 升為榜首。這不是退化——W25 的 15 是 `chore/skill-quality` 那批 skill 設計工作的尖峰，本週重心轉到實際畫面建構，`requirement` 回到常態量。
- **`mockup`/`user-flow`/`chimesflow-design` 同步抬頭**，與 ChimesFlow 前端建構的工作型態一致；CLAUDE.md「UI Feature」flow 的前段（requirement→user-flow→design→mockup）被完整走過，是 routing 正常運作的正面訊號。
- **agent 失敗面縮小（5→4）**：W25 連 4 週點名的 `harvest`「skill 成功、wrapper exit 1」假失敗，本週快照為 **exit 0**（每日報告照常產出）。真實失敗集中在 news_stock 的兩支 `research-agent`（`recent_commit` 停在 2026-05-10，已逾 7 週未成功 commit）與 rivendell 的 `doctor`/`janitor`。

## 重複痛點

### Theme 1：harvest→build 這條鏈，throughput 仍是零（第 5 次）

- **頻率**: W19/W20/W22/W25 retro 連續母題 + 本週 harvest（06-23~06-28）再產出 `phm-soft-sensor`（跨 06-10/06-26，**n=2**）、`xmind-convert`(06-26)、補助/RFP 撰稿(06-24)、「架構設計 ≠ 需求」岔路(06-24)、「單 app→多 app 平台外殼重塑」(06-25)。W25 自評 Strong/n=2 的 `demo-anonymize` **本週仍未建**。
- **類別**: Architectural（流程缺一個「候選→落地」的執行閘；候選不缺、判讀不缺，缺的是把 Moderate/n=2 推進 `skill-creator` 的那一步）。
- **代表性事件**: W25 Action 2 把「建 `demo-anonymize`」明文當成「證明 harvest→build 會動」的測試——結果它沒動，等於測試判定**鏈是斷的**。
- **建議**: 見下方 Action 1/3（先用最成熟的 1 個候選把鏈跑通），不要再擴大候選清單。

### Theme 2：排程 agent 的「執行軌跡」污染 harvest 訊號

- **頻率**: 06-22/23/24/25/26/28 **6 份** harvest 報告，開頭都得花篇幅排除 `crm-projection`/`subsidy-scraper`/`material-health` 的排程執行——「這些是既有 skill 正常呼叫，非新 pattern」幾乎成了每份 harvest 的固定段落。
- **類別**: Mechanical（harvest 的 session 取樣沒過濾掉「由 launchd agent 觸發的 skill 執行」session，把例行排程當成人類工作流在收割）。
- **代表性事件**: 06-28 harvest 4 個 session 有 3 個是 `crm-projection`(×2)+`material-health` 的排程重跑，真正可分析的人類 session 只剩 1 個——訊號密度被排程稀釋到剩 1/4。
- **建議**: harvest 取樣時用「session 是否由 `com.sk.agent.*` plist 觸發 / cwd 是否為排程 agent 的 working_directory」做前置過濾，把例行執行排除在收割池外。這是本週**唯一全新且純機械**的痛點，且直接抬高 Theme 1 的訊號品質。

> 註：skill-audit 待處理 issue 本週 **50→62**（+24%，W22→W25 為 22→50），但拆開後絕大多數是 41 支「可能棄用」+ tag-overlap 的組合性雜訊，非新缺陷。**不列為獨立痛點、不逐條追**——把它當債務水位計即可，避免把組合性雜訊誤當需要逐條處理的退化。

## 集中度

- **Token 集中**: 本週 7 天 **$16,306 / 71 sessions / 23.9M tokens**（前 7 天 $13,367 / 49 / 17.3M → **+22% 成本、+45% session**）。與 W25「session 砍半、每 session 更重」相反，本週是 **session 變多、每 session 較輕**，符合畫面建構（多次短迭代）型態。峰值 06-27 $3,710。**但 per-project 7-day 切片仍取不到**：`/api/tokens/filtered` 對 `days`/`start-end`/`from-to`/`period` 全部無視、回全量 all-time。ChimesFlow 家族（本體 $13.3k + backend $3.4k + frontend $2.8k ≈ **$19.5k all-time**）顯然是長期主力、且本週 skill firing 全指向它，但**無法正式歸因本週**。連 **5 次 retro**（W19/W20/W22/W25/W26）卡在同一觀測缺口。
- **失敗集中**: 4/16 agent exit 1——news_stock 兩支 `research-agent`（逾 7 週未成功 commit，但屬外部專案）+ rivendell 的 `doctor`(7:00)、`janitor`(週日 3:00)。後兩者是 rivendell 自家排程，值得一次 root-cause（W25 點名的雙態混淆問題，本週因 `harvest` 轉綠而稍微好辨識）。
- **Dashboard 健康**: 本週 watchdog **4 FAIL / 0 RESTART / 0 ESCALATE**——全是 API 單次失敗、≤1 分鐘自動 recover（06-23/25/26/27 各一次）。比 W25 的 1 FAIL 略升，但全為單點瞬斷、無連續失敗、無 escalate，仍屬健康區間。趨勢輕微抬頭，先記錄不 action。

## 下週 Actions (max 3, prioritized)

1. **退掉 `knowledge-graph`，或退掉 retro 自己——升級條件已觸發** — Why now: W25 明文最後通牒（「不退就停 retro agent」），本週 `skills/meta/knowledge-graph` 仍在、usage 0 紀錄，**連 5 次未動**。連最便宜、零風險的 cleanup 都排不進實作，是 retro 信任度的存亡問題，比任何指標重要。Est. effort: **10 min**（`rm -rf skills/meta/knowledge-graph` → `bin/sk audit` → README skill count −1 + Structure tree 同步）。**我可在本 session 直接代執行，只需你一句確認**；若你選擇不退，誠實的結論是**正式暫停 `workflow-retro` agent**，停止生產沒人消化的報告。二擇一，不要第三次「下週再說」。

2. **harvest 取樣過濾掉排程 agent 的執行 session（Theme 2）** — Why now: 連 6 份 harvest 報告被 `crm-projection`/`subsidy-scraper`/`material-health` 排程執行稀釋訊號（06-28 真實訊號只剩 1/4）。這是本週唯一全新、純機械、且能直接抬高 harvest 品質（進而救 Theme 1）的修法。Est. effort: ~30-45 min（在 harvest 取樣處比對 session cwd 是否落在 `com.sk.agent.*` plist 的 `working_directory`，或 session 是否由排程觸發，命中即排除）。Expected impact: harvest 訊號密度回升，候選判讀不再被例行執行噪音淹沒。

3. **用 `demo-anonymize` 把 harvest→build 鏈跑通一次（Theme 1 carry-over）** — Why now: 它是堆積中最成熟的訊號（n=2、presales 剛性缺口、現有 skill 零覆蓋），W25 已把它當「鏈會不會動」的測試卻沒執行。與其再擴大候選清單，不如**只挑這一個**用 `skill-creator` 落地，證明鏈能動。Est. effort: 1-1.5 hr。Expected impact: 五週來第一個「候選→產出」的閉環；若本週仍卡，則 Theme 1 應升級為「harvest 一律先擱置、停止產出新候選直到鏈被修通」。

> 不重列的 backlog：`/api/tokens/filtered` 日期參數（連 5 週缺口、價值仍在，但本週無單一專案 token spike 急需歸因，不塞第 4 個 action 稀釋執行力）；`doctor`/`janitor` exit-1 root-cause（待 Action 1 決定 retro 去留後再排）。

## 對照上週

W25 三個 actions 完成度：

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | 退休 `knowledge-graph`（第 4 次） | ❌ NOT DONE | `skills/meta/knowledge-graph` 仍存在、usage 0 紀錄。**升級為連 5 次未動。** |
| 2 | 抽 `demo-anonymize` | ❌ NOT DONE | `find skills -iname '*anonymize*'` 無結果；presales 去識別化仍零覆蓋。 |
| 3 | 修 `concurrent-session-git` 描述（auto-stage 逐字複製） | ✅ DONE | 描述已改為 shared-worktree git 衛生語意，不再與 `auto-stage` 重複。 |

完成率 **1/3**——與 W22→W25 **完全同型**：唯一完成的（Action 3）是 5-min mechanical fix；兩個需要「決定退場 / 動手建造」判斷的 editorial/build action 連一條都沒動。**這是 W19 就預判、W26 仍未破的 pattern——retro 最重要的 meta-finding 依舊是它自己的非機械 action 永遠排不進實作。** 本週 Action 1 的二選一設計，就是為了強制終結這條延期鏈。

指標變化（W25 → W26）：
- watchdog incidents：1 FAIL/0 RESTART → **4 FAIL/0 RESTART** —— API 單點瞬斷增加，但全自動 recover、無 escalate。
- exit-1 agent 數：5 → **4** —— −1（`harvest` 假失敗本週快照轉 exit 0）。
- 週度 token：7d ~$13.4k → **$16.3k** —— +22%（session +45%、每 session 較輕）。
- skill-audit 待處理 issue：50 → **62** —— +24%（多為 41 支可能棄用 + tag-overlap 組合性雜訊）。
- per-project 7d 歸因能力：W19/W20/W22/W25/W26 連 **5 週**缺口 —— 無變化。
- retro action 完成率：W25 1/3 → W26 **1/3** —— 持平（且完成的又只是 mechanical 那條）。
