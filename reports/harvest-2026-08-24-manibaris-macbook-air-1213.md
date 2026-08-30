# Session Harvest 報告 — 2026-08-24

**結論先講**：8 個 session 裡有 3 個 Strong 候選，都來自同一類根因——「這份東西最新/正確版本在哪、是怎麼生出來的」在多個 repo/資料夾/系統之間散落，得靠 ad-hoc `find`/`stat`/`git log`/PDF metadata 現場拼湊，其中 1 個還因為信任了過期的 `STATE.md` 而回答錯誤，被使用者糾正。另有 1 個候選（新客戶骨架建立 + Excel 情蒐評估）判定為既有工具已覆蓋，不重複開。

---

### 一、Session 摘要

| # | 專案 | 訊息數 | 關鍵活動 | 產出/素材 |
|---|------|--------|----------|----------|
| 1 | Vault-Peter-Work | 23 | 找「立積電最近一次簡報」：先信任 `STATE.md`（2026-08-21）送錯份（5/12 舊 deck），被使用者說「不是吧」後才靠 `git log` + 跨 repo（`~/code/IC-YMS`）比對找到真正最新版（8/20 demo 簡報） | 送出 2 個檔案（1 個是錯的） |
| 2 | Vault-Peter-Work | 17 | 中華電新案「勗連科技」：建客戶骨架 → 收 Excel 附件進 SOT → 呼叫既有 `office-xlsx` skill 分析排程表 → 寫評估報告 + README/STATE | `2026-08-24-AI流程優化評估.md`, README.md, STATE.md |
| 3 | Urd-WMS | 11 | 確認 dev server 是否已在跑（port 3071/8071），用 `lsof` + PID→cwd 追溯避免重複啟動 | — |
| 4 | Verdandi-AutoML | 5 | 討論 tukey-automl branch 是否該獨立出去（純討論，無產出） | — |
| 5 | Verdandi-AutoML | 57 | 「首頁復刻這個畫面」：navigate 到 `dev.chimes.ai/tukey/account/login` → `javascript_exec` 抓 computed style（色彩/字體/間距）→ 寫入本專案 `page.tsx`/`globals.css` → 本機起 dev server → 截圖比對 → 420px 響應式斷點驗證 | DESIGN.md, globals.css, page.tsx, rwd-420.png, rwd-420b.png |
| 6 | rivendell | 1 | 既有 `token-analysis-cron` 排程 agent 產出當日 token 用量日報 | 日報（既有機制） |
| 7 | sales-assistant | 40 | 執行既有 `subsidy-scraper` skill：爬三個政府補助來源、去重、更新 INDEX | （既有機制） |
| 8 | code (跨 repo) | 77 | 給一張「立積電子軟體授權書」截圖，回推是哪個系統生成的：`grep` 找不到樣板 → 讀 PDF metadata（Producer/Creator）判斷是 Chrome headless 列印 → 掃過 4 個 ChimesFlow 分支 repo 的 `uploads/generated_documents` 與對應 sqlite DB schema → 解 PDF text stream 比對關鍵字（"2028"）鎖定確切生成檔案 | 溯源結論（無檔案產出） |

---

### 二、Skill 候選清單

#### 🟢 Strong

**1. `client-deliverable-finder`**
- **用途**：使用者問「[客戶] 最近一次的[簡報/報告/文件]在哪」時，不能只讀單一資料夾的 `STATE.md` 就回答——`STATE.md` 常常沒回填最新交付（案例：Vault 的立積電 `STATE.md` 停在 8/21，但真正最新的 8/20 demo 簡報其實在完全不同的 repo `~/code/IC-YMS/reports/decks/`，Vault 資料夾裡只找得到 5/12 的舊版）。要跨「客戶主資料夾 + 有連動的產品/專案 repo」找同名/同關鍵字檔案，用 `stat -f "%Sm"` 或 `git log` 比實際修改時間，不是資料夾深度或檔名日期。
- **觸發詞**：「最近一次的簡報/報告/文件在哪」「幫我找 X 最新版」「上次交付到哪了」
- **分類**：business（緊鄰 `client-kickoff-docs`、`crm-projection`）
- **理由**：session 1 是活生生的失敗案例——第一次回答就送錯檔案，使用者一句「不是吧」才觸發第二輪跨 repo 搜尋。這代表現有心智模型（先讀 STATE.md）本身有陷阱：**STATE.md 是登記制，不是 ground truth**，登記者忘記回填就會產生假新鮮度。這條規則值得寫成 skill 的 hard rule，而不是每次都重新現場推導。

**2. `artifact-provenance-trace`**
- **用途**：給一份輸出檔案（PDF/PNG/截圖），回推它是被哪個系統、哪個樣板、哪筆資料生成的。標準鑑識步驟：(a) 讀 PDF metadata 的 Producer/Creator/Created 欄位判斷生成工具（如 `Skia/PDF m151` = Chrome headless 列印，不是 Word/InDesign）；(b) 抓內文關鍵字（PDF text stream 或 `pdftotext -layout`）鎖定精確檔案，尤其當同名候選檔案有好幾個分支版本時；(c) 跨候選 repo/DB（本案是 4 個 ChimesFlow 分支）查 `generated_documents`/`uploads` 表，用 schema (`.schema <table>`) 而非猜欄位名。
- **觸發詞**：「這份文件是怎麼生成的」「這張圖哪個系統出的」「幫我查這份 PDF 的來源」
- **分類**：workflow（鑑識類，與 `qa-dataflow` 的「反證」精神相近，但對象是單一產出物而非整條資料流）
- **理由**：session 8（77 則訊息、Bash 68 次）是目前唯一一次做這種鑑識，過程中反覆試錯：先搜整個 `~/code` 找樣板（落空）→ 讀 PNG 猜內容 → 才想到讀 PDF metadata → 又在 4 個高度相似的 ChimesFlow 分支 repo 之間反覆確認到底是哪一份。這條路徑高度可重複（任何「客戶截圖 → 這是哪來的」都會重新踩一次），但目前完全靠現場摸索，沒有一個起手式清單。

**3. `webpage-clone-extract`**
- **用途**：給一個外部參考網址，把它的視覺設計（色彩、字體、間距、佈局）萃取出來、在本專案技術棧中重建成一個新頁面，並用截圖迭代比對到視覺一致，含響應式斷點驗證。核心手法是用瀏覽器 `javascript_exec` 讀 `getComputedStyle()` 抓實際算出來的顏色/字級/padding（不是憑截圖用肉眼猜），而非單純截圖臨摹。
- **觸發詞**：「復刻這個畫面」「照這個網站的樣子做一頁」「clone this page」「參考 [URL] 做首頁」
- **分類**：frontend（緊鄰 `chimesflow-design`、`frontend-design`、`mockup`）
- **理由**：session 5（57 則訊息）完整跑過一套可重複的 10 步流程（讀專案 DESIGN.md → navigate 參考網址 → 截圖 → JS 抓 computed style → 寫入本地頁面 → 起 dev server → 截圖比對 → 迭代修正 → 420px 響應式驗證 → 送出最終截圖），但現有 skill 都不是為此設計：`chimesflow-design` 是「載入自家設計系統當預設」，`mockup` 是從零畫線框圖，`frontend-design` 是產生原創設計，沒有一個是「已知一個活生生的外部頁面、要精準複製視覺」。這個模式明確可跨專案重用（任何「照競品/客戶現有畫面做」的需求都會走同一套流程）。

#### 🟡 Moderate

無。

#### 🔴 Weak / 排除

- **Session 2（新客戶骨架 + Excel 情蒐評估）**：流程本身已經被「既有 new-client 腳本 + `office-xlsx` skill」覆蓋（session 中直接呼叫兩者完成），沒有拼裝證據，不構成新候選。
- **Session 3（Urd-WMS port 確認）**：完全符合已存在的 `run` skill 定位（「先找專案自己的啟動 skill，否則退回內建模式」）與 CLAUDE.md 既有的「Port verification before X is running」gotcha，是既有知識的正常應用，非缺口。
- **Session 4（branch 獨立性討論）**：純討論、無產出，訊息數過少（5 則）無法判斷模式。
- **Session 6、7**：分別是 `token-analysis-cron`、`subsidy-scraper` 既有排程機制的正常執行，非新模式。

---

### 三、結論與建議

- 開 3 個 Strong 候選：`client-deliverable-finder`（business）、`artifact-provenance-trace`（workflow）、`webpage-clone-extract`（frontend）。三者共通的根因是「權威來源在哪」的問題——STATE.md 可能沒回填、生成物可能來自好幾個相似分支 repo 之一、外部頁面的真實樣式只有讀 DOM 才準——而不是「不知道要用什麼工具」。建議三個 skill 都把「不要相信第一個看起來像答案的來源，要有交叉驗證步驟」寫成 hard rule，直接對應本次 session 1 送錯檔案的教訓。
- `client-deliverable-finder` 優先度最高：不只是效率問題，是**曾經真的答錯、且是對客戶簡報這種高風險內容答錯**，值得盡快收斂成 skill 避免重演。
