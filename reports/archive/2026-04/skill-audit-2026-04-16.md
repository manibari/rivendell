# Skills 稽核報告 — 2026-04-16

## 摘要

## 結構健康度

- Symlinks: OK
- 部署: **11 個未部署**
- audio-transcription-flow
- docker-compose-setup
- rbac-permissions
- discovery-interview
- metadata-workshop
- pitch-deck
- rfq-writer
- slide-template-extractor
- slide-workflow
- sow-writer
- session-wrap

- Frontmatter: **2 missing tags**
- Frontmatter: **3 missing version**
- 檔案完整性: OK — 所有引用檔案皆存在。

## Skill 生命週期

| 階段 | 數量 | 說明 |
|-------|-------|---------|
| 🆕 新建 | 0 | 已建立但尚未 commit |
| 🔧 開發中 | 10 | 14 天內有多次修訂 |
| ✅ 穩定 | 71 | 正常運作，近期無需修改 |
| ❓ 可能棄用 | 0 | 超過 90 天未更動 |

### 🔧 開發中

**docs/**
- office-docx — 4 次修訂, 8天前
- pitch-deck — 2 次修訂, 6天前

**meta/**
- dev-process-gate — 4 次修訂, 9天前
- session-harvest — 2 次修訂, 6天前
- skill-creator — 3 次修訂, 9天前

**workflow/**
- agent-observability — 2 次修訂, 9天前
- launchd-agent — 4 次修訂, 9天前
- planning-with-files — 5 次修訂, 9天前
- requirement — 2 次修訂, 9天前
- sales-material — 2 次修訂, 6天前

<details><summary>✅ 穩定 (71)</summary>

**backend/**
- audio-transcription-flow — 1 次, 9天前
- db-migration — 1 次, 35天前
- doc-to-structured-data — 1 次, 21天前
- docker-compose-setup — 1 次, 9天前
- firebase-backend — 1 次, 39天前
- imap-smtp-integration — 1 次, 23天前
- markdown-file-ssot — 1 次, 23天前
- oauth-token-vault — 1 次, 23天前
- rbac-permissions — 1 次, 9天前
- sqlite-to-postgres — 1 次, 32天前
- tunnel-proxy-deploy — 1 次, 32天前
- tw-company-lookup — 2 次, 31天前
- vector-search-setup — 1 次, 17天前

**docs/**
- discovery-interview — 1 次, 9天前
- gdoc-report-builder — 1 次, 3天前
- iot-factory-report — 1 次, 3天前
- mcp-builder — 3 次, 37天前
- metadata-workshop — 1 次, 8天前
- office-pdf — 3 次, 37天前
- office-pptx — 3 次, 37天前
- office-xlsx — 3 次, 37天前
- rfq-writer — 1 次, 8天前
- slide-template-extractor — 1 次, 6天前
- slide-workflow — 1 次, 2天前
- sow-writer — 1 次, 9天前
- telegram-bot — 1 次, 32天前

**frontend/**
- frontend-design — 2 次, 38天前
- ios-integration — 1 次, 39天前
- swiftui-patterns — 1 次, 39天前
- ui-ux-pro-max — 3 次, 37天前

**git/**
- auto-stage — 1 次, 21天前
- repo-rename — 1 次, 21天前

**meta/**
- agent-persona — 1 次, 3天前
- audit-fix — 1 次, 35天前
- ci-pipeline — 1 次, 35天前
- deploy — 1 次, 35天前
- init-project — 2 次, 38天前
- knowledge-graph — 1 次, 32天前
- plan-check-style — 3 次, 35天前
- self-improving-agent — 2 次, 17天前
- session-wrap — 1 次, 2天前
- setup-permissions — 3 次, 35天前
- skill-scout — 1 次, 32天前
- sync-readme — 1 次, 16天前

**quality/**
- de-slopify — 1 次, 32天前
- github-repo-audit — 1 次, 3天前
- large-file-refactor — 1 次, 17天前
- protect-secrets — 1 次, 21天前
- qa-auto — 1 次, 32天前
- qa-planner — 1 次, 32天前
- qa-testing — 1 次, 37天前

**workflow/**
- autoresearch — 1 次, 23天前
- candidate-analysis — 1 次, 21天前
- claude-to-telegram — 1 次, 32天前
- context-recovery — 1 次, 32天前
- crm-projection — 1 次, 31天前
- customer-intel — 4 次, 31天前
- dispatching-parallel-agents — 3 次, 37天前
- executing-plans — 3 次, 37天前
- gdrive-to-skills — 2 次, 38天前
- headless-agent — 6 次, 23天前
- investment-research — 3 次, 32天前
- jd-writer — 1 次, 3天前
- keyword-discovery — 1 次, 23天前
- material-health — 1 次, 31天前
- mockup — 1 次, 39天前
- settings-audit — 1 次, 22天前
- subsidy-scraper — 1 次, 31天前
- tender-scraper — 3 次, 23天前
- user-flow — 1 次, 39天前
- writing-plans — 3 次, 37天前

</details>

## 全部 Skills 功能一覽

### 基礎建設

| Skill | 功能 |
|-------|------|
| agent-observability | Agent 可觀測性：exec-lib 整合、執行歷史、即時 log 串流、timeline 事件 |
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
| settings-audit | 審計 settings.local.json：移除無效權限、修正 JSON 語法、驗證格式 |
| setup-permissions | 偵測專案工具鏈，自動配置 settings.local.json 權限白名單 |
| skill-creator | Skill 全生命週期：建立、測試、benchmark、優化觸發描述 |
| skill-scout | 從 Clawdbot/OpenClaw 生態系搜尋、評估、移植 skills |
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
| db-migration | 設定資料庫 migration 工具，產生 schema 變更的 migration 檔 |
| firebase-backend | Firebase 架構設計：Firestore schema、Security Rules、Cloud Functions v2、FCM 推播 |
| imap-smtp-integration | IMAP/SMTP 郵件整合：FastAPI 收發信、Gmail 備援方案 |
| markdown-file-ssot | Markdown + YAML frontmatter 作為半結構化資料 SSOT |
| oauth-token-vault | OAuth 2.0 flow + Fernet 加密 token 儲存（FastAPI + PostgreSQL） |
| sqlite-to-postgres | SQLite → PostgreSQL 遷移指南：語法差異、schema 轉換、連線層更新 |

### 文件

| Skill | 功能 |
|-------|------|
| mcp-builder | MCP Server 開發指南：FastMCP、工具設計、外部 API 整合 |
| office-docx | Word 文件處理：建立（docx-js）、編輯（redlining）、追蹤修訂、批註 |
| office-pdf | PDF 處理：擷取文字/表格、合併拆分、建立、表單填寫、OCR |
| office-pptx | PowerPoint 處理：建立（html2pptx）、投影片設計、講者備註、縮圖 |
| office-xlsx | 試算表處理：公式計算（openpyxl）、財務模型色彩規範、pandas 分析 |

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

### backend

| Skill | 功能 |
|-------|------|
| audio-transcription-flow | Implement a complete audio upload → speech-to-text → transcript display workflow in a web app. |
| docker-compose-setup | 非結構化文件轉結構化 CSV/JSON：格式偵測、欄位辨識、多表輸出 |
| rbac-permissions | OAuth 2.0 flow + Fernet 加密 token 儲存（FastAPI + PostgreSQL） |
| vector-search-setup | 台灣公司登記查詢：findbiz.nat.gov.tw 基本資料、董監事、變更紀錄 |

### docs

| Skill | 功能 |
|-------|------|
| discovery-interview | 台灣公司登記查詢：findbiz.nat.gov.tw 基本資料、董監事、變更紀錄 |
| gdoc-report-builder | 台灣公司登記查詢：findbiz.nat.gov.tw 基本資料、董監事、變更紀錄 |
| iot-factory-report | 台灣公司登記查詢：findbiz.nat.gov.tw 基本資料、董監事、變更紀錄 |
| metadata-workshop | MCP Server 開發指南：FastMCP、工具設計、外部 API 整合 |
| pitch-deck | 試算表處理：公式計算（openpyxl）、財務模型色彩規範、pandas 分析 |
| rfq-writer | 試算表處理：公式計算（openpyxl）、財務模型色彩規範、pandas 分析 |
| slide-template-extractor | 試算表處理：公式計算（openpyxl）、財務模型色彩規範、pandas 分析 |
| slide-workflow | 試算表處理：公式計算（openpyxl）、財務模型色彩規範、pandas 分析 |
| sow-writer | 試算表處理：公式計算（openpyxl）、財務模型色彩規範、pandas 分析 |

### local

| Skill | 功能 |
|-------|------|
| gstack |  |
| gstack-autoplan |  |
| gstack-benchmark |  |
| gstack-browse |  |
| gstack-canary |  |
| gstack-careful |  |
| gstack-checkpoint |  |
| gstack-codex |  |
| gstack-connect-chrome |  |
| gstack-cso |  |
| gstack-design-consultation |  |
| gstack-design-html |  |
| gstack-design-review |  |
| gstack-design-shotgun |  |
| gstack-devex-review |  |
| gstack-document-release |  |
| gstack-freeze |  |
| gstack-guard |  |
| gstack-health |  |
| gstack-investigate |  |
| gstack-land-and-deploy |  |
| gstack-learn |  |
| gstack-office-hours |  |
| gstack-open-gstack-browser |  |
| gstack-pair-agent |  |
| gstack-plan-ceo-review |  |
| gstack-plan-design-review |  |
| gstack-plan-devex-review |  |
| gstack-plan-eng-review |  |
| gstack-qa |  |
| gstack-qa-only |  |
| gstack-retro |  |
| gstack-review |  |
| gstack-setup-browser-cookies |  |
| gstack-setup-deploy |  |
| gstack-ship |  |
| gstack-unfreeze |  |
| gstack-upgrade |  |
| gstack.bak |  |

### meta

| Skill | 功能 |
|-------|------|
| agent-persona | Git repo 改名：系統性掃描所有跨位置引用，產生遷移 checklist |
| session-wrap | Session 結束時回顧工作，萃取可復用的 skill 候選 |
| sync-readme | 從 Clawdbot/OpenClaw 生態系搜尋、評估、移植 skills |

### quality

| Skill | 功能 |
|-------|------|
| github-repo-audit | 移除 AI 生成的 slop 痕跡（含繁中模式：值得注意的是…） |
| large-file-refactor | 移除 AI 生成的 slop 痕跡（含繁中模式：值得注意的是…） |

### workflow

| Skill | 功能 |
|-------|------|
| jd-writer | 持續投資組合管理：alpha 發掘、風險管理、回測、財報分析 |

### 人資

| Skill | 功能 |
|-------|------|
| candidate-analysis | 面試候選人管理：PDF 履歷結構化、GitHub 程式碼品質分析、候選人檔案產生 |

### 商業

| Skill | 功能 |
|-------|------|
| crm-projection | CRM 客戶索引：nx_client + nx_deal 投射至本地 markdown |
| customer-intel | B2B 客戶情蒐：公司概覽、領導層、財務、競爭者、痛點、銷售策略 |
| material-health | 銷售素材庫健康檢查：frontmatter 缺漏、過期補助、陳舊資訊偵測 |
| sales-material | 客製化銷售簡報：匹配情蒐、案例、方案、補助，產生 PPTX |
| subsidy-scraper | 政府補助爬蟲：自動擷取補助公告、去重、歸檔、產生 INDEX.md |
| tender-scraper | 政府標案爬蟲：g0v API 擷取、關鍵字過濾、自動探索、dashboard 可觀測 |

## 描述品質

### 缺少 TRIGGER / DO NOT TRIGGER (3)

- auto-stage
- de-slopify
- protect-secrets

## 標籤重疊分析

- **[business,docs,workflow]**: discovery-interview metadata-workshop sow-writer — 建議檢查邊界是否清楚
- **[docs]**: gdoc-report-builder office-docx office-pdf office-pptx office-xlsx — 建議檢查邊界是否清楚
- **[docs,workflow]**: iot-factory-report pitch-deck slide-template-extractor slide-workflow — 建議檢查邊界是否清楚
- **[meta]**: agent-persona audit-fix ci-pipeline deploy dev-process-gate init-project plan-check-style setup-permissions skill-creator sync-readme — 建議檢查邊界是否清楚
- **[workflow]**: dispatching-parallel-agents executing-plans jd-writer planning-with-files requirement user-flow writing-plans — 建議檢查邊界是否清楚

## 專案儀表板

### Edict

| | |
|---|---|
| **狀態** | 💤 沉寂 — 0 個 commit（本週）, 43 個（本月） |
| **技術棧** |  Docker Python |
| **分支** | `main` (1 total) | 9 個 open PR |
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
| **狀態** | 💤 沉寂 — 0 個 commit（本週）, 30 個（本月） |
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

### RTK

| | |
|---|---|
| **狀態** | 💤 沉寂 — 0 個 commit（本週）, 1 個（本月） |
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
| **狀態** | 💤 沉寂 — 0 個 commit（本週）, 5 個（本月） |
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
| **狀態** | ✅ 近期有動 — 1 個 commit（本週）, 151 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) | 10 個 open PR |
| **Git** | 36 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | no CLAUDE.md | **權限** | OK (9 rules) |

<details><summary>近期 commits</summary>

```
c6e6a21d refactor: AI slop reduction with cross-model quality review (v0.16.3.0) (#941)
dbd7aee5 feat: relationship closing — office-hours adapts to repeat users (v0.16.2.0) (#937)
a7593d70 fix: cookie picker auth token leak (v0.15.17.0) (#904)
b73f3644 feat: browser data platform for AI agents (v0.16.0.0) (#907)
9d34baa9 fix: gstack-slug produces deterministic slugs across sessions (#897)
```
</details>

### lorien

| | |
|---|---|
| **狀態** | ✅ 近期有動 — 2 個 commit（本週）, 12 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) |
| **Git** | clean |
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
| **狀態** | 💤 沉寂 — 0 個 commit（本週）, 20 個（本月） |
| **技術棧** |  Docker Node.js Python |
| **分支** | `main` (1 total) |
| **Git** | 52 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | OK | **權限** | OK (25 rules) |

<details><summary>近期 commits</summary>

```
02f8349 fix(chart): improve candlestick trade markers with scatter series
2d9cbb6 chore(agent): research-agent-daily run 2026-03-31
7246400 chore(agent): research-agent-daily run 2026-03-30
b60a58b fix: market report differentiates US vs TW content
2d51cee feat: switch narrative service to Azure OpenAI (GPT-4)
```
</details>

