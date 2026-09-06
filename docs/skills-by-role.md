# Skills by Role — 你是誰，就從哪一頁開始

> 這頁是給**使用者**看的視角，不是給 skill 目錄用的分類。skill 實體照循環放在 `skills/<loop>/`（見 README Skills Catalog），
> 這裡只回答一個問題：**我現在扮演什麼角色、手上這件事走到哪一步、該叫哪支 skill**。
> 同一支 skill 出現在多個角色是正常的；一個人一天也會換好幾個角色。
>
> 每個角色一套 **PDCA**：Plan（想清楚要做什麼）→ Do（做出來）→ Check（驗證、審查）→ Act（收尾、沉澱、下一輪）。
> 每列是「情境 → 用誰 → 一句話」，順序照一件事從頭到尾。標 `(gstack)` 的是外部 gstack skill，不在本 repo。
>
> 維護規則：新 skill 進來要在這頁至少出現一次；`sk check` 會列出沒被任何角色收編的 skill。
> 更新：2026-09-06。

---

## 角色索引

| 角色 | 你在做什麼 | 主要循環 / 資料夾 |
|---|---|---|
| [1. 產品開發者](#1-產品開發者) | 蓋新產品、加功能、修 bug、部署 | dev · planning · backend · frontend · git |
| [2. QA／驗收者](#2-qa驗收者) | 驗收自己、別人或 AI 寫的東西；接手 code | qa · quality |
| [3. 業務／Presales](#3-業務presales) | 找客戶、情蒐、做提案 deck、kickoff | sales · docs 簡報類 |
| [4. 顧問／報告與標案撰寫](#4-顧問報告與標案撰寫) | 政府案、SOW、廠務報告、Word / Google Docs 交付 | gov · docs 文件類 |
| [5. 分析師／投資研究](#5-分析師投資研究) | 從資料算東西、畫數據圖、財報、ML 平台 | invest · chart-design data 類 |
| [6. 人資](#6-人資) | JD、履歷分析、內部公告 | hr |
| [7. 知識工作者](#7-知識工作者) | 看影片、讀文件、整理成可查的筆記 | knowledge |
| [8. 平台維護者](#8-平台維護者) | 維護 rivendell 本身：skill、agent、排程、hook | platform · agents · workflow |

橫向共用（每個角色都會碰到）：`task-brief`（開工前先定義任務、判斷階段）、`say-it-plain`（把話講清楚）、`knowledge-graph`（記住人／公司／專案的事實）、`context-journal` / `context-recovery`（長 session 不掉 context）、`session-wrap`（收工）。

---

## 1. 產品開發者

你在做：蓋一個新產品，或在既有產品上加功能、修 bug、重構、部署。對應 `~/.claude/CLAUDE.md` 的「UI Feature / New Page」與「Backend-only / Bug Fix」兩條流程。

### Plan — 想清楚要做什麼

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 接到一句「幫我做 X」，還不知道在哪個階段 | `task-brief` | 先判斷思考／探索／決定／執行，執行才產五欄位 brief |
| 這值不值得做、產品層面的質疑 | `gstack-office-hours` (gstack) | YC 式反問，不產草稿 |
| 定 user story 與驗收標準 | `requirement` | 結構化需求 |
| 新產品 / 新 web app 起手 | `app-ops-baseline` | 注入 roadmap / logs / changelog / feedback / api-keys / settings 基線 |
| 全新 repo 要有 CLAUDE.md、AGENTS.md | `init-project` | 初始化專案設定 |
| 減少權限彈窗 | `setup-permissions` | 只放專案真的用到的工具 |
| 畫使用者操作路徑（畫面切換、錯誤分支） | `user-flow` | Mermaid 旅程圖，之後 qa-journey 照著走 |
| 畫給工程師看的系統架構、時序、狀態機 | `mermaid-diagram` | .mmd → PNG，圖要 argue 不是 display |
| 新前端／新頁面 | `chimesflow-design` → `mockup` → `frontend-design` | 先鎖設計系統，再出 wireframe，再做 |
| 挑風格、色盤、字型 | `ui-ux-pro-max` | 設計資料庫 |
| 進 plan mode 做 UI 任務 | `plan-check-style` | 自動載入對應風格慣例 |
| 寫給零 context 工程師的實作計畫 | `writing-plans` | 小任務切分 |
| 多步驟、要追蹤進度的專案 | `planning-with-files` | task_plan / findings / progress 三檔 |
| 跳過需求／設計直接要 code | `dev-process-gate` | 擋下來，補前置 |
| 加後端功能前先決定同步 / 非同步 / 多輪 pipeline | `backend-async-jobs` | 分級決策，不要一律開 job |

### Do — 做出來

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 照計畫分批執行、每批 review | `executing-plans` | 有 checkpoint 的執行 |
| 加登入、JWT、密碼 | `spine-auth` | fleet 收斂的 crypto core + 每產品自決的 token 政策 |
| 加角色權限 | `spine-rbac`（決策）→ `rbac-permissions`（實作） | 先選 Tier-1 寫死或 Tier-2 矩陣，再做 |
| DB schema 變更、dev↔prod 同步 | `spine-schema-sync` → `db-migration` | Alembic，deploy 在 serve 前跑 upgrade head |
| 版本號、changelog、忘記 bump | `spine-versioning` | 核心是 pre-push 閘門 |
| 多服務 Docker 起手 | `docker-compose-setup` | Next.js + FastAPI + Postgres/Redis |
| SQLite 搬到 Postgres | `sqlite-to-postgres` | 語法差異、資料搬遷、驗證 |
| 向量搜尋、知識庫 | `vector-search-setup` | embedding 選型到 API |
| 收發 email | `imap-smtp-integration` | FastAPI 內建 IMAP/SMTP |
| 串第三方 OAuth、存 token | `oauth-token-vault` | Fernet 加密儲存 |
| Telegram bot | `telegram-bot` | grammY 或 python-telegram-bot |
| 做 MCP server | `mcp-builder` | FastMCP 模式 |
| Firebase / Firestore | `firebase-backend` | schema、rules、deploy |
| 語音上傳轉逐字稿功能 | `audio-transcription-flow` | 上傳 → STT → 顯示 |
| 拍照給 AI 抽結構 | `ai-vision-extract` | identify → normalize → cache → persist |
| 半結構資料要人可編、程式可查 | `markdown-file-ssot` | Markdown + frontmatter 當 SSOT |
| iOS：SwiftUI 架構、系統整合 | `swiftui-patterns` · `ios-integration` | MVVM、Extension、Deep Link |
| 500 行以上的大檔要拆 | `large-file-refactor` | 保介面拆模組 |
| 多個 Claude session 共用一個 working tree | `concurrent-session-git` | 不要把別人的改動掃進自己的 commit |
| merge / rebase 卡衝突 | `resolving-merge-conflicts` | 回到兩邊意圖，用專案自己的檢查證明結果 |
| 3 個以上獨立問題要平行修 | `agent-dispatch` | 每個 agent 一個 worktree |
| 被 bug 擋住 | `gstack-investigate` (gstack) | 先找根因 |
| 重構時保護穩定區 | `gstack-freeze` / `gstack-unfreeze` (gstack) | 鎖住不該動的 |
| 危險指令前 | `gstack-careful` (gstack) | rm、force push 前的護欄 |

### Check — 驗證與審查

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 功能做完，要出 QA 計畫 | `qa-planner` → `qa-auto` | 影響分析 → 自動產測試並跑 |
| 寫測試、選 mock 策略 | `qa-testing` | pytest / Vitest / Swift Testing |
| 像真使用者走一遍 UI | `qa-journey` | persona 驅動的旅程測試 |
| 這次動到資料寫入 / 跨模組 / 新 store | `qa-dataflow` | 功能關係圖 + 反證關卡有沒有牙齒（HARD GATE） |
| commit 前看 diff | `gstack-review` (gstack) | 差異審查 |
| 想要獨立第二意見 | `gstack-codex` (gstack) | Codex 看一次 |
| 另一台機器跑出來不一樣 | `env-doctor` | 產 doctor 腳本比環境 |
| 要給別人一份標準考題驗算法 | `repro-exam` | 輸入 → 期望輸出 |
| 架構圖放進交付物前 | `chart-design`（含 `check-html-figure.mjs`） | 套風格、字級、機械檢查、三欄收據 |

### Act — 部署、沉澱、下一輪

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 設 CI | `ci-pipeline` | 偵測 stack 生 GitHub Actions |
| 要上線 | `deploy` → `gstack-land-and-deploy` / `gstack-ship` (gstack) | 選平台、生設定，合併並部署 |
| 對外開一個新網域 | `cloudflare-tunnel-provision` | 從零建 tunnel |
| tunnel 掛了、搬機器 | `cloudflare-tunnel-ops` | 現有 tunnel 的維運 |
| FastAPI + Next.js 走 tunnel 的反代坑 | `tunnel-proxy-deploy` | trailing slash、CORS、port |
| 上線後盯回歸 | `gstack-canary` (gstack) | 部署後監控 |
| 版本動了，CHANGELOG / ROADMAP / CLAUDE.md 對不齊 | `doc-drift-sync` | 偵測並修文件漂移 |
| 上線後更新 README / docs | `gstack-document-release` (gstack) | 文件跟上 |
| 收工 | `session-wrap` | commit、歸檔 learnings、更新 progress |
| 踩到坑 | `self-improving-agent` | 記進對的 learnings 檔 |

常搭配：QA／驗收者（第 2 節）、平台維護者的 `agent-launchd`（要排程時）。

---

## 2. QA／驗收者

你在做：驗收一包程式碼，不管是自己寫的、外包的、還是 AI 生的。重點不是「跑得起來」，是「走的路對不對、關卡擋不擋得住」。

### Plan

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 先定義要驗什麼、成功長什麼樣 | `task-brief` | 完成定義要是「看得到證據」 |
| 從 diff 推要測哪裡、風險在哪 | `qa-planner` | 影響分析 + 測試案例 |
| 有 user-flow 圖，要決定旅程怎麼走 | `user-flow`（讀） | 旅程測試的劇本來源 |

### Do

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 從 QA 計畫產測試並執行 | `qa-auto` | 回報覆蓋缺口 |
| 手寫測試、測試策略 | `qa-testing` | 跨框架指引 |
| 模擬一個沒耐心的真使用者 | `qa-journey` | 找 UX 摩擦 |
| 接手 code、懷疑資料流走鐘、表沒人讀、閘門是裝飾 | `qa-dataflow` | 畫地圖 → 拔依賴反證 → 只釘重要接縫 |
| 整個 repo 健康度 | `github-repo-audit` | 結構、文件、CI、依賴打分 |
| 拿外部 skill 集（如 matt-skills）審自己的 code | `skill-apply` | 把外部 skill 當 review 鏡片 |
| 跨機器結果不一致 | `env-doctor` · `repro-exam` | 比環境、比考題 |
| headless 瀏覽器跑 UI 流程 | `gstack-qa` / `gstack-qa-only` (gstack) | 修或只報告 |
| 安全審計 | `gstack-cso` (gstack) | 上線前 |

### Check

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 產出的功能關係圖要交付 | `chart-design` 的 `check-html-figure.mjs` | 重疊、wrap、字級、溢出的機械診斷 |
| 視覺一致性 | `gstack-design-review` (gstack) | 設計走鐘 |
| 報告文字給委員或客戶看 | `de-slopify`（審查文體模式） | 去 AI 腔、去內部代號 |

### Act

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 落差報告交回開發者 | `qa-dataflow` 的 gap-report 模板 | 附「不要動壞的東西」那節 |
| 500 行大檔的重構建議 | `large-file-refactor` | 交給開發者執行 |
| 文件跟實作對不齊 | `doc-drift-sync` | 回頭修文件 |

常搭配：產品開發者（第 1 節）。

---

## 3. 業務／Presales

你在做：從一家公司的名字開始，到第一次拜訪、提案 deck、簽 NDA 後 kickoff。對應 CLAUDE.md 的「Slide / Deck Building」流程，storyline-first 是硬閘門。

### Plan — 情蒐與定位

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 新客戶進來 | `presales-pipeline` | 建 `01_presales/<client>/` 標準資料夾 |
| 查公司登記、董監事 | `tw-company-lookup` | findbiz 官方資料 |
| 會前情蒐、猜製程與業務流程 | `sales-customer-intel` | operator-level 推測 > 公開資料轉述 |
| 跟客戶對話挖最痛的手工流程 | `discovery-interview` | 30 分鐘訪談腳本 |
| 把客戶的業務知識變 schema | `metadata-workshop` | 第二個同業客戶可重用七成 |
| 爬蟲關鍵字一直漏 | `sales-keyword-discovery` | 從漏網之魚找新詞 |
| 這個提案值不值得做 | `gstack-office-hours` (gstack) | 反問模式 |

### Do — 做提案

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 從素材庫組客製提案 | `sales-material` | 情蒐 + 案例 + 方案 + 補助 |
| 你寫 storyline，AI 補洞 | `slide-workflow` | 七階段閘門 |
| storyline 紅隊審查 | `slide-office-hours` | 沒 signed-off 不准生成 |
| 客戶 sales / 導入提案要像企業提案 | `sales-deck-design` | 暖色乾淨、16:9、自截圖驗證 |
| 投資人 BP | `pitch-deck` | 含 discovery 與敘事規劃 |
| 有參考 PPTX 要鎖風格 | `slide-template-extractor` | 抽成 HTML 模板 |
| deck 裡的圖表 / 架構圖 | `chart-design` → `excalidraw-diagram` / `mermaid-diagram` | 先 triage 再畫，套風格檔 |
| 出 PPTX | `office-pptx` | html2pptx |
| 出 Google Slides | `gdoc-report-builder` | MCP 批次寫入 |
| 繁中打磨、講者備註 | `de-slopify` · `say-it-plain` | 去 AI 腔、結論先行 |
| 簽完 NDA 要 kickoff | `sales-client-kickoff-docs` | 三件套專案初始檔 |
| 報價 | `gov-rfq-writer` | 比 SOW 輕的報價單 |

### Check

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 素材庫有沒有過期補助、缺 frontmatter | `sales-material-health` | 排程跑 |
| deck 視覺一致性 | `gstack-design-review` (gstack) | 出貨前 |
| 圖檔切版、字級 | `chart-design` 的 `check-html-figure.mjs` | 機械檢查 + 截圖 |

### Act

| 情境 | 用誰 | 一句話 |
|---|---|---|
| CRM 資料投影到本機 markdown | `sales-crm-projection` | 每日排程 |
| 客戶的人、決策、里程碑 | `knowledge-graph` | 記成可查事實 |
| 案子 archive / lost | `presales-pipeline` | 狀態流轉 |

常搭配：顧問（第 4 節，SOW 與標案）、知識工作者（第 7 節，客戶影片與文件消化）。

---

## 4. 顧問／報告與標案撰寫

你在做：政府標案與補助、SOW、廠務報告、給委員或客戶老闆看的文字交付物。對應 CLAUDE.md 的「Text Report Generation」流程。

### Plan — 找案、定框架

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 找標案 | `gov-tender-scraper` | g0v API，排程 |
| 找補助 | `gov-subsidy-scraper` | 政府入口去重 |
| 定任務與交付定義 | `task-brief` | 五欄位 brief |
| 客戶業務知識梳理 | `metadata-workshop` · `discovery-interview` | schema 與痛點 |
| 官方計畫書的章節代碼當頂層框架 | `gov-subsidy-writer` 的目錄 framing | 先讀官方 SOT 全文再引用代碼 |

### Do — 寫

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 補助計畫書（SBIR、數產署） | `gov-subsidy-writer` | 分項 → 拍板 → 紅字 → docx，Phase 8 審查意見回覆 |
| 詢價 / 規格回覆 | `gov-rfq-writer` | 報價單 |
| 工作說明書 | `sow-writer` | 台灣格式 12 節，含 Gantt |
| 多方利害關係人的長文件 | `doc-coauthoring` | Context → Refinement → 新 Claude 讀者測試 |
| 交付到 Google Docs | `gdoc-report-builder` | 表格、樣式、分享 |
| IoT / SCADA 時序 → 報告 + PPTX | `iot-factory-report` | UPW、壓縮機、冷凍機 |
| 專案週報、3P、事故報告 | `internal-comms` | 模板 |
| 舊文件（doc / pdf / xlsx）抽成結構資料 | `doc-to-structured-data` | 先偵測格式再選策略 |
| Word / PDF / Excel 產出 | `office-docx` · `office-pdf` · `office-xlsx` | 各自格式 |
| 文件裡的圖表、架構圖 | `chart-design`（入口）→ `mermaid-diagram` / `excalidraw-diagram` | Word 內嵌圖不是 slide，尺寸另算 |

### Check — 審查文體

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 給委員看，掃內部策略痕跡、英文行話、自評 | `de-slopify` 審查文體模式 | 「這是最關鍵的一題」這種要拿掉 |
| 結論沒先講、術語沒解釋 | `say-it-plain` | BLUF 重寫 |
| 圖檔切版、字級、留白 | `chart-design` 的 Post-check + `check-html-figure.mjs` | 三欄收據 |

### Act

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 審查意見回來 | `gov-subsidy-writer` Phase 8 | 意見 → 審查會議簡報 |
| 客戶、案子、委員的事實 | `knowledge-graph` | 下次不用重查 |
| 域內還沒有 skill 的報告類型（市調、EHS、排程） | `doc-coauthoring` 通用模式 | 接到真案子再抽 skill，見 `.learnings/FEATURE_REQUESTS.md` |

常搭配：業務（第 3 節）、分析師（第 5 節，數據圖）。

---

## 5. 分析師／投資研究

你在做：從資料算出東西，畫數據圖，做財報或製程分析；或在建 ML / AutoML 平台。

### Plan — 拿到資料

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 台股財務三表、月營收 | `mops-financial-scraper` | MOPS → SQLite / DuckDB |
| 非結構文件變表 | `doc-to-structured-data` | CSV / JSON |
| IC 批號、產品碼要標準化 | `ic-lot-normalization` | YMS / ETL 的領域參考 |
| PCB ODB++ 解析、DFM | `odb-dfm-reference` | 製造端 EDA 的坑 |
| 定義目標、指標、驗證指令 | `task-brief` · `autoresearch` 前置 | 可量測才能迭代 |

### Do — 算與畫

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 持續追蹤持股、回測、風險 | `invest-research` | 本機 news_stock + 自主搜尋 |
| 廠務時序：週期偵測、異常 | `iot-factory-report` | 圖 + PPTX |
| 數據圖（趨勢、分佈、相關、占比） | `chart-design` data 類 | matplotlib / plotly / ECharts，R1–R4 |
| 試算表分析與公式 | `office-xlsx` | .xlsx / .csv |
| ML 平台的評估與品質層 | `ml-eval-quality` | 指標分派、小資料 CV 閘門 |
| ML 平台的模型登錄與治理 | `ml-model-registry` | run → 版本 → 生命週期 |
| 慢的分析要不要丟背景 | `backend-async-jobs` | 分級 |
| 讓 agent 自己迭代到指標變好 | `autoresearch` | modify → verify → keep/discard |

### Check

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 兩台機器算出來不一樣 | `repro-exam` · `env-doctor` | 先比考題再比環境 |
| 圖能不能看、有沒有截軸誤導 | `chart-design` Post-check | R3 同軸同單位 |
| 平台的資料流真的照宣稱跑嗎 | `qa-dataflow` | 治理欄位有沒有牙齒 |

### Act

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 分析結論、公司事實 | `knowledge-graph` | 沉澱 |
| 報告交付 | 顧問（第 4 節）的 `gdoc-report-builder` / `office-docx` | 換角色 |

常搭配：顧問（第 4 節）、產品開發者（第 1 節，ML 平台後端）。

---

## 6. 人資

你在做：開缺、看履歷、發內部公告。

### Plan

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 從組織需求推職缺 | `hr-jd-writer` 前段 | 職責、必備、加分、職涯 |

### Do

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 寫 JD、招募文 | `hr-jd-writer` | 結構化 JD |
| 公告、newsletter、FAQ | `internal-comms` | 模板 |
| 文字去 AI 腔 | `de-slopify` | 對外前 |

### Check

| 情境 | 用誰 | 一句話 |
|---|---|---|
| PDF 履歷抽結構、看 GitHub 程式品質 | `hr-candidate-analysis` | 產候選人 profile |
| 候選人的 repo 健康度 | `github-repo-audit` | 打分 |

### Act

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 候選人、面試決策 | `knowledge-graph` | 記事實 |

---

## 7. 知識工作者

你在做：消化外部內容（影片、錄音、文件），變成 `knowledge/` 裡可查的筆記。`knowledge/` 是內容摘要庫，`knowledge-graph` 是實體事實庫，兩者不同。

### Plan — 決定看什麼

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 訂閱頻道、UP 主、podcast，自動掃新集 | `yt-channel-scraper` | 掃到就歸檔 |
| Google Drive 裡的文件要變 skill | `gdrive-to-skills` | 讀、分類、建 skill |

### Do — 消化

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 線上影片：摘要、繁中文章、翻譯 | `video-transcript` | 抓真字幕，比 ASR 準 |
| 本機錄影、錄音、螢幕錄製 | `local-media-transcribe` | mlx-whisper 離線，含畫面取樣 |
| 要字幕檔（srt / vtt）保留時間軸 | `subtitle-file` | 雙語、翻譯不掉軸 |
| 只要影片某一段 | `video-clip-extract` | 不下載全片 |

### Check

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 這份筆記能信幾分 | 筆記 frontmatter 的 reliability 標記 | 手動字幕 ✅ / 自動字幕 ⚠️ / whisper 🤖 |
| INDEX 有沒有更新 | `knowledge/videos/INDEX.md`（自動重生） | 每次寫入重生 |

### Act

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 內容裡提到的人、公司、決策 | `knowledge-graph` | 從摘要庫抽到事實庫 |
| 看完發現可以做成 skill | `session-harvest` | 交給平台維護者 |

常搭配：業務（客戶的公開影片）、平台維護者。

---

## 8. 平台維護者

你在做：維護 rivendell 本身，讓 skill、agent、排程、hook 一直可用。這是 `platform` 循環，也是唯一有完整 PDCA 覆蓋的循環。

### Plan — 決定要加什麼

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 想找外面有沒有現成 skill | `skill-scout` | 搜 → 評估 → port → 驗證 |
| 寫 skill 前先讀原則 | `writing-great-skills` | model-invoked vs user-invoked |
| 要建一個新 agent 角色 | `agent-persona` | tester / maintainer / reviewer 的 prompt |
| 先定義任務 | `task-brief` | 五欄位 |

### Do — 建與接線

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 從零建、改、評測 skill | `skill-creator` | 含 eval 與 trigger 優化 |
| 拿外部 skill 集審自己的東西 | `skill-apply` | 不裝也能用 |
| 排程 agent（launchd plist） | `agent-launchd` | 用 `launchctl bootout / bootstrap`，不要 kill |
| 無人值守跑 Claude Code | `agent-headless` | 結構化 log、輸出管理 |
| 讓腳本 agent 在 dashboard 看得到 | `agent-observability` | 執行歷史、live log |
| 多個獨立修復平行跑 | `agent-dispatch` | 各自 worktree |
| 從手機遙控 session | `claude-to-telegram` | ask_user 走 Telegram |
| settings.local.json 亂了 | `settings-audit` · `setup-permissions` | 清無效權限、只放用到的 |
| 自動 stage、擋 .env | `auto-stage` · `protect-secrets` | hook，不用手動叫 |
| README 目錄跟 skill 對不上 | `sync-readme` | 新 skill 進表；描述改了要手動改那列 |
| 長 session 保護 | `context-journal` · `context-recovery` | compact 不掉 context |
| 讓 agent 自己迭代到指標變好 | `autoresearch` | 夜間跑 |
| repo 改名 | `repo-rename` | plist、settings、sibling repo 全掃 |

### Check — 健康與漂移

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 每日健康 | `bin/sk check` · `bin/sk maintain` | symlink、frontmatter、agent、磁碟 |
| audit 報告有問題要修 | `audit-fix` | 自動修權限問題 |
| 這個 session 有沒有可抽的 skill | `session-harvest` | 告一段落時跑 |
| CHANGELOG / ROADMAP / CLAUDE.md 對不齊 | `doc-drift-sync` | 版本動就跑 |
| 素材庫、reports 過期 | `sales-material-health` · `sk reports-janitor` | 排程 |

### Act — 沉澱與回顧

| 情境 | 用誰 | 一句話 |
|---|---|---|
| 踩坑、被糾正、知識過期 | `self-improving-agent` | 分流到對的 learnings vault |
| 各專案 learnings 堆太多 | `learnings-promotion-sprint` | 跨專案蒸餾，升進 CLAUDE.md |
| 每週回顧下一個瓶頸 | `workflow-retro` | 讀 telemetry，出 1–3 個 action |
| 收工 | `session-wrap` | commit、歸檔、progress |
| gstack 有新版 | `gstack-upgrade` (gstack) | 升級 |
| 學到東西 | `gstack-learn` (gstack) | 記進 gstack |

---

## 覆蓋檢查

`bin/sk check` 會列出 `skills/*/*/SKILL.md` 中沒有在這頁出現的 skill 名稱。新 skill 進來，或改名後，這裡要跟著補。
角色不需要互斥；一支 skill 出現在三個角色是資訊，不是錯誤。
