# Changelog

Versioning: `MAJOR.MINOR.PATCH`(規則取自 PTI-ARES,fleet 共用慣例)。

- **PATCH**(第 3 碼)— 每次 push(碰 skills/dashboard/bin;`reports/*` 不算)。
- **MINOR**(第 2 碼)— 一個過 gate 的 initiative/Wave 項完成
  (eng-review / QA / office-hours design doc 任一 gate)。
- **MAJOR**(第 1 碼)— 只在產品負責人(Peter)明示時。

本檔是 release notes 的 **single source of truth**,與根目錄 `VERSION` 同步。
cut 一版:bump `VERSION` → 本檔前置一段 → `release: cut X.Y.Z — 主題` commit。

**Granularity rule(承 PTI-ARES 2026-07-01):事無大小都要寫上** —— 每個 shipped
feature/fix 一條 bullet 帶短 hash;不把多個修正捲成一條模糊敘述。進行中的放
`## Unreleased`。

## Unreleased

（空）

## 0.2.2 — tokens 頁誠實化：雙軸吞吐 + 砍幻覺金額 — 2026-07-19

- **fix(tokens): Max 吃到飽用戶的幻覺 $**。舊頁頭條大字是 `$total_cost_usd`
  ($64K),但那是 cache_read × opus 預設價（現役 fable-5 / opus-4-8 根本不在
  價格表→全 fallback opus $15/$75），而 Max 逐 token 實付 $0 → 純虛構。改：
  headline 拆「產出(in+out) / Context 重讀(cache) / 估算花費(API 等值·非實付)」；
  砍掉「每日花費」bar。
- **feat(tokens): context 疊加可視化**。後端 `DailyUsage.cache_tokens` +
  `total_cache_tokens`（read+create）；每日圖改**雙軸並排**（產出左軸·百萬、
  context 右軸·十億——兩者差 ~280× 不能共軸，疊線性軸會壓死產出那條）。
  recharts bar 關 `isAnimationActive`（headless QA 才截得到，rAF 動畫在虛擬
  時間下不觸發→bar 卡高度 0）。

## 0.2.1 — api 死亡螺旋根治 — 2026-07-18

- **fix(api): watchdog death-spiral** — 1GB session 語料冷掃 × 併發疊加 + 每
  agent 一次 launchctl(18s)→ 5s 探針必死 → kickstart 殺 → cache 清空 → 重掃,
  歷史累計 22,474 次重啟。修法:per-file granular JSONL cache(SQLite,
  mtime+size key,老檔一生解析一次)+ launchctl 單次 dump snapshot(5s TTL)+
  探針 5→15s。實測 overview 冷 2.4s/熱 1.4ms、agents 0.69s、tokens 3ms。

## 0.2.0 — 平台月:部署管理 × token 三層 × spine × skeleton — 2026-07-18

> Catch-up cut:0.1.0(6/13)後一個月的主線。當時無 granularity 規則,本段按
> initiative 收攏、每條帶代表 hash;此後恢復逐條記。紅藍隊評估(R1–R7)同日完成,
> 對應 Wave 0–3 見 ROADMAP。

### 部署管理頁(原 Port 對應)
- 當前部署 default + 相關部署 toggle(`31105be`);docker-label 認 owner + 來源
  資料夾 + iCloud 紅旗,解「5432 誰家的」(`76d4023`);改名部署管理(`a712887`)
- 健康維度讀共用 `ops/monitors.toml`(`80f3d6b`);WSL self-host 部署工具
  systemd+git-poll(`8f3e2fa`)+ 可設分支(`0bb5948`)
- `/api/*` 同源 proxy,不再 bake host 進 bundle(`991360d`)
- 系統程序 wild listeners 折疊一列(QA ISSUE-002,`268845d`)

### Token 三層
- 歸因收斂到頂層 repo(不再有 `xxx/apps/web` 碎片,`a88f647`)
- 30 天預設視圖 + `token_project_usage` 永久明細表(34 天回填,`02c8bae`)
- 每日「錢做了什麼」分析 agent(haiku)+ Telegram 日報(`46cb94e`)
- /api/tokens 歷史合併 SQLite(>30 天可視,`74b2bc1` `7a5c331`)

### Fleet spine + skeleton
- 登錄表 `docs/spine-modules.md` 19 模組 + 兩 spine family(`31a7745` `5cd850d`)
- spine skills:auth(`31271a4`)rbac(`be0404c`)schema-sync + logs n=1 defer
  (`69c0ff8`)versioning=enforcement gate(`c11a16e`)ai-vision-extract(`49c4f99`)
- `product-skeleton` repo:脊椎接線 + 出生走查驗證(抓到 .env cwd bug)+ 8 tests
  + CI + GitHub(`8f70421`→`d2cd600`,repo `manibari/product-skeleton`)
- 抽取 roadmap demand-driven 化(`302ad72`)

### 穩定性 / QA
- tester 每日 build 兩度弄壞 live dashboard(7/5 失敗版 / 7/13 成功版同炸)→
  build 隔離 `NEXT_DIST_DIR=.next-tester` 根治(`9291515`)
- FlowView useSearchParams 缺 Suspense 修復(7/5 全站 500 的斷根;仍待獨立 commit,R1b)
- QA 手冊法走查 6 頁:磁碟明細 list(`c2e13b8`)、總覽 skeleton + 60s TTL cache
  4.98s→3ms(`6d154b3`);操作手冊 + 箭頭圖 `docs/manual/`(`5cb3174`)
- 背景 agents 釘 model(harvest/retro→sonnet,防跟 CLI 預設飄,`ad1b0b9`)

### 治理
- port SoT `docs/port-allocation.md`(3=前端 8=後端 5=資料庫 + NN;tukey/Verdandi
  遷 05 區塊,`2b20554`)
- 平台資料地基 ADR(Postgres-now,`910219e`)
- ops 中央監控器 repo(`manibari/ops`:config 驅動 3-check、狀態變更告警、多 host、
  keyed health)+ family-fiscal host-local `/api/health`(branch 待合)

## [0.1.0] - 2026-06-13

### Added

- Established the first explicit Rivendell baseline version.
- Added `docs/ROADMAP.md` as the canonical development roadmap.
- Added backend regression tests for the port map parser and drift semantics.
- Documented release hygiene: version changes belong in `VERSION`, notable
  human-authored changes belong in this changelog, and scheduled report output
  remains owned by agents.

### Changed

- Clarified current operational priorities: launchd agent loading, CI coverage,
  dashboard/API tests, audit report correctness, and generated artifact hygiene.
- CI now runs dashboard frontend checks, backend lint/tests, and skill structure
  validation on pull requests without relying on unavailable PR filename fields.
- `sk-setup-agents` now uses the explicit `launchctl bootstrap gui/$UID` domain,
  with legacy `load` fallback.
- launchd agent PATH now includes `/usr/sbin:/sbin` so dashboard API can run
  system tools such as `lsof`.
- `sk check agents` now reads the same GUI launchd domain used by setup.

### Fixed

- Port map behavior now distinguishes declared compose ports from live listeners
  and untracked local listeners.
- Dashboard production builds now use the documented webpack path by default.
- Cleaned existing dashboard lint blockers so CI lint can pass.
- Cleared objective skill frontmatter warnings for missing `tags`, `version`,
  and `gdrive-to-skills` `imported_at`.
- Restored launchd agent loading: all 16 agents in `agents.conf` now report as
  loaded.
All notable changes to the rivendell platform are recorded here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

**Versioning = ISO week** (one iteration per week, closed at `workflow-retro`).
The `[Unreleased]` section collects changes mid-week; it is promoted to a dated
`## [YYYY-Www]` heading when the iteration closes. Kept aligned with
[ROADMAP.md](ROADMAP.md) by the `doc-drift-sync` skill.

## [Unreleased]

### Added
- `doc-drift-sync` skill (`skills/meta/`) — detects/fixes drift across
  CHANGELOG / ROADMAP / CLAUDE.md / progress and defines the weekly iteration cycle.
- `ROADMAP.md` + `CHANGELOG.md` — version/roadmap discipline for rivendell itself,
  reviewed each iteration at `workflow-retro`.

## [2026-W24] — 2026-06-13

### Added
- chimesflow-design + app-ops-baseline gate skills (`ff8ea85`).

### Fixed
- sk-setup-agents PROJECTS_DIR landmine + ssot-drift cron 11-arg (`8007c6d`).
- `bin/sk` cmd_check_ssot derives project from PROJECT_REL_PATH not label (`389eacb`).

### Added (earlier in W24)
- dashboard Git 衛生 panel — uncommitted/unpushed across ~/code repos (`7523816`).
- learnings: iCloud-detach + agent gotchas, 3 entries (`2181b66`).

---

_Earlier history predates this changelog (待補 if reconstructed from git log)._
