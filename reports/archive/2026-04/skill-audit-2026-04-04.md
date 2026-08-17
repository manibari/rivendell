# Skills 稽核報告 — 2026-04-04

## 摘要

- **總計:** 65 skills
- **待處理:** 19 issue(s)


## 結構健康度

- Symlinks: OK
- 部署: OK (全部 65 個已部署)
- Frontmatter: **2 missing tags**
- Frontmatter: **3 missing version**
- 檔案完整性: OK — 所有引用檔案皆存在。

## Skill 生命週期

| 階段 | 數量 | 說明 |
|-------|-------|---------|
| 🆕 新建 | 0 | 已建立但尚未 commit |
| 🔧 開發中 | 4 | 14 天內有多次修訂 |
| ✅ 穩定 | 61 | 正常運作，近期無需修改 |
| ❓ 可能棄用 | 0 | 超過 90 天未更動 |

### 🔧 開發中

**meta/**
- self-improving-agent — 2 次修訂, 5天前

**workflow/**
- headless-agent — 6 次修訂, 11天前
- launchd-agent — 3 次修訂, 11天前
- tender-scraper — 3 次修訂, 11天前

<details><summary>✅ 穩定 (61)</summary>

**backend/**
- db-migration — 1 次, 23天前
- doc-to-structured-data — 1 次, 9天前
- firebase-backend — 1 次, 27天前
- imap-smtp-integration — 1 次, 11天前
- markdown-file-ssot — 1 次, 11天前
- oauth-token-vault — 1 次, 11天前
- sqlite-to-postgres — 1 次, 20天前
- tunnel-proxy-deploy — 1 次, 20天前
- tw-company-lookup — 2 次, 19天前
- vector-search-setup — 1 次, 5天前

**docs/**
- mcp-builder — 3 次, 25天前
- office-docx — 3 次, 25天前
- office-pdf — 3 次, 25天前
- office-pptx — 3 次, 25天前
- office-xlsx — 3 次, 25天前
- telegram-bot — 1 次, 20天前

**frontend/**
- frontend-design — 2 次, 26天前
- ios-integration — 1 次, 27天前
- swiftui-patterns — 1 次, 27天前
- ui-ux-pro-max — 3 次, 25天前

**git/**
- auto-stage — 1 次, 9天前
- repo-rename — 1 次, 9天前

**meta/**
- audit-fix — 1 次, 23天前
- ci-pipeline — 1 次, 23天前
- deploy — 1 次, 23天前
- dev-process-gate — 3 次, 23天前
- init-project — 2 次, 26天前
- knowledge-graph — 1 次, 20天前
- plan-check-style — 3 次, 23天前
- session-harvest — 1 次, 20天前
- setup-permissions — 3 次, 23天前
- skill-creator — 2 次, 26天前
- skill-scout — 1 次, 20天前
- sync-readme — 1 次, 4天前

**quality/**
- de-slopify — 1 次, 20天前
- large-file-refactor — 1 次, 5天前
- protect-secrets — 1 次, 9天前
- qa-auto — 1 次, 20天前
- qa-planner — 1 次, 20天前
- qa-testing — 1 次, 25天前

**workflow/**
- agent-observability — 1 次, 10天前
- autoresearch — 1 次, 11天前
- candidate-analysis — 1 次, 9天前
- claude-to-telegram — 1 次, 20天前
- context-recovery — 1 次, 20天前
- crm-projection — 1 次, 19天前
- customer-intel — 4 次, 19天前
- dispatching-parallel-agents — 3 次, 25天前
- executing-plans — 3 次, 25天前
- gdrive-to-skills — 2 次, 26天前
- investment-research — 3 次, 20天前
- keyword-discovery — 1 次, 11天前
- material-health — 1 次, 19天前
- mockup — 1 次, 27天前
- planning-with-files — 4 次, 21天前
- requirement — 1 次, 27天前
- sales-material — 1 次, 19天前
- settings-audit — 1 次, 10天前
- subsidy-scraper — 1 次, 19天前
- user-flow — 1 次, 27天前
- writing-plans — 3 次, 25天前

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
| vector-search-setup | 台灣公司登記查詢：findbiz.nat.gov.tw 基本資料、董監事、變更紀錄 |

### local

| Skill | 功能 |
|-------|------|
| gstack |  |
| gstack-autoplan |  |
| gstack-benchmark |  |
| gstack-browse |  |
| gstack-canary |  |
| gstack-careful |  |
| gstack-codex |  |
| gstack-connect-chrome |  |
| gstack-cso |  |
| gstack-design-consultation |  |
| gstack-design-html |  |
| gstack-design-review |  |
| gstack-design-shotgun |  |
| gstack-document-release |  |
| gstack-freeze |  |
| gstack-guard |  |
| gstack-investigate |  |
| gstack-land-and-deploy |  |
| gstack-learn |  |
| gstack-office-hours |  |
| gstack-plan-ceo-review |  |
| gstack-plan-design-review |  |
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
| sync-readme | 從 Clawdbot/OpenClaw 生態系搜尋、評估、移植 skills |

### quality

| Skill | 功能 |
|-------|------|
| large-file-refactor | 移除 AI 生成的 slop 痕跡（含繁中模式：值得注意的是…） |

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

- **[docs]**: office-docx office-pdf office-pptx office-xlsx — 建議檢查邊界是否清楚
- **[meta]**: audit-fix ci-pipeline deploy dev-process-gate init-project plan-check-style setup-permissions skill-creator sync-readme — 建議檢查邊界是否清楚
- **[workflow]**: dispatching-parallel-agents executing-plans planning-with-files requirement user-flow writing-plans — 建議檢查邊界是否清楚

## 專案儀表板

### Family-Fiscal

| | |
|---|---|
| **狀態** | 🔥 活躍 — 22 個 commit（本週）, 24 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) |
| **Git** | 3 dirty, 3 unpushed |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | no CLAUDE.md | **權限** | **missing** |

<details><summary>近期 commits</summary>

```
1b75c34 Refactor data model to account-centric cashflow architecture
5147e52 fix(data): correct bank_account_id for Peter's 3 FCN investments
accb6ac fix(data): restore missing coupon returns for Grace's 14 FCNs; redesign CouponTimeline
727fe10 feat(investments): show active-only by default, move matured to history
8b52bdf feat(assets): add bank account balance editing and admin management tab
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
| **狀態** | 💤 沉寂 — 0 個 commit（本週）, 1 個（本月） |
| **技術棧** |  Python |
| **分支** | `main` (1 total) |
| **Git** | clean |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | OK | **權限** | OK (10 rules) |

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
| **狀態** | ✅ 近期有動 — 1 個 commit（本週）, 2 個（本月） |
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
| **狀態** | 💤 沉寂 — 0 個 commit（本週）, 10 個（本月） |
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
| **狀態** | ✅ 近期有動 — 4 個 commit（本週）, 5 個（本月） |
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
| **狀態** | 🔥 活躍 — 22 個 commit（本週）, 178 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `main` (1 total) |
| **Git** | 31 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | no CLAUDE.md | **權限** | OK (9 rules) |

<details><summary>近期 commits</summary>

```
6169273 feat: /design-html works from any starting point (v0.15.1.0) (#734)
562a675 feat: Session Intelligence Layer — /checkpoint + /health + context recovery (v0.15.0.0) (#733)
8115951 feat: recursive self-improvement — operational learning + full skill wiring (v0.13.8.0) (#647)
db35b8e feat: session intelligence roadmap + design doc (#727)
7ea6ead fix: ship idempotency + skill prefix name patching (v0.14.3.0) (#693)
```
</details>

### news_stock

| | |
|---|---|
| **狀態** | ✅ 近期有動 — 3 個 commit（本週）, 43 個（本月） |
| **技術棧** |  Docker Node.js Python |
| **分支** | `main` (1 total) |
| **Git** | 4 dirty |
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

### sales-assistant

| | |
|---|---|
| **狀態** | 🔥 活躍 — 10 個 commit（本週）, 112 個（本月） |
| **技術棧** |  Docker Node.js Python |
| **分支** | `main` (2 total) |
| **Git** | 676 dirty |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ✅ |
| **Config** | OK | **權限** | OK (32 rules) |

<details><summary>近期 commits</summary>

```
cfc3dfd refactor(contacts): extract CreateClientModal and CreatePartnerModal components
e0575e1 refactor(deals): split DealDetailPage into focused components
5a334e8 feat: audio transcription → intel (Whisper API)
27b92ca fix(qa): ISSUE-001 — fix hydration mismatch on all pages
faca5b4 chore: stage all in-progress changes before QA run
```
</details>

### workspace

| | |
|---|---|
| **狀態** | ⏸️ 暫停 — 0 個 commit（本週）, 0 個（本月） |
| **技術棧** |  Node.js |
| **分支** | `` (0 total) |
| **Git** | no git |
| **CI/CD** | CI ❌ · 部署 ❌ · Hooks ❌ |
| **Config** | **missing** | **權限** | OK (5 rules) |

**2 個專案問題待處理。**
## Agent 健康狀態

| 專案 | Agent | 排程 | 狀態 | 最近 Exit |
|---------|-------|----------|--------|-----------|
| news_stock | research-agent | daily 7:30 | ● loaded | 1 |
| news_stock | research-agent-weekly | weekly 10:00 | ● loaded | 0 |
| news_stock | maintainer | daily 4:00 | ○ unloaded | — |
| news_stock | tester | daily 5:00 | ○ unloaded | — |
| news_stock | developer | weekly 3:00 | ○ unloaded | — |
| rivendell | maintain | daily 22:00 | ● loaded | 0 |
| rivendell | harvest | interval :00 | ● loaded | 0 |
| rivendell | tester | daily 6:00 | ● loaded | 1 |
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
    x-axis ["03-29", "03-30", "03-31", "04-01", "04-02", "04-03", "04-04"]
    y-axis "USD" 0 --> 650
    bar [12, 567, 326, 116, 151, 0, 0]
~~~

| 日期 | Sessions | API 呼叫 | Tokens | 預估花費 |
|------|----------|-----------|--------|-----------|
| 2026-03-29 (Sun) | 7 | 70 | 3.1M | $11.97 |
| 2026-03-30 (Mon) | 20 | 2,464 | 223.5M | $566.82 |
| 2026-03-31 (Tue) | 16 | 1,628 | 135.9M | $325.53 |
| 2026-04-01 (Wed) | 7 | 583 | 47.9M | $115.51 |
| 2026-04-02 (Thu) | 13 | 748 | 64.6M | $150.57 |
| 2026-04-03 (Fri) | 5 | 3 | 0 | $0.00 |
| 2026-04-04 (Sat) | 2 | 2 | 0 | $0.00 |
| **Total** | | | **475.0M** | **$1170.40** |

### 各專案花費（7 日）

| 專案 | API 呼叫 | Tokens | 預估花費 |
|---------|-----------|--------|-----------|
| Family-Fiscal | 2,166 | 202.5M | $451.20 |
| -Users-manibari-Documents-Projects | 1,401 | 127.3M | $313.60 |
| rivendell | 728 | 58.3M | $142.96 |
| sales-assistant | 483 | 34.9M | $97.77 |
| news-stock | 261 | 22.5M | $73.75 |
| curia | 237 | 18.8M | $55.16 |
| news_stock | 19 | 453K | $30.48 |
| -Users-manibari-Documents-Chimes-AI-SDP | 70 | 4.1M | $13.03 |
| -Users-manibari-Documents-Chimes-AI-sabre | 68 | 3.6M | $9.68 |
| 3DGS | 35 | 1.2M | $7.36 |
| -Users-manibari-Documents-Chimes-AI-bp | 38 | 1.5M | $4.78 |
| -Users-manibari-Documents-Chimes-AI-richwave | 8 | 162K | $0.62 |
| -Users-manibari | 2 | 36K | $0.30 |
| rivendell-dashboard-next-api | 1 | 20K | $0.19 |

_計價: Opus input $15/M, output $75/M, cache create $18.75/M, cache read $1.50/M_


---

*由以下工具產生 `./bin/sk audit` — 2026-04-04 — 65 skills, 19 issue(s)*
