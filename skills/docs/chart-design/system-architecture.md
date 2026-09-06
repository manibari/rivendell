# System Architecture Diagrams (系統架構圖)

> Read this after triage. 主檔 `SKILL.md` 的 R1–R4 + pre/post must-check 依然全套適用。本檔重點：**R3 homogeneity** 在這類最常出錯（兩個獨立系統被塞進同一個 box）。

---

## What Counts as "System Architecture"

描述一個技術系統的結構或行為：

- Component / block diagram（高階架構，服務 + connection）
- Sequence diagram（時序互動、API 呼叫）
- Flowchart（決策邏輯、business logic）
- ER diagram（資料 schema）
- Data flow diagram (DFD)
- Network / deployment diagram（基礎設施）
- State machine（狀態轉換）
- C4 model（context / container / component / code）

---

## Tool Defaults

| 用途 | 工具 | 為什麼 |
|------|------|--------|
| 結構嚴謹 / 工程 doc | **Mermaid** | 文字驅動、Git diff 友善、Notion/GitHub 原生 render |
| 簡報 hand-drawn 感 / external audience | **Excalidraw**（`.excalidraw` JSON → PNG via Playwright） | 親和、不 corporate |
| 精準排版（slide 內 inline） | **HTML/CSS** + box-arrow CSS | 跟 slide template 共用樣式 |
| C4 model | **Structurizr** 或 **Mermaid C4 extension** | 內建 C4 圖類型 |
| 網路拓樸 / 雲端架構 | **draw.io / Lucidchart export → PNG** | AWS / GCP / Azure icon set 完整 |

判斷：

- 內部工程文件 → Mermaid
- 對客戶 / 投資人 → Excalidraw 或 HTML/CSS
- 跟 mermaid-diagram / excalidraw-diagram skill 的差異：那些 skill 負責**渲染**，本 skill 負責**設計決策**（要畫什麼、怎麼分群、用哪種 diagram type）

---

## Per-Type Rules

### Block / Component Diagram

**用條件**：高階架構，N 個服務 + 之間 connection。

- **每個 box = 一個 noun**（"UserService"、"PostgreSQL"），不是 verb（"處理用戶請求"）
- **N ≤ 12** boxes per diagram；超過 → 抽成 group / 拆 zoom diagram
- **箭頭方向有語義**：實線 = 同步 call、虛線 = async / event、雙向 = bidirectional
- Group by **boundary**（VPC / network zone / trust boundary）— R3 重點：boundary 是 homogeneity 的視覺化
- 元件 type 用**形狀**區分（rectangle = service、cylinder = DB、cloud = external、queue = stack rectangle）

### Sequence Diagram

**用條件**：N 個 actor 之間的時序互動（API call、authentication flow）。

- Actor / participant **左→右排** 按互動發起順序
- 每個 message 必有 **verb + object**（`POST /login (credentials)`，不是只寫 `login`）
- 加 **activation bar**（粗豎條）顯示 actor 處理區間
- 錯誤分支用 alt / opt block，不要畫第二張圖
- Lifeline 不要超過 7 個 actor

### Flowchart

**用條件**：決策邏輯，有 if/else / loop。

- Decision diamond **必為 yes/no question**（"Auth valid?" 而不是 "Auth"）
- 箭頭 label **必標 yes/no**（不要靠位置推測）
- Start / End 用 rounded rectangle / circle 區分一般 step
- **不要做 > 1 個 entry point**（不然 reader 不知從哪讀）

### ER Diagram

**用條件**：data schema 描述。

- 每個 entity 一個 box，內含 PK / FK / 主要 attr（不是所有 column — 5–8 個關鍵的）
- Relationship 標 cardinality（1:N、N:M）
- FK 用箭頭指向 PK，箭頭頭表示 N 那一端
- 大 schema → 拆 sub-domain 分多張

### Data Flow Diagram

**用條件**：資料怎麼在系統內流動。

- Process / store / external entity 用**不同形狀**（圓 / 矩形 / 兩條平行線）— Yourdon/DeMarco 標準
- **每條 flow 必有 label**（"order_id, qty"），不是只寫「資料」
- Level 0 ≤ 5 process；展開時用 Level 1, Level 2 多張

### Network / Deployment Diagram

**用條件**：服務跑在哪個機器 / region / cloud。

- 用 cloud 廠商**官方 icon set**（AWS / GCP / Azure 都有），不要自繪
- Group by region / VPC / AZ — boundary 視覺化
- 標清楚 **public** vs **private** subnet
- 加 protocol + port（"HTTPS:443"、"PostgreSQL:5432"）

---

## R3 反例集（user 親見）

| 應該分開 | 被塞進同框 | 為什麼錯 | 改用 |
|---------|----------|---------|------|
| 前端 + 後端 | 一個 "Application" box | 部署、scaling、語言都不同 | 兩個 box + connection |
| Web API + Worker queue | 一個 "Service" box | 不同 process、不同 scaling | 兩個 box，中間放 queue |
| Primary DB + Read replica | 一個 "Database" box | 寫路徑跟讀路徑不同 | 兩個 box + replication arrow |
| Internal + 3rd party | 一個 "API" box | trust boundary 不同 | 拆兩個 + 標 external boundary |
| Multi-region | 一個 "AWS" box | region failure domain 重要 | 一個 region 一個 group |

---

## Hierarchy & Composition Rules

- 一張圖只解一個 question — **不要試圖把所有層級在同一張畫完**
- 用 **C4 model 邏輯**：context（系統跟外界）→ container（部署單位）→ component（程式碼模組）→ code（class 細節）
- 跨層級 → **多張圖 + 對應 label**，不要 zoom-in 線
- 每張圖開頭 caption 一句寫：「這張圖回答了什麼問題」

---

## Style & Color

- **顏色用於分層**（front-end / back-end / data 各一色），不用於美觀
- **不要超過 5 色** — 多了 reader 失去顏色 → 含義的記憶
- Mermaid 慎用 `style` override — 會跟 deck CSS 衝突
- Excalidraw 用 default sketch palette + 1 個 accent for highlight
- Group / boundary 用**虛線框 + 半透明底色**，不要實線（會跟 box 邊界混淆）

---

## Pre-Check (此類專屬補充)

- [ ] **這張圖要回答哪一個 question？**（一句話寫下來，無法寫 → 砍）
- [ ] **是否 group by boundary**（VPC / trust / failure domain）— R3 視覺化
- [ ] **箭頭語義一致**（同步 vs async vs bi-directional）
- [ ] **N（box / actor / process）≤ 上限**（block ≤ 12、sequence ≤ 7、DFD L0 ≤ 5）
- [ ] **顏色 ≤ 5 色，且每色有語義**

---

## Anti-Patterns (此類專屬)

| 不要 | 要 |
|------|---|
| 兩個獨立系統塞同一個 box | 拆兩個 + connection |
| Box label 寫 verb（"處理請求"） | 用 noun（"RequestHandler"） |
| 箭頭沒方向 / 沒語義 | 實線同步 / 虛線 async / 標 protocol |
| Sequence diagram 沒 activation bar | 加粗豎條顯示處理區間 |
| Flowchart decision diamond 不寫 question | "Auth valid?" 而非 "Auth" |
| 一張圖混 context + container + code 三層級 | 拆 C4 多張 |
| 用顏色「裝飾」 | 顏色 = 分層語義（front/back/data） |
| 雲端服務自繪 icon | 用官方 icon set |
| Network diagram 不標 public/private | 必標 + 標 protocol:port |
| > 5 色 | ≤ 5、每色有意義 |
| 不寫 caption「這張圖回答什麼問題」 | 每張圖開頭一句說清楚 |

---

## 架構前後比對（Before / Delta / After）— 用 archify，不 vendor

> 2026-09-06 實測紀錄見 rivendell `.learnings/LEARNINGS.md`。這節是 recipe，不是 skill：
> 需要的時候臨時裝，用完不留。等某個產品真的維護起一份 architecture JSON 基準，再升級成 skill。

**什麼時候值得**：架構評審（plan-eng-review）要看「改了什麼」、大重構前後、RBAC / auth 這類 tier 升級。
**什麼時候不值得**：只是畫一張圖（走 mermaid / excalidraw）；30+ 節點的功能關係圖（qa-dataflow 手工模板，archify 排不出來）。

**步驟**：

```bash
npx skills add tt-a1i/archify -g            # 裝進 ~/.claude/skills/archify（MIT）
export ARCHIFY_UPDATE_CHECK_DISABLED=1     # 它預設會 GET 更新 manifest，關掉
cd ~/.claude/skills/archify
node bin/archify.mjs validate architecture base.json --quality showcase --json
node bin/archify.mjs validate architecture head.json --quality showcase --json
node bin/archify.mjs compare  architecture base.json head.json delta.html --quality showcase --json
```

**JSON 怎麼寫**：`references/archify-examples/` 有三份可直接抄形狀——
`rbac-tier1.base` → `rbac-tier2.head`（一次 compare 的 base/head 對），`spine-skeleton`（帶 GitHub 行號證據的單張）。
規則：同一個元件在 base 與 head 用**同一個 id**，delta 才會標成 changed 而不是 removed+added；
≤ 12 元件；`size: [150, 64]`；橫向間距 ≥ 110px 標籤才排得下；標籤壓到框就照診斷建議加 `labelDy`。

**限制**：
- `meta.repository` 只吃 `https://github.com/<owner>/<repo>` + 40 碼 commit SHA；純 local repo 用不了 `--repo-root` 證據。
- viewer UI 只有 en / zh-CN；圖上文字可以繁中。
- `visual-check` 的「首屏不可捲動」規則跟我們的 1600×900 slide 規則不同用途，fail 不代表圖不能用。
- 每次都要手排 pos / via，11 元件約 4–5 輪 validate；這是它不 vendor 的主因。
