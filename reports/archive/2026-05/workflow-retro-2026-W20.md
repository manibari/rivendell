---
date: 2026-05-17
iso_week: 2026-W20
period: 2026-05-11 to 2026-05-17 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W20

## TL;DR

本週頭條是 **5/12 dashboard API 持續 44 分鐘 outage**（16:52→17:36），watchdog
3 次 ESCALATE 到 DEEP recovery 全部失敗於同一行錯誤：`pip: Resource deadlock avoided`
—— launchd → /bin/bash → pip 的 macOS TCC 死鎖（同 2026-03-24 已知教訓的回歸面）。
RESTART 觸發 12+ 次才靠 launchd 自己回穩。**watchdog 偵測層健康，恢復層在最關鍵的
DEEP path 是空的**。其餘訊號：harvest 候選量比 W19 反彈（W19 是 5/7 「Strong：無」、
本週 4/7 harvest 含 Strong/Moderate 候選共 5 個），但 deck-building cluster
（`slide-workflow` / `pitch-deck` / `iot-factory-report` 三者本週 0 次觸發）反映本週
deck 工作量本身偏低，不是 routing 問題。**W19 三個 actions 完成率 0/3 ——
連兩週 retro action 未執行，是 retro 機制本身需要警惕的訊號。**

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+) | `crm-projection` (5) | — |
| 中頻 (3-4) | `excalidraw-diagram` (3)、`gstack-browse` (3)、`workflow-retro` (3) | — |
| 低頻 (2) | `investment-research`、`user-flow`、`planning-with-files`、`subsidy-scraper`、`self-improving-agent` | — |
| 低頻 (1) | `requirement`、`gstack-plan-eng-review`、`session-wrap`、`office-pptx`、`mockup`、`context-recovery`、`skill-creator`、`skill-scout`、`mermaid-diagram`、`session-harvest`、`candidate-analysis`、`gstack-office-hours` | 9/14 exit 0；5 exit 1（research-agent、research-agent-weekly、doctor、janitor、crm-projection） |
| 沉寂 (30+ days) | 50+ 個；新進沉寂區：`dev-process-gate`（最後觸發 4/06 = 42 天）；持續沉寂代表：`knowledge-graph` 63 天、`ui-ux-pro-max` 68 天、`telegram-bot` / `claude-to-telegram` 63 天 | — |

**值得注意**：
- **`crm-projection` 5 次** 維持 daily agent 觸發節奏（W19=7、W18=7、W20=5）— 5/14 漏跑（其他天每天 1 次，5/15 兩次補跑）。但對應的 launchd agent 顯示 exit_code=1 —— **skill 觸發成功但 agent 整體 exit 非 0**，需要 root cause（git push? 還是 agent wrapper 拋錯？）。
- **deck-building cluster 全 0**（`slide-workflow` 6→0、`pitch-deck` 3→0、`iot-factory-report` 3→0）。對照同期 token data：deck-related project 本週幾乎無新 session（之前留下的 `cache/pitch-build` 等都是 2026-05-07 前的工作）。**這是本週 deck 工作量本身減少**，非 routing miss，不是 finding。
- **`excalidraw-diagram` 3 次（5/15 一天全部）** 是 W19 用戶抱怨「ASCII→PNG 流程圖轉得很爛」之後的延續使用 —— 既有 skill 本身夠用。
- **`dev-process-gate` 從 W19 「剛越界 32 天」進入 42 天**，連兩週沉寂，且其角色（development gate）本週理應觸發於 5/13 的 `gstack-plan-eng-review` session 但未被路由。下週仍未動就應退休或重寫 description。

## 重複痛點

### Theme 1: Watchdog DEEP recovery 在 launchd 環境中無法執行 pip

- **頻率**: 5/12 16:54、17:10、17:26 三次 ESCALATE 全部死於 `bin/sk-watchdog: line 90: .venv/bin/pip: Resource deadlock avoided`。另 5/13、5/14、5/15、5/16 共 8 個 RESTART 事件（threshold-3 觸發後 kickstart）。一週 watchdog log 從 W19 23 行膨脹到 W20 80+ 行。
- **類別**: **Mechanical** — root cause 已在 2026-03-24 學到（`macOS TCC blocks /bin/bash from ~/Documents/ in launchd`）並在 `~/.claude/CLAUDE.md` Engineering Gotchas 第 6 點明文記錄：「Scripts under `~/Documents/` need Full Disk Access — `/bin/bash` doesn't have it; use a compiled launcher」。`bin/sk-watchdog` 由 launchd `com.sk.dashboard.watchdog` 啟動，spawning `pip` 子程序時 inherit 同樣的 TCC 限制 → EDEADLK。`deep_recovery_api` 在這個環境下**永遠**會失敗。
- **代表性事件**: 5/12 16:52→17:36 的 44 分鐘 API blackout。watchdog 偵測到 12 次 threshold breach，每次 RESTART 都成功（kickstart 不需 pip），但 ESCALATE 到 5th-same-day-restart 觸發 DEEP recovery 時 pip 死鎖無法重灌 venv。最後 API 自己復原（17:36 OK），與 DEEP recovery 無關。
- **建議**: 兩條路徑可選 ——（a）`deep_recovery_api` 不直接執行 pip，改 fire-and-forget 一個獨立的 launchctl-spawned job 觸發 `agents/sk-agent-run.c`（已是有 FDA 的 compiled launcher）；（b）直接拿掉 DEEP recovery，只留 kickstart——因 5/12 證據顯示 kickstart 12 次後 API 還是自己回穩，DEEP 在這個 class 的問題上沒救援價值。優先 (b)：簡單、立刻可做、消除假希望。

### Theme 2: W19 三個 actions 完成率 0/3，且 W18/W19 模式相同

- **頻率**: 連兩週 0/3 → 1/3 → 0/3 完成率（W18: 1/3、W19: 0/3、本週同款 actions 仍未動）。具體：W19 Action 1（doctor + janitor 修 exit 1）：兩者本週仍 exit 1；W19 Action 2（退休 knowledge-graph）：本週仍 0 觸發、63 天沉寂；W19 Action 3（watchdog grace period 調查）：未做、且本週 watchdog 出更大事故（Theme 1）取代了原本擔心的問題。
- **類別**: **Editorial** — 不是 retro 寫得不對，是 retro 本身的 actions 沒被綁到任何強制 trigger。W19 已預判「mechanical action 會 ship、editorial action 容易延期」並故意把 W20 action 設計成 mechanical（修 agent），但仍未執行。
- **代表性事件**: W19 報告白紙黑字寫「連兩週同 action 不執行會侵蝕 retro 自身的信任度」，第三週仍未執行。
- **建議**: 把 retro 的 actions 從 markdown 文字升級成可執行 todo —— W20 結束時自動生成 `reports/.workflow-retro-todos.md` 或寫進 `agents/agents.conf` 的下週一 prompt。**不再列舊 actions 進新 retro**，逾期視同退場。改進方向：(a) doctor/janitor 在 W19 retro 提過、本週繼續提就是延期一週、第三週再列等於放棄；(b) knowledge-graph 連三週都列：本週直接刪除 skill 檔案而非又提一次。

> Theme 3 候選（harvest 候選累積 ≥3 Strong 未建）：n=2（presentation-qa-rehearsal、gov-proposal-kpi-drafting、fmcg-shelf-life-forecast 算 3，但 learnings-promotion-sprint 已建）。**未跨 3 次門檻**，本週不列為痛點。下週若 5/12 與 5/15 兩個 Strong 仍無實作，升為 Editorial theme。

## 集中度

- **失敗集中**: 5/14 agents 為 exit_code=1（研究 daily、研究 weekly、doctor、janitor、crm-projection）—— **比 W19 的 2 個翻倍**。`research-agent` 與 `crm-projection` 都有 daily skill 觸發紀錄（skill 看似有跑、agent 卻 exit 1），最可能是 git push 失敗或 wrapper 邊界拋錯。
- **Token 集中**: 工作日均 $580（5/11–5/15 五天合計 $2901）—— 比 W19 工作日均 $930 降 38%。週末（5/16=$3、5/17=$36）正常低點。Per-project 7-day 切片無法精準計（W19 已標記為 dashboard API 觀測缺口，本週仍未修）。從 last-30d 累計 top 看仍是 `news_stock`（$2728）+ `rivendell`（$2272）+ `Peter/Work`（$1846）三足。
- **Dashboard 健康**: 本週 watchdog log **80+ 行事件**（W19 23 行 → W20 80+，3.5×）。8 個 RESTART 事件（W19 0 個 RESTART、3 個 incident）。其中 5/12 16:52→17:36 是單一最嚴重事件，本身就佔了 12+ RESTART。Theme 1 列為下週首要 action。

## 下週 Actions (max 3, prioritized)

1. **拿掉 `bin/sk-watchdog` 的 DEEP recovery，只留 kickstart restart** — Why now: 5/12 證據顯示 DEEP recovery 在 launchd 環境**永遠**失敗（pip TCC EDEADLK），但 kickstart-only 反覆 12 次後 API 自己回穩，所以 DEEP 不是救援、是假希望。Est. effort: 15 min（修 `deep_recovery_api` / `deep_recovery_web` 兩函式為 noop 或刪除 `ESCALATE` block）。Expected impact: watchdog log 不再出現 `Resource deadlock avoided`；下次同 class 事件 watchdog 行為可預測（單純 kickstart 直到回穩）。完成後若仍想要真 DEEP recovery，改走 compiled launcher（`agents/sk-agent-run.c` 已是有 FDA 的 binary）—— 列為 follow-up，非本週 action。

2. **退休 `knowledge-graph` skill** — Why now: 連三週 retro 都列、連三週都未動、63 天 0 觸發。**今天就刪 skill 檔案**，把 retro 信任度補回來。Est. effort: 10 min（移除 `skills/<category>/knowledge-graph/`、跑 `bin/sk audit` 確認、更新 README skill catalog count）。Expected impact: 證明 retro action 是會被執行的、不是 read-only 報告。**這個 action 本身就是 retro 機制的 dogfooding**。

3. **修 `crm-projection` agent 的 exit_code=1（同時看 `research-agent` 與 `research-agent-weekly`）** — Why now: 三個 agent 都呈現「skill 有跑、agent exit 非 0」這個雙態 —— skill log 寫成功、agent 包裝層失敗。最可能是 git push 失敗（無 remote / 衝突）或 wrapper 邊界拋錯。Est. effort: 30 min（讀 stderr log、定位 wrapper 失敗點）。Expected impact: agent 健康度從 9/14 回到至少 12/14；以及驗證上週留下的「`/api/agents/{label}/runs` 對 exit-1 agent 回傳 `[]`」是不是同源問題。

> **不重複列 W19 action 3（watchdog grace period）**：本週 Theme 1 已替它 supersede——grace period 不是真的問題，DEEP recovery 才是。原 action 退場。

## 對照上週

W19 三個 actions 完成度：

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | 修 `doctor` + `janitor` agent | ❌ NOT DONE | 兩者本週 exit_code 仍 1。 |
| 2 | 退休或重寫 `knowledge-graph` skill description | ❌ NOT DONE | 0 觸發，沉寂從 56 → 63 天。 |
| 3 | 檢查 watchdog 在 kickstart 後的 grace period | ❌ NOT DONE | 本週 watchdog 真實事故型態與 grace period 無關（是 DEEP recovery 死於 EDEADLK）。原假設不成立，action 退場。 |

完成率 0/3。**連兩週 retro action 落空** —— 本週 Action 2（退休 knowledge-graph）特意設成最低 effort、最高象徵性，用來驗證 retro 自己是否還是 load-bearing。下週若 Action 2 仍未動，建議**暫停 workflow-retro 兩週**，讓上一輪 actions 先消化完再做新 retro（否則就是噪音生產線）。

指標變化：
- watchdog incidents：W19 3 起 → W20 8 RESTART（其中 5/12 單日佔 12+ RESTART）—— **+150%**。
- exit-1 agent 數：W19 2 → W20 5 —— **+150%**。
- harvest Strong 候選比例：W19 0/7 → W20 3/7（5/12 1、5/15 2）—— skill ecosystem **不再收斂**，重新回到「有候選不下手」狀態。
- deck-building cluster 觸發：W19 12 → W20 0 —— 是本週 deck 工作量本身減少，非系統 health 訊號。
- W19 retro action 完成率：0/3。連兩週 0/3 → 1/3 → 0/3。
