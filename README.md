# Skills Library

Personal Claude Code and Codex skills library — manage, version control, and deploy custom skills.

## Structure

```
skills/
├── platform/   # platform 循環：rivendell 自我改善（harvest/retro/skill 產線）(12)
├── agents/     # 自動化 Agent：排程、觀測、persona (5)
├── planning/   # 需求與規劃：requirement → user-flow → mockup → plans (7)
├── workflow/   # dev 循環工具與 Session 維運 (15)
├── qa/         # QA 與驗收：測試、旅程、資料流稽核 (5)
├── quality/    # 程式品質、審查、文字打磨 (5)
├── git/        # Git/GitHub 操作 (4)
├── frontend/   # 前端設計、iOS、測試 (5)
├── backend/    # 後端服務 (26)
├── sales/      # sales 循環：情蒐 → 提案 → 素材健檢 → CRM 投影 (8)
├── gov/        # gov 循環：標案/補助 sourcing → RFQ/計畫書 (4)
├── invest/     # invest 循環：MOPS 抓取 → 投資研究 (2)
├── hr/         # hr 循環：JD、履歷分析 (2)
├── knowledge/  # knowledge 循環：影音抓讀 → 知識庫 (6 + _shared)
└── docs/       # 文件處理與簡報 (18)
```

## Quick Start

```bash
# Deploy all skills globally for Claude Code and Codex
./bin/sk deploy

# Use in any project
cd ~/any-project && claude
/init-project          # Set up project config
/setup-permissions     # Configure permission allowlists
```

## Commands

| Command | Description |
|---------|-------------|
| `./bin/sk deploy` | Symlink all skills → `~/.claude/skills/` and `${CODEX_HOME:-~/.codex}/skills/` + install plist templates → `~/Library/LaunchAgents/` |
| `./bin/sk undeploy` | Remove repo symlinks from Claude Code and Codex skill directories |
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
| `./bin/sk reboot [--check]` | Reboot so every service returns without a manual FileVault unlock (`fdesetup authrestart`); `--check` = pre-flight report only |

## Roadmap And Releases

| File | Purpose |
|------|---------|
| `VERSION` | Current human-managed Rivendell baseline version |
| `CHANGELOG.md` | Notable human-authored changes by version/date |
| `docs/ROADMAP.md` | Development priorities and release checklist |

Release changes should update `VERSION` and `CHANGELOG.md` together. Generated
`reports/*` remain owned by scheduled agents and should not be manually edited
as release notes.

## Skills Catalog (124 skills)

> 依角色看（我是誰、事情走到哪一步、該叫誰，每個角色一套 PDCA）→ [docs/skills-by-role.md](docs/skills-by-role.md)。
> 下面的目錄照循環 / 資料夾分，是 skill 實體的所在；角色頁是使用者視角，同一支 skill 可出現在多個角色。

### platform/ — 平台自我改善

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **audit-fix** | 自動 | 分析 `sk audit` 報告，自動清理各專案 permission 白名單（刪 one-off、統一格式、移除全域重複） |
| **doc-drift-sync** | 自動 | Keep a project's living docs aligned when version or state moves — detect and |
| **learnings-promotion-sprint** | 自動 | Periodic cross-project `.learnings/` distillation. Sweeps every project's `. |
| **self-improving-agent** | 自動 + hook | 捕捉學習與錯誤修正，記錄至 .learnings/，提升有價值見解到 CLAUDE.md |
| **session-harvest** | `/session-harvest` | 工作告一段落時，自動審查 session 內容，找出可重複使用的模式並建議建立新 skill |
| **session-wrap** | 自動 | End-of-session cleanup: auto-commit uncommitted changes, archive learnings |
| **skill-apply** | `/skill-apply` 或自動 | Turn a skill you have imported but not installed into a review of your own |
| **skill-creator** | 自動 | 建立、修改、評測 skills，含 eval 和 benchmark 工具 |
| **skill-scout** | `/skill-scout` | 從 GitHub 與社群資源發現、評估、移植 Claude Code skills |
| **sync-readme** | 自動 + hook | Keep README.md sections in sync with code structure across repos |
| **workflow-retro** | 自動 | Weekly observability retrospective for the rivendell skills + agents system. |
| **writing-great-skills** | `/writing-great-skills` | Reference for writing and editing skills well — the vocabulary and principles |

### agents/ — 自動化 Agent（排程、觀測、persona）

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **agent-dispatch** | 自動 | Use multiple Claude agents to investigate and fix independent problems |
| **agent-headless** | `/agent-headless` | Pattern for running Claude Code as an automated |
| **agent-launchd** | 自動 | Create / debug / manage macOS launchd LaunchAgents — plist generation |
| **agent-observability** | 自動 | Make any script-based agent visible in rivendell: execution history |
| **agent-persona** | 自動 | Generate structured role prompts for headless Claude Code agents (tester |

### planning/ — 需求與規劃（requirement → user-flow → mockup → plans）

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **app-ops-baseline** | 自動 | Planning-stage gate that injects a standard "ops baseline" feature checklist |
| **executing-plans** | 自動 | Execute detailed plans in batches with review checkpoints |
| **mockup** | `/mockup` 或自動 | Create UI mockups at three fidelity levels (ASCII → static HTML → interactive |
| **planning-with-files** | 自動 | Manus-style file-based planning with task_plan.md, findings.md, and progress.md |
| **requirement** | `/requirement` 或自動 | Define structured requirements, user stories |
| **user-flow** | `/user-flow` 或自動 | 使用者旅程圖（畫面切換、happy path / 錯誤分支）；主角是使用者不是系統，泛用「畫流程圖」走 chart-design |
| **writing-plans** | 自動 | Create detailed implementation plans with bite-sized tasks for engineers with |

### workflow/ — 工作流程與 Session 維運

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **autoresearch** | `/autoresearch` 或自動 | Autonomous goal-directed iteration loop for Claude Code agents. |
| **ci-pipeline** | 自動 | 偵測專案 stack，自動產生 GitHub Actions CI workflow（lint、test、build）+ pre-commit config |
| **claude-to-telegram** | `/claude-to-im setup` | 設定 Telegram 橋接器遠端控制 Claude Code，支援兩種實作方式 |
| **context-journal** | `/context-journal` + hook | 每回合自動追加工作日誌到磁碟，讓 /compact 無損：操作/決策紀錄存在 context 之外、compact 後自動注回、context 超過門檻自動提醒壓縮 |
| **context-recovery** | 自動 + hook | Session 壓縮後自動復原工作上下文，使用 Git 狀態與專案 metadata |
| **deploy** | 自動 | 推薦部署平台，產生部署配置（Dockerfile、fly.toml、vercel.json）+ CD workflow |
| **dev-process-gate** | 自動 | 開發守門：確保 requirement → flow → wireframe → mockup → dev → QA testing 流程不跳步 |
| **env-doctor** | 自動 | 為專案產生 `doctor.sh`（或 `doctor. |
| **gdrive-to-skills** | `/gdrive-to-skills` | 讀取 Google Drive 文件，分類並自動建立 knowledge skills |
| **init-project** | 自動 | 專案缺少 CLAUDE.md / AGENTS.md 時自動初始化，偵測框架自動填入 |
| **plan-check-style** | 自動 | 進入 plan mode 做前端任務時，自動掃描並套用 style skills |
| **repro-exam** | 自動 | 依照專案的核心邏輯（如 backtest engine、portfolio strategy）產生一組 deterministic 測驗（input → |
| **settings-audit** | 自動 | 審查清理 .claude/settings.local.json — 移除無效 permissions、修正 JSON 語法、偵測一次性指令誤存為永久權限 |
| **setup-permissions** | 自動 | 偵測專案工具鏈，自動設定 permission allowlists，減少手動核准 |
| **task-brief** | `/task-brief` 或自動 | 把模糊的交辦翻譯成 AI 能正確執行的「任務定義」。先判斷任務落在四階段 （思考 / 探索 / 決定 / 執行）的哪一階段，每階段餵 AI |

### qa/ — QA 與驗收（測試、旅程、資料流稽核）

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **qa-auto** | `/qa-auto` | 從 QA 計畫或 diff 自動產生測試程式碼、執行測試、報告覆蓋率缺口 |
| **qa-dataflow** | `/qa-dataflow` 或自動 | 驗證資料流是否照宣稱在跑，以及路上的關卡到底擋不擋得住（寫了沒人讀、閘門不擋、基準永不報警）；產出功能關係主表 + 落差報告 |
| **qa-journey** | `/qa-journey` 或自動 | Persona-driven journey QA — simulate a REAL user (with limited knowledge and |
| **qa-planner** | `/qa-planner` | 分析程式碼變更產生結構化 QA 計畫：影響分析、測試案例、風險評估 |
| **qa-testing** | 自動 | 跨框架測試指導：pytest / Vitest / Swift Testing 的策略、mock 模式、模板 |

### quality/ — 程式品質

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **de-slopify** | 自動 | 移除 AI 生成「廢文」痕跡，讓文本讀起來像人寫的 |
| **github-repo-audit** | 自動 | Audit a GitHub repository for structure quality, documentation coverage |
| **large-file-refactor** | 自動 | Systematically split large single-file components (500+ lines) into modular |
| **protect-secrets** | Hook (PreToolUse) | 攔截讀取/修改 .env、private keys、credentials 等敏感檔案 |
| **say-it-plain** | `/say-it-plain` 或自動 | 把「講不清、抓不到重點、要人一問再問」的中文重寫成人能秒懂的版本——結論先行 |

### git/ — Git/GitHub

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **auto-stage** | Hook (PostToolUse) | 檔案編輯/建立後自動 git add，跳過 .env 和 node_modules |
| **concurrent-session-git** | 自動 | Git hygiene when multiple Claude sessions (or a human + an agent) share ONE |
| **repo-rename** | `/repo-rename` | Repo 改名時全系統審計引用（plist、Claude 設定、腳本、兄弟 repo），產出遷移清單並執行 |
| **resolving-merge-conflicts** | `/resolving-merge-conflicts` 或自動 | Resolve an in-progress git merge or rebase conflict by recovering each side's |

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
| **ai-vision-extract** | 自動 | The pattern for "photo → AI does the OCR/extraction → structured data" |
| **audio-transcription-flow** | 自動 | Implement a complete audio upload → speech-to-text → transcript display |
| **backend-async-jobs** | 自動 | Design decision + pattern for backend work that might be slow: when to keep a |
| **cloudflare-tunnel-ops** | `/cloudflare-tunnel-ops` 或自動 | Operate, move, and troubleshoot an EXISTING Cloudflare Tunnel for a dockerized |
| **cloudflare-tunnel-provision** | `/cloudflare-tunnel-provision` 或自動 | Stand up a brand-new public domain for a self-hosted dockerized app behind a |
| **db-migration** | 自動 | 偵測 DB stack，設定 migration 工具（Alembic/Prisma/Drizzle），指導安全 schema 變更 |
| **doc-to-structured-data** | 自動 | 非結構化技術文件（.doc/.pdf 測試計畫、規格書、datasheet）→ 結構化 CSV/JSON，含格式偵測、欄位對映、驗證 |
| **docker-compose-setup** | 自動 | Set up Docker Compose for multi-service projects (Next. |
| **firebase-backend** | 自動 | Firebase 全方位開發：Firestore CRUD/queries、Cloud Functions (1st/2nd gen, TS+Python)、CLI、emulator、Security Rules、Auth、Hosting、GCP 整合 |
| **ic-lot-normalization** | 自動 | Domain reference for normalizing semiconductor lot / batch / product codes when |
| **imap-smtp-integration** | 自動 | IMAP/SMTP Integration - Integrate email reading and sending via IMAP/SMTP into |
| **markdown-file-ssot** | 自動 | Markdown File SSOT - Use Markdown files with YAML frontmatter as a data SSOT. |
| **mcp-builder** | 自動 | 建立 MCP server 的指南（Python FastMCP / Node MCP SDK） |
| **ml-eval-quality** | 自動 | Domain reference for the evaluation + quality backbone of an ML/AutoML |
| **ml-model-registry** | 自動 | Domain reference for the model-registry / governance layer of an ML platform: |
| **oauth-token-vault** | 自動 | OAuth Token Vault - Implement OAuth 2. |
| **odb-dfm-reference** | 自動 | Domain reference for PCB manufacturing-side EDA — parsing ODB++ jobs and |
| **rbac-permissions** | 自動 | Design and implement Role-Based Access Control (RBAC) for full-stack apps. |
| **spine-auth** | 自動 | Canonical FastAPI auth for the product fleet — the CONVERGENT crypto core (jose |
| **spine-rbac** | 自動 | Canonical RBAC tiering for the FastAPI product fleet. |
| **spine-schema-sync** | 自動 | Canonical DB schema migration + dev↔prod sync for the FastAPI + Postgres fleet. |
| **spine-versioning** | 自動 | Canonical version + changelog for the product fleet — and crucially the |
| **sqlite-to-postgres** | 自動 | SQLite → PostgreSQL/Supabase 遷移指南：語法差異、schema 轉換、資料遷移、驗證 |
| **telegram-bot** | 自動 | grammY / python-telegram-bot 機器人開發指南：架構、Bot API、部署模式 |
| **tunnel-proxy-deploy** | 自動 | Deploy FastAPI + Next.js behind Cloudflare Tunnel. |
| **vector-search-setup** | 自動 | Set up a vector search knowledge base in a FastAPI project from scratch. |

### sales/ — 業務開發

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **presales-pipeline** | 自動 | Manage a B2B presales pipeline on the file system |
| **sales-client-kickoff-docs** | 自動 | At new-client kickoff (NDA signed, before the first working session) |
| **sales-crm-projection** | `/sales-crm-projection` | Project nx_client + nx_deal data to local markdown files at materials/clients/. |
| **sales-customer-intel** | `/sales-customer-intel` | B2B customer intelligence: company name → web research → actionable sales |
| **sales-keyword-discovery** | 自動 | Automated keyword discovery for scraper filter systems. |
| **sales-material** | `/sales-material` | Assemble client-specific sales presentations by matching customer intelligence |
| **sales-material-health** | `/sales-material-health` | Health check for the sales materials library — detects missing frontmatter |
| **tw-company-lookup** | `/tw-company-lookup` 或自動 | Query Taiwan's official business registry (findbiz.nat.gov. |

### gov/ — 政府案件

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **gov-rfq-writer** | 自動 | Generate Request for Quotation (RFQ / 報價單) for consulting projects. |
| **gov-subsidy-scraper** | `/gov-subsidy-scraper` | Automated government subsidy scraper — fetches grant listings from Taiwan |
| **gov-subsidy-writer** | `/gov-subsidy-writer` | Write Taiwan government subsidy proposals (政府補助計畫書) end-to-end — official 目錄 |
| **gov-tender-scraper** | `/gov-tender-scraper` | Automated government tender scraper — fetches public tender listings from |

### invest/ — 投資研究

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **invest-research** | `/invest-research` | Continuous portfolio agent: alpha discovery, risk, backtesting |
| **mops-financial-scraper** | 自動 | Scrape listed/OTC company financials from Taiwan's MOPS (公開資訊觀測站, mopsov.twse. |

### hr/ — 人資

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **hr-candidate-analysis** | `/hr-candidate-analysis` | Interview candidate management — extract structured data from PDF resumes |
| **hr-jd-writer** | 自動 | Generate structured Job Descriptions (JD / 職缺描述) from organizational context. |

### knowledge/ — 內容消化

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **knowledge-graph** | `/knowledge-graph` | 三層記憶系統：人物/公司/專案持久事實，經 scripts/kg.py 寫入 JSONL + 摘要；sk-facts-cron 每日自動抽取 |
| **local-media-transcribe** | 自動 | Transcribe a LOCAL audio/video file on disk (screen recording, meeting capture |
| **subtitle-file** | 自動 | Produce a subtitle FILE (.srt / . |
| **video-clip-extract** | 自動 | Cut a highlight clip out of an online video and save it as a standalone file — |
| **video-transcript** | 自動 | Read an online video's spoken content (via its subtitles) and transform it into |
| **yt-channel-scraper** | 自動 | Subscribe to YouTube channels, Bilibili UP 主, and podcast shows |

### docs/ — 文件處理與簡報

| Skill | 觸發方式 | 說明 |
|-------|---------|------|
| **chart-design** | 自動 | 畫圖的單一入口：泛用「畫圖／畫架構圖／畫流程圖」與所有要進報告／簡報的圖先到這裡 triage，再轉 mermaid / excalidraw；含 R1–R4、check-html-figure.mjs 機械檢查、三欄交付收據 |
| **discovery-interview** | 自動 | Run a structured Discovery interview with a potential consulting client to find |
| **doc-coauthoring** | `/doc-coauthoring` 或自動 | Structured workflow for collaboratively co-authoring documentation through |
| **excalidraw-diagram** | 自動 | 手繪風 .excalidraw → PNG；renderer 不是入口，由指名風格或 chart-design / pitch-deck 轉入 |
| **gdoc-report-builder** | 自動 | Build structured reports in Google Docs/Slides via MCP tools — batch table |
| **internal-comms** | `/internal-comms` 或自動 | Templates and formats for ongoing organizational communications during and |
| **iot-factory-report** | 自動 | Analyze factory IoT/SCADA time-series data (CSV/Excel) and produce visual |
| **mermaid-diagram** | `/mermaid-diagram` 或自動 | 給工程師看的 Mermaid 技術圖 .mmd → PNG（README、設計文件）；指名 Mermaid 或由 chart-design / user-flow 轉入 |
| **metadata-workshop** | 自動 | Run a structured Metadata Workshop with a consulting client to convert their |
| **office-docx** | 自動 | Word (.docx) 建立、編輯、分析，支援追蹤修訂與註解 |
| **office-pdf** | 自動 | PDF 操作：文字/表格擷取、建立、合併/分割、表單填寫 |
| **office-pptx** | 自動 | PowerPoint (.pptx) 建立、編輯、分析，支援版面配置、講者備註與 Codex 圖片資產 placement |
| **office-xlsx** | 自動 | 試算表 (.xlsx/.csv) 建立、編輯、分析，支援公式與資料視覺化 |
| **pitch-deck** | 自動 | 投資人/BP pitch deck 製作：discovery → narrative → Codex visual briefs → HTML slides → PPTX 匯出 |
| **slide-office-hours** | 自動 | Red-team review for a B2B presales deck storyline (storyline. |
| **slide-template-extractor** | 自動 | Extract design system from an existing PPTX or Google Slides deck and produce a |
| **slide-workflow** | 自動 | 簡報 gated workflow：目的 → 風格鎖定 → 大綱 → 內容 → Codex 視覺資產 → 生成 → 審查 → 匯出 |
| **sow-writer** | 自動 | Generate professional Taiwan-format Statement of Work (工作說明書 / SOW) for |

### Loop × PDCA 覆蓋表

| Loop | plan | do | check | act |
|------|------|----|-------|-----|
| sales | 5 | 5 | 2 | 1 |
| gov | 2 | 2 | — | — |
| invest | 1 | 1 | — | — |
| hr | — | 1 | 1 | — |
| knowledge | 1 | 5 | — | 1 |
| platform | 1 | 13 | 5 | 5 |
| dev | 19 | 21 | 8 | 8 |
| shared | 1 | 13 | 2 | — |


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

Each skill directory gets symlinked individually into both `~/.claude/skills/` and `${CODEX_HOME:-~/.codex}/skills/`. Edits to skill files take effect immediately — re-deploy only when adding new skills.

Codex reads repo-level system guidance from `AGENTS.md`, which delegates to `.claude/CLAUDE.md` so the same Rivendell operating rules apply in both agents.

Deploy also installs `com.*.plist` templates into `~/Library/LaunchAgents/`, replacing `REPO_PATH` with the actual repo path.

Gstack skills are managed by the gstack repo, not by `./bin/sk deploy`. To refresh
Codex's gstack skills, run:

```bash
cd /Users/manibari/code/gstack
./setup --host codex
```

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

The `/ports` dashboard page compares `docker-compose.yml` declarations with
local TCP listeners:

| Status | Meaning |
|--------|---------|
| `live` | Declared in compose and listening locally |
| `declared-only` | Declared in compose but not listening |
| `wild` | Listening locally but not declared in compose |
| `unknown` | Listener scan failed |

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

Skills deploy 後會在 Claude Code 和 Codex **全域生效**，不需要在每個專案裡做任何設定。

```bash
# Deploy once
./bin/sk deploy

# Use anywhere — restart Claude Code to pick up new skills
cd ~/any-project && claude
```

| 情境 | 做法 |
|------|------|
| 新增 skill 後看不到 | `./bin/sk deploy` 然後重啟 Claude Code / Codex |
| 修改現有 skill | 直接編輯 SKILL.md，symlink 立即生效 |
| 確認部署狀態 | `./bin/sk list` |
| 移除所有 skills | `./bin/sk undeploy` |

## Prerequisites

- **Claude Code** — install from Anthropic first; rivendell runs on top
- **Python 3** — for ui-ux-pro-max search CLI + dashboard api
- **Node + npm** — for dashboard web frontend
- **`agent-skills-cli`** (optional) — for importing from SkillsMP: `npm install -g agent-skills-cli`

For first-time install on a new machine or onboarding a colleague: see **[`docs/SETUP.md`](docs/SETUP.md)** — full runbook + gotchas (turbopack, `.next/` cache, IPv4/IPv6 conflicts).
