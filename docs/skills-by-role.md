# Skills by Role — 角色 → 工作 → PDCA

> 給**使用者**看的視角。skill 實體照循環放在 `skills/<loop>/`（見 README Skills Catalog），
> 這頁回答：**我是誰 → 我手上是哪一件工作 → 這件工作走到哪一步 → 該叫誰**。
>
> 三層：**角色**（你是誰）→ **工作**（同一個角色會有好幾條不同的路徑，例如業務的陌生開發、客製提案、募資、kickoff 各走各的）→ **PDCA**（每件工作自己的 Plan / Do / Check / Act）。
> 每格「用誰」分三段：**主線**（必經，照順序）｜**視情況：**（有那個條件才叫）｜**自動：**（hook 或 gate，自己會跳出來，不用叫）。
> `★` 代表這一步還沒有 skill（缺環）。標 `(gstack)` 的是外部 gstack skill。
> 同一支 skill 出現在多個角色、多件工作是正常的。
>
> 維護規則：新 skill 進來要在這頁至少出現一次；`sk check` 會列出沒被收編的 skill。
> 某件工作需要更細的展開（狀態機、資料欄位、缺口優先序），另開 `docs/loops/<loop>-<工作>.md`，這裡只連過去。
> 更新：2026-09-07。

---

## 角色索引

| 角色 | 工作 |
|---|---|
| [1. 產品開發者](#1-產品開發者) | 1a 新產品起手 · 1b 新功能／新頁面 · 1c 後端功能／修 bug／重構 · 1d 部署與上線 · 1e iOS app |
| [2. QA／驗收者](#2-qa驗收者) | 2a 接手或驗收別人／AI 的 code · 2b 功能完成後的 QA · 2c 使用者旅程測試 · 2d 跨機器重現 |
| [3. 業務／Presales](#3-業務presales) | 3a 陌生開發到第一次拜訪 · 3b 客戶客製提案 · 3c 投資人募資 BP · 3d 簽約與 kickoff · 3e 素材庫與 CRM 維護 |
| [4. 顧問／報告與標案撰寫](#4-顧問報告與標案撰寫) | 4a 政府標案 · 4b 政府補助計畫 · 4c 顧問案交付文件 · 4d 客戶資料梳理 |
| [5. 分析師／投資研究](#5-分析師投資研究) | 5a 投資研究 · 5b 廠務時序分析 · 5c ML／AutoML 平台 · 5d 製造領域資料 · 5e 自動迭代實驗 |
| [6. 人資](#6-人資) | 6a 開缺 · 6b 履歷篩選 · 6c 內部公告 |
| [7. 知識工作者](#7-知識工作者) | 7a 訂閱與掃描 · 7b 單支影片／錄音消化 · 7c Drive 文件變 skill |
| [8. 平台維護者](#8-平台維護者) | 8a 新增或修改 skill · 8b 排程 agent · 8c session 與環境 · 8d repo 維運 |

橫向共用（每個角色、每件工作都會碰到）：`task-brief`（開工前先定義任務、判斷階段）、`say-it-plain`（把話講清楚）、`knowledge-graph`（記住人／公司／專案的事實）、`context-journal` / `context-recovery`（長 session 不掉 context）、`session-wrap`（收工）、`self-improving-agent`（踩坑就記）。

畫圖不分角色，一律從 `chart-design` 進：它 triage 後轉 `mermaid-diagram`（工程師看）或 `excalidraw-diagram`（簡報用）；使用者旅程用 `user-flow`；要驗證資料流用 `qa-dataflow`。

---

## 1. 產品開發者

你在做：蓋新產品、加功能、修 bug、重構、部署。對應 `~/.claude/CLAUDE.md` 的「UI Feature / New Page」與「Backend-only / Bug Fix」。

### 1a 新產品起手（greenfield）

| | 用誰 | 說明 |
|---|---|---|
| Plan | `task-brief` → `requirement` → `user-flow` → `mockup` → `app-ops-baseline` ｜ 視情況：`gstack-office-hours` (gstack)、`discovery-interview`、`chimesflow-design`、`ui-ux-pro-max` ｜ 自動：`dev-process-gate` | 主線五步：定義任務 → 產品範圍與 user story → 第一條核心旅程 → 首頁 wireframe → 注入 ops 基線（roadmap / logs / changelog / feedback / api-keys / settings）。還沒想清楚值不值得做才叫 office-hours；有客戶才做 discovery；要接 ChimesFlow 設計系統才載 chimesflow-design |
| Do | product-skeleton clone → `init-project` → `spine-auth` → `spine-schema-sync` → `spine-versioning` ｜ 視情況：`spine-rbac`（多人用才需要）、`docker-compose-setup`、`markdown-file-ssot`、`setup-permissions` | 骨架已接好線，每個 spine 模組各有一個要自己決定的政策；init-project 建 CLAUDE.md / AGENTS.md |
| Check | `qa-testing` → `env-doctor` ｜ 視情況：`qa-journey`（第一條旅程能走通） | 測試策略；另一台機器跑得起來 |
| Act | `ci-pipeline` → `deploy` ｜ 視情況：`cloudflare-tunnel-provision`（要對外）｜ 自動：`doc-drift-sync` | 起手的 Act 就是第一次上線，之後進 1b / 1c 循環 |

### 1b 新功能／新頁面（UI）

| | 用誰 | 說明 |
|---|---|---|
| Plan | `task-brief` → `requirement` → `user-flow` → `mockup` → `writing-plans` ｜ 視情況：`gstack-office-hours` (gstack，值不值得做)、`chimesflow-design`（新前端）、`ui-ux-pro-max`（挑風格）、`planning-with-files`（多步驟要追蹤進度時取代 writing-plans）｜ 自動：`dev-process-gate`、`plan-check-style` | 主線五步；跳步會被 gate 擋；進 plan mode 做 UI 時 style 自動載入 |
| Do | `executing-plans` → `frontend-design` ｜ 視情況：`gstack-freeze` / `gstack-unfreeze` (gstack，重構時鎖穩定區) | 分批執行有 checkpoint |
| Check | `qa-planner` → `qa-auto` → `gstack-review` (gstack) ｜ 視情況：`qa-journey`（有旅程要走）、`qa-dataflow`（動到資料寫入時 HARD GATE）、`gstack-qa`、`gstack-design-review` (gstack) | QA 計畫 → 自動測試 → diff 審查 |
| Act | `gstack-land-and-deploy` / `gstack-ship` → `gstack-canary` → `gstack-document-release` (gstack) ｜ 自動：`spine-versioning` | 合併部署、盯回歸、更新文件；沒 bump 版本 push 會被擋 |

### 1c 後端功能／修 bug／重構

| | 用誰 | 說明 |
|---|---|---|
| Plan | `task-brief` → `gstack-investigate` (gstack，bug 才要) ｜ 視情況：`backend-async-jobs`（慢工作先決定同步 / job / pipeline）、`spine-rbac`（權限先選 tier） | 先找根因再動手 |
| Do | 對應功能的那一支 ｜ 視情況：`spine-auth` · `rbac-permissions` · `db-migration` · `sqlite-to-postgres` · `vector-search-setup` · `imap-smtp-integration` · `oauth-token-vault` · `telegram-bot` · `mcp-builder` · `firebase-backend` · `audio-transcription-flow` · `ai-vision-extract` · `large-file-refactor`（500 行以上）· `concurrent-session-git`（多 session 共用 tree）· `resolving-merge-conflicts`（卡衝突）· `agent-dispatch`（3 個以上獨立問題）｜ 自動：`gstack-careful` (gstack，破壞性指令前) | 一次只會用到其中一兩支，看功能是什麼 |
| Check | `qa-testing` → `gstack-review` (gstack) ｜ 視情況：`qa-dataflow`（資料流反證）、`gstack-codex` (gstack，第二意見)、`repro-exam`（要給人標準考題） | |
| Act | `deploy` → `gstack-canary` (gstack) ｜ 視情況：`gstack-benchmark` (gstack，動到請求路徑) ｜ 自動：`doc-drift-sync` | |

### 1d 部署與上線

| | 用誰 | 說明 |
|---|---|---|
| Plan | `deploy` ｜ 視情況：`ci-pipeline`（還沒有 CI） | 選平台、生設定 |
| Do | `cloudflare-tunnel-provision` → `tunnel-proxy-deploy` ｜ 視情況：`docker-compose-setup` | 從零開網域；FastAPI + Next.js 走 tunnel 的反代坑 |
| Check | `gstack-canary` (gstack) → `env-doctor` ｜ 視情況：`gstack-cso` (gstack，上線前安全審計) | 上線後回歸；環境一致 |
| Act | `cloudflare-tunnel-ops` ｜ 自動：`spine-versioning`、`doc-drift-sync` ｜ 視情況：`gstack-document-release` (gstack) | tunnel 掛了／搬機器 |

### 1e iOS app

| | 用誰 | 說明 |
|---|---|---|
| Plan | `requirement` → `user-flow` → `mockup` | 同 1b |
| Do | `swiftui-patterns` ｜ 視情況：`ios-integration`（Extension、Deep Link、地圖） | MVVM 為主 |
| Check | `qa-testing`（Swift Testing）→ `gstack-ios-qa` (gstack) ｜ 視情況：`gstack-ios-design-review` (gstack) | |
| Act | `gstack-ios-sync` ｜ 視情況：`gstack-ios-clean` (gstack) | |

工作之間怎麼接：1a 只跑一次，產出的是 repo（骨架接好 spine、CLAUDE.md、權限、CI、第一次部署），之後 1b 與 1c 都在它裡面反覆跑。1b 的計畫（writing-plans 任務清單）裡「要一個 endpoint」就是 1c 的輸入；1c 的 qa-dataflow 反證結果回到 1b 的 Check。1d 是每一輪 1b／1c 的 Act 都會經過的那段，獨立成一件工作是因為開網域、搬機器不綁任何功能。接縫都是檔案：requirement → user-flow 圖 → 任務清單 → QA 計畫（交 2b）→ 版本號與 CHANGELOG（spine-versioning 閘門擋沒 bump 的 push）→ 下一輪 1b。

常搭配：QA／驗收者（第 2 節）、平台維護者 8b（要排程時）。

---

## 2. QA／驗收者

你在做：驗收一包程式碼，不管是自己寫的、外包的、還是 AI 生的。重點不是「跑得起來」，是「走的路對不對、關卡擋不擋得住」。

### 2a 接手或驗收別人／AI 的 code

| | 用誰 | 說明 |
|---|---|---|
| Plan | `task-brief` · `github-repo-audit` | 完成定義要是「看得到證據」；先打 repo 健康分 |
| Do | `qa-dataflow` · `skill-apply` | 畫地圖 → 拔依賴反證 → 只釘重要接縫；拿外部 skill 集當 review 鏡片 |
| Check | `chart-design` 的 `check-html-figure.mjs` · `de-slopify`（報告給人看時） | 功能關係圖的機械檢查；報告文字 |
| Act | `qa-dataflow` gap-report（含「不要動壞的東西」）· `large-file-refactor`（建議）· `doc-drift-sync` | 落差報告交回開發者；文件對齊 |

### 2b 功能完成後的 QA

| | 用誰 | 說明 |
|---|---|---|
| Plan | `qa-planner` | 從 diff 推影響、測試案例、風險 |
| Do | `qa-auto` · `qa-testing` · `gstack-qa` / `gstack-qa-only` (gstack) | 產測試並跑；手寫測試；headless 瀏覽器跑 UI |
| Check | `gstack-review` · `gstack-cso` (gstack) | diff 審查；安全 |
| Act | 覆蓋缺口回 1b / 1c | |

### 2c 使用者旅程測試

| | 用誰 | 說明 |
|---|---|---|
| Plan | `user-flow`（讀） | 旅程劇本來源 |
| Do | `qa-journey` | 模擬沒耐心的真使用者，記 friction ledger |
| Check | `gstack-design-review` (gstack) | 視覺一致性 |
| Act | friction 回 1b | |

### 2d 跨機器重現

| | 用誰 | 說明 |
|---|---|---|
| Plan | `repro-exam` | 先出一組標準考題 |
| Do | `env-doctor` | 比環境、依賴 hash、模型檔 |
| Check | 逐 key 比覆蓋，不看總量 | CLAUDE.md gotcha：一個角落少一列是常見根因 |
| Act | doctor 腳本進 repo | |

---

## 3. 業務／Presales

你在做：從一家公司的名字開始，到第一次拜訪、客製提案、簽約 kickoff；另外還有募資、素材庫維護。對應 CLAUDE.md「Slide / Deck Building」，storyline-first 是硬閘門。**五條路徑各走各的，不要混。**

### 3a 陌生開發到第一次拜訪（B2B 首拜）

| | 用誰 | 說明 |
|---|---|---|
| Plan | `presales-pipeline`（建 client 檔）→ `tw-company-lookup` → `sales-customer-intel` → `metadata-workshop`（猜製程）· `gstack-office-hours` (gstack) | 公司登記；情蒐要 operator-level 猜製程與業務流程，不是轉述公開資料；值不值得追 |
| Do | storyline.md（**你寫**，AI 補洞）→ `slide-office-hours` → `slide-workflow` → `office-pptx` → `de-slopify` ｜ 視情況：`chart-design`（deck 有圖才進，它再轉 `excalidraw-diagram` / `mermaid-diagram`）、`gdoc-report-builder`（要出 Google Slides） | 通用流程 D：storyline 紅隊過了才生成；繁中打磨 |
| Check | `slide-office-hours`（`status: signed-off` 才准生成）· `gstack-design-review` (gstack) · `check-html-figure.mjs` | 硬閘門；視覺一致；圖檔切版與字級 |
| Act | `presales-pipeline`（active → 下一步）· `knowledge-graph` | 狀態流轉；人與決策記成事實 |

### 3b 客戶客製提案（已接觸，要提案）

| | 用誰 | 說明 |
|---|---|---|
| Plan | `discovery-interview` · `metadata-workshop` · `sales-customer-intel`（更新） | 挖最痛的手工流程；業務知識變 schema |
| Do | `sales-material` → `sales-deck-design` → `slide-workflow` ｜ 視情況：`slide-template-extractor`（有參考 PPTX 要鎖風格）、`gov-rfq-writer`（要附報價）、`chart-design`（有圖） | 從素材庫組裝；客製提案要像企業提案；報價比 SOW 輕 |
| Check | `slide-office-hours` · `sales-material-health`（素材沒過期）· `gstack-design-review` (gstack) | |
| Act | won → 3d；lost → `presales-pipeline` lost + 原因 · `knowledge-graph` | |

### 3c 投資人募資 BP

| | 用誰 | 說明 |
|---|---|---|
| Plan | `pitch-deck` 的 discovery interview · `gstack-office-hours` (gstack) | 敘事先於投影片 |
| Do | `pitch-deck` → `excalidraw-diagram`（示意圖）· `chart-design`（數據頁）· `office-pptx` | |
| Check | `slide-office-hours` · `de-slopify` | 案例去識別化（身分匿名、數字留具體） |
| Act | `knowledge-graph`（投資人、回饋） | |

### 3d 簽約與 kickoff

| | 用誰 | 說明 |
|---|---|---|
| Plan | `gov-rfq-writer` → `sow-writer` | 報價 → 工作說明書（12 節、Gantt、驗收、人天） |
| Do | `sales-client-kickoff-docs` | NDA 簽完，讀客戶 homework 建三件套 |
| Check | `de-slopify` 審查文體 · `say-it-plain` | 合約給客戶老闆看 |
| Act | `presales-pipeline` won · 轉顧問（第 4 節）或開發者（第 1 節） | 案子從 presales 變專案 |

### 3e 素材庫與 CRM 維護（排程）

| | 用誰 | 說明 |
|---|---|---|
| Plan | `sales-keyword-discovery` | 爬蟲關鍵字一直漏就跑 |
| Do | `sales-crm-projection` | CRM 投影到本機 markdown，每日 |
| Check | `sales-material-health` | 過期補助、缺 frontmatter、孤兒檔 |
| Act | 修素材、更新 keywords | |

---

## 4. 顧問／報告與標案撰寫

你在做：政府標案與補助、SOW、廠務報告、給委員或客戶老闆看的文字交付物。對應 CLAUDE.md「Text Report Generation」。

### 4a 政府標案 → 展開見 [docs/loops/gov-tender.md](loops/gov-tender.md)

| | 用誰 | 說明 |
|---|---|---|
| Plan | `gov-tender-scraper`（排程抓、過濾、歸檔、INDEX）· ★ **triage：要不要投**（fit 評分、資格門檻、go / no-go 與理由）· `tw-company-lookup`（機關、競爭者） | 現在 `status` 只有 active / archived，由截止日決定，不是由人的決定 |
| Do | `gov-rfq-writer`（報價）· `sow-writer` · ★ **投標文件／服務建議書 writer**（fallback `doc-coauthoring`）· `chart-design` → `office-docx` | 標案要交的是服務建議書，不是 RFQ；writer 形狀照 `gov-subsidy-writer`，框架來自招標文件與評選表 |
| Check | ★ **投標前檢核**（資格文件、押標金、印章、份數、截止時間、格式）· `de-slopify` 審查文體 · `say-it-plain` | 漏一項就廢標，整條循環最貴的失敗 |
| Act | ★ **決標回填**（won / lost / no-bid、決標價、得標者、落差原因；g0v 有端點）· `gov-tender-scraper` Step 7 關鍵字回饋 · ★ 得標案沉澱：推進 `sales-material` 案例庫與 `knowledge-graph` · ★ 命中率／投標率／得標率回顧 | 現在唯一的學習迴路是「標題像不像」，不是「投得上投不上」 |

### 4b 政府補助計畫

| | 用誰 | 說明 |
|---|---|---|
| Plan | `gov-subsidy-scraper` · `gov-subsidy-writer` Phase 1（官方文件先行、目錄 framing） | 先讀官方 SOT 全文再用章節代碼 |
| Do | `gov-subsidy-writer` Phase 2–5（分項架構 → 逐題拍板 → 內文 → 效益量化）· `chart-design` · `office-docx` | |
| Check | `gov-subsidy-writer` Phase 6（紅字▲歸零 + 文體掃描）· `de-slopify` 審查文體 · `say-it-plain` | |
| Act | Phase 7 輸出 → Phase 8 書面審查意見 → 審查會議簡報 · `knowledge-graph`（委員、意見） | 這條線的 Check / Act 是完整的，標案線可以抄它 |

### 4c 顧問案交付文件（SOW、廠務報告、週報、通用文件）

| | 用誰 | 說明 |
|---|---|---|
| Plan | `task-brief` · `metadata-workshop` · `discovery-interview` | 五欄位 brief；先梳理客戶知識 |
| Do | `sow-writer` · `iot-factory-report`（UPW／壓縮機／冷凍機）· `internal-comms`（週報、3P、事故）· `doc-coauthoring`（多方長文件）· `gdoc-report-builder` · `office-docx` / `office-pdf` / `office-xlsx` · `chart-design` → `mermaid-diagram` / `excalidraw-diagram` | Word 內嵌圖不是 slide，尺寸另算 |
| Check | `de-slopify` 審查文體 · `say-it-plain` · `check-html-figure.mjs` | 三欄收據：機械檢查／截圖／人眼分開寫 |
| Act | `knowledge-graph` · 沒 skill 的報告類型（市調、EHS、排程）記 `.learnings/FEATURE_REQUESTS.md`，接到真案子再抽 | |

### 4d 客戶資料梳理

| | 用誰 | 說明 |
|---|---|---|
| Plan | `discovery-interview` | 找最痛的手工流程 |
| Do | `metadata-workshop` · `doc-to-structured-data` | 業務知識 → YAML schema；舊文件 → 結構資料 |
| Check | 第二個同業客戶能重用七成才算成功 | metadata-workshop 的護城河定義 |
| Act | schema 進 `markdown-file-ssot` 或客戶 repo · `knowledge-graph` | |

---

## 5. 分析師／投資研究

你在做：從資料算出東西，畫數據圖，做財報或製程分析；或在建 ML／AutoML 平台。

### 5a 投資研究

| | 用誰 | 說明 |
|---|---|---|
| Plan | `mops-financial-scraper` · `tw-company-lookup` | 財務三表、月營收 → SQLite / DuckDB |
| Do | `invest-research` · `chart-design`（data 類）· `office-xlsx` | 持股追蹤、回測、風險；圖走 R1–R4 |
| Check | `repro-exam` · `env-doctor` | 兩台機器算出來要一樣 |
| Act | `knowledge-graph` · 報告交付走 4c | |

### 5b 廠務時序分析

| | 用誰 | 說明 |
|---|---|---|
| Plan | `metadata-workshop`（PI tag 梳理）· `doc-to-structured-data` | 先弄清楚 tag 是什麼 |
| Do | `iot-factory-report` · `chart-design` | 週期偵測、異常標記、趨勢 → 圖 + PPTX |
| Check | `chart-design` Post-check（R3 同軸同單位）· `check-html-figure.mjs` | |
| Act | 報告交付走 4c · `knowledge-graph` | |

### 5c ML／AutoML 平台

| | 用誰 | 說明 |
|---|---|---|
| Plan | `ml-eval-quality` · `ml-model-registry` · `backend-async-jobs` | 領域參考：指標分派、小資料 CV 閘門、登錄與治理、訓練要不要丟 pipeline |
| Do | 走 1c 後端 | |
| Check | `qa-dataflow` | 治理欄位有沒有牙齒（retired 的模型還能不能推論） |
| Act | 走 1d 部署 | |

### 5d 製造領域資料

| | 用誰 | 說明 |
|---|---|---|
| Plan | `ic-lot-normalization` · `odb-dfm-reference` | 批號標準化；ODB++ 解析與 DFM 的坑 |
| Do | 走 1c | |
| Check | `repro-exam` | 一張真板子當考題 |
| Act | 領域學到的回寫 reference skill | |

### 5e 自動迭代實驗

| | 用誰 | 說明 |
|---|---|---|
| Plan | 定目標、指標、驗證指令 | 可量測才能迭代 |
| Do | `autoresearch` | modify → verify → keep / discard，夜間跑 |
| Check | 指標曲線 · `agent-observability` | dashboard 看得到 |
| Act | 留下的改動進 commit | |

---

## 6. 人資

### 6a 開缺

| | 用誰 | 說明 |
|---|---|---|
| Plan | `hr-jd-writer` 前段 | 從組織需求推職責、必備、加分 |
| Do | `hr-jd-writer` | 結構化 JD、招募文 |
| Check | `de-slopify` | 對外前去 AI 腔 |
| Act | `knowledge-graph` | |

### 6b 履歷篩選

| | 用誰 | 說明 |
|---|---|---|
| Plan | JD 的必備條件當篩選標準 | |
| Do | `hr-candidate-analysis` | PDF 履歷抽結構、看 GitHub |
| Check | `github-repo-audit` | 候選人 repo 打分 |
| Act | `knowledge-graph`（候選人、面試決策） | |

### 6c 內部公告

| | 用誰 | 說明 |
|---|---|---|
| Do | `internal-comms` | 公告、newsletter、FAQ 模板 |
| Check | `say-it-plain` · `de-slopify` | 結論先行、去 AI 腔 |

---

## 7. 知識工作者

你在做：消化外部內容，變成 `knowledge/` 裡可查的筆記。`knowledge/` 是內容摘要庫，`knowledge-graph` 是實體事實庫。

### 7a 訂閱與掃描（排程）

| | 用誰 | 說明 |
|---|---|---|
| Plan | 決定訂閱哪些頻道、UP 主、podcast | |
| Do | `yt-channel-scraper` | 掃到新集就歸檔 |
| Check | `knowledge/videos/INDEX.md`（自動重生）· 筆記 reliability 標記 | 手動字幕 ✅ / 自動字幕 ⚠️ / whisper 🤖 |
| Act | `knowledge-graph` | |

### 7b 單支影片／錄音消化

| | 用誰 | 說明 |
|---|---|---|
| Plan | 決定要摘要、繁中文章、翻譯、字幕檔還是片段 | 四種輸出各一支 |
| Do | `video-transcript`（線上，抓真字幕）· `local-media-transcribe`（本機錄影錄音，離線）· `subtitle-file`（srt / vtt 保留時間軸）· `video-clip-extract`（只要一段） | |
| Check | reliability 標記 | |
| Act | `knowledge-graph` · 可以做成 skill 的交 `session-harvest` | |

### 7c Drive 文件變 skill

| | 用誰 | 說明 |
|---|---|---|
| Do | `gdrive-to-skills` | 讀 Drive、分類、建 knowledge skill |
| Check | `sk check`（gdrive 段） | 過期匯入 |
| Act | `sync-readme` | |

---

## 8. 平台維護者

你在做：維護 rivendell 本身。這是 `platform` 循環。

### 8a 新增或修改 skill

| | 用誰 | 說明 |
|---|---|---|
| Plan | `skill-scout`（外面有沒有現成）· `writing-great-skills`（先讀原則）· `task-brief` | |
| Do | `skill-creator` · `skill-apply` · `sync-readme` | 建、改、評測；README 目錄（描述改了要手動改那列） |
| Check | `sk lint` · `sk check`（symlink、frontmatter、Role coverage）· `audit-fix` | 新 skill 沒進角色頁會被抓 |
| Act | `session-harvest` · `learnings-promotion-sprint` | 告一段落收割；跨專案蒸餾 |

### 8b 排程 agent

| | 用誰 | 說明 |
|---|---|---|
| Plan | `agent-persona` | tester / maintainer / reviewer 的 prompt |
| Do | `agent-launchd` · `agent-headless` · `agent-observability` · `agent-dispatch` | plist（bootout / bootstrap，不要 kill）；無人值守；dashboard 看得到；平行修 |
| Check | 系統健康「排程健康」· `sk check agents` | agents.conf 與 launchd 對帳 |
| Act | `workflow-retro` | 每週讀 telemetry 找下一個瓶頸 |

### 8c session 與環境

| | 用誰 | 說明 |
|---|---|---|
| Plan | `setup-permissions` · `settings-audit` | 只放用到的權限；清無效設定 |
| Do | `context-journal` · `context-recovery` · `claude-to-telegram` · `auto-stage` · `protect-secrets` | 長 session 不掉 context；手機遙控；hook 自動 stage、擋 .env |
| Check | `sk check` | |
| Act | `session-wrap` · `self-improving-agent` · `learnings-promotion-sprint` | 收工；踩坑分流到對的 vault；升進 CLAUDE.md |

### 8d repo 維運

| | 用誰 | 說明 |
|---|---|---|
| Plan | `doc-drift-sync`（偵測） | CHANGELOG / ROADMAP / CLAUDE.md 對不齊 |
| Do | `repo-rename` · `doc-drift-sync`（修） | plist、settings、sibling repo 全掃 |
| Check | `sk check portability` · `sk check ports` | 硬編碼路徑、port 漂移 |
| Act | `gstack-upgrade` · `gstack-learn` (gstack) · `autoresearch`（指標型改善） | |

---

## 覆蓋檢查

`bin/sk check` 會列出 `skills/*/*/SKILL.md` 中沒有在這頁出現的 skill 名稱。新 skill 進來，或改名後，這裡要跟著補。
角色與工作都不需要互斥；一支 skill 出現在三件工作是資訊，不是錯誤。
