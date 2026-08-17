# Session Harvest Supplement — 2026-05-14

> Manual harvest of an interactive session (rivendell). Companion to
> `harvest-2026-05-14.md`, which the headless harvest agent produced earlier
> today for 5 other sessions but missed this one (JSONL not yet flushed
> at agent fire time).

## Session 概要

- **日期**: 2026-05-14
- **專案**: rivendell
- **主要工作**:
  1. Dashboard 啟動失敗除錯：venv shebang 過時 → 重建；前端「載入中」卡住 → 根因 launchd `com.sk.dashboard.web` respawn 與手動 build 競態 → Turbopack runtime chunk 路徑損毀
  2. `.learnings/` 跨專案知識碎片化討論 → promotion sprint：掃 11 個專案 / 125 entries → 分類 → 14 條 generic 規則寫入 `~/.claude/CLAUDE.md`、6 條 platform-meta 寫入 `rivendell/.claude/CLAUDE.md`
  3. 開 `~/.claude/learnings/` global vault；改 `activator.sh` hook 加 routing 提示；`self-improving-agent` SKILL.md v1.0 → v2.0；8 個專案 LEARNINGS.md 加 promotion-sprint header note
- **涉及技術**: macOS launchd / launchctl, Next.js 16 / Turbopack, FastAPI venv, Anthropic CLAUDE.md auto-load mechanism, Skill 系統

## Skill 候選清單

### 🟢 Strong: `learnings-promotion-sprint`

- **用途**: 定期（每月或 global vault 條目過多時）做一次跨專案 `.learnings/` 的 distillation —
  掃所有 `~/Documents/Projects/*/.learnings/` → 分類為 generic / platform-meta /
  project-specific / drop → 將 generic 條目濃縮成 dense 一行規則寫入 `~/.claude/CLAUDE.md`、
  platform-meta 寫入該平台 repo 的 CLAUDE.md → 在被 promote 的原始 LEARNINGS.md 加
  header note 標記 → 留下 classification 報告供未來查核
- **觸發時機**:
  - 使用者說「整理 learnings」、「learnings 太多」、「跨專案整理」、「promotion sprint」
  - `~/.claude/learnings/LEARNINGS.md` 條目超過 ~30
  - `.learnings/` 累積條目跨多個專案 ≥ 80 條
  - workflow-retro 標出「相同 theme 在多個專案 .learnings/ 重複」
- **涵蓋步驟**:
  1. `find ~/Documents/Projects -maxdepth 3 -type d -name .learnings` 統計 size + entry 數
  2. dump 所有 entries 到 `/tmp/learnings-sweep/all.txt`
  3. 委派 general-purpose agent 做分類（避免主 context 爆掉）
  4. agent 產出 `classified.md`：4 buckets + 每條 proposed rule
  5. 把 generic 規則 distilled 後寫入 `~/.claude/CLAUDE.md`「Engineering Gotchas」section
  6. 把 platform-meta 寫入 `<repo>/.claude/CLAUDE.md`
  7. 每個受影響專案的 LEARNINGS.md 加 promotion header note
  8. 將 `classified.md` 存入 `reports/learnings-promotion-sprint-YYYY-MM-DD.md` 留檔
- **分類建議**: `meta/`
- **來源**: 本 session 直接執行的工作流程（11 projects / 125 entries / 14 promoted rules）
- **現有相似**:
  - `self-improving-agent` v2.0：只負責**寫**（單筆）+ 在 SKILL.md 內提到 promotion sprint
    應該每月跑，但沒提供工作流。本 skill 是把那段執行細節 codify。
  - `workflow-retro`：讀 rivendell 一家的 `.learnings/`，看 theme repetition；本 skill
    是跨所有專案的 distillation，scope 不同。
  - `gstack-retro`：讀 git 歷史；無關。
- **預估 SKILL.md 大小**: ~150 行（含分類 prompt template、CLAUDE.md 插入位置範例、
  header note 模板）

### 🟡 Moderate: `launchd-service-safe-restart`

- **用途**: 安全重啟由 launchd 管理的服務 —
  `launchctl list | grep <label>` 確認 ownership → `launchctl bootout gui/$(id -u) <plist>`
  停止 respawn → 修改 on-disk state（rebuild、move stale dir 等）→
  `launchctl bootstrap gui/$(id -u) <plist>` 重新拉起 → tail
  `~/Library/Logs/sk-agent/<label>-stderr.log` 驗證
- **觸發時機**:
  - 服務行為異常但 `kill` 沒用（被 launchd respawn）
  - 需要修改 launchd 管理的服務的 on-disk artifacts（`.next/`, venv, 設定檔等）
  - 使用者說「重啟 dashboard」「重啟 launchd 服務」
- **涵蓋步驟**: 同上（4 步 + 驗證）
- **分類建議**: `infra/` 或 `gstack/` (gstack-careful 系列)
- **來源**: 本 session 第一次「修好」dashboard 後使用者說「現在還是沒跑出來椰」，
  根因就是沒 bootout 直接 kill + build → 競態。已寫入 global CLAUDE.md 與
  rivendell CLAUDE.md。
- **現有相似**: `launchd-agent` skill 已涵蓋 create/debug/manage，但**沒有專門
  describing the safe-restart sequence**。建議**enhance `launchd-agent`** 加一個
  「Safe Restart Sequence」section，而非新建 skill。
- **不獨立成 skill 的理由**: 4 步、規則性強，CLAUDE.md 一條 rule 就夠。
  enhance 既有 skill 即可。

### 🔴 Weak: `next-prod-build-recovery`

- **用途**: 偵測並修復 Next.js prod build 損毀（chunks 404, Turbopack runtime
  ENOENT）
- **原因不建議獨立 skill**:
  - 太特定（只適用 Next 16 + Turbopack）
  - 已被 global CLAUDE.md「`.next/` 是 atomic」規則覆蓋
  - 真的遇到時，invocation pattern 已經是「跟著 CLAUDE.md rule 走」

### 🔴 Weak: `stale-venv-detector`

- **用途**: 偵測 Python venv 的 shebang 指向不存在的路徑（專案搬家後常見），
  搬 venv 重建
- **原因不建議**: 單一指令解決（檢查 shebang + recreate），不需要 skill。
  CLAUDE.md 可加一條提醒。

## 觀察（不一定要 skill）

### 兩次使用者更正模式

1. 第一次 "fix" dashboard 後說「現在還是沒跑出來椰 / 畫面的 css 壞了」
   → 根因：我宣稱完成沒驗證實際狀態，沒檢查 launchd 是否在 respawn
   → 已記錄為 correction 到 `rivendell/.learnings/LEARNINGS.md`
   → 已 promote 為 global CLAUDE.md rule（launchd safe restart）

2. 「我的意思是，所有不同專案下的 learnings」
   → 我預設只看 rivendell vault，沒檢查跨專案 scope
   → 教訓：使用者問評估性問題（"can you read all of this?"）時，
   先確認 scope 是否跨所有專案
   → 太對話模式，不適合單獨 skill；可考慮在 self-improving-agent 提醒「跨專案
   scope check」

### 工具委派模式

本 session 用 `general-purpose` Agent 處理 125 entries 分類（避免主 context 爆）。
這個「重複性大量 markdown 分類 → 委派 → 接結果」的模式在
`dispatching-parallel-agents` skill 內應已涵蓋。

## 建議行動

1. **建立 `learnings-promotion-sprint` skill**（Strong 候選，本 session 的主要產出
   值得 codify）
2. **enhance `launchd-agent` skill** 加 Safe Restart Sequence section
3. （可選）將 self-improving-agent 與 learnings-promotion-sprint 在 SKILL.md
   裡互相 cross-link，clearly state 兩者邊界（單筆 write vs. 定期 distillation）

## 與工作中既有條目交叉

- `~/.claude/CLAUDE.md` 今天剛擴充 Engineering Gotchas section (14 條)
- `~/Documents/Projects/rivendell/.claude/CLAUDE.md` 今天剛擴充 Rivendell Operations
  section (6 條)
- `~/.claude/learnings/{README,LEARNINGS,ERRORS}.md` + `archive/` 今天剛建立
- `~/.claude/skills/self-improving-agent/SKILL.md` v2.0 + `scripts/activator.sh` 今天剛改

下次 promotion sprint 預估觸發時機：~/.claude/learnings/LEARNINGS.md 累積 30 條或
2026-06-13 前後（依累積速度）。
