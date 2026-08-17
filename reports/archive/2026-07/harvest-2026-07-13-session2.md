# Session Harvest Report — 2026-07-13

## Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|-------|---------|
| 1 | Vault-Peter-Work（詠鋐） | 102 | 115年 AI 創新服務研發補助計畫：讀申請須知 PDF → 產出摘要 → 為柏宇達（POS 廠商）起草 500 萬提案，參考美珍香配貨預測案例（`A1-配貨預測-導入步驟-美珍香試點.md`、`STATE.md`） |
| 2 | Verdandi-AutoML | 5610 | 參考 tukeyCorePy / tukey-main 兩個 legacy repo 移植功能；拆成獨立語意 commits（optimizer / GAM / dq）；「再優化」階段：CV auto-tuning、DALEX 診斷、anomaly 風險分數正規化；含 Alembic migration（reconcile_model_drift）與截圖驗證 |
| 3 | sales-assistant | 1 | headless 排程執行 subsidy-scraper（既有 skill；注意：此專案已標記 deprecated，排程仍指向它） |
| 4 | urd-bi | 420 | 由截圖出發重塑 IA：補 Projects 列表 + sidebar（AppShell.tsx / DashboardViews.tsx / ProductDetail.tsx）；有走 gstack-office-hours 釐清方向 |
| 5 | urd-bi | 52 | 驗證「RO 水系統畫面跟原本不一樣」——使用者兩度糾正 AI 憑印象斷言，最後以 legacy-check.png 截圖對照確認 legacy 畫面 |
| 6 | code | 63 | context-recovery skill 執行 + 寫入 norns-fleet-naming 記憶（既有能力，無新 pattern） |

工具分佈：Bash(2765)、Edit(1622)、Read(1102)、Write(243)、AskUserQuestion(58)。Session 2/4 的 AskUserQuestion 密度高，顯示互動式釐清迴圈是常態。

## 跨 Session 重複 Pattern

1. **政府文件 PDF → 摘要 → 提案草稿**（Session 1）：申請須知 → 資格/格式/評分要點摘要 → 引用既有案例素材起草計畫書。sourcing 端已有 subsidy-scraper / tender-scraper，但「計畫書撰寫」端沒有 skill。
2. **參考 legacy repo 移植功能 + 乾淨 commit 拆分**（Session 2）：讀兩個舊 repo → 對照移植 → 按語意單位（optimizer / GAM / dq）拆 commit。
3. **截圖為 ground truth**（Session 2、5）：模型頁截圖驗證、legacy 畫面比對——與 CLAUDE.md「生成圖後自我截圖檢查」規則同源，Session 5 顯示「憑印象斷言 legacy UI」是實際踩坑點。
4. **Fleet 產品 app shell 收斂**（Session 4）：urd-bi 補 sidebar + Projects 列表，與 fleet-infra-spine 策略（recipe skills 從成熟產品交集抽取）方向一致。

## Skill 候選

### 🟢 Strong — subsidy-proposal-writer（補助計畫書撰寫）

- **名稱**: `subsidy-proposal-writer`
- **目的**: 政府補助案申請書產製流程——讀申請須知 PDF → 抽取資格 / 補助上限 / 評分標準 / 格式要求成摘要 → 依官方章節代碼為 framing（呼應 CLAUDE.md「官方文件 framing 優先」）→ 引用素材庫既有案例（如美珍香 A1）起草計畫書，並以 STATE.md 追蹤進度。
- **觸發**: 「開補助案」「寫申請書 / 計畫書」「幫 X 申請 Y 補助」
- **類別**: docs（與 rfq-writer / sow-writer 同層）
- **理由**: Session 1 完整走過一次此流程（102 msgs）。現有 skill 只覆蓋 sourcing（subsidy-scraper / tender-scraper），撰寫端是 CLAUDE.md「文字報告」路由中明確的 ★暫無 缺口；且此類案子有明確可重複的結構（須知解析 → 章節對映 → 案例引用），第二次接案即可回收成本。

### 🟡 Moderate — reference-repo-port（參考 repo 功能移植）

- **名稱**: `reference-repo-port`
- **目的**: 把 legacy / 參考 repo 的功能系統化移植到新 codebase：對照兩邊架構 → 列移植清單 → 逐項移植並適配新框架 → 按語意單位拆成獨立 commits（而非一坨 WIP）→ 每項移植後截圖 / 測試驗證。
- **觸發**: 「參考 X repo 開發」「把 Y 的功能搬過來」「移植 Z 模組」
- **類別**: workflow
- **理由**: Session 2 以 5610 msgs 實走此模式（tukeyCorePy + tukey-main → Verdandi），commit 拆分（optimizer / GAM / dq）是使用者明確要求的紀律。但目前只有一次大型實例，且部分紀律（乾淨 commit、截圖驗證）已散落在 CLAUDE.md 規則中——建議再累積一次同型任務後成形。

### 🟡 Moderate — spine-app-shell（Fleet 產品 App Shell 骨架）

- **名稱**: `spine-app-shell`
- **目的**: Fleet 產品共用的前端外殼 recipe：sidebar 導覽 + Projects / 應用列表 + detail 頁的 IA 骨架，錨定 ChimesFlow design SoT，收斂「每個產品自己長一套 shell」的發散。
- **觸發**: fleet 產品需要補 sidebar / 專案列表 / app shell 時；「在外面應該要有 Projects」這類 IA 重塑需求
- **類別**: frontend（與 spine-auth / spine-schema-sync 同策略、不同層）
- **理由**: Session 4 是一個實例，且與 fleet-infra-spine 記憶的 recipe-skill 策略吻合。但該策略明言「從成熟產品交集抽取」——目前僅 urd-bi 一個資料點，建議等第二個產品（如 chimesflow 之外再一個）長出同構 shell 後，做交集稽核再抽 skill（比照 spine-auth 的 2026-06-27 audit 做法）。

### 🔴 Weak — legacy-ui-verification（Legacy 畫面查證）

- **名稱**: `legacy-ui-verification`
- **目的**: 回答「這畫面跟原本不一樣？」時，禁止憑印象斷言——先從 git 歷史 / 舊部署 / 截圖存檔取得 legacy ground truth，截圖比對後才回覆。
- **觸發**: 使用者質疑畫面與過去版本不符
- **類別**: quality
- **理由**: Session 5 只有 52 msgs、單次發生，且核心已被 gstack-investigate（root cause first）與「事實查核優先」原則覆蓋。**建議降級為 learning 而非 skill**：記入 `.learnings/`——「legacy UI 疑問 = 先找 ground truth（git log + 舊截圖），不憑記憶回答」。

## 非 skill 的觀察（建議處理）

1. **sales-assistant 排程殘留**：Session 3 的 headless subsidy-scraper 仍跑在已 deprecated 的 sales-assistant 專案上（見 memory: sales-assistant-deprecated）。建議把該排程的工作目錄遷到接手專案（chimesflow）或明確保留並註記，避免產出寫進死專案。
2. **Session 5 的糾正**（「可以不要亂講好嗎」）符合 self-improving-agent 的 correction 類別，應記入 urd-bi 的 `.learnings/LEARNINGS.md`。

## 結論

本輪 6 個 sessions 產出 1 個 Strong 候選（subsidy-proposal-writer，建議下次接補助案前用 skill-creator 建立）、2 個 Moderate 候選（reference-repo-port、spine-app-shell，各再等一個實例）、1 個降級為 learning。無與現有 138 個 skills 重複的建議。
