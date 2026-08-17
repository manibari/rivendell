---
date: 2026-06-21
iso_week: 2026-W25
period: 2026-06-15 to 2026-06-21 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W25

## TL;DR

本週 infra 延續 W22 的平靜：watchdog 整週 **1 FAIL（web，06-20，自動 recover）、0 RESTART、0 ESCALATE**，API 全程在線（本 retro 四個 endpoint 都正常回應）。工作重心明顯轉到 **skill 本身的開發**——`chore/skill-quality` branch 本週新增/改寫 `backend-async-jobs`、`concurrent-session-git`、`task-brief` 納管、填實 5 個 harvest-auto stub，`requirement`(15) 也因此成為本週最高頻 skill。

但這波快速擴張帶出本週兩個結構性訊號，都在「使用度/痛點」而非 infra：
1. **skill-audit 待處理 issue 從 W22 的 22 個漲到 50 個**（+127%），skill 數只 +5（94→99）、穩定數從 ~91 掉到 62。多數是 tag-overlap 邊界警告（隨 skill 數組合爆炸，雜訊性質），但其中夾著一個**真 bug**：`concurrent-session-git` 的描述是 `auto-stage` 的逐字複製。
2. **harvest 候選堆積、建造率近零**：14 天內 ~10 個 Strong/Moderate 候選，幾乎全在 n=1 被正確遞延——但本週**去識別化候選已累積到 n=2**（`demo-anonymize` 06-08 + `deck-anonymizer` 06-09，presales 剛性缺口、現有 skill 零覆蓋），`doe-ml-analysis` 更是 Strong 且命中 CLAUDE.md 已標註的 domain gap，兩者皆未建。

而最重要的 finding 仍是 **retro 機制自己**：W22 三個 action 只完成 1（`material-health` exit 修回 0），`knowledge-graph` 退休 **連第 4 次 retro 沒動**、`/api/tokens/filtered` 仍無視日期參數。W22 明文「若仍不退 `knowledge-graph` 就暫停 retro 兩週」——W23/W24 確實被跳過（無檔案），本週重啟、它**依然在原地**。

## 使用度

本週共 18 個 skill 觸發（usage API 追蹤範圍內），45 次 firing（W24 為 20 skills / 44 次，大致持平）。

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+) | `requirement` (15)、`crm-projection` (5) | — |
| 中頻 (3-4) | `gstack-plan-eng-review` (4)、`user-flow` (4) | — |
| 低頻 (1-2) | `gstack-autoplan`(2)、`subsidy-scraper`(2)、`mops-financial-scraper`(2)、`chimesflow-design`、`mockup`、`planning-with-files`、`material-health`、`gstack-plan-ceo-review`、`workflow-retro`、`session-harvest`、`env-doctor`、`presales-pipeline`、`repro-exam`、`client-kickoff-docs`（各 1） | 11/16 exit 0；5 exit 1（`research-agent`、`research-agent-weekly`、`doctor`、`harvest`、`janitor`） |
| 沉寂 (30+ days) | `gdoc-report-builder`、`iot-factory-report`、`pitch-deck`、`slide-workflow`（皆 last 2026-05-18） | — |

**值得注意**：
- **`requirement` (15) 暴衝為本週榜首**（W24 為 6）——與 `chore/skill-quality` 的 skill 設計/規劃工作量一致（rivendell 本週 37 sessions）。這不是異常，是工作型態使然。
- **沉寂的 4 個全是 slide/deck domain**（`pitch-deck`、`slide-workflow`、`iot-factory-report`、`gdoc-report-builder`，都停在 05-18）——本週零簡報工作的自然結果，**非 routing 問題，不需 action**。與 W22「sales-material/slide-template-extractor 沉寂是 deck 工作量低」同一性質。
- **agent 失敗面縮小**：W22 的 6 exit-1 → 本週 5。`material-health` 從 exit 1 修回 **exit 0**（W22 Action 2 兌現一半，見對照上週）。但 `harvest` 仍 exit 1 的「假失敗」雙態未解（有日報產出、`-stderr.log` 0-byte），連 4 週點名。

## 重複痛點

### Theme 1: harvest 候選堆積，但已有 n≥2 訊號穿過門檻仍未建

- **頻率**: 近 14 天 harvest 報告產出 ~10 個 Strong/Moderate 候選（`demo-anonymize` 06-08、`deck-anonymizer` 06-09、`phm-soft-sensor` 06-10、`doc-drift-sync` 06-12、`doe-ml-analysis` 06-13、`roadmap-decision-capture` 06-14、`seed-deployed-app` 06-15、`repo-consolidation-advisor` 06-17…）。這是 W19/W20/W22 retro 都點過的母題（第 4 次）。
- **類別**: **Editorial**（轉為可行動）。前幾週的判讀是「都 n=1、被正確遞延、機制按設計運作」。**本週質變**：去識別化候選 `demo-anonymize`(06-08) + `deck-anonymizer`(06-09) 是**同一個 presales 需求連兩天出現＝n=2**，harvest 自評 Strong、明文 grep 確認現有 presales skill 群（`customer-intel`/`sales-material`/`pitch-deck`/`presales-pipeline`）+ `protect-secrets` **零覆蓋**。`doe-ml-analysis`(06-13) 雖 n=1 但 Strong 且**正中 CLAUDE.md「製造運營/時序製程 ★ 暫無 skill」已標註缺口**。
- **代表性事件**: harvest 自己引用的 promote 門檻是「fired ≥2× 才抽」——去識別化已達標、仍未建。堆積不再是「健康的遞延」，是「達標訊號沒被消化」。
- **建議**: 抽 `demo-anonymize`（presales 資產去識別化），見 Action 2。`doe-ml-analysis` 列觀察、待第 2 案再促進（單 session、雖命中 gap 但 N=1）。

### Theme 2: 快速加 skill 累積結構債——audit issue 三週翻倍

- **頻率**: skill-audit 待處理 issue 單調爬升——20(05-27) → 22(05-31) → 46(06-15) → **50(06-21)**；穩定 skill 從 91→62。skill 數只從 94→99（+5）。
- **類別**: **Mechanical + Editorial 混合**。大部分 +28 增量是 tag-overlap 邊界警告（`[docs]`、`[meta]`、`[workflow]` 群「建議檢查邊界是否清楚」），這類警告隨 skill 數**組合性**增長，本質是雜訊、非真退化。但夾帶**真缺陷**：`concurrent-session-git`（本週新增，commit 64b905e，講 shared-worktree git 衛生）的描述被逐字寫成 `auto-stage` 的「PostToolUse hook，Claude 編輯/寫入檔案後自動 git stage」——複製貼上沒改。
- **代表性事件**: audit 報告中 `auto-stage` 與 `concurrent-session-git` 兩列描述一字不差，這正是 overlap 警告其中一條的來源——但這條是真的、該修。
- **建議**: 修 `concurrent-session-git` 描述（Action 3），其餘 overlap 警告認列為組合性雜訊、**不要當成 50 個都要修的退化**——否則會製造假工。

## 集中度

- **Token 集中**: 本週 7 天 **~$12,361**（47 sessions、16.2M tokens；06-16 $4,301 為峰值）。對比 W24（06-08..14）~$12,989 / **79 sessions**——成本持平、但 session 數幾乎砍半 → **本週每 session 更深更重**（與 skill 設計/規劃的長 session 工作型態一致，非異常）。**但 per-project 7-day 切片仍取不到**：`/api/tokens/filtered` 對 `start/end`、`from/to`、`days`、`period` **四種參數全部無視**，回傳 byte 數與全量一致（$48,675 all-time）。累計榜首 `ChimesFlow` 家族（本體 $14.3k + backend $3.6k + frontend $2.2k ≈ $20k）顯然是長期主力，但**無法歸因本週**。這是連 **4 次 retro**（W19/W20/W22/W25）卡在同一觀測缺口。
- **失敗集中**: 5/16 agent exit 1（`research-agent`、`research-agent-weekly`、`doctor`、`harvest`、`janitor`）。其中 `harvest` 確定是「skill 成功、wrapper exit 1」假失敗（每日報告都有產出、`-stderr.log` 0-byte）。真實失敗面（兩個 `research-agent`、`doctor`、`janitor`）仍被假陽性混淆，無法乾淨區分——連 4 週訊號。
- **Dashboard 健康**: 本週 watchdog **1 FAIL / 0 RESTART / 0 ESCALATE**（web 於 06-20 15:34 單次失敗、15:35 自動 recover）。API 全程在線。**延續 W22，是 W19 以來最健康的水準。**

## 下週 Actions (max 3, prioritized)

1. **退休 `knowledge-graph` — 第 4 次 retro，這次不退就退掉 retro 本身** — Why now: W20 把它設成 retro 的 dogfooding 測試、W22 重申、W22 結尾明文「不退就暫停兩週」。W23/W24 確實被跳過、本週重啟它**還在 `skills/meta/knowledge-graph`、usage 資料集 0 紀錄**。連 4+ 次 retro 動不了最便宜的 action，是 retro 信任度的存亡問題，比任何數字重要。Est. effort: 10 min（`rm -rf skills/meta/knowledge-graph` → `bin/sk audit` → README skill count -1）。Expected impact: 終結延期鏈；**若本週仍不執行，下一步不是再寫一份 retro，是正式停掉 `workflow-retro` agent**——停止生產沒人消化的報告本身就是誠實的結論。

2. **抽 `demo-anonymize`（presales 資產去識別化）** — Why now: 去識別化候選已 n=2（06-08 + 06-09 連兩天、同一需求），harvest 自評 Strong、grep 確認現有 presales/secret skill 群零覆蓋，且穿過 harvest 自己引用的「≥2× 才抽」門檻。這是「把真實 A 客戶資產洗成可重用 demo 版本、不洩漏身分」的剛性 presales 需求，會反覆出現。Est. effort: 1-1.5 hr（`skill-creator`：流程＝定位客戶識別欄位 → redact → 截圖驗證殘留，可沿用 CLAUDE.md「生成後自我截圖檢查」延伸）。Expected impact: 補上 presales 流程最後一個未覆蓋環節；把堆積中最成熟的訊號變成產出，證明 harvest→build 這條鏈會動。

3. **修 `concurrent-session-git` 描述（auto-stage 的逐字複製）** — Why now: 本週新增此 skill 時描述複製貼上沒改，audit 兩列一字不差、且是 overlap 警告的真實來源之一。Est. effort: 5 min（改 SKILL.md frontmatter description 為 shared-worktree git 衛生語意 → `bin/sk audit` → README 同步）。Expected impact: 修掉 50 個 audit issue 裡少數的真缺陷；其餘 overlap 警告認列組合性雜訊、不追，避免把 +28 雜訊當成需要逐條處理的退化。

> **W22 Action 3（修 `/api/tokens/filtered` days 參數）降為 backlog 不重列**：連 4 週缺口、價值仍在，但本週成本與 W24 持平、無 spike 急需歸因，且本週三個 action 已有兩個是「終結延期鏈/兌現堆積訊號」的高象徵性項目，不宜再塞第 4 個稀釋執行力。待下次出現單一專案 token spike 時再提。

## 對照上週

> 註：W23、W24 無 retro 檔案（被跳過，與 W22 結尾「Action 1 未動則暫停兩週」的建議一致）。以下對照 **W22**。

W22 三個 actions 完成度：

| # | Action | 狀態 | 證據 |
|---|--------|------|------|
| 1 | 退休 `knowledge-graph` | ❌ NOT DONE | `skills/meta/knowledge-graph` 仍存在、usage 0 紀錄。**連 4+ 次 retro 未動。** |
| 2 | Root-cause agent exit-1 雙態（`harvest`+`material-health`） | 🟡 PARTIAL | `material-health` 本週 **exit 0**（已修）；`harvest` 仍 exit 1 假失敗（有產出、stderr 0-byte）。 |
| 3 | 修 `/api/tokens/filtered` days 參數 | ❌ NOT DONE | 四種日期參數（start/end、from/to、days、period）全被無視，仍回全量 all-time。 |

完成率 **1/3**（Action 2 半成）。與 W18→W22 完全同型：回升全靠 **mechanical** action（這次是修 `material-health` exit）；**editorial/cleanup** action（退休 skill、修 endpoint）連一條都沒動。這是 W19 就預判、至今未破的 pattern——**本 retro 的最重要 meta-finding 仍是它自己的 cleanup action 永遠排不進實作**。

指標變化（W22 → W25）：
- watchdog incidents：1 FAIL/0 RESTART → **1 FAIL/0 RESTART** —— 持平，健康。
- exit-1 agent 數：6 → **5** —— -1（`material-health` recover）。
- 週度 token：7d ~$10.5k → **~$12.4k** —— +18%（但 session 數砍半、每 session 更重）。
- **skill-audit 待處理 issue：22 → 50** —— **+127%**（新債務軸，多為組合性 overlap 雜訊 + 1 真缺陷）。
- per-project 7d 歸因能力：W19/W20/W22/W25 連 4 週缺口 —— **無變化**。
- retro action 完成率：W22 1/3 → W25 **1/3** —— 持平。
