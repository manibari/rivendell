# Skills Library

Personal Claude Code skills library — manage, version control, and deploy custom skills.

## Structure

```
skills/
├── meta/       # Claude Code 自身管理工具 (17)
├── workflow/   # 工作流程與規劃 (31)
├── quality/    # 程式品質、審查、除錯、測試 (7)
├── git/        # Git/GitHub 操作 (2)
├── frontend/   # 前端設計、iOS、測試 (5)
├── backend/    # 後端服務 (13)
└── docs/       # 文件處理與 MCP 建置 (20)
```

## Quick Start

```bash
# Deploy all skills globally
./bin/sk deploy

# Use in any project
cd ~/any-project && claude
/init-project          # Set up project config
/setup-permissions     # Configure permission allowlists
```

## Commands

| Command | Description |
|---------|-------------|
| `./bin/sk deploy` | Symlink all skills → `~/.claude/skills/` + install plist templates → `~/Library/LaunchAgents/` |
| `./bin/sk undeploy` | Remove repo symlinks from `~/.claude/skills/` |
| `./bin/sk create <cat/name>` | Scaffold new skill (e.g. `quality/my-linter`) |
| `./bin/sk import <name>` | Import from SkillsMP via `agent-skills-cli` |
| `./bin/sk import-gh <url>` | Clone skill from GitHub URL |
| `./bin/sk list` | Show all skills grouped by category |
| `./bin/sk check [--verbose]` | Health check: symlinks, reviews, gdrive, frontmatter |
| `./bin/sk run <task>` | Run a task via `sk_exec()` — structured logging + cost tracking (`--resume`, `--context`) |
| `./bin/sk audit` | Generate audit report → `reports/skill-audit-YYYY-MM-DD.md` |
| `./bin/sk permissions [dir]` | Scan project tooling → update `.claude/settings.local.json` |
| `./bin/sk maintain` | Nightly: deploy check + permissions sync + agent health + audit |
| `./bin/sk agent <cmd>` | Manage automated agents: `list`, `start`, `stop`, `status`, `log`, `create` |
| `./bin/sk readme` | Regenerate Skills Catalog in README.md from SKILL.md frontmatter |
| `./bin/sk sync` | Show Google Drive import status for re-import |

## Skills Catalog (97 skills)

### meta/ — Claude Code 管理

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **agent-persona** | 自動 | Generate structured role prompts for headless Claude Code agents (tester |
| **audit-fix** | 自動 | 分析 `sk audit` 報告，自動清理各專案 permission 白名單（刪 one-off、統一格式、移除全域重複） |
| **ci-pipeline** | 自動 | 偵測專案 stack，自動產生 GitHub Actions CI workflow（lint、test、build）+ pre-commit config |
| **deploy** | 自動 | 推薦部署平台，產生部署配置（Dockerfile、fly.toml、vercel.json）+ CD workflow |
| **dev-process-gate** | 自動 | 開發守門：確保 requirement → flow → wireframe → mockup → dev → QA testing 流程不跳步 |
| **doc-drift-sync** | 自動 | Keep a project's living docs aligned when version or state moves — detect and |
| **init-project** | 自動 | 專案缺少 CLAUDE.md / AGENTS.md 時自動初始化，偵測框架自動填入 |
| **knowledge-graph** | `/knowledge-graph` | 三層記憶系統：追蹤人物、公司、專案的持久事實，寫入 JSONL + 摘要 |
| **learnings-promotion-sprint** | 自動 | Periodic cross-project `.learnings/` distillation. Sweeps every project's `. |
| **plan-check-style** | 自動 | 進入 plan mode 做前端任務時，自動掃描並套用 style skills |
| **self-improving-agent** | 自動 + hook | 捕捉學習與錯誤修正，記錄至 .learnings/，提升有價值見解到 CLAUDE.md |
| **session-harvest** | `/session-harvest` | 工作告一段落時，自動審查 session 內容，找出可重複使用的模式並建議建立新 skill |
| **session-wrap** | 自動 | End-of-session cleanup: auto-commit uncommitted changes, archive learnings |
| **setup-permissions** | 自動 | 偵測專案工具鏈，自動設定 permission allowlists，減少手動核准 |
| **skill-creator** | 自動 | 建立、修改、評測 skills，含 eval 和 benchmark 工具 |
| **skill-scout** | `/skill-scout` | 從 GitHub 與社群資源發現、評估、移植 Claude Code skills |
| **sync-readme** | 自動 + hook | Keep README.md sections in sync with code structure across repos |
| **workflow-retro** | 自動 | Weekly observability retrospective for the rivendell skills + agents system. |

### workflow/ — 工作流程與規劃

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **agent-observability** | 自動 | 讓 script-based agent 在 rivendell 可見：exec-lib 執行歷史、progress logging、log discovery 三層整合指南 |
| **app-ops-baseline** | 自動 | Planning-stage gate that injects a standard "ops baseline" feature checklist |
| **autoresearch** | `/autoresearch` 或自動 | Autonomous goal-directed iteration loop for Claude Code agents. |
| **candidate-analysis** | `/candidate-analysis` 或自動 | 面試候選人管理：PDF 履歷解析、GitHub repo 程式品質分析、候選人 profile markdown 產出 |
| **claude-to-telegram** | `/claude-to-im setup` | 設定 Telegram 橋接器遠端控制 Claude Code，支援兩種實作方式 |
| **client-kickoff-docs** | 自動 | 新客戶 kickoff 時（NDA 簽過、首次討論前），讀客戶提供的 homework 檔 → 建立 `scope.md` + `deadline. |
| **context-recovery** | 自動 + hook | Session 壓縮後自動復原工作上下文，使用 Git 狀態與專案 metadata |
| **crm-projection** | `/crm-projection` | Project nx_client + nx_deal data to local markdown files at materials/clients/. |
| **customer-intel** | `/customer-intel` 或自動 | B2B 客戶情蒐：公司名 → WebSearch + Playwright → 結構化報告（概覽、管理層、財務、競爭、痛點、策略建議） |
| **dispatching-parallel-agents** | 自動 | 3+ 個獨立問題時，派 subagent 並行處理 |
| **env-doctor** | 自動 | 為專案產生 `doctor.sh`（或 `doctor. |
| **executing-plans** | 自動 | 分批執行計畫，每批有 review checkpoint |
| **gdrive-to-skills** | `/gdrive-to-skills` | 讀取 Google Drive 文件，分類並自動建立 knowledge skills |
| **headless-agent** | 自動 | 將 Claude Code 作為非互動式 agent 執行，含排程、結構化日誌、auto-commit/push、QA gate、branch workflow、multi-role agents |
| **investment-research** | `/investment-research` 或自動 | 投資研究流程：總經掃描 → 選股池 → Alpha 發現 → 風險評估 → 回測 → 四大報表 → 報告 |
| **jd-writer** | 自動 | Generate structured Job Descriptions (JD / 職缺描述) from organizational context. |
| **keyword-discovery** | 自動 | 自動分析爬蟲未匹配項目，發現新關鍵字候選詞，高信心詞自動升級至 active 列表 |
| **launchd-agent** | 自動 | 建立、設定、除錯 macOS launchd agents（plist 產生、排程、launchctl 生命週期管理） |
| **material-health** | `/material-health` | Health check for the sales materials library — detects missing frontmatter |
| **mockup** | `/mockup` 或自動 | 三階段 UI mockup（ASCII → 靜態 HTML → 互動 HTML），讀取 design system，支援 Figma 匯出 |
| **mops-financial-scraper** | 自動 | 自動化從 MOPS（`mopsov.twse.com. |
| **planning-with-files** | `/planning-with-files` | Manus 風格的檔案式規劃，用 task_plan.md 追蹤進度，支援 session 恢復 |
| **presales-pipeline** | 自動 | 以檔案系統（`01_presales/<client-slug>/`）管理 B2B 售前 pipeline：`new-client. |
| **repro-exam** | 自動 | 依照專案的核心邏輯（如 backtest engine、portfolio strategy）產生一組 deterministic 測驗（input → |
| **requirement** | `/requirement` 或自動 | 定義需求：user story、acceptance criteria、scope boundary |
| **sales-material** | `/sales-material` | Assemble client-specific sales presentations by matching customer intelligence |
| **settings-audit** | 自動 | 審查清理 .claude/settings.local.json — 移除無效 permissions、修正 JSON 語法、偵測一次性指令誤存為永久權限 |
| **subsidy-scraper** | `/subsidy-scraper` | Automated government subsidy scraper — fetches grant listings from Taiwan |
| **tender-scraper** | `/tender-scraper` 或自動 | 自動爬取政府標案（g0v API）、data-driven 關鍵字篩選（keywords.yml + 自動發現）、網路韌性（retry/backoff）、歸檔過期、生成索引、dashboard 可觀測性 |
| **user-flow** | `/user-flow` 或自動 | 用 Mermaid 繪製使用者流程圖，含 happy path 與 error branch |
| **writing-plans** | 自動 | 產出 bite-sized 實作計畫，假設工程師零 codebase context |

### quality/ — 程式品質

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **de-slopify** | 自動 | 移除 AI 生成「廢文」痕跡，讓文本讀起來像人寫的 |
| **github-repo-audit** | 自動 | Audit a GitHub repository for structure quality, documentation coverage |
| **large-file-refactor** | 自動 | Systematically split large single-file components (500+ lines) into modular |
| **protect-secrets** | Hook (PreToolUse) | 攔截讀取/修改 .env、private keys、credentials 等敏感檔案 |
| **qa-auto** | `/qa-auto` | 從 QA 計畫或 diff 自動產生測試程式碼、執行測試、報告覆蓋率缺口 |
| **qa-planner** | `/qa-planner` | 分析程式碼變更產生結構化 QA 計畫：影響分析、測試案例、風險評估 |
| **qa-testing** | 自動 | 跨框架測試指導：pytest / Vitest / Swift Testing 的策略、mock 模式、模板 |

### git/ — Git/GitHub

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **auto-stage** | Hook (PostToolUse) | 檔案編輯/建立後自動 git add，跳過 .env 和 node_modules |
| **repo-rename** | `/repo-rename` | Repo 改名時全系統審計引用（plist、Claude 設定、腳本、兄弟 repo），產出遷移清單並執行 |

### frontend/ — 前端設計、iOS、測試

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **chimesflow-design** | 自動 | HARD GATE loader that anchors all new frontend / UI work to ChimesFlow's design |
| **frontend-design** | 自動 | 設計哲學 — 產出獨特、避免 AI 感的 production-grade UI |
| **ios-integration** | 自動 | iOS 系統整合：App Extensions、Deep Links、Universal Links、App Groups、權限、地圖 |
| **swiftui-patterns** | 自動 | SwiftUI iOS 17+ 架構模式：@Observable、MVVM、strict concurrency、NavigationStack |
| **ui-ux-pro-max** | `/ui-ux-pro-max` 或自動 | UI/UX 資料庫搜尋 — 97 色票、57 字體配對、50+ 風格、25 圖表類型，含 Python CLI |

### backend/ — 後端服務

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **audio-transcription-flow** | 自動 | Implement a complete audio upload → speech-to-text → transcript display |
| **db-migration** | 自動 | 偵測 DB stack，設定 migration 工具（Alembic/Prisma/Drizzle），指導安全 schema 變更 |
| **doc-to-structured-data** | 自動 | 非結構化技術文件（.doc/.pdf 測試計畫、規格書、datasheet）→ 結構化 CSV/JSON，含格式偵測、欄位對映、驗證 |
| **docker-compose-setup** | 自動 | Set up Docker Compose for multi-service projects (Next. |
| **firebase-backend** | 自動 | Firebase 全方位開發：Firestore CRUD/queries、Cloud Functions (1st/2nd gen, TS+Python)、CLI、emulator、Security Rules、Auth、Hosting、GCP 整合 |
| **imap-smtp-integration** | 自動 | IMAP/SMTP Integration - Integrate email reading and sending via IMAP/SMTP into |
| **markdown-file-ssot** | 自動 | Markdown File SSOT - Use Markdown files with YAML frontmatter as a data SSOT. |
| **oauth-token-vault** | 自動 | OAuth Token Vault - Implement OAuth 2. |
| **rbac-permissions** | 自動 | Design and implement Role-Based Access Control (RBAC) for full-stack apps. |
| **sqlite-to-postgres** | 自動 | SQLite → PostgreSQL/Supabase 遷移指南：語法差異、schema 轉換、資料遷移、驗證 |
| **tunnel-proxy-deploy** | 自動 | Deploy FastAPI + Next.js behind Cloudflare Tunnel. |
| **tw-company-lookup** | `/tw-company-lookup` 或自動 | 用 Playwright 查詢經濟部 findbiz.nat.gov.tw：公司基本資料、董監事、工廠、歷史變更 |
| **vector-search-setup** | 自動 | Set up a vector search knowledge base in a FastAPI project from scratch. |

### docs/ — 文件處理與 MCP 建置

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **chart-design** | 自動 | Chart / table / diagram sub-workflow shared by every report + deck skill. |
| **discovery-interview** | 自動 | Run a structured Discovery interview with a potential consulting client to find |
| **doc-coauthoring** | `/doc-coauthoring` 或自動 | Structured workflow for collaboratively co-authoring documentation through |
| **excalidraw-diagram** | 自動 | Create Excalidraw diagram JSON files that make visual arguments |
| **gdoc-report-builder** | 自動 | Build structured reports in Google Docs/Slides via MCP tools — batch table |
| **internal-comms** | `/internal-comms` 或自動 | Templates and formats for ongoing organizational communications during and |
| **iot-factory-report** | 自動 | Analyze factory IoT/SCADA time-series data (CSV/Excel) and produce visual |
| **mcp-builder** | 自動 | 建立 MCP server 的指南（Python FastMCP / Node MCP SDK） |
| **mermaid-diagram** | `/mermaid-diagram` 或自動 | Generate Mermaid `.mmd` files that argue visually (flowcharts, sequence, state |
| **metadata-workshop** | 自動 | Run a structured Metadata Workshop with a consulting client to convert their |
| **office-docx** | 自動 | Word (.docx) 建立、編輯、分析，支援追蹤修訂與註解 |
| **office-pdf** | 自動 | PDF 操作：文字/表格擷取、建立、合併/分割、表單填寫 |
| **office-pptx** | 自動 | PowerPoint (.pptx) 建立、編輯、分析，支援版面配置與講者備註 |
| **office-xlsx** | 自動 | 試算表 (.xlsx/.csv) 建立、編輯、分析，支援公式與資料視覺化 |
| **pitch-deck** | 自動 | Create professional business pitch decks and investor presentations with |
| **rfq-writer** | 自動 | Generate Request for Quotation (RFQ / 報價單) for consulting projects. |
| **slide-office-hours** | 自動 | Red-team review for a B2B presales deck storyline (storyline. |
| **slide-template-extractor** | 自動 | Extract design system from an existing PPTX or Google Slides deck and produce a |
| **slide-workflow** | 自動 | Step-by-step presentation creation workflow with confirmation gates. |
| **sow-writer** | 自動 | Generate professional Taiwan-format Statement of Work (工作說明書 / SOW) for |
| **telegram-bot** | 自動 | grammY / python-telegram-bot 機器人開發指南：架構、Bot API、部署模式 |


## Built-in Claude Code Skills (not in this repo)

These ship compiled into the `claude` binary itself — invisible to `./bin/sk` and the catalog above, but available everywhere Claude Code runs. **Onboard new colleagues with these — easy to miss.**

### Skills (registered via `T$({name:...})`)

| Skill | 用途 |
|-------|------|
| `update-config` | 改 `.claude/settings.json` — hooks / permissions / env vars。**任何「以後每次 X 都自動 Y」的需求都靠這個**（memory 不會 enforce 自動行為，hook 才會） |
| `fewer-permission-prompts` | 掃 transcript，把常用 read-only command 加進 allowlist，少點擊確認 |
| `simplify` | Pre-commit 自動 review changed code |
| `loop` | 把 prompt / slash 命令設成定時重複（如「每 5 分鐘 /foo」） |
| `schedule` | Cron 排程遠端 agent 跑 routine（rivendell 的 schedule skill 是同名 wrapper） |
| `keybindings-help` | 自訂鍵盤快捷鍵（`~/.claude/keybindings.json`） |
| `claude-api` | Anthropic SDK / Claude API 開發助手，含 prompt caching |
| `batch` | 大規模平行改動：分派 5-30 個 worktree agent，各自開 PR |
| `claude-in-chrome` | 用 Chrome 瀏覽器操作網頁（不同於 Playwright MCP） |
| `debug` | 開啟 debug logging 診斷 issue |
| `dream` | 描述未公開（可能 feature-gated） |

### Slash commands (registered as builtin prompts)

| Command | 用途 |
|---------|------|
| `/init` | 為現有 codebase 生成 CLAUDE.md |
| `/init-verifiers` | 自動建立 verifier skill — 跟 rivendell 的 QA pipeline 互補 |
| `/insights` | 分析你的 Claude Code session，產 usage report |
| `/review` | Review 一個 PR |
| `/commit` | 快速 git commit |

### Feature gating

不是每個內建 skill 都會出現在每個 session 的 available-skills 列表。如 `batch` / `claude-in-chrome` / `debug` / `dream` / `/insights` / `/init-verifiers` / `/commit` 在某些設定下會被隱藏（feature flag / 版本旗標 / env var）。

### Self-discovery

```bash
# Skills (T$ registration)
strings $(which claude) | grep -oE 'T\$\(\{name:"[a-z][a-z0-9-]+"' | sort -u

# Slash commands
strings $(which claude) | grep -oE '\{type:"prompt",name:"[a-z][a-z0-9-]+"[^}]+source:"builtin"' \
  | grep -oE 'name:"[^"]+"' | sort -u
```

升級 Claude Code 後再跑一次，可看出新增的內建。


## How Deploy Works

Each skill directory gets symlinked individually into `~/.claude/skills/`. Edits to skill files take effect immediately — re-deploy only when adding new skills.

Deploy also installs `com.*.plist` templates into `~/Library/LaunchAgents/`, replacing `REPO_PATH` with the actual repo path.

## System Architecture

rivendell runs three classes of long-lived processes, all managed by macOS `launchd`:

```
┌─ Dashboard (always-on) ─────────────────────────┐
│  com.sk.dashboard.api     FastAPI :8000         │
│  com.sk.dashboard.web     Next.js :3000         │
│  com.sk.dashboard.watchdog  HTTP health probe   │  ← restarts hung API/web
└─────────────────────────────────────────────────┘
┌─ Scheduled agents (cron-like) ──────────────────┐
│  rivendell.harvest    every 8h  → reports/      │
│  rivendell.maintain   daily 22:00               │
│  rivendell.tester     daily 6:00                │
│  rivendell.doctor     daily 7:00                │
│  news_stock.*, sales.*  (per-project schedules) │
└─────────────────────────────────────────────────┘
```

**Single source of truth:** `agents/agents.conf` — pipe-delimited list of every agent.
`bin/sk-setup-agents` reads it, generates one plist per row in `~/Library/LaunchAgents/`,
and `launchctl load`s them. Re-run after editing the conf.

**Agent SSOT vs project metadata** (two separate vaults, don't conflate):
- **`agents/agents.conf`** is authoritative for: agent label, schedule, script path, log directory, project binding (via label convention `com.sk.agent.<project>.<name>`).
- **`~/.claude/projects.json`** is authoritative for: project metadata — repo path, description, mission brief. The dashboard uses it to *enrich* agent rows with the project's working directory, but it does NOT define what agents exist.
- An agent in `projects.json`'s `agents` list but missing from `agents.conf` is **drift**, not a working agent. Run `./bin/sk check ssot` (when implemented) to surface this.

**Why a custom runner (`sk-agent-run`)?** macOS TCC blocks `launchd`-spawned processes
from reading `~/Documents/`. The compiled C wrapper runs `chdir()` before `execvp()`,
which TCC permits. All `launchd` stdout/stderr go to `~/Library/Logs/sk-agent/` to
avoid the same restriction.

**Schedule types** (column 4 of `agents.conf`):
| Type | Value | Meaning |
|------|-------|---------|
| `interval` | seconds | Run every N seconds (e.g. `60`, `28800`) |
| `calendar` | `H:MM` or `W:H:MM` | Daily at time, or weekly on weekday W (0=Sun) |
| `calendar_multi` | `W1:H:MM,W2:H:MM` | Multiple weekly slots |
| `keepalive` | `-` | Run forever, restart if process exits |

### Operating the dashboard

```bash
# Status
launchctl list | grep com.sk.dashboard

# Manual restart (kills + relaunches via launchd)
launchctl kickstart -k gui/$UID/com.sk.dashboard.api
launchctl kickstart -k gui/$UID/com.sk.dashboard.web

# Logs
tail -f ~/Library/Logs/sk-agent/com.sk.dashboard.api-stderr.log
tail -f reports/api-stderr.log    # also captured here
tail -f reports/watchdog.log       # only written when health checks fail
```

The dashboard URLs are http://localhost:8000 (API) and http://localhost:3000 (web).
`start-api.sh` / `start-web.sh` handle venv + deps; you do not invoke them directly.

### How the watchdog works

`bin/sk-watchdog` runs every 60s (via `com.sk.dashboard.watchdog`) and HTTP-probes
both services. `launchd`'s `KeepAlive` only catches process death — it cannot detect
a hung process whose port is still listening. The watchdog covers that gap:

- Failure threshold: **3 consecutive failures** (~3 min) before restart
- After restart: **60s grace period** before re-checking that service
- State: `reports/.watchdog-state` (consecutive-failure counter, last-restart timestamp)
- Log: `reports/watchdog.log` — written only on FAIL / RESTART / RECOVER events

Tune by editing `THRESHOLD` / `GRACE_SECONDS` at the top of `bin/sk-watchdog`.

### Adding or changing an agent

1. Edit `agents/agents.conf` (add a row, comment out, or change schedule)
2. Run `./bin/sk-setup-agents` — regenerates plists and re-loads them all
3. Verify: `launchctl list | grep com.sk.<your-label>`

To temporarily disable an agent, comment its row in `agents.conf` and re-run setup,
**then** delete the stale plist from `~/Library/LaunchAgents/` (the script does not
clean up rows that no longer exist).

### Troubleshooting

| Symptom | Where to look |
|---------|---------------|
| Dashboard returns nothing | `tail -f reports/api-stderr.log` and `~/Library/Logs/sk-agent/com.sk.dashboard.api-stderr.log` |
| Watchdog restarting every 3 min | `cat reports/watchdog.log` — find the failing endpoint, then read the API stderr log |
| Agent didn't run on schedule | `launchctl list \| grep com.sk.<label>` — last column is exit code; `0` = success, `-` = never ran |
| Permission errors writing to `reports/` | macOS TCC — re-run `./bin/sk-setup-agents` to recompile `sk-agent-run` |
| Audit / health questions | `./bin/sk audit` (writes `reports/skill-audit-YYYY-MM-DD.md`) |

## Using Skills in Other Projects

Skills deploy 後是**全域生效**的，不需要在每個專案裡做任何設定。

```bash
# Deploy once
./bin/sk deploy

# Use anywhere — restart Claude Code to pick up new skills
cd ~/any-project && claude
```

| 情境 | 做法 |
|------|------|
| 新增 skill 後看不到 | `./bin/sk deploy` 然後重啟 Claude Code |
| 修改現有 skill | 直接編輯 SKILL.md，symlink 立即生效 |
| 確認部署狀態 | `./bin/sk list` |
| 移除所有 skills | `./bin/sk undeploy` |

## Prerequisites

- **Claude Code** — install from Anthropic first; rivendell runs on top
- **Python 3** — for ui-ux-pro-max search CLI + dashboard api
- **Node + npm** — for dashboard web frontend
- **`agent-skills-cli`** (optional) — for importing from SkillsMP: `npm install -g agent-skills-cli`

For first-time install on a new machine or onboarding a colleague: see **[`docs/SETUP.md`](docs/SETUP.md)** — full runbook + gotchas (turbopack, `.next/` cache, IPv4/IPv6 conflicts).
