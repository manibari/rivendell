---
name: system-design
loop: dev
pdca: plan
description: >
  SA/SD 環節 — 在「畫面定了 / 需求定了」之後、「拆成實作任務」之前，把系統設計
  一次講清楚並畫出來：資料模型、模組職責邊界、介面契約、關鍵流程時序、功能關係圖
  (target 版)、NFR 與反證關卡。Flow-agnostic：有畫面的專案接在 mockup 之後，
  沒畫面的 backend / refactor 專案接在 requirement / investigate 之後，兩條都走這裡。
  產出 docs/design/YYYY-MM-DD-<feature>-sd.md + 圖檔；每張圖 sub-call chart-design
  (system-architecture 類)；功能關係圖沿用 qa-dataflow 的 diagram-spec 同一規格，
  讓事後 qa-dataflow 能拿同一張圖對照 actual，形成閉環。
  TRIGGER when: mockup / design-html 完成要進實作規劃；backend-only 功能或 refactor
  要動 schema / 跨模組傳遞 / 新增 store；使用者說「系統設計」「SA SD」「先把架構定下來」
  「資料表怎麼設計」「API 怎麼切」「模組怎麼拆」；或 planning-with-files / writing-plans
  發現手上沒有可依據的設計文件。
  DO NOT TRIGGER when: 純樣式 / 文案 / 複製貼上級小改（無 schema、無跨模組契約變動）；
  設計文件已存在且未過期（改去 gstack-plan-eng-review 審它）；還在問「該不該做」
  (gstack-office-hours)；要的是使用者旅程而非系統結構 (user-flow)；
  要驗證既有系統實際怎麼跑 (qa-dataflow)。
tags: [workflow, planning, architecture]
version: 1.0.0
source: manual
user_invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion"
---

# System Design (SA/SD)

把「要做什麼」翻譯成「系統長什麼樣」，**在拆任務之前**。

**Announce at start:** "I'm using the System Design skill to lock the SA/SD before task breakdown."

> **這支 skill 補的是流程斷點**：畫面設計有完整鏈路（requirement → user-flow →
> design-consultation → shotgun → mockup → design-html），系統設計卻只有
> `writing-plans` plan header 裡的一句 `**Architecture:** [2-3 sentences]`。
> `gstack-plan-eng-review` 審的正是 SA/SD，但沒有任何 skill 負責**產出**它 ——
> 結果是審一份不存在的東西，而那些該在此決定的事被推到實作時各自即興，
> 最後由 `qa-dataflow` 事後挖出來。本 skill 就是那個產出端。

---

## Step 0: Scale Triage（先決定要做多深）

**不是每個任務都需要完整 SA/SD。** 先判斷檔位，別把改個按鈕文案的任務拖進六節文件。

| 檔位 | 判準（任一命中即進此檔） | 產出 |
|------|----------------------|------|
| **Skip** | 純樣式 / 文案 / 常數調整；不動 schema、不動介面契約、不新增資料落點 | 不出文件，直接進 planning。在回覆裡寫一句「SD skipped：本次無 schema / 契約 / store 變動」 |
| **Light** | 動到既有模組內部邏輯，但介面契約不變；或只新增一個端點且沿用既有實體 | 只出 §1 §3 §4 §8（scope / 職責邊界 / 契約 / 未決事項），不畫圖或只畫一張序列圖 |
| **Full** | **動到資料寫入**、**跨模組傳遞**、**新增 store**、新增/修改 schema、新增外部整合、或這是一個新功能的第一版 | 六節全出 + 圖組（見 Step 4） |

Full 檔的三個判準 **刻意跟 `qa-dataflow` 的 HARD GATE 條件一字不差**（見
`~/.claude/CLAUDE.md`「動到資料寫入 / 跨模組傳遞 / 新增 store」）。
理由：事前該設計的和事後該驗的是同一件事。事前跳過 Full，事後 `qa-dataflow`
一定會挖到落差 —— 只是那時已經寫完了。

判不出檔位 → 用 `AskUserQuestion` 問，不要預設 Light 混過去。

---

## Step 1: Load Inputs（先讀，不要憑常識編）

**強制**，缺哪項就寫「無」，不要用業界常識補：

| 輸入 | 去哪找 | 缺了會怎樣 |
|------|--------|-----------|
| 需求 / 驗收標準 | `docs/requirements/<feature>.md`（`requirement` skill 產出） | 設計沒有對映對象，無法驗收 |
| 使用者流程 | `docs/user-flow/*` 或 requirement 內的流程段 | 序列圖會漏掉錯誤分支 |
| 畫面 | `mockups/<feature>.html` + 元件清單（`mockup` skill Step handoff 的 component inventory） | 前端要的資料形狀是猜的 |
| 既有資料模型 | `models.py` / ORM class / migration 目錄 / `.schema <table>` | schema delta 會寫成「新建」而其實是「改既有」 |
| 既有介面 | `ls routers/`、`find app -name 'route.ts'`、OpenAPI schema | 會發明一個已經存在的端點 |
| 既有資料流圖 | `docs/**/dataflow-*`（`qa-dataflow` 上次的 actual 圖） | 沒有起點，target 圖變成空中樓閣 |

> **代碼引用 ≠ 已讀內容**（`~/.claude/CLAUDE.md` 同名規則）：看到 `US-3`、`A1.1`、
> 某張表名被提及，不代表你知道它的內容。動筆前 `grep` + Read 全文。
> 不確定就在文件裡寫「待補」，**不要憑常識編**。

沒有畫面的專案（backend-only / CLI / 排程 / refactor）：畫面那兩列直接寫「無 UI」，
其餘照走。這支 skill 不依賴 mockup 存在。

---

## Step 2: 六節內容

寫進 `docs/design/YYYY-MM-DD-<feature>-sd.md`。
完整模板見 `references/sd-template.md`（**直接 copy 改，不要重新發明章節**）。

### §1 Scope — 這次要動什麼

- 對映需求編號（`US-1`, `US-3`）或 bug 的 root cause 一句話
- **In / Out of scope 兩欄表**（沿用 `requirement` skill 的格式，防 scope creep）
- 一句話寫「這次改動的一句話摘要」——寫不出來代表還沒想清，回 Step 1

### §2 資料模型 — 現況 + delta

- **先寫現況**（實查來的，標明從哪個檔案讀到），再寫 delta
- Delta 用三態列表：`+ 新增` / `~ 修改（含型別與 nullable 變化）` / `- 刪除`
- 每個新欄位回答：**誰寫它、誰讀它、可不可為 null、預設值、有沒有索引**
- 遷移策略：可否 backfill、舊資料怎麼辦、能不能 rollback
- → 出 **ER 圖**（見 Step 4）

**踩過的坑**：不要相信跨表的命名慣例（`report_date` vs `year_month` vs `date`），
也不要相信符號慣例（`2330.TW` vs `2330`）。第一次跨表查詢前先 `.schema` 每張表，
正規化放在服務邊界，不要藏在查詢深處。

### §3 模組拆分與職責邊界

每個模組一列，**必須寫「不負責什麼」**：

| 模組 | 負責 | **不負責** | 依賴 |
|------|------|-----------|------|
| `IngestService` | 解析上傳檔、寫 `raw_upload` | 不做欄位驗證（那是 `Validator`） | object store, PG |

「不負責」那欄是這節的全部價值 —— 它是日後爭議「這段邏輯該放哪」的唯一裁判。
寫不出「不負責什麼」的模組，通常是切錯了。

### §4 介面契約

對每個新增/修改的介面（HTTP 端點、事件、跨模組函式簽章）：

- 路徑 / 名稱、方法、**輸入形狀**（欄位 + 型別 + 必填）
- **成功輸出形狀**
- **錯誤形狀**：不是只寫「回 400」，要寫**回什麼 body、呼叫端怎麼分辨哪一種錯**
- **冪等性**：重送會怎樣（這題最常被跳過，然後在 retry 時炸掉）
- 前置條件：需要哪個 id 才能呼叫（這同時是 §6 功能關係圖的邊）

### §5 關鍵流程

**只畫會出錯的那條**，不要把 happy path 畫得很漂亮然後略過錯誤分支。

- 有多個 actor 的時序互動 → **序列圖**，錯誤分支用 `alt` block 放在同一張，不要另開一張
- 有生命週期的實體 → **狀態機**，每個轉換標「誰觸發、什麼條件」
- 兩者都不需要（單一同步呼叫）→ 寫三行文字就好，不要硬畫圖

### §6 功能關係圖（target 版）

**這節是本 skill 跟 `qa-dataflow` 的接點。**

照 `skills/qa/qa-dataflow/references/diagram-spec.md` **同一份規格**畫，
但畫的是 **target**（設計意圖），不是 actual（實查現況）。

Spec 的重點原文照用：

- 節點是**功能**，邊是**傳遞的識別碼**（`dataset_id` → `split_id` → `run_id` → `version_id`）
- **價值全在邊的標籤上** —— 只有箭頭等於沒說
- 一定要畫**回頭路**（退回修正、重做、重訓）與**旁掛**（唯讀分析工具）
- 節點名用**使用者看得到的名字**，內部元件名放副標
- 帶的入口要標「帶進來的是什麼」，**也要標「不是什麼」**（負向資訊防誤解）

動筆前先開 spec 裡的參考實例 PNG 看一眼（Verdandi-AutoML `docs/verification/` 四圖分工，
PTI-ARES `docs/architecture/` actual/target 對照），比讀規格快。

檔名 `docs/design/diagrams/dataflow-target-<YYYY-MM>.html`，
跟 `qa-dataflow` 的 `dataflow-actual-<YYYY-MM>` **同命名、同版面**，才能並排比對。

### §7 NFR 與反證關卡

- **量級**：預期資料筆數、併發使用者、單次請求資料量。
  這欄直接決定要不要上雲 —— ≤10k rows / ≤20 users 就別開 Postgres + multi-region，
  用列數當證據推回過度設計
- **失敗模式**：外部依賴掛掉會怎樣、部分成功怎麼辦、有沒有重試
- **權限**：誰能讀、誰能寫、跨租戶隔離在哪一層
- **反證關卡（teeth）**：每個你設計的閘門，寫一句「**它實際擋得住什麼、擋不住什麼**」。
  三態，不要二態：`✓ 有防護` / `✗ 無防護` / `◐ 只做一半`。
  `◐` 那態最有用 —— 「只擋一半」是事後抽查最容易漏掉的狀態。
  這節寫完，`qa-dataflow` 事後那張「關卡實況」四欄表就有對照基準了

### §8 未決事項與假設

- 每條寫：**問題 / 目前假設 / 誰能拍板 / 什麼時候必須決定**
- 「待補」是合法答案，**編造不是**
- 這節非空是健康的；空的通常代表沒認真想邊界

---

## Step 3: 圖組 —— 一律 sub-call chart-design

**不要自己決定畫什麼圖型、用什麼顏色。** 每張圖都走 `chart-design`：

```
Read skills/docs/chart-design/SKILL.md            # R1–R4 + pre/post must-check
Read skills/docs/chart-design/system-architecture.md   # triage 結果固定是這一類
```

SA/SD 的圖 **100% 落在 system-architecture 類**（元件、序列、ER、資料流、狀態機、部署）。
Triage 不用猶豫，但 `system-architecture.md` 的 per-type 規則必須照做：

| 本 skill 的節 | chart-design 的 type | 該檔的關鍵規則 |
|--------------|---------------------|--------------|
| §2 資料模型 | ER Diagram | 每個 entity 5–8 個關鍵欄位（不是全部）、標 cardinality、大 schema 拆 sub-domain |
| §3 模組拆分 | Block / Component | box = noun 不是 verb、N ≤ 12、group by boundary、實線同步/虛線 async |
| §5 關鍵流程 | Sequence / State | actor 左→右按發起順序、message 要 verb+object、加 activation bar、錯誤走 alt、lifeline ≤ 7 |
| §6 功能關係圖 | Data Flow | 每條 flow 必有 label、L0 ≤ 5 process；**再疊 qa-dataflow diagram-spec 的加嚴規則** |
| §7 部署（有才畫） | Network / Deployment | 官方 icon set、標 public/private、標 protocol:port |

**R2 narrative gate 照跑**：每張圖生成前回答「這張圖回答哪一個問題 / 要 argue 什麼 /
讀者該記得什麼」，三題填不完就不要畫。SA/SD 的圖同樣不是裝飾。

**R3 在這類最常出錯**：兩個獨立系統被塞進同一個 box。
`system-architecture.md` 的 R3 反例集（前端+後端、API+Worker、Primary+Replica、
內部+第三方、multi-region）逐條對一遍。

**排版與驗證**（`~/.claude/CLAUDE.md` Diagram Output Defaults，不重述細節）：
16:9 1600×900 固定、字級下限、生成後**自我截圖 + Read PNG 肉眼檢查**。
HTML 圖檔另跑機械檢查：

```bash
node skills/docs/chart-design/references/check-html-figure.mjs <fig.html> \
  --width 1600 --height 900 --screenshot /tmp/sd-check.png
```

多 band 的功能關係圖（節點 > ~15）**不要交給 mermaid 自動排版** —— dagre 會排成長條或
階梯狀、邊互相穿越。改手工正交排版（一 band 一列、跨 band 走水平通道、回頭路走外側、
邊標籤加白底標籤片）。這是 `diagram-spec.md` 實測過的結論，不要重新踩。

圖檔存 `docs/design/diagrams/`，在 SD 文件內用相對路徑引用 + 一句 caption 寫
「這張圖回答什麼問題」。

---

## Step 4: 交付前 Must-Check

全勾才算完成：

- [ ] **檔位已標**（Skip / Light / Full），且判準寫在文件開頭
- [ ] **§1 一句話摘要寫得出來**
- [ ] **§2 現況是實查來的**，每個宣稱標得出檔案 / `.schema` 出處（不是憑命名慣例推測）
- [ ] **§3 每個模組都寫了「不負責什麼」**
- [ ] **§4 每個介面都寫了錯誤形狀 + 冪等性**
- [ ] **§6 功能關係圖的每條邊都標了傳遞的識別碼**（只有箭頭 = 沒做）
- [ ] **§6 畫了回頭路**（沒有回頭路的圖幾乎一定是漏了，真實系統都是循環）
- [ ] **§7 每個閘門標了三態**（`✓` / `✗` / `◐`），且 `✗` `◐` 後面接一句為什麼
- [ ] **§8 未決事項每條都有「誰能拍板」**
- [ ] **每張圖跑過機械檢查 + 自我截圖並 Read 過**，交付收據三欄分開寫
      （`mechanical_check` / `screenshot` / `visual_review`，不准互相冒充）
- [ ] **footer 標來源與日期**（`依 YYYY-MM-DD 程式碼實查`），逼自己回頭驗證

**修正輪數上限 2**。同一條 feedback 出現第二次 = 方向錯不是幅度不夠，
停止微調，回 Step 3 重選圖型或回 Step 0 重評檔位。

---

## Step 5: Handoff

存檔後輸出：

> **SA/SD 完成** → `docs/design/YYYY-MM-DD-<feature>-sd.md`（檔位：Full / Light）
>
> | 下一步 | Skill | 做什麼 |
> |--------|-------|--------|
> | 審設計 | `/gstack-plan-eng-review` | 架構、邊界條件、測試策略 —— **現在它有東西可審了** |
> | 拆任務 | `/planning-with-files` 或 `/writing-plans` | 依這份 SD 拆 bite-sized task |
> | UI 任務 | `/gstack-plan-design-review` | UX 落差（有畫面才跑）|
> | 大功能 | `/gstack-autoplan` | 三審一次跑完 |
>
> 實作完成後：`/qa-dataflow` 會拿 §6 的 target 圖對照 actual —— **那時的落差表，
> 就是這份設計被驗證或被推翻的地方**。

---

## Anti-Patterns

| 不要 | 要 |
|------|---|
| 跳過 SD 直接 `planning-with-files` 拆任務 | 拆任務前先定資料模型與契約，否則各任務會各自發明 |
| plan header 寫 `Architecture: 2-3 sentences` 當作設計完了 | 那是摘要不是設計；六節該有的東西一個都沒有 |
| 憑常識編既有 schema / 端點 | Step 1 實查；不確定寫「待補」 |
| 模組表只寫「負責什麼」 | 一定要寫「**不負責**什麼」，那才是邊界 |
| 契約只寫成功路徑 | 錯誤形狀 + 冪等性是契約的一半 |
| 功能關係圖只有箭頭沒有標籤 | 邊上寫傳遞的識別碼，否則不叫關係圖 |
| 圖上只畫單向管線 | 畫回頭路與旁掛，真實系統都是循環 |
| 閘門寫「有做驗證」 | 三態 `✓/✗/◐` + 一句「擋得住什麼、擋不住什麼」 |
| 一張圖回答三個問題 | 一題一張（模組全景 / 功能關係 / 資料實體 各自分開）|
| 自己挑顏色字型畫圖 | sub-call `chart-design`，style file 是 SSOT |
| 節點 > 15 還丟給 mermaid 自動排版 | 手工正交排版（實測 dagre 會排壞）|
| 沒截圖就說圖做好了 | 截圖 + Read PNG，收據三欄照實填 |
| 把每個小改都拖進 Full 檔 | Step 0 檔位分流，Skip 就大方寫「SD skipped：無 schema / 契約 / store 變動」|

---

## 為什麼是獨立 skill，不是塞進 writing-plans

- `writing-plans` 是 upstream Anthropic 的 plan family 命名，刻意不收斂（見
  `.claude/CLAUDE.md` naming 段），改動它會跟上游 drift
- backend-only flow **不經過** `writing-plans`，塞進去補不到
- 產出物（設計文件 + 圖組）、gate 條件（三判準）、sub-call（chart-design）
  都跟「把工作拆成 2–5 分鐘的步驟」是不同職責，混在一起會讓 `writing-plans` 變成兩件事
