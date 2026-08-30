---
date: 2026-08-09
iso_week: 2026-W32
period: 2026-08-03 to 2026-08-09 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W32

## TL;DR

**W31 的三條 action，完成 0 條；本週 0 個 commit。** 這是本週唯一重要的發現，其餘都是它的推論。W31 花了一整份報告論證「dashboard 會安靜地說謊」「janitor 每次都死在同一行」「tester 停了 13 週」——一週後，`bin/sk-reports-janitor:45` 一字未改、`server.py:394` 仍在呼叫 `launchctl`、`sk-exec-lib:751` 仍寫進另一個 DB、tester 仍未安裝（現在是第 14 週）。janitor 在 08-09 03:00 **第二次以同一根因 exit 1**，而 08-02 那次搬到一半的檔案移動**至今仍卡在 git status（114 個未提交變更）**。

好消息是執行面沒有退步：8 個 rivendell unit 本週全數觸發、7 個 exit 0、watchdog 零事件、dashboard API 三個 endpoint 全部 HTTP 200。成本從 W31 的 $1,623 降到 **$385（-76%）**、session 49 → 15——但這是活動量下降，不是效率提升。

本週唯一的**新增**產出，是把 W18 起累積 14 週的「skill 描述錯置」定位到根因：`bin/sk:2363` 的 `local name category summary` 在迴圈內**不會重置**，配上 `data/skill-summaries-zh.tsv` 缺 9 筆新 skill，導致每份 audit 都把上一個 skill 的描述掛到下一個身上。一行可修。

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+ this week) | — | — |
| 低頻 (1-4 this week) | `cloudflare-tunnel-provision` (08-03)、`gstack` (08-03)、`workflow-retro` (08-09)　**共 3 次** | 8 個 rivendell unit 本週皆有執行：`harvest`、`maintain`、`janitor`、`ssot-drift`、`disk-monitor`、`symlink-fix`、`token-snapshot`、`workflow-retro` |
| 沉寂 (30+ days) | 99 個 skill 中 **93 個**近 30 天無紀錄。有紀錄的僅 6 個：`gstack` (4)、`cloudflare-tunnel-provision` (4)、`workflow-retro` (2)、`user-flow`、`requirement`、`update-config` | `tester`（daily 6:00）、`doctor`（daily 7:00）**仍未安裝 systemd unit**；news_stock (2) + sales-assistant (4) 共 6 個同樣未安裝 |

**資料品質警告（沿用 W31，未改善）**：`/api/skills/usage` 是現場解析 `~/.claude/projects/*.jsonl`，最早只回溯到 2026-06-27。W31 建議的「讓 `sk-token-snapshot` 順便持久化 skill usage」未實作，所以「沉寂 30 天」這條軸**仍在隨 JSONL 輪替腐爛**，數字偏悲觀。

**值得注意**：
- `tester` 未安裝 → `reports/test-*.md` 最後一份仍是 **2026-05-05**，每日結構驗證停擺**第 14 週**。`sk maintain` 每晚照常印出 `tester ○ unloaded`（見 `skill-audit-2026-08-09.md:486-494` 的「1 個 agent 問題待處理」），連續 14 週沒有人讀那一行。
- **audit issue 數 85 → 105（08-07 跳升）**，但這是**純老化**：`✅ 穩定` 32 → 12、`❓ 可能棄用` 67 → 87，剛好 +20。原因是 2026-05-08 那次批次編修的一大批 skill 在 08-07 同時跨過 90 天門檻。**結構性缺陷數字完全沒動**（3 missing tags、4 missing version、2 缺 TRIGGER，symlink / 部署 / 檔案完整性全部 OK）。這個指標會因為批次編修而階梯式跳動，不宜當趨勢讀。
- `knowledge-graph`（W18 首次點名「建好沒人用」）仍零觸發，第 **147** 天。

## 重複痛點

### Theme 1: 回饋迴路空轉——建議產出正常，執行為零（meta）

- **頻率**: n≫3，六條獨立證據 —
  1. **W31 三條 action 完成 0 條**（逐條驗證見「對照上週」）。
  2. **W18 的兩條未完成 action 仍未完成**：`presales-pipeline` README 通路段落、`knowledge-graph` 描述對齊——分別是第 14 週。
  3. **skill 描述錯置從 W18 延續到 W32**，跨越 3 份 retro、14 週零進展。
  4. **`llm-batch-classify` 被 harvest 連續兩次提報 Strong**（08-02、08-04）仍未建立；`harvest-2026-08-02.md` 建議 #5（digest 摺疊）同樣未實作，08-04 已自行把它從「建議」升級成「該做」。
  5. **`.learnings/LEARNINGS.md` 最後一筆是 2026-06-08**，9 週無新增。`self-improving-agent` 這層也停轉。
  6. **本週 0 個 commit**（W31 有 3 個）。
- **類別**: **Architectural**——不是沒有人想修，是**系統只有產生建議的機制，沒有執行與追蹤建議的機制**。retro 寫進 `reports/`、harvest 寫進 `reports/`、audit 寫進 `reports/`，三者都沒有出口。`.harvest-decisions.json` 這個原本該當追蹤器的檔案在 repo 根目錄**根本不存在**。
- **代表性事件**: W31 Action 1 是「10 分鐘、單一行、根因已定位」的修法。一週後那一行原樣未動，而 janitor 又用同一個根因失敗了一次。**難度不是瓶頸，執行入口才是。**
- **建議**: 見 Action 3。W31 已經預先寫下退場條件：「如果 W32 再開起來時這三條都還在，那該退休的是 retro 而不是那些 skill」——**條件已成立**。

### Theme 2: Shell strict-mode 靜默早死

- **頻率**: n≥5，且每一次都真的爆過 —
  - `bin/sk-reports-janitor:45` — `file_date=$(echo "$base" | grep -oE '...' | head -1)`，檔名無 `YYYY-MM-DD` 時 grep 回 1 → pipefail → set -e 殺掉整支。**08-02 與 08-09 連續兩次週排程皆 exit 1**（`ExecMainStatus=1`），第 48-58 行的 ISO-week 分支是永遠到不了的死碼。
  - `bin/sk` 曾有 33 處 `((count++))`（2026-07-17 修）— 計數器從 0 起算時整段求值為零 → exit 1 → `sk deploy` 連完第一個 skill 就死，**還印綠色成功訊息**。
  - `bin/sk-watchdog` 的 `touch .next/.build-complete`（2026-07-27 加 `[ -d .next ]` 才擋住）。
  - **本週新增**：`bin/sk:2363` 的 `local name category summary` 在 `for` 迴圈內**不重置**（實測 `local` 對同一 function scope 的第二次宣告不清值）。變數殘留跨迭代——這是同一個家族的陷阱：語法正確、shellcheck 不抓、失敗時安靜。
  - 現存 **12 個未防護的 `$( ... grep ... )` 分佈在 6 支腳本**（`sk-reports-janitor:45,49`、`sk-ssot-drift-cron:28`、`sk-disk-monitor-cron:32,34`、`sk-agent-doctor:164,173`、`sk:272,283,287,1277`），全部在 `set -euo pipefail` 下。
- **類別**: **Mechanical**——可稽核、可 agent 化。正確寫法已存在於同一 repo（`bin/sk-harvest-cron:59` 的 `|| echo "0"`），缺的是執行機制。
- **代表性事件**: 本週最有價值的單一發現（描述錯置的根因）本身就是這一類 bug——找了 14 週，因為它的失敗表現是「輸出看起來完全正常，只是內容是錯的」。
- **建議**: `harvest-2026-08-04.md` 已把解法寫成 Strong skill 提案 `bash-strict-mode-audit`，論證完整（含最小重現與修法分類），此處不重複。retro 只補一句：**該提案的第一個掃描目標，應該包含 `local` 在迴圈內的殘留**——原提案的陷阱清單漏了這一類。

### Theme 3: 觀測層說謊（W31 原樣延續）

- **頻率**: 5 個症狀點，本週**全部複驗仍然成立**，無任何一項改善 —
  1. `/api/agents` 回 `{"total":0,"agents":[],"by_project":{}}`，而同一時間 8 個 systemd unit 活著、本週全數執行過（`server.py:394-399` 仍 `subprocess.run(["launchctl", ...])`）。
  2. `/api/tokens/filtered` 收下 `start`/`end`/`days` 但完全忽略——本週實測傳 `?start=2026-08-03&end=2026-08-09` 仍回 178 sessions 的全量 payload。
  3. `bin/sk-exec-lib:751` 寫入 `dashboard/data/sk-dashboard.db`，`dashboard/lib/db.py:6` 讀 `dashboard/data/rivendell.db`。
  4. `reports/watchdog.log` **不存在**（skill 的 Data Sources 表仍指名它）。
  5. `ssot-drift` 連續 8 天回報 **16/16**，一天都沒有變動。
- **類別**: **Architectural**
- **代表性事件**: 三個 endpoint 本週全部 HTTP 200——**API 沒有壞，API 在誠實地回報它問錯地方得到的答案**。這比 500 更難發現。
- **建議**: 不變，見 W31 Action 2（收斂 DB 路徑 + `/api/agents` 改走 `bin/lib/platform.sh` 既有的 `svc_*` adapter + 修 `filtered` 參數）。本週**刻意不再重列為 action**，理由見 Action 3。

## 集中度

- **Token 集中**: 本週 **約 $385 / 460K tokens / 15 sessions**（`skill-audit-2026-08-09.md` 今日稍早的快照為 $368.29，差額是今天這場 retro session 本身）。
  - 兩個專案雙雙超過 40% 門檻：`~/projects` 根目錄 **$182.78 = 49.6%**、`mops_dbs` **$168.17 = 45.7%**，合計 **95.3%**。`rivendell` 僅 $10.01 (2.7%)。
  - 但**這週不值得當成「用錯工具」的訊號**：分母只有 15 個 session、$385，任何單一 session 都會把百分比推過門檻。W31 的 mops_dbs 78% 同樣源自單一超長 session。**要連續兩週在高活動量下維持 >40% 才有意義**，目前不成立。
  - ⚠️ 此拆分取自 `skill-audit` 報告與 `/api/tokens` 的 `projects` 陣列，**不是** `/api/tokens/filtered`（該端點忽略時間參數，見 Theme 3）。
- **失敗集中**:
  - `janitor` — 08-09 03:00 exit 1。**與 08-02 同一根因、同一行**（`sk-reports-janitor:45`）。這是本週唯一的 non-zero exit，也是連續第二次。後果累積中：`reports/` 有 **50 個已刪除 + 44 個未追蹤的 archive 檔案、共 114 個未提交變更**卡在 git status 已滿 7 天，且 `janitor.log` 因為死在寫檔之前**兩次都沒有產生**。
  - 其餘 7 個 rivendell agent 全部 exit 0（`harvest`、`maintain`、`ssot-drift`、`disk-monitor`、`symlink-fix`、`token-snapshot`、`workflow-retro`）。W31 的 `maintain` exit 2 已確認自癒，本週未再發生。
- **Dashboard 健康**: **零次 watchdog 觸發重啟**（連續第二週）。`api` / `web` 在 08-07 有 3 次 `Started`，但對照 `journalctl --list-boots`，那是 WSL 的 systemd user manager 在 11:18 結束、12:33 與 12:41 兩次重啟造成的**宿主層重啟**，非 watchdog 事件。兩個服務目前皆 `active`。
- **API 可用性**: **本週 API 未中斷**，`/api/skills/usage`、`/api/agents`、`/api/tokens` 全部 HTTP 200。但如 Theme 3 所述，「上線」與「說真話」在此不是同一件事——`/api/agents` 回報 0 個 agent 的同時有 8 個在跑。**下週若這條仍未修，建議把它從 Theme 降級處理的理由就不存在了。**

## 下週 Actions (max 3, prioritized)

1. **修 `bin/sk:2363` 的 `local` 未重置 + 補 `data/skill-summaries-zh.tsv` 的 9 筆缺漏** — Why now：這是 W18 → W31 → W32 橫跨 **14 週**、三份 retro 都點名卻從未定位根因的項目，本週已定位完成，且**修法是一行**。
   - 根因：`bin/sk:2363` 的 `local name category summary` 在 `for skill_dir` 迴圈內執行第二次以後不會清值（bash 對同一 function scope 的重複 `local` 宣告不重置）。當 `get_skill_zh` 對 TSV 沒有的 skill 回傳空字串時，`summary` 保留**上一個迭代**的值；因為 `all_skill_dirs()` 有 `sort`，「上一個」正好是同目錄下字母序前一名的 skill。
   - 證據鏈：TSV（113 列，最後更新 2026-05-18）缺 `doc-drift-sync`、`workflow-retro`、`learnings-promotion-sprint`、`app-ops-baseline`、`client-kickoff-docs`、`env-doctor`、`mops-financial-scraper`、`presales-pipeline`、`repro-exam` 共 9 筆。對應到 `skills/meta/dev-process-gate` → `doc-drift-sync`、`skills/meta/sync-readme` → `workflow-retro`、`skills/workflow/planning-with-files` → `presales-pipeline` → `repro-exam`（**連續兩格繼承同一段文字，是殘留而非位移的鐵證**）。英文 fallback `get_skill_summary` 救不了，因為 `[ -z "$summary" ]` 對殘留值為 false。
   - 修法：`local name="" category="" summary=""`，並補上 9 筆 TSV。Est. effort：**30 分鐘**。Expected impact：`skill-audit` 的「功能一覽」恢復可信——這份表格是 retro / harvest 判斷 skill 邊界的輸入，錯了 14 週。

2. **修 `bin/sk-reports-janitor:45` 並提交那 114 個卡住的檔案變更** — Why now：**原封不動再列一次 W31 Action 1**。它是本週唯一失敗的 agent、連續第二次同根因失敗，而未提交的檔案移動已經髒了 7 天、`janitor.log` 兩次都沒生成。
   - 修法：第 45 行改為 `file_date=$(echo "$base" | grep -oE '...' | head -1 || true)`，確認第 48-58 的 ISO-week 分支從此走得到，然後 `git add -A reports/` 提交那批已發生的移動。Est. effort：**10 分鐘 + 一次提交**。Expected impact：歸檔恢復原子性、`janitor.log` 開始有 audit trail、git status 清乾淨。

3. **給 action 一個執行入口，並設定 retro 的退場條件** — Why now：這是本份 retro 最重要的發現（Theme 1）。W31 已寫下退場條件、而條件**本週成立**。
   - 三件具體的事：(a) 把 W31 Action 2（觀測層收斂，1-2h）與 Action 3（安裝 `tester` + `doctor` unit，20 分鐘）從「每週被 retro 重抄一次」移到**單一追蹤清單**——`.harvest-decisions.json` 這個原本該當追蹤器的檔案在 repo 根目錄根本不存在，先把它建起來或改用 GitHub issues；(b) 本週**不新增任何其他 backlog**；(c) 明確的退場條件：**若 W33 開起來時 Action 1 與 2（合計 40 分鐘）仍未完成，就停掉 `workflow-retro` 的 systemd timer**——一份沒有人執行其結論的週報，成本是真的、價值是零，而 SKILL.md 自己寫了這句話。
   - Est. effort：建追蹤清單 20 分鐘 + 一個決定。Expected impact：讓「完成度」變成可驗證的數字，而不是每週由 retro 重新考古一次。

> **刻意不列入 actions**：W31 Action 2（觀測層收斂）與 Action 3（安裝 tester / doctor）**都仍然有效且仍然重要**，但這一週連 10 分鐘的修法都沒有執行，再排一條 1-2 小時的只會讓下一份 retro 的完成度分母變大。它們改由 Action 3 的追蹤清單承接。同理，`harvest-2026-08-04.md` 的 `bash-strict-mode-audit` 與 `llm-batch-classify` 由 harvest 自己追蹤，retro 不重複佔額度。

## 對照上週

對照對象：**W31（2026-08-02）**。這是 W18 以來第一次有真正的「上週」。

**上週 actions 完成度：0 / 3**

| # | W31 Action | 狀態 | 證據 |
|---|-----------|------|------|
| 1 | 修 `sk-reports-janitor` 的 pipefail 早死 | ❌ **未做** | 第 45 行原樣無 `\|\| true`；janitor 08-09 03:00 再次 `ExecMainStatus=1`；114 個未提交變更仍在 git status |
| 2 | 收斂觀測層（DB 路徑 / `/api/agents` / `filtered` 參數） | ❌ **未做**（0/3 子項） | `sk-exec-lib:751` 仍 `sk-dashboard.db`、`dashboard/lib/db.py:6` 仍 `rivendell.db`；`server.py:394-399` 仍 `launchctl`；`filtered?start=&end=` 實測仍回全量 |
| 3 | 補裝 `tester` + `doctor` 的 systemd unit | ❌ **未做** | `~/.config/systemd/user/` 仍只有 8 個 `com.sk.agent.rivendell.*`；`reports/test-*.md` 最後一份仍是 2026-05-05 |

**指標變化（W31 → W32）**

| 指標 | W31 | W32 | 方向 |
|------|-----|-----|------|
| 上週 action 完成度 | 1/3（對照 W18） | **0/3** | ❌ 退步 |
| Commits | 3 | **0** | ❌ 退步 |
| Sessions / 成本 | 49 / $1,623 | 15 / **$385** | ➖ 活動量下降，非效率改善 |
| Skill 觸發次數 | 2 | **3** | ➖ 同一量級，統計上無差異 |
| 30 天內有觸發的 skill | 7 / 99 | **6 / 99** | ➖ 持平（含 JSONL 輪替造成的低估） |
| Agent non-zero exit | 2（janitor 未解、maintain 已自癒） | **1**（janitor，同根因第 2 次） | ➖ maintain 已癒，janitor 未動 |
| Agent 排程覆蓋率 | rivendell 8/10；news_stock + sales 0/6 | **完全相同** | ❌ 零進展 |
| Watchdog 事件 | 0 | **0** | ✅ 維持 |
| SSOT drift | 16/16 | **16/16** | ❌ 零進展 |
| Audit 結構性缺陷 | 7（frontmatter） | **7 + 2 缺 TRIGGER** | ➖ 持平（105 vs 85 的差額全是 90 天老化） |
| W18 Theme 3（audit 描述錯置） | 原樣存在（第 13 週） | **根因已定位，仍未修**（第 14 週） | ➕ 首次有進展 |
| `.learnings/` 最後一筆 | 2026-06-08 | **2026-06-08** | ❌ 第 9 週無新增 |
