# Skills 稽核報告 — 2026-06-02

## 摘要

- **總計:** 94 skills
- **待處理:** 21 issue(s)


## 結構健康度

- Symlinks: OK
- 部署: OK (全部 94 個已部署)
- Frontmatter: **2 missing tags**
- Frontmatter: **3 missing version**
- 檔案完整性: OK — 所有引用檔案皆存在。

## Skill 生命週期

| 階段 | 數量 | 說明 |
|-------|-------|---------|
| 🆕 新建 | 0 | 已建立但尚未 commit |
| 🔧 開發中 | 0 | 14 天內有多次修訂 |
| ✅ 穩定 | 94 | 正常運作，近期無需修改 |
| ❓ 可能棄用 | 0 | 超過 90 天未更動 |

<details><summary>✅ 穩定 (94)</summary>

**backend/**
- audio-transcription-flow — 1 次, 56天前
- db-migration — 1 次, 82天前
- doc-to-structured-data — 1 次, 68天前
- docker-compose-setup — 2 次, 46天前
- firebase-backend — 3 次, 25天前
- imap-smtp-integration — 1 次, 70天前
- markdown-file-ssot — 1 次, 70天前
- oauth-token-vault — 1 次, 70天前
- rbac-permissions — 1 次, 56天前
- sqlite-to-postgres — 2 次, 25天前
- tunnel-proxy-deploy — 1 次, 79天前
- tw-company-lookup — 2 次, 78天前
- vector-search-setup — 1 次, 64天前

**docs/**
- chart-design — 1 次, 15天前
- discovery-interview — 1 次, 56天前
- doc-coauthoring — 2 次, 25天前
- excalidraw-diagram — 2 次, 17天前
- gdoc-report-builder — 2 次, 25天前
- internal-comms — 2 次, 25天前
- iot-factory-report — 2 次, 25天前
- mcp-builder — 3 次, 84天前
- mermaid-diagram — 1 次, 18天前
- metadata-workshop — 2 次, 25天前
- office-docx — 4 次, 55天前
- office-pdf — 3 次, 84天前
- office-pptx — 3 次, 84天前
- office-xlsx — 3 次, 84天前
- pitch-deck — 3 次, 25天前
- rfq-writer — 1 次, 55天前
- slide-office-hours — 2 次, 25天前
- slide-template-extractor — 2 次, 25天前
- slide-workflow — 4 次, 25天前
- sow-writer — 2 次, 25天前
- telegram-bot — 1 次, 79天前

**frontend/**
- frontend-design — 2 次, 85天前
- ios-integration — 1 次, 86天前
- swiftui-patterns — 1 次, 86天前
- ui-ux-pro-max — 3 次, 84天前

**git/**
- auto-stage — 3 次, 25天前
- repo-rename — 1 次, 68天前

**meta/**
- agent-persona — 1 次, 50天前
- audit-fix — 1 次, 82天前
- ci-pipeline — 1 次, 82天前
- deploy — 1 次, 82天前
- dev-process-gate — 4 次, 56天前
- init-project — 2 次, 85天前
- knowledge-graph — 1 次, 79天前
- learnings-promotion-sprint — 1 次, 18天前
- plan-check-style — 3 次, 82天前
- self-improving-agent — 3 次, 17天前
- session-harvest — 3 次, 25天前
- session-wrap — 1 次, 49天前
- setup-permissions — 3 次, 82天前
- skill-creator — 4 次, 46天前
- skill-scout — 2 次, 34天前
- sync-readme — 1 次, 63天前
- workflow-retro — 2 次, 25天前

**quality/**
- de-slopify — 2 次, 46天前
- github-repo-audit — 1 次, 50天前
- large-file-refactor — 1 次, 64天前
- protect-secrets — 3 次, 25天前
- qa-auto — 1 次, 79天前
- qa-planner — 1 次, 79天前
- qa-testing — 1 次, 84天前

**workflow/**
- agent-observability — 2 次, 56天前
- autoresearch — 2 次, 25天前
- candidate-analysis — 1 次, 68天前
- claude-to-telegram — 1 次, 79天前
- client-kickoff-docs — 1 次, 41天前
- context-recovery — 1 次, 79天前
- crm-projection — 1 次, 78天前
- customer-intel — 5 次, 25天前
- dispatching-parallel-agents — 4 次, 46天前
- env-doctor — 1 次, 41天前
- executing-plans — 3 次, 84天前
- gdrive-to-skills — 2 次, 85天前
- headless-agent — 6 次, 70天前
- investment-research — 4 次, 25天前
- jd-writer — 1 次, 50天前
- keyword-discovery — 1 次, 70天前
- launchd-agent — 6 次, 25天前
- material-health — 1 次, 78天前
- mockup — 1 次, 86天前
- mops-financial-scraper — 1 次, 41天前
- planning-with-files — 5 次, 56天前
- presales-pipeline — 1 次, 41天前
- repro-exam — 1 次, 41天前
- requirement — 2 次, 56天前
- sales-material — 3 次, 42天前
- settings-audit — 1 次, 69天前
- subsidy-scraper — 1 次, 78天前
- tender-scraper — 3 次, 70天前
- user-flow — 2 次, 18天前
- writing-plans — 3 次, 84天前

</details>

## 全部 Skills 功能一覽

### 基礎建設

| Skill | 功能 |
|-------|------|
| agent-observability | Agent 可觀測性：exec-lib 整合、執行歷史、即時 log 串流、timeline 事件 |
| agent-persona | Headless agent 角色 prompt 產生器（tester/maintainer/reviewer/developer/researcher）：自動注入專案結構、工具權限與輸出格式 |
| audit-fix | 分析 sk audit 報告，自動修復專案權限問題 |
| ci-pipeline | 偵測專案技術棧，自動產生 GitHub Actions CI 工作流 |
| deploy | 推薦部署平台，產生 Dockerfile / fly.toml / vercel.json 等配置 |
| dev-process-gate | 攔截跳過設計直接寫 code 的行為，引導走完整開發流程 |
| headless-agent | Headless agent 模式範本：排程、structured logging、output 管理 |
| init-project | 初始化 AGENTS.md + .claude/CLAUDE.md 專案配置 |
| launchd-agent | macOS launchd 排程管理：plist 產生、StartCalendarInterval、launchctl 生命週期 |
| plan-check-style | Plan mode 進入 UI 任務時，掃描並載入對應的設計風格 |
| repo-rename | Git repo 改名：系統性掃描所有跨位置引用，產生遷移 checklist |
| self-improving-agent | 記錄錯誤/修正/最佳實踐到 .learnings/，持續學習改進 |
| session-harvest | Session 結束時回顧工作，萃取可復用的 skill 候選 |
| session-wrap | Session 結束清理：auto-commit 未提交變更、歸檔 learnings、更新 progress.md |
| settings-audit | 審計 settings.local.json：移除無效權限、修正 JSON 語法、驗證格式 |
| setup-permissions | 偵測專案工具鏈，自動配置 settings.local.json 權限白名單 |
| skill-creator | Skill 全生命週期：建立、測試、benchmark、優化觸發描述 |
| skill-scout | 從 Clawdbot/OpenClaw 生態系搜尋、評估、移植 skills |
| sync-readme | 跨 repo 同步 README.md 的 Skills Catalog / 參考章節（SKILL.md 修改時 hook 自動觸發） |
| tunnel-proxy-deploy | FastAPI + Next.js 經 Cloudflare Tunnel 部署：反向代理、CORS、port mapping |

### 工作流

| Skill | 功能 |
|-------|------|
| autoresearch | 自主迭代迴圈：定義目標 + 指標 + 驗證指令，agent 自動 modify → verify → keep/discard |
| context-recovery | Session compaction 後自動恢復上下文（git/檔案/memory） |
| dispatching-parallel-agents | 派遣多個 agent 平行處理 3+ 個獨立問題 |
| executing-plans | 分批執行實作計畫，每批完成後 review checkpoint |
| keyword-discovery | 自動關鍵字探索：分析未匹配項目、寫入候選 YAML、高信心自動晉升 |
| planning-with-files | Manus 風格檔案式規劃（task_plan.md / findings.md / progress.md） |
| requirement | 定義結構化需求：user story + acceptance criteria + scope |
| user-flow | 設計使用者流程 Mermaid 流程圖（happy path + error branch） |
| writing-plans | 撰寫詳細實作計畫（TDD、2-5 分鐘 task、零背景工程師可執行） |

### 品質

| Skill | 功能 |
|-------|------|
| de-slopify | 移除 AI 生成的 slop 痕跡（含繁中模式：值得注意的是…） |
| doc-to-structured-data | 非結構化文件轉結構化 CSV/JSON：格式偵測、欄位辨識、多表輸出 |
| github-repo-audit | GitHub repo 健康度審計：結構、文件覆蓋、CI/CD、相依性、code hygiene，產出可行動評分報告 |
| large-file-refactor | 系統化拆分 500+ 行單一檔案：保持介面相容、模組化、介面測試 |
| protect-secrets | PreToolUse hook，阻擋讀寫 .env、私鑰、credentials 等機密檔案 |
| qa-auto | 根據 QA 計畫自動產生測試程式碼、執行測試、回報覆蓋率缺口 |
| qa-planner | 分析 code diff 產出 QA 計畫：影響範圍、測試案例、風險評估 |
| qa-testing | 跨框架測試撰寫指南：pytest / Vitest / Swift Testing |

### 前端

| Skill | 功能 |
|-------|------|
| frontend-design | 產生高品質、有設計感的前端 UI，避免 AI 罐頭風格 |
| ios-integration | iOS 系統整合：Share Extension、Deep Link、App Groups、權限、地圖 |
| mockup | 三階段 UI mockup：ASCII → 靜態 HTML → 互動 HTML，可匯出 Figma |
| swiftui-patterns | SwiftUI 架構模式：@Observable、Navigation、iOS 17+ 最佳實踐 |
| ui-ux-pro-max | UI/UX 設計資料庫：50+ 風格、97 色盤、57 字型配對、25 圖表類型 |

### 後端

| Skill | 功能 |
|-------|------|
| audio-transcription-flow | 音檔上傳 → speech-to-text → 逐字稿顯示 的完整 web 流程（Whisper 整合） |
| db-migration | 設定資料庫 migration 工具，產生 schema 變更的 migration 檔 |
| docker-compose-setup | Docker Compose 多服務設定（Next.js + FastAPI + Postgres/Redis）：Dockerfile、dev/prod compose.yml、.env.example、healthcheck |
| firebase-backend | Firebase 架構設計：Firestore schema、Security Rules、Cloud Functions v2、FCM 推播 |
| imap-smtp-integration | IMAP/SMTP 郵件整合：FastAPI 收發信、Gmail 備援方案 |
| markdown-file-ssot | Markdown + YAML frontmatter 作為半結構化資料 SSOT |
| oauth-token-vault | OAuth 2.0 flow + Fernet 加密 token 儲存（FastAPI + PostgreSQL） |
| rbac-permissions | 全端 RBAC 權限設計：角色階層、FastAPI decorator 保護、React AuthContext + AuthGuard |
| sqlite-to-postgres | SQLite → PostgreSQL 遷移指南：語法差異、schema 轉換、連線層更新 |
| vector-search-setup | FastAPI 向量搜尋知識庫建置：embedding 套件選型、資料模型、語意搜尋 API、索引管理 |

### 文件

| Skill | 功能 |
|-------|------|
| gdoc-report-builder | 經 MCP 建 Google Docs/Slides 結構化報告：批次編表、段落樣式、find-and-replace、多媒體插入 |
| iot-factory-report | 廠務 IoT/SCADA 時序資料分析（UPW/RO/壓縮機/冷凍機）：cycle detection、異常標記、趨勢分析、PPTX 匯出 |
| mcp-builder | MCP Server 開發指南：FastMCP、工具設計、外部 API 整合 |
| office-docx | Word 文件處理：建立（docx-js）、編輯（redlining）、追蹤修訂、批註 |
| office-pdf | PDF 處理：擷取文字/表格、合併拆分、建立、表單填寫、OCR |
| office-pptx | PowerPoint 處理：建立（html2pptx）、投影片設計、講者備註、縮圖 |
| office-xlsx | 試算表處理：公式計算（openpyxl）、財務模型色彩規範、pandas 分析 |
| slide-template-extractor | 從既有 PPTX/Google Slides 萃取設計系統，產出鎖定的 HTML slide template（CSS 變數：色彩、字型、版面） |
| slide-workflow | 簡報製作七階段 gate：目的 → 風格鎖定 → 大綱 → 內容 → 生成 → 審查 → 匯出 |

### Git

| Skill | 功能 |
|-------|------|
| auto-stage | PostToolUse hook，Claude 編輯/寫入檔案後自動 git stage |

### 整合

| Skill | 功能 |
|-------|------|
| claude-to-telegram | 設定 Telegram bridge 遠端控制 Claude Code（兩種方案比較） |
| gdrive-to-skills | 讀取 Google Drive 文件（MCP），分類後建立 knowledge skills |
| investment-research | 持續投資組合管理：alpha 發掘、風險管理、回測、財報分析 |
| knowledge-graph | 三層記憶系統：Entity JSONL + Auto Memory + MEMORY.md |
| telegram-bot | Telegram bot 開發指南：grammY (TS) / python-telegram-bot (Python) |
| tw-company-lookup | 台灣公司登記查詢：findbiz.nat.gov.tw 基本資料、董監事、變更紀錄 |

### docs

| Skill | 功能 |
|-------|------|
| chart-design | FastAPI 向量搜尋知識庫建置：embedding 套件選型、資料模型、語意搜尋 API、索引管理 |
| doc-coauthoring | 結構化客戶 Discovery 訪談：找最痛的手動流程，產出 discovery-summary.md（接 sow-writer） |
| excalidraw-diagram | 結構化客戶 Discovery 訪談：找最痛的手動流程，產出 discovery-summary.md（接 sow-writer） |
| internal-comms | 經 MCP 建 Google Docs/Slides 結構化報告：批次編表、段落樣式、find-and-replace、多媒體插入 |
| mermaid-diagram | MCP Server 開發指南：FastMCP、工具設計、外部 API 整合 |
| slide-office-hours | RFQ 報價單：pre-contract 議價、範圍選項、版本控制（合約前輕量版） |

### local

| Skill | 功能 |
|-------|------|
| _gstack-command | Fast headless browser for QA testing and site dogfooding. (gstack) |
| gstack | Fast headless browser for QA testing and site dogfooding. (gstack) |
| gstack-autoplan | Auto-review pipeline — reads the full CEO, design, eng, and DX review skills from disk and runs them sequentially w... |
| gstack-benchmark | Performance regression detection using the browse daemon. (gstack) |
| gstack-benchmark-models | Cross-model benchmark for gstack skills. (gstack) |
| gstack-browse | Fast headless browser for QA testing and site dogfooding. (gstack) |
| gstack-canary | Post-deploy canary monitoring. (gstack) |
| gstack-careful | Safety guardrails for destructive commands. (gstack) |
| gstack-codex | OpenAI Codex CLI wrapper — three modes. (gstack) |
| gstack-connect-chrome | Launch GStack Browser — AI-controlled Chromium with the sidebar extension baked in. |
| gstack-context-restore | Restore working context saved earlier by /context-save. (gstack) |
| gstack-context-save | Save working context. (gstack) |
| gstack-cso | Chief Security Officer mode. (gstack) |
| gstack-design-consultation | Design consultation: understands your product, researches the landscape, proposes a complete design system (aesthetic... |
| gstack-design-html | Design finalization: generates production-quality Pretext-native HTML/CSS. (gstack) |
| gstack-design-review | Designers eye QA: finds visual inconsistency, spacing issues, hierarchy problems, AI slop patterns, and slow interact... |
| gstack-design-shotgun | Design shotgun: generate multiple AI design variants, open a comparison board, collect structured feedback, and iterate. |
| gstack-devex-review | Live developer experience audit. (gstack) |
| gstack-document-generate | Generate missing documentation from scratch for a feature, module, or entire project. (gstack) |
| gstack-document-release | Post-ship documentation update. (gstack) |
| gstack-freeze | Restrict file edits to a specific directory for the session. (gstack) |
| gstack-guard | Full safety mode: destructive command warnings + directory-scoped edits. (gstack) |
| gstack-health | Code quality dashboard. (gstack) |
| gstack-investigate | Systematic debugging with root cause investigation. (gstack) |
| gstack-ios-clean | Remove the DebugBridge SPM package and all #if DEBUG wiring from an iOS app. (gstack) |
| gstack-ios-design-review | Visual design audit for iOS apps on real hardware. (gstack) |
| gstack-ios-fix | Autonomous iOS bug fixer. (gstack) |
| gstack-ios-qa | Live-device iOS QA for SwiftUI apps. (gstack) |
| gstack-ios-sync | Regenerate the iOS debug bridge against the latest upstream gstack templates. (gstack) |
| gstack-land-and-deploy | Land and deploy workflow. (gstack) |
| gstack-landing-report | Read-only queue dashboard for workspace-aware ship. (gstack) |
| gstack-learn | Manage project learnings. |
| gstack-make-pdf | Turn any markdown file into a publication-quality PDF. (gstack) |
| gstack-office-hours | YC Office Hours — two modes. (gstack) |
| gstack-open-gstack-browser | Launch GStack Browser — AI-controlled Chromium with the sidebar extension baked in. |
| gstack-pair-agent | Pair a remote AI agent with your browser. (gstack) |
| gstack-plan-ceo-review | CEO/founder-mode plan review. (gstack) |
| gstack-plan-design-review | Designers eye plan review — interactive, like CEO and Eng review. (gstack) |
| gstack-plan-devex-review | Interactive developer experience plan review. (gstack) |
| gstack-plan-eng-review | Eng manager-mode plan review. (gstack) |
| gstack-plan-tune | Self-tuning question sensitivity + developer psychographic for gstack (v1: observational). (gstack) |
| gstack-qa | Systematically QA test a web application and fix bugs found. (gstack) |
| gstack-qa-only | Report-only QA testing. (gstack) |
| gstack-retro | Weekly engineering retrospective. (gstack) |
| gstack-review | Pre-landing PR review. (gstack) |
| gstack-scrape | Pull data from a web page. (gstack) |
| gstack-setup-browser-cookies | Import cookies from your real Chromium browser into the headless browse session. (gstack) |
| gstack-setup-deploy | Configure deployment settings for /land-and-deploy. |
| gstack-setup-gbrain | Set up gbrain for this coding agent: install the CLI, initialize a local PGLite or Supabase brain, register MCP, capt... |
| gstack-ship | Ship workflow: detect + merge base branch, run tests, review diff, bump VERSION, update CHANGELOG, commit, push, crea... |
| gstack-skillify | Codify the most recent successful /scrape flow into a permanent browser-skill on disk. (gstack) |
| gstack-spec | Turn vague intent into a precise, executable spec in five phases. (gstack) |
| gstack-sync-gbrain | Keep gbrain current with this repos code and refresh agent search guidance in CLAUDE.md. |
| gstack-unfreeze | Clear the freeze boundary set by /freeze, allowing edits to all directories again. (gstack) |
| gstack-upgrade | Upgrade gstack to the latest version. |
| gstack.bak |  |

### meta

| Skill | 功能 |
|-------|------|
| learnings-promotion-sprint | 三層記憶系統：Entity JSONL + Auto Memory + MEMORY.md |
| workflow-retro | 跨 repo 同步 README.md 的 Skills Catalog / 參考章節（SKILL.md 修改時 hook 自動觸發） |

### workflow

| Skill | 功能 |
|-------|------|
| client-kickoff-docs | 設定 Telegram bridge 遠端控制 Claude Code（兩種方案比較） |
| env-doctor | 派遣多個 agent 平行處理 3+ 個獨立問題 |
| mops-financial-scraper | 三階段 UI mockup：ASCII → 靜態 HTML → 互動 HTML，可匯出 Figma |
| presales-pipeline | Manus 風格檔案式規劃（task_plan.md / findings.md / progress.md） |
| repro-exam | Manus 風格檔案式規劃（task_plan.md / findings.md / progress.md） |

### 人資

| Skill | 功能 |
|-------|------|
| candidate-analysis | 面試候選人管理：PDF 履歷結構化、GitHub 程式碼品質分析、候選人檔案產生 |
| jd-writer | 結構化 JD 產生：工作職責、必要/加分技能、職涯路徑、薪資範圍（讀組織階層寫出精準 JD） |

### 商業

| Skill | 功能 |
|-------|------|
| crm-projection | CRM 客戶索引：nx_client + nx_deal 投射至本地 markdown |
| customer-intel | B2B 客戶情蒐：公司概覽、領導層、財務、競爭者、痛點、銷售策略 |
| discovery-interview | 結構化客戶 Discovery 訪談：找最痛的手動流程，產出 discovery-summary.md（接 sow-writer） |
| material-health | 銷售素材庫健康檢查：frontmatter 缺漏、過期補助、陳舊資訊偵測 |
| metadata-workshop | 客戶 Metadata Workshop：商業知識轉 YAML schema（廠務 PI/SCADA/MES、ERP、travel）— AI 顧問的 moat |
| pitch-deck | 投資人/BP pitch deck 製作：discovery → narrative → HTML slides → PPTX 匯出 |
| rfq-writer | RFQ 報價單：pre-contract 議價、範圍選項、版本控制（合約前輕量版） |
| sales-material | 客製化銷售簡報：匹配情蒐、案例、方案、補助，產生 PPTX |
| sow-writer | 台灣格式 SOW 工作說明書：12+ 標準章節、Mermaid Gantt、人天計費 |
| subsidy-scraper | 政府補助爬蟲：自動擷取補助公告、去重、歸檔、產生 INDEX.md |
| tender-scraper | 政府標案爬蟲：g0v API 擷取、關鍵字過濾、自動探索、dashboard 可觀測 |

## 描述品質

### 缺少 TRIGGER / DO NOT TRIGGER (2)

- auto-stage
- protect-secrets

## 標籤重疊分析

- **[business,docs,workflow]**: discovery-interview metadata-workshop sow-writer — 建議檢查邊界是否清楚
- **[docs]**: gdoc-report-builder office-docx office-pdf office-pptx office-xlsx — 建議檢查邊界是否清楚
- **[docs,workflow]**: chart-design iot-factory-report pitch-deck slide-template-extractor slide-workflow — 建議檢查邊界是否清楚
- **[meta]**: agent-persona audit-fix ci-pipeline deploy dev-process-gate init-project plan-check-style setup-permissions skill-creator sync-readme — 建議檢查邊界是否清楚
- **[workflow]**: client-kickoff-docs dispatching-parallel-agents executing-plans jd-writer planning-with-files requirement user-flow writing-plans — 建議檢查邊界是否清楚

## 專案儀表板

### ChimesFlow

| | |
|---|---|
| **狀態** | 🔥 活躍 — 80 個 commit（本週）, 221 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) |
| **Git** | 1 dirty |
| **CI/CD** | CI ❌ · 部署 ✅ · Hooks ❌ |
| **Config** | **missing** | **權限** | OK (0 rules) |

<details><summary>近期 commits</summary>

```
a621e84 docs(learnings): idempotent migration vs startup create_all race
487b6fd feat(products): product category tree — frontend cascade (#8 Phase 1)
a160956 feat(products): product category tree — backend (#8 Phase 1)
fc04395 fix(version): correct to v1.1.2 — product tree (#8) not yet shipped
25a9d15 feat(warranty): warranty_years on quote + contract + informational liability estimate
```
</details>

### Edict

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Docker Python |
| **分支** | `main` (1 total) | 2 個 open PR |
| **Git** | 1 unpushed |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | **missing** | **權限** | OK (9 rules) |

<details><summary>近期 commits</summary>

```
fc10c4c feat: Traditional Chinese UI + NTD currency conversion
65c09cb chore: remove unrelated tracked files and update .gitignore
e9aea53 feat: 添加 QQ 机器人通知渠道 (#244)
c3c4e2a fix: CWE-22 path traversal in file:// URL handling (#258)
4e51e34 fix: 修复任务卡死三大问题
```
</details>

### Family-Fiscal

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) |
| **Git** | clean |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | no CLAUDE.md | **權限** | OK (0 rules) |

<details><summary>近期 commits</summary>

```
fc3f1a2 feat: FCN full edit, outstanding loans by currency, asset linkage fixes
8c72c59 refactor(db): complete migration from zombie tables to canonical account-centric schema
7783aa2 fix(ui): hide outstanding loans when no transaction records exist
e6c69c7 feat(admin): add CSV import/export data management tab
ab65f82 fix(loans): show outstanding loans from account_transfers instead of transactions
```
</details>

### Marketing-Pal

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Node.js Xcode |
| **分支** | `main` (1 total) |
| **Git** | clean |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | OK | **權限** | OK (12 rules) |

<details><summary>近期 commits</summary>

```
d38d2bb Merge pull request #9 from manibari/feature/v3-line-share-order-link
25807c1 Add Next.js web app MVP: content creation, shop, style management
ab67bef Implement v3: LINE share, order link integration, direct reach optimization
4fdaf1e Merge pull request #8 from manibari/chore/update-claude-md
c0845bc Update CLAUDE.md with v2 P0+P1 feature docs
```
</details>

### MingOS

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Python |
| **分支** | `main` (1 total) |
| **Git** | 3 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | OK | **權限** | OK (11 rules) |

<details><summary>近期 commits</summary>

```
caac18e feat: add camping groceries list, wednesday meals, and projects data
a2765e1 refactor: switch email monitor from MS Graph to Gmail API
59f8aaf feat: add email monitor — auto-fetch M365 inbox, classify, and notify
a07a319 feat: add Projects page with persistent conversations and context
32ac944 fix: split context — raw text for classification, history for drafting
```
</details>

### PTI-ARES

| | |
|---|---|
| **狀態** | 🔥 活躍 — 36 個 commit（本週）, 45 個（本月） |
| **技術棧** |  Python |
| **分支** | `next-wave-2026-05` (5 total) | 1 個 open PR |
| **Git** | 2 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | **missing** | **權限** | OK (8 rules) |

<details><summary>近期 commits</summary>

```
220a65b docs(README): 模組段重寫為 attributed-component × ARES 三段架構
33ffcf0 docs(README): 加 ARES 釋義 (Recognition/Extraction/Screening↔pipeline) + 修沙盒路徑 + 更新測試數
55589ca refactor!: rename project odb-dfm → PTI-ARES (Agentic Recognition, Extraction & Screening)
964d7e5 docs: Phase 1 驗收改 pipeline S1~S4 + 決策日誌 + README 重寫
b049d21 docs: state-of-the-codebase snapshot (2026-05-28) as /requirement input
```
</details>

### RTK

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) |
| **Git** | 3 dirty, 1 unpushed |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | OK | **權限** | OK (8 rules) |

<details><summary>近期 commits</summary>

```
3fff6b8 feat(3dgs): add Gaussian Splatting viewer POC at /3dgs
4d1cbb4 fix: update StrategicMap component
c709193 balance: raise capturedCityLoyalty and lower foreignDecayPerTick
687b4c0 fix: add capturedAtTick.clear() to reset()
3579114 feat: monthly calendar system (1 tick = 1 month) and loyalty decay fix
```
</details>

### TailTrack

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Node.js Xcode |
| **分支** | `main` (1 total) |
| **Git** | clean |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | OK | **權限** | OK (11 rules) |

<details><summary>近期 commits</summary>

```
4e50252 feat: tutorial system, expanded preview data, fullscreen map mockup
c7d2f76 feat: add Smart Search with Google Places + business hours check
fa6d1dc fix: use text-based matching for onboarding UI tests
126bea3 test: update UI tests for 2-tab MVP and single-screen onboarding
d452c9f refactor: simplify onboarding, remove ProfileView, drop scheduledDate
```
</details>

### curia

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) |
| **Git** | 9 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | OK | **權限** | OK (8 rules) |

<details><summary>近期 commits</summary>

```
a3a6e85 docs: QA plan for Phase 2 + Phase 3 (13/13 tests passed)
7529255 feat: Phase 3 — company research, editable proposals, clients API
d98b744 feat: Phase 2 — Azure OpenAI scoring + proposal generation
dbd5915 chore: add learnings log for Upwork RSS deprecation
1807900 feat: Curia project skeleton + RSS fetch pipeline + dashboard UI
```
</details>

### gstack

| | |
|---|---|
| **狀態** | 🔥 活躍 — 7 個 commit（本週）, 45 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) | 10 個 open PR |
| **Git** | 52 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | no CLAUDE.md | **權限** | OK (9 rules) |

<details><summary>近期 commits</summary>

```
62024d11 v1.52.2.0 fix(make-pdf): render emoji instead of tofu (▯) on Linux (#1787)
070722ac v1.52.1.0 feat: brain-aware planning — 5 skills read structured gbrain context before asking (#1742)
ce5fbfa9 v1.52.0.0 feat(plan-tune): explicit consent + first-run setup wizard for contributors (#1741)
19770ea8 v1.51.0.0 feat: $B memory diagnostic + 4 CDP-resource leak fixes (#1751)
a6fb3172 v1.48.0.0 feat: AskUserQuestion split rule + runtime AUTO_DECIDE carve-out (#1740)
```
</details>

### lorien

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) |
| **Git** | 1 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | no AGENTS.md | **權限** | OK (13 rules) |

<details><summary>近期 commits</summary>

```
2657775 docs: make metadata schema format-neutral across templates
0de7552 fix: load .env via dotenv + pin openai>=1.54.4
a174d8a feat: switch runtime to Azure OpenAI + integrate SerpAPI travel data
574d20d feat: client portal agents view — Sabre can see their own agents
8f90cde feat: stage 2 — portal view-only, RBAC, locked PATCH, CODEOWNERS
```
</details>

### news_stock

| | |
|---|---|
| **狀態** | ✅ 近期有動 — 1 個 commit（本週）, 27 個（本月） |
| **技術棧** |  Docker Node.js Python |
| **分支** | `feat/entry-allocation-tradingview-ui` (5 total) |
| **Git** | 21 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | OK | **權限** | OK (25 rules) |

<details><summary>近期 commits</summary>

```
20cdcb0 feat(stock-picking): add today's entry allocation + TradingView UI redesign
a011064 chore(agent): research-agent-daily run 2026-05-23
37ff179 chore(agent): research-agent-daily run 2026-05-19
1c5fc93 chore(agent): research-agent-daily run 2026-05-18
67afc0c chore(agent): research-agent-daily run 2026-05-16
```
</details>

### rakucamp

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) |
| **Git** | 15 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | **missing** | **權限** | OK (7 rules) |

<details><summary>近期 commits</summary>

```
63b3cd1 chore: scaffold Next.js app and interactive multi-section mockup
```
</details>

### sales-assistant

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Docker Node.js Python |
| **分支** | `main` (2 total) |
| **Git** | 1861 dirty, 2 unpushed |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ✅ |
| **Config** | OK | **權限** | OK (35 rules) |

<details><summary>近期 commits</summary>

```
3eb1d3e refactor(nexus): S44 drop nx_project.client_id redundancy + nullable invoice.deal_id
5fc6b1b feat(nexus): projects + roles + financial flow
c363920 feat(account): allow users to update own name/password via PATCH /me
b2e162d feat: role system (admin/manager/user), invoice/project CRUD, login register tab
ffeffc2 fix(compliance): P0 — close_deal Won/Lost logic, require_finance guard, audit log
```
</details>

### taiwan-company

| | |
|---|---|
| **狀態** | ✅ 近期有動 — 3 個 commit（本週）, 38 個（本月） |
| **技術棧** |  Docker Make Python |
| **分支** | `refactor/p0-data-safety` (2 total) |
| **Git** | 1 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | **missing** | **權限** | OK (13 rules) |

<details><summary>近期 commits</summary>

```
5257df0 chore: gitignore refactor planning files (task_plan/findings/progress)
2a47fa1 refactor(data): crash-safe atomic writes + race-safe locking for JSON store
2294508 feat: 簡報摘要功能（上傳簡報 → Opus 4.7 生成 → 逐段審核套用公司簡介）
36ce0f4 feat: 標籤自動歸攏群組、GCIS 重試區分、自動補抓每股金額
c46fe17 fix(mops): 接軌 mops_notes（port 8085）、investee-holders 去重、法人溯源列 CSS 修正
```
</details>

**5 個專案問題待處理。**
## Agent 健康狀態

| 專案 | Agent | 排程 | 狀態 | 最近 Exit |
|---------|-------|----------|--------|-----------|
| news_stock | research-agent | daily 7:30 | ● loaded | 1 |
| news_stock | research-agent-weekly | weekly 10:00 | ● loaded | 1 |
| news_stock | maintainer | daily 4:00 | ○ unloaded | — |
| news_stock | tester | daily 5:00 | ○ unloaded | — |
| news_stock | developer | weekly 3:00 | ○ unloaded | — |
| rivendell | maintain | daily 22:00 | ● loaded | 0 |
| rivendell | harvest | interval :00 | ● loaded | 0 |
| rivendell | tester | daily 6:00 | ● loaded | 0 |
| sales-assistant | crm-projection | daily 7:00 | ○ unloaded | — |
| sales-assistant | subsidy-scraper | calendar 8:00 | ○ unloaded | — |
| sales-assistant | material-health | weekly 9:00 | ○ unloaded | — |
| sales-assistant | tender-scraper | daily 8:30 | ○ unloaded | — |

**9 個 agent 問題待處理。**

## Token 用量

### 7 日趨勢

~~~mermaid
xychart-beta
    title "每日花費（USD）"
    x-axis ["05-27", "05-28", "05-29", "05-30", "05-31", "06-01", "06-02"]
    y-axis "USD" 0 --> 2150
    bar [1718, 1095, 2080, 1693, 50, 1549, 996]
~~~

| 日期 | Sessions | API 呼叫 | Tokens | 預估花費 |
|------|----------|-----------|--------|-----------|
| 2026-05-27 (Wed) | 4 | 1,668 | 868.1M | $1718.08 |
| 2026-05-28 (Thu) | 15 | 1,671 | 452.5M | $1095.50 |
| 2026-05-29 (Fri) | 12 | 2,247 | 978.1M | $2079.88 |
| 2026-05-30 (Sat) | 11 | 1,025 | 403.0M | $1692.81 |
| 2026-05-31 (Sun) | 5 | 102 | 8.5M | $50.17 |
| 2026-06-01 (Mon) | 10 | 1,882 | 747.2M | $1548.55 |
| 2026-06-02 (Tue) | 6 | 1,091 | 460.0M | $996.34 |
| **Total** | | | **3917.3M** | **$9181.34** |

### 各專案花費（7 日）

| 專案 | API 呼叫 | Tokens | 預估花費 |
|---------|-----------|--------|-----------|
| -Users-manibari-code-ChimesFlow | 3,979 | 2051.8M | $4180.19 |
| -Users-manibari-code-odb-dfm | 2,020 | 1064.6M | $2157.54 |
| -Users-manibari-code | 483 | 77.3M | $824.93 |
| -Users-manibari-Vault-Peter | 1,465 | 348.7M | $767.34 |
| -Users-manibari-code-rivendell | 321 | 107.3M | $529.92 |
| -Users-manibari-Vault-Peter-Work | 556 | 187.1M | $456.26 |
| -Users-manibari-code-news-stock | 345 | 41.6M | $132.77 |
| -Users-manibari-code-sales-assistant | 352 | 23.4M | $92.70 |
| news_stock | 28 | 603K | $40.77 |
| -Users-manibari-Documents-Peter | 165 | 15.5M | $39.69 |

_計價: Opus input $15/M, output $75/M, cache create $18.75/M, cache read $1.50/M_


---

*由以下工具產生 `./bin/sk audit` — 2026-06-02 — 94 skills, 21 issue(s)*
