---
date: 2026-08-16
iso_week: 2026-W33
period: 2026-08-10 to 2026-08-16 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W33

## TL;DR

**W32 寫下的退場條件，本週成立。** W32 Action 3 的原文是：「若 W33 開起來時 Action 1 與 2（合計 40 分鐘）仍未完成，就停掉 `workflow-retro` 的 systemd timer」。本週逐條複驗：`bin/sk:2364` 的 `local name category summary` 一字未改、`data/skill-summaries-zh.tsv` 仍是 113 列缺同樣 9 筆、`bin/sk-reports-janitor:45` 仍無 `|| true`、卡住的檔案變更從 114 個長到 **131 個**。**完成度 0 / 3，連續第二週；commit 連續第二週為 0**（最後一次是 08-02 `bf44ff7`）。

而 janitor 在本週 **08-16 03:00 以同一根因第三次 exit 1**（08-02、08-09、08-16，另加 08-13 20:38 開機觸發的一次，共四次）。W32 說「難度不是瓶頸，執行入口才是」——再過一週，這句話本身也變成了沒有人執行的結論。

執行面其餘部分沒有退步：8 個 rivendell unit 本週全部觸發、7 個 exit 0、watchdog 零事件、三個 API endpoint 全部 HTTP 200。活動量連續第二週下降（16 → 7 sessions、$471 → $152），08-13 至 08-15 連續三天零 session。**本份 retro 只有一個決定要下**：把那 40 分鐘做完，或把這個 timer 關掉。

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+ this week) | — | — |
| 低頻 (1-4 this week) | `gstack` (08-11)、`workflow-retro` (08-16)　**共 2 次** | 8 個 rivendell unit 本週皆觸發：`harvest`、`maintain`、`janitor`、`ssot-drift`、`disk-monitor`、`symlink-fix`、`token-snapshot`、`workflow-retro` |
| 沉寂 (30+ days) | 99 個 skill 中 **94 個**近 30 天無紀錄。有紀錄的僅 5 個：`gstack` (4)、`workflow-retro` (3)、`cloudflare-tunnel-provision`、`user-flow`、`requirement` | `tester`（daily 6:00）、`doctor`（daily 7:00）**仍未安裝 systemd unit**（第 3 週複驗，`~/.config/systemd/user/` 仍只有 8 個 `com.sk.agent.rivendell.*`）；news_stock + sales-assistant 6 個同樣未安裝 |

**資料品質警告（W31 → W32 → W33 沿用，未改善）**：`/api/skills/usage` 是現場解析 `~/.claude/projects/*.jsonl`，無持久化。W31 提的「讓 `sk-token-snapshot` 順便存 skill usage」仍未做，所以「沉寂 30 天」這條隨 JSONL 輪替腐爛，5/99 是**偏悲觀**的數字。

**值得注意**：

- **`harvest` 本週跑了 8 次、每次 exit 0、一份報告都沒產出**——這**不是缺陷**。`bin/sk-harvest-cron:52` 的 `MIN_SESSIONS=3` 門檻正確擋掉了低活動量的空轉，最後一份報告是 08-13。查證這一條的成本是 5 分鐘，寫進來是為了讓下一份 retro 不用再查一次。
- `tester` 未安裝 → `reports/test-*.md` 最後一份仍是 **2026-05-05**，每日結構驗證停擺**第 15 週**。`sk maintain` 每晚照常印 `tester ○ unloaded`（`skill-audit-2026-08-16.md:510`）。
- **audit issue 105 → 111**，增量**全部是老化**：`✅ 穩定` 12 → 7、`❓ 可能棄用` 87 → 92，加上專案問題 8 → 9。**結構性缺陷三項全部一字未動**（3 missing tags、4 missing version、2 缺 TRIGGER；symlink / 部署 / 檔案完整性 OK）。這個總數會因批次編修階梯式跳動，**不宜當趨勢讀**。
- **描述錯置仍在現行報告裡**：`skill-audit-2026-08-16.md:308` 的 `env-doctor` 描述是「派遣多個 agent 平行處理 3+ 個獨立問題」——那是 `dispatching-parallel-agents` 的文字。W18 首次點名，第 **15 週**，根因已於 W32 定位，修法一行。

## 重複痛點

### Theme 1: 回饋迴路空轉——建議產出正常，執行為零（meta）

- **頻率**: n≫3，本週複驗五條，**全部成立且全部惡化** —
  1. **W32 三條 action 完成 0 條**（逐條證據見「對照上週」），且 W32 本身就是「W31 完成 0 條」的報告。**連續兩週 0/3。**
  2. **connect 到程式碼的證據**：`bin/sk:2364`、`sk-reports-janitor:45`、`sk-exec-lib:751`、`server.py:394` 四個被三份 retro 點名的位置，本週 `grep` 複驗**全部原樣**。
  3. **卡住的變更從 114 → 131 個**（`git status --porcelain | wc -l`）。W32 說「已髒 7 天」，現在是 14 天，而且變多了。
  4. **commits：W31 有 3、W32 有 0、W33 有 0**。
  5. **`.learnings/LEARNINGS.md` 最後一筆仍是 2026-06-08，第 10 週無新增。**
- **類別**: **Architectural**——系統有產生建議的機制，沒有執行與追蹤的機制。W32 Action 3 要建的追蹤清單也沒建（`reports/.harvest-decisions.json` 仍停在 2026-05-18，repo 根目錄無任何追蹤檔）。
- **代表性事件**: W32 為這個問題寫了退場條件當作止損。一週後，**連那個退場條件也沒有被執行**——這正是它想描述的病。
- **建議**: 見 Action 1。這是本週唯一需要下的決定。

### Theme 2: Shell strict-mode 靜默早死（W32 原樣延續）

- **頻率**: n≥5，本週新增一次真實爆炸 —
  - `bin/sk-reports-janitor:45` — `file_date=$(echo "$base" | grep -oE '...' | head -1)`，檔名無 `YYYY-MM-DD` 時 grep 回 1 → pipefail → `set -e` 殺掉整支。**08-16 03:00 第三次 exit 1**（`Result=exit-code`、`ExecMainStatus=1`），第 48-58 行的 ISO-week 分支仍是永遠到不了的死碼。
  - `bin/sk:2364` 的 `local name category summary` 在 `for` 迴圈內不重置——**這是本週 `skill-audit` 仍在輸出錯誤描述的原因**。
  - 既有清單不變：`sk-reports-janitor:49`、`sk-ssot-drift-cron:28`、`sk-disk-monitor-cron:32,34`、`sk-agent-doctor:164,173`、`sk:272,283,287,1277`，共 12 處未防護的 `$( ... grep ... )` 在 `set -euo pipefail` 下。
- **類別**: **Mechanical**——正確寫法已存在同 repo（`bin/sk-harvest-cron:59` 的 `|| echo "0"`）。
- **代表性事件**: 兩個症狀（janitor 死掉、audit 描述錯置）**根因同一族、修法都在一行以內、合計 40 分鐘**，而它們已經分別存活了 3 週與 15 週。
- **建議**: 見 Action 2。`harvest-2026-08-04.md` 的 `bash-strict-mode-audit` 提案由 harvest 自己追蹤，retro 不重複佔額度。

### Theme 3: 觀測層說謊（W31 → W32 → W33，五個症狀點全部原樣）

- **頻率**: 本週逐條複驗，**5/5 成立，零改善** —
  1. `/api/agents` 回 `{"total":0,"agents":[],"by_project":{}}`，同一時間 8 個 systemd unit 活著、本週全數執行過（`server.py:394-399` 仍 `subprocess.run(["launchctl", ...])`，而這台機器是 WSL/systemd）。
  2. `/api/tokens/filtered?start=2026-08-10&end=2026-08-16` 實測仍回 **176 sessions / 25 天 / $3,337 的全量 payload**，參數完全被忽略。
  3. `bin/sk-exec-lib:751` 寫 `dashboard/data/sk-dashboard.db`，`dashboard/lib/db.py:6` 讀 `dashboard/data/rivendell.db`。
  4. `reports/watchdog.log` **不存在**（本 skill 的 Data Sources 表仍指名它；本週改由 `journalctl --user -u com.sk.dashboard.watchdog` 取代）。
  5. `ssot-drift` **連續 15 天回報 16/16**（08-02 至 08-16 每日報告 `total_drift: 16`），一天都沒變動。
- **類別**: **Architectural**
- **本週新增證據（mechanical，非 architectural）**：`.learnings/LEARNINGS.md` 開頭的 2026-05-13 promotion sprint 指定「新的 generic learnings 寫到 `~/.claude/learnings/LEARNINGS.md`」——**該目錄在這台機器上不存在**（`~/.claude/CLAUDE.md` 同樣不存在，兩者都是 WSL 搬遷的遺失）。10 週無新 learning 未必全是行為問題，**目的地本身是壞的**。修法是 `mkdir -p ~/.claude/learnings` + 建檔，30 秒；**刻意不列為 numbered action**（理由見下方註記），但誰先看到誰順手做掉。
- **建議**: 不變，見 W31 Action 2。**本週第三次刻意不列為 action**——理由同 W32：連 10 分鐘的修法都沒執行，再排 1-2 小時的只會讓下一份 retro 的分母變大。

## 集中度

- **Token 集中**: 本週 **$151.91 / 279K tokens / 7 sessions**（`/api/tokens` 日資料加總；`skill-audit-2026-08-16.md` 的 $150.71 是今日稍早快照，差額是本場 retro session）。
  - `~/projects` 根目錄 **$120.81 = 80.2%**，遠超 40% 門檻，且**連續第二週居首**（W32 為 49.6%）。其餘：`mops_dbs` $11.87 (7.9%)、`pti-ares` $11.07 (7.3%)、`rivendell` $6.97 (4.6%)。
  - **但仍不構成「用錯工具」訊號**：$120.81 中的 $105 來自 08-11 的**單一 session**。分母 7 個 session 時，任何長 session 都會把百分比推過門檻。W32 已寫下判準：**要連續兩週在高活動量下維持 >40% 才有意義**——「連續兩週」成立，「高活動量」不成立。
  - 附帶一提：成本集中在 `~/projects` **根目錄**而非各專案子目錄，意味這些 session 是在專案外啟動的（不會載入專案 CLAUDE.md）。目前樣本太小，記一筆，不下結論。
  - ⚠️ 此拆分取自 `skill-audit` 報告，**不是** `/api/tokens/filtered`（該端點忽略時間參數，見 Theme 3）。
- **失敗集中**: `janitor` — **本週唯一 non-zero exit**，08-16 03:00 `ExecMainStatus=1`，與 08-02、08-09 同一根因同一行；08-13 20:38 另有一次開機觸發的同因失敗。unit 目前停在 `failed` 狀態。其餘 7 個 agent 全部 exit 0（harvest、maintain、ssot-drift、disk-monitor、symlink-fix、token-snapshot、workflow-retro）。
- **Dashboard 健康**: **零次 watchdog 觸發重啟**（連續第三週）。`api` / `web` 在 08-12 有 4 組 `Started`，但 systemd PID 依序為 225 → 213 → 205，是 **WSL user manager 重啟造成的宿主層事件**，非 watchdog 動作（`journalctl -u com.sk.dashboard.watchdog` 本週 0 筆 restart/unhealthy）。兩個服務目前皆 `active (running)`。
- **API 可用性**: **本週未中斷**，`/api/skills/usage`、`/api/agents`、`/api/tokens` 全部 HTTP 200。但如 Theme 3 第 1 點：`/api/agents` 誠實地回報了它問錯地方得到的答案。

## 下週 Actions (max 3, prioritized)

**只列 2 條，且第 2 條與 W32 完全相同。** 這是刻意的：連續兩週 0/3 的情況下，新增第三條只會把下一份 retro 的分母墊大。

1. **執行 W32 寫下的退場條件——停掉 `workflow-retro` 的 systemd timer（或改雙週）** — Why now：條件已成立且無爭議（Action 1 與 2 皆未完成，逐條證據見「對照上週」）。這是 Theme 1 唯一能由 retro 自己執行的動作，其餘全部需要人動手。
   - 做法：`systemctl --user disable --now com.sk.agent.rivendell.workflow-retro.timer`；或若判斷仍有價值，改成雙週（`OnCalendar=Sun *-*-* 23:00:00` + 週次判斷），並**明確寫下恢復條件 = Action 2 完成**。
   - Est. effort：**一個指令 + 一個決定**。Expected impact：一份沒有人執行其結論的週報，成本是真的、價值是零——這是 SKILL.md「如果它一直產生不出行動，該退休的是 retro 自己」的原話。**這條不是自我否定，是這份報告唯一還能證明自己有用的方式。**

2. **那 40 分鐘：修 `sk-reports-janitor:45` + `bin/sk:2364` + 補 TSV 9 筆 + 提交 131 個變更** — Why now：**W32 Action 1 與 2 原封不動再列一次**（janitor 那條已是第三次列出）。合併成一條，因為它們是同一族 bug、同一次可以做完，也是 Action 1 的恢復條件。
   - (a) `sk-reports-janitor:45` 改 `... | head -1 || true)`，確認第 48-58 行 ISO-week 分支走得到 → janitor 三連敗終止、`janitor.log` 開始有 audit trail。
   - (b) `bin/sk:2364` 改 `local name="" category="" summary=""`，並補 `data/skill-summaries-zh.tsv` 缺的 9 筆（`doc-drift-sync`、`workflow-retro`、`learnings-promotion-sprint`、`app-ops-baseline`、`client-kickoff-docs`、`env-doctor`、`mops-financial-scraper`、`presales-pipeline`、`repro-exam`）→ `skill-audit` 的「功能一覽」在錯了 15 週後恢復可信。
   - (c) `git add -A reports/ && git commit` 清掉卡了 14 天的 131 個變更。
   - Est. effort：**40 分鐘**（W32 的估計，本週複驗仍然正確——沒有任何東西讓它變難）。Expected impact：唯一失敗的 agent 恢復、retro/harvest 的輸入資料恢復可信、git status 乾淨。

> **刻意不列入 actions**：W31 Action 2（觀測層收斂，1-2h）、安裝 `tester` + `doctor` unit（20 分鐘）、`mkdir ~/.claude/learnings`（30 秒）——三者都仍然有效、仍然重要。它們不在清單上，不是因為不重要，而是因為**清單長度從來不是瓶頸**。

## 對照上週

對照對象：**W32（2026-08-09）**

**上週 actions 完成度：0 / 3**（連續第二週 0/3）

| # | W32 Action | 狀態 | 證據 |
|---|-----------|------|------|
| 1 | 修 `bin/sk:2363` 的 `local` 未重置 + 補 TSV 9 筆 | ❌ **未做** | `bin/sk:2364` 仍為 `local name category summary`；TSV 仍 113 列、9 筆全缺；`skill-audit-2026-08-16.md:308` 的 `env-doctor` 仍掛著 `dispatching-parallel-agents` 的描述 |
| 2 | 修 `sk-reports-janitor:45` + 提交 114 個卡住的變更 | ❌ **未做** | 第 45 行仍無 `\|\| true`；janitor 08-16 03:00 第三次 `ExecMainStatus=1`；未提交變更 114 → **131** |
| 3 | 建立 action 追蹤入口 + 設定 retro 退場條件 | ⚠️ **半條**（0.5/1） | 退場條件**有寫下**（本週據以成立，見 Action 1）；追蹤清單**未建**——repo 根目錄無追蹤檔，`reports/.harvest-decisions.json` 仍停在 2026-05-18 |

**指標變化（W32 → W33）**

| 指標 | W32 | W33 | 方向 |
|------|-----|-----|------|
| 上週 action 完成度 | 0/3 | **0/3** | ❌ 連續第二週 |
| Commits | 0 | **0** | ❌ 連續第二週（最後一次 08-02） |
| 未提交變更 | 114 | **131** | ❌ 惡化 |
| Sessions / 成本 | 16 / $471 | **7 / $152** | ➖ 活動量續降，非效率改善 |
| Skill 觸發次數 | 3 | **2** | ➖ 同量級，統計上無差異 |
| 30 天內有觸發的 skill | 6 / 99 | **5 / 99** | ➖ 持平（含 JSONL 輪替低估） |
| Agent non-zero exit | 1（janitor，第 2 次） | **1**（janitor，**第 3 次**） | ❌ 同根因未動 |
| Agent 排程覆蓋率 | rivendell 8/10；news_stock + sales 0/6 | **完全相同** | ❌ 零進展 |
| Watchdog 事件 | 0 | **0** | ✅ 維持（連續第三週） |
| SSOT drift | 16/16 | **16/16** | ❌ 零進展（連續 15 天同數字） |
| Audit 結構性缺陷 | 3 tags + 4 version + 2 TRIGGER | **完全相同** | ➖ 持平（111 vs 105 的差額全是老化 + 1 個專案問題） |
| W18 Theme（audit 描述錯置） | 根因已定位，未修（第 14 週） | **仍未修（第 15 週）** | ❌ 零進展 |
| `.learnings/` 最後一筆 | 2026-06-08 | **2026-06-08** | ❌ 第 10 週無新增（且本週查出寫入目的地 `~/.claude/learnings/` 根本不存在） |
| 每日結構驗證（`test-*.md`） | 停擺第 14 週 | **停擺第 15 週** | ❌ 零進展 |

**W32 → W33 的淨變化，只有三件事**：janitor 多失敗一次、未提交變更多了 17 個、退場條件從「已寫下」變成「已成立」。其餘 13 項指標**全部原樣**。

> **註**：W32 報告記載的「15 sessions / $385」是當時執行中的快照。本週以同一 API 重算 08-03～08-09 為 **16 sessions / $471.43**，上表採用重算值以維持兩週可比。
