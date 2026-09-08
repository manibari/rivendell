---
date: 2026-08-02
iso_week: 2026-W31
period: 2026-07-26 to 2026-08-02 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W31

## TL;DR

距離上一份 retro（W18, 2026-05-03）已經 **13 週**——retro 本身停擺，比它這次找到的任何一條發現都重要。本週 49 個 session、$1,623、3 個 commit，全部是 macOS→WSL 平台遷移的長尾修補（`OnActiveSec`、BSD `sed`、`launchctl`→systemd）。系統的**執行面在復原**（8 個 rivendell agent 本週都跑過，dashboard 零次 watchdog 重啟，遠優於 W18 的 6 次），但**觀測面是瞎的**：`/api/agents` 回 `agents: []`（仍在 shell out 到 `launchctl`）、`agent_runs` 寫進 `sk-dashboard.db` 而 API 讀 `rivendell.db`、`/api/tokens/filtered` 忽略時間參數、`agents.conf` 宣告 16 個 agent 但 `projects.json` 一個都沒有。Dashboard 一臉正常地回報 0——這正是本週 `deployment-inventory.md` 寫下的 D-1「探測，不要讀設定檔」的活證據。Token 極度集中：mops_dbs 吃掉 78.1%。

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+ this week) | — | — |
| 低頻 (1-4 this week) | `user-flow` (07-29)、`workflow-retro` (08-02) | rivendell 8 個 unit 本週皆有執行：`harvest` ×2、`maintain` ×2、`disk-monitor` / `ssot-drift` / `symlink-fix` / `token-snapshot` / `workflow-retro` / `janitor` 各 ×1 |
| 沉寂 (30+ days) | 99 個 skill 中 92 個在近 30 天無紀錄。30 天內有紀錄的只有 7 個：`gstack` (3)、`cloudflare-tunnel-provision` (2)、`fewer-permission-prompts`、`requirement`、`update-config`、`user-flow`、`workflow-retro` | `tester`（daily 6:00）、`doctor`（daily 7:00）**宣告了但沒有 systemd unit**；news_stock (2) + sales-assistant (4) 共 6 個 agent 同樣未安裝 |

**必要的資料品質警告**：`/api/skills/usage` 是從 `~/.claude/projects/*.jsonl` 現場解析出來的，而那些檔案最早只回溯到 **2026-06-27**。`sk-token-snapshot` 把 token 數字持久化進 SQLite（29 天），但 **skill 使用紀錄沒有對應的 snapshot**。所以「沉寂 30+ 天」這條軸這週只能算「近 5 週」，再往前的歷史已經被 JSONL 輪替吃掉了——W18 那份 retro 引用得出 `slide-workflow` 6 次、`office-pptx` 4 次，今天已經完全查不到。**這條軸正在腐爛，不是 skill 真的都沒人用。**

**值得注意**：
- 49 個 session 只觸發 2 次 skill。扣掉 telemetry 缺口，本週的性質也確實不是 skill-driven——是基礎設施搶修（3 個 commit 全是 `fix(sk)`）。這個數字本身不是警訊。
- `tester` agent 沒安裝 → `reports/test-*.md` 最後一份是 **2026-05-05**，等於**每日結構驗證已經停了 13 週**。`bin/sk maintain` 的 agent health 有抓到（`tester ○ unloaded`）並印出「1 agent issue(s) found」，但沒有人在讀那行輸出。
- `knowledge-graph`（W18 就點名的「建好沒人用」）SKILL.md 自 2026-03-15 起未再修改，仍然零觸發，現在是第 140 天。

## 重複痛點

### Theme 1: macOS-ism 殘留（平台遷移長尾）
- **頻率**: n≥8 跨三個來源 — commit `bf44ff7`（interval timer 要 `OnActiveSec`）、`38a07d2`（BSD `sed -i ''` → GNU）、`b27a54d`（sk-watchdog 從 launchctl 移植）；`harvest-2026-08-02.md` 觀察 #2 自行判定 n≥5（session 23 node 路徑寫死、24 platform.sh/systemd 盤點、26 跨機器權限殘留）；**尚未修掉的兩處**：`dashboard-next/api/server.py:394-399` 仍 `subprocess.run(["launchctl", ...])`、`bin/sk-reports-janitor:33,54` 仍用 BSD `date -j -v`。
- **類別**: **Architectural** — 不是零星 bug，是同一個假設（「這台是 macOS」）散在整個 codebase。
- **代表性事件**: `/api/agents` 回 `{"metrics":{"total":0,...},"agents":[]}` 而同一時間 systemd 有 8 個 rivendell unit 活著、本週跑了 10 次。API 沒有報錯，它只是誠實地回報它從 launchctl 問到的東西——什麼都沒有。
- **建議**: `harvest-2026-08-02.md` 已經把解法寫成兩支 Strong skill 提案（`systemd-user-agent`、`portability-sweep`），論證充分、不在此重複。retro 這邊只補一句：**先把 `server.py` 的 launchctl 呼叫換成 `bin/lib/platform.sh` 既有的 `svc_*` adapter**——那個 adapter 已經寫好了，API 卻沒用它。

### Theme 2: 觀測層的寫入端與讀取端分裂
- **頻率**: 4 個獨立症狀點，同一個病因 —
  1. `bin/sk-exec-lib:751` 把 agent_runs 寫進 `dashboard/data/sk-dashboard.db`（今天已寫入 9 筆，含 `maintain` 兩次 exit 2）；`dashboard/lib/db.py:6` 的 `get_conn()` 讀 `dashboard/data/rivendell.db`（agent_runs **0 筆**）。API 看不到自己剛記下來的東西。
  2. repo 根目錄還有第三個 `data/rivendell.db`，兩張表都是空的——孤兒。
  3. `/api/tokens/filtered` 收下 `days` / `start` / `end` 但完全忽略，回傳與 `/api/tokens` 逐字相同的全量 payload。retro 的「本週 token 分佈」因此只能自己重算 JSONL。
  4. `ssot-drift-2026-08-02.md`：`agents.conf` 宣告的 **16 個 agent，`~/.claude/projects.json` 一個都沒有**（total_drift 16/16）。
- **類別**: **Architectural** — 每一項單獨看都像小 bug，合起來是「dashboard 說系統是空的，而系統其實在跑」。
- **代表性事件**: 本週 `maintain` 在 02:29 與 02:30 連續兩次 exit 2、02:32 才恢復正常。這件事**只存在於 journalctl 和 sk-dashboard.db**；dashboard UI、`/api/agents`、任何報告都不會顯示它。
- **建議**: 收斂成單一 DB 路徑（建議 `dashboard/data/rivendell.db`，因為 token_usage 的 29 天歷史在那），把 `sk-exec-lib` 指過去並把 sk-dashboard.db 的 9 筆搬過去；順手修 `/api/tokens/filtered` 的參數。

### Theme 3: 回饋迴路自己停轉（meta）
- **頻率**: 3 條獨立證據 —
  1. **W18 → W31 中間 13 週沒有 retro**。`workflow-retro` agent 的 systemd unit 存在且今天正常觸發，但中間的空窗代表它在遷移期整段沒跑。
  2. **W18 的 Theme 3 一字未改地還在**：`skill-audit-2026-08-02.md:304,311,312` 依然是 `workflow-retro` 顯示 sync-readme 的描述、`client-kickoff-docs` 顯示 telegram-bot、`env-doctor` 顯示 dispatching-parallel-agents——同樣三個，隔了 13 週。
  3. **`.learnings/LEARNINGS.md` 最後一筆是 2026-06-08**，8 週沒有新增。而本週光是 commit 訊息就埋著至少 3 個非直覺的教訓（`OnActiveSec` vs `OnUnitActiveSec`、BSD/GNU sed、WSL systemd 是 opt-in）——`self-improving-agent` 這層也停了。
- **類別**: **Editorial**（機制都在，是沒有人在收）
- **代表性事件**: W18 明確寫下「Theme 3 本週不列入 actions……記錄在此供下週若仍存在再升級」。下週從來沒有到來。
- **建議**: 這條不列 action，而是本份 retro 的存在本身。但如果 W32 再開起來時這三條都還在，那該退休的是 retro 而不是那些 skill——skill 的 SKILL.md 自己寫了這句話。

## 集中度

- **Token 集中**: 本週 **$1,622.84 / 1.70M tokens / 49 sessions / 1,434 messages**（上週 07-19~07-25：$948.48 / 3.11M / 135 sessions）。單一專案 `mops_dbs` 佔 **$1,271.10 = 78.1%**，遠超 40% 門檻；其次 `~/projects` 根目錄 8.1%、`pti-ares` 6.8%、`rivendell` 6.1%。
  - 這 78% 集中在 **一個 session**（harvest #21，520 則訊息，Phase C schema + 手動 migration + F17 財報 PDF），大量成本來自 cache-read 累積而非新輸出。**不是「用錯工具」，是一個超長 session**。若下週 mops_dbs 仍 >70%，才值得問工具問題。
  - ⚠️ 這份 per-project 拆分是我自己重解 JSONL 算的（總額 $1,626.75，與 API 的 $1,622.84 對得上），**因為 `/api/tokens/filtered` 壞了**（見 Theme 2）。
- **失敗集中**:
  - `janitor` — 本週 1 次排程執行，**失敗**（exit 1）。已定位到根因：`bin/sk-reports-janitor:45` 在 `set -euo pipefail` 下跑 `echo "$base" | grep -oE ... | head -1`，遇到檔名裡沒有 `YYYY-MM-DD` 的檔案時 grep 回 1 → pipefail 讓整個命令替換失敗 → set -e 直接殺掉腳本。第一個踩到的檔案就是 `workflow-retro-2026-W18.md`。**後果是它今天 03:00 搬了一半就死**：`reports/archive/2026-04/` 多了幾十個檔案、原檔已刪，全部躺在 git status 裡未提交，而且 `janitor.log` 因為死在寫檔之前**完全沒產生**。第 48-58 行專門處理 ISO-week 檔名的分支是死碼，永遠到不了。
  - `maintain` — 02:29、02:30 連續兩次 exit 2（`status=2/INVALIDARGUMENT`），02:32 與 22:00 恢復 exit 0。時間點與今天的 `38a07d2`（BSD sed 修正）吻合，判定為修補期間的暫態，已自癒。
  - 其餘 6 個 rivendell agent 本週全部 exit 0。
- **Dashboard 健康**: **零次 watchdog 觸發重啟**。watchdog 每 1-2 分鐘探測一次、全部 `Finished` 無事件；`api` / `web` 各只在 07-27 重啟一次（就是 `b27a54d` 那次 launchctl→systemd 移植）。對照 W18 的 6 次 watchdog event，這是本週最紮實的改善——W18 Action 1 的 sentinel file 修正確實生效了。
  - 但 skill 文件指名的資料源 **`reports/watchdog.log` 不存在**，`logs/` 目錄是 root 所有且空的。watchdog 現在只留 journalctl。SKILL.md 的 Data Sources 表需要更新，否則下次 retro 會誤判成「沒有 watchdog」。
- **Audit issues**: 99 skills / 85 issues。組成是 3 missing tags + 4 missing version + **67 個「>90 天未更動」的生命週期分類** + 專案 config/權限缺口。**不要拿 85 跟 W18 的 18 直接比**——那 67 個是年齡不是缺陷，計數基礎不同。真正的結構性缺陷只有 7 個 frontmatter 問題，symlink / 部署 / 檔案完整性全部 OK。

## 下週 Actions (max 3, prioritized)

1. **修 `bin/sk-reports-janitor` 的 pipefail 早死** — Why now：唯一一個本週真的失敗的 agent，根因已定位到單一行，而且它每次失敗都留下一個搬到一半的 `reports/`（現在就有幾十個未提交的檔案移動卡在 git status 裡）+ 零 log。修法：第 45 行改成 `file_date=$(echo "$base" | grep -oE '...' | head -1 || true)`，並確認第 48-58 的 ISO-week 分支從此走得到。Est. effort：10 分鐘 + 提交這批已發生的檔案移動。Expected impact：`reports/` 歸檔恢復原子性、`janitor.log` 開始有 audit trail。

2. **收斂觀測層：統一 DB 路徑 + `/api/agents` 改走 `platform.sh`** — Why now：這份 retro 的三軸有兩軸得靠我手動繞過 API 才拿得到數字（per-project token 自己重算、agent 執行史從 journalctl 撈）。dashboard 現在回報 0 agent / 0 run，而實際有 8 個 agent 本週跑了 10 次——**一個會安靜地說謊的儀表板比沒有儀表板更糟**。三件事：(a) `sk-exec-lib:751` 的 DB 路徑改成 `dashboard/data/rivendell.db` 並搬移既有 9 筆；(b) `server.py:394-399` 的 `launchctl` 換成 `bin/lib/platform.sh` 的 `svc_*`（adapter 已經寫好了）；(c) `/api/tokens/filtered` 真的吃進 `days`/`start`/`end`。Est. effort：1-2 小時。Expected impact：下一份 retro 可以真的只讀 API。
   - 附帶（同一趟做完，~15 分鐘）：讓 `sk-token-snapshot` 順便持久化 skill usage。否則「沉寂 30 天」這條軸會繼續隨 JSONL 輪替腐爛。

3. **補裝 `tester` + `doctor` 的 systemd unit** — Why now：兩者都在 `agents.conf` 裡宣告，但 `~/.config/systemd/user/` 沒有對應檔案；`reports/test-*.md` 最後一份是 2026-05-05，**每日結構驗證停了 13 週**。`sk maintain` 每晚都印出 `tester ○ unloaded`，只是沒人在讀。Est. effort：20 分鐘（跑 `bin/sk` 的 agent 安裝路徑，順便確認為什麼遷移時漏了這兩個而其他 8 個沒漏）。Expected impact：恢復每日回歸訊號，下次 retro 的「使用度」才有 agent 這一欄的真實資料。

> 刻意不列入 actions：`harvest-2026-08-02.md` 提的三支 Strong skill（`systemd-user-agent` / `portability-sweep` / `llm-batch-classify`）論證完整、已有自己的優先序表，由 harvest 負責追蹤，retro 不重複佔額度。上面三項都是**只有 retro 這個視角才看得到**的東西。

## 對照上週

對照對象是 **W18（2026-05-03）**，不是上週——中間 13 週沒有 retro（見 Theme 3）。

**上週 actions 完成度：1 / 3**

| # | W18 Action | 狀態 | 證據 |
|---|-----------|------|------|
| 1 | 修 `start-web.sh` 的 sentinel file build 偵測 | ✅ **完成** | `dashboard-next/start-web.sh:29` `SENTINEL=".next/.build-complete"`，檔案存在。效果直接反映在本週 watchdog 事件 6 → 0 |
| 2 | `presales-pipeline` README 補「通路媒介客戶」段落 | ❌ **未做** | `skills/*/presales-pipeline/` 底下只有 `SKILL.md`，全目錄無「通路」二字 |
| 3 | 檢查 `knowledge-graph` skill description 對齊度 | ❌ **未做** | SKILL.md 自 2026-03-15 未再修改，仍零觸發（第 140 天） |

**指標變化（W18 → W31）**

| 指標 | W18 | W31 | 方向 |
|------|-----|-----|------|
| Watchdog / dashboard 重啟事件 | 6 次 | **0 次**（另有 1 次移植造成的手動重啟） | ✅ 大幅改善 |
| Agent non-zero exit | 0 個 | 2 個（`janitor` 未解、`maintain` 已自癒） | ⚠️ 退步 |
| Agent 排程覆蓋率 | 13/13 loaded | rivendell 8/10 安裝（缺 tester、doctor）；news_stock + sales 0/6 | ❌ 遷移未完成 |
| Token 最高集中度 | news-stock 35% | mops_dbs **78.1%** | ⚠️ 集中度翻倍（但源自單一長 session） |
| Skill 觸發總數（週） | 17+ 次可辨識 | 2 次 | ⚠️ 部分真實、部分是 telemetry 視窗腐蝕 |
| Audit 結構性缺陷 | 18 | 7（frontmatter）+ symlink/部署/完整性全 OK | ✅ 改善（計數基礎已變，見上） |
| W18 Theme 3（audit 描述錯置） | 首次記錄 | **原樣存在** | ❌ 13 週零進展 |
