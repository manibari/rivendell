---
date: 2026-04-29
session_focus: rivendell self-maintenance workshop
note: scheduled cron harvest already wrote harvest-2026-04-29.md covering other projects; this is a manual harvest of THIS session's rivendell work, complementary not overlapping.
source: session-harvest
---

# Session Harvest — 2026-04-29 (rivendell session)

## Session 概要

- **日期**: 2026-04-29
- **主要工作**: rivendell 自我維護系統的一次大幅補完 — 建 watchdog（兩階段 recovery）、建 workflow-retro skill 並 dogfood 一次、新增 4 個 maintenance agent（symlink-fix、workflow-retro-cron、janitor、watchdog 升級）、port 兩個 anthropic skill（doc-coauthoring、internal-comms）、評估 1 個哲學文章（agent-fungibility 不採納）。
- **涉及技術**: bash + launchd + curl + git + Claude Code skills system + Anthropic skills 生態系

## 觀察到的反覆模式

| # | 模式 | 出現次數 | 說明 |
|---|------|---------|------|
| 1 | **新增 cron-style agent** | 4x | watchdog → symlink-fix → workflow-retro-cron → janitor。每次同一套 ritual：寫 bash → chmod +x → 加 agents.conf → 跑 sk-setup-agents → `launchctl list` 驗證 |
| 2 | **Idempotent cron-script 範式** | 5x | 全部 cron 都長同樣的形：`set -euo pipefail` + `REPO_DIR=$(cd .. && pwd)` + state file 在 reports/ + healthy 時靜默不寫 log + 重跑無副作用 + source sk-exec-lib |
| 3 | **Port external skill** | 2x | doc-coauthoring + internal-comms。同套：clone source → read 完整 SKILL.md → 對照現有 89 skills 找 gap → 改 frontmatter 成 rivendell 慣例（加 TRIGGER / DO NOT TRIGGER）→ 移除平台 refs → 拷貝 examples/ → 加 source attribution → sk deploy → 驗證 symlink |
| 4 | **Build-then-iterate** | 3x | watchdog v1 → 真實 80min outage 暴露盲點 → v2 加 deeper recovery；symlink-fix v1 跳過 non-symlink → 發現 11 個是 stale copy → v2 加 diff-rq 安全替換；start-web.sh BUILD_ID 偵測 → 半損 build bug → 改 sentinel 檔 |
| 5 | **Diff-before-replace 安全模式** | 1x | 但是 1 次出現的「real dir → symlink」遷移，使用 `diff -rq` 確認 byte-identical 才 clobber。是個珍貴的 cautious migration pattern |

## Skill 候選清單

### 🟡 Moderate: `agent-add`（不獨立建立，建議併入 launchd-agent）

- **用途**: rivendell 新增一個 cron-style maintenance agent 的 5 步 ritual checklist
- **觸發時機**: user 說「建一個 daily/weekly 跑 X 的 agent」「加一條到 agents.conf」
- **涵蓋步驟**:
  1. `bin/sk-<name>` bash 腳本（套用既有 cron-script 範式）
  2. `chmod +x`
  3. 在 `agents/agents.conf` 加一行
  4. 跑 `./bin/sk-setup-agents`
  5. `launchctl list | grep com.sk.<name>` 驗證
- **分類建議**: 不適合獨立成 skill — **太 project-specific（依賴 agents.conf 跟 sk-setup-agents 這個 rivendell 專屬工具）**。
- **建議**: 以 **enhancement** 的形式加進現有 `launchd-agent` skill，當作「rivendell-flavored quick-start」section，1 段約 30 行 markdown。

### 🟡 Moderate: `skill-scout` references/port-checklist.md 補充

- **用途**: 把這 session 兩次 port 累積的「frontmatter mapping table」（anthropic 格式 → rivendell 慣例）跟「平台 refs 移除清單」（Anthropic / OpenClaw / Clawdbot 字眼處理）固化為 reference doc
- **觸發時機**: 已被 `skill-scout` Phase 3 (Port) 涵蓋；補充的是具體 mapping table
- **分類建議**: 不獨立成 skill — 加進 `skills/meta/skill-scout/references/port-checklist.md`，讓 skill-scout 在 port 階段直接 Read 這個 reference
- **內容**: anthropic 的 `description` 單段 → rivendell 多段 frontmatter（含 TRIGGER / DO NOT TRIGGER / when_to_use / version / tags）；examples/ 用 cp 而非 Edit 不會被 auto-stage hook 抓到，需手動 git add；source attribution HTML 註解格式

### 🟡 Moderate: cron-script 範式段落 → 加進 headless-agent 或 launchd-agent

- **用途**: 把這 session 5 個 cron 全部使用的「shape」codify
- **要點**:
  - `set -euo pipefail` + grep/cut pipeline 用 `{ ...; } || true` 包起避免 pipefail+set-e 致命退出
  - state file 放 `reports/.<name>-state`（runtime, gitignore）
  - log file 放 `reports/<name>.log`，**healthy 時不寫**（讓異常自然浮現）
  - REPO_DIR 用 `$(cd "$(dirname "$0")/.." && pwd)` 規避 launchd cwd 不可預期
  - source `bin/sk-exec-lib` 接 dashboard 觀測
  - exit 0 always（maintenance 腳本，不是 health check）
- **分類建議**: 加進 `headless-agent` skill 的 references/，或 `launchd-agent` 的 reference，不獨立成 skill

### 🔴 Weak: `safe-symlink-migration`

- **原因**: 模式只出現 1 次（11 個 stale dir → symlink）；雖然 `diff -rq` 安全替換是好觀念，但 30 行 bash 不值得獨立 skill。
- **替代**: 已 log 到 `.learnings/LEARNINGS.md` 2026-04-28 條目（pattern: diff before replace when migrating copies to symlinks）。

### 🔴 Weak: `dogfood-validation` / `build-then-iterate`

- **原因**: 這是 **設計哲學**（「建好新 skill 立刻跑一次驗證」），太 meta，不是工作流。
- **替代**: 寫進 `skill-creator` reference 即可（已隱含於它的 eval 流程）。

### 🔴 Weak: `dashboard-telemetry-reader`

- **原因**: 讀 rivendell `/api/skills/usage`、`/api/tokens`、`/api/agents/{label}/runs` 的模式，但已內嵌於 `workflow-retro`，沒必要獨立。

## 跨 session 觀察

跟 `harvest-2026-04-29.md`（同日 cron 版）的 candidates 對照：
- cron 版抓到「repo-cold-start」（拿到陌生 repo 在本地跑起來）— 跟本 session 完全不重疊。代表自動排程的 harvest 跟手動 session-targeted harvest 互補。
- session-harvest 自身的盲點（04-26 報告自己提的「連續多日只看到既有 skill 排程觸發」）在這次手動 harvest 中被解：手動觸發看的是「有問題要解」的 session，不是「排程跑」的 session。

## 建議行動

**不新增任何獨立 skill**。改用 enhancement：

1. **更新 `skills/meta/skill-scout/`**：加 `references/port-checklist.md`，把這 session 兩次 port 累積的 frontmatter mapping、平台 ref 清理、source attribution 等固化成 100-150 行的 reference。下次 skill-scout port 流程時 Read 這檔減少 ad-hoc 思考。
2. **更新 `skills/workflow/launchd-agent/` 或 `skills/workflow/headless-agent/`**：加 cron-script 範式段落（5 次反覆出現的 shape）。
3. **不採納** `agent-add` 獨立 skill — 太 project-specific。

如果決定執行 enhancement #1 跟 #2，可以用 `/skill-creator` 的「modify existing skill」模式做。

## 不採納的候選（已被既有 skill / .learnings 覆蓋）

| 觀察 | 既有覆蓋 |
|------|---------|
| `agent-add` 5 步 ritual | 部分被 `launchd-agent` 覆蓋；建議 enhance 而非新建 |
| Port skill 流程 | 被 `skill-scout` 覆蓋；補 references/ 即可 |
| Cron-script 範式 | 部分被 `headless-agent` 覆蓋；補一段即可 |
| diff-before-replace 模式 | 已記錄至 `.learnings/LEARNINGS.md` 2026-04-28 |
| Half-built `.next` 偵測 | 已記錄至 `.learnings/LEARNINGS.md` 2026-04-27 |
| KeepAlive 不抓 hung process | 已記錄至 `.learnings/LEARNINGS.md` 2026-04-26 |
