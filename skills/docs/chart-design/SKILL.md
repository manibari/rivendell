---
name: chart-design
loop: shared
pdca: do
description: >
  Chart / table / diagram sub-workflow shared by every report + deck skill.
  Three-class triage (data-analysis / business / system-architecture) routes to
  typed rules. Four universal rules: R1 canvas (≥80% fill, no >8% empty band),
  R2 narrative-beat gate (no chart without storyline link), R3 homogeneity
  (same axes = same metric, same unit, same population), R4 type-to-structure
  (a linear flow is NEVER a 2×2 matrix). Per-project visual style lives in
  `styles/<name>.md`, loaded by the skill — not hardcoded.
  TRIGGER: "畫圖表", "做表格", "生成 chart", "畫架構圖", "畫流程圖", "做圖", or invoked
  as sub-call by slide-workflow Gate 5, iot-factory-report Step 4, pitch-deck
  data-page generation, gdoc-report-builder visualization step.
  SKIP: pure text slides; one-liner mermaid/excalidraw sketches owned by those
  skills directly; non-visual tables that are just data dumps.
tags: [docs, workflow]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Chart Design

Shared sub-workflow for any chart / table / diagram generated for reports or presentations.

> 上層 routing: `slide-workflow` Gate 5 (生成內容)、`iot-factory-report` Step 4 (chart 生成)、
> `pitch-deck` 數據頁、`gdoc-report-builder` 視覺化階段，都把「這支圖怎麼做」sub-call 到這裡。
> 本 skill 不負責 slide 結構、不負責 data analysis 邏輯 — 只負責**這支圖/表/架構圖要怎麼做出來才不爛**。

---

## Triage: Three Chart Classes

每張要做的圖，**先決定屬於哪一類**，然後讀對應 sub-file。判斷不清 → 問用戶；三類混合 → 拆多張圖。

| 類別 | 用在 | 工具預設 | Sub-file |
|------|------|---------|----------|
| **Data analysis (數據分析圖表)** | 由真實 dataset 驅動 — 趨勢、分佈、相關、占比、量化對比 | Python matplotlib / plotly → PNG，或 Chart.js / ECharts → HTML | `data-analysis.md` |
| **Business (業務圖表)** | 結構/定位/比較概念圖 — 2×2、value chain、timeline、framework、comparison table | HTML/CSS（精準排版）、office-pptx 原生圖塊 | `business.md` |
| **System architecture (系統架構圖)** | 元件、流程、序列、API、資料流、部署拓樸 | Mermaid（嚴謹）、Excalidraw（簡報 hand-drawn 感） | `system-architecture.md` |

**Triage 第一句要問自己**：這支圖的內容**從 dataset 算出來**、**從商業概念推出來**、還是**描述一個系統**？

---

## Universal Rules (R1–R4)

四條規則對三類都適用，sub-file 衍生特化。

### R1: Canvas / Whitespace

- 主元素必須佔畫布 **≥ 80%**
- 不可有長邊（任一邊）空白帶 **> 8%**
- 幾何中心必須對齊容器中心（slide / panel / cell）
- **生成後強制量測 bbox** — 超標 → 重排，不超標才進下一題

判定：

```
bbox_fill_ratio  = chart_bbox_area / canvas_area  ≥ 0.80
max_edge_padding = max(top, bottom, left, right) / canvas_dim  ≤ 0.08
center_offset    = |chart_center - canvas_center| / canvas_dim  ≤ 0.05
```

若使用 matplotlib：`plt.tight_layout()` 不夠 — 同時設 `figsize` 跟 `bbox_inches="tight"` 並再量測。

### R2: Narrative-Beat Gate (生成前 hard gate)

**No beat, no chart.** 在生成任何 chart / table / 架構圖之前**強制**回答三題：

1. 對應 `storyline.md` 哪一句？（必填，照抄那一句）
2. 這張圖要 argue 什麼？一句話：__________
3. 觀眾看完應該記得什麼？一句話：__________

三題填不完整 → **STOP，不生成**。

這條 gate 對齊 deck-building memory 的 storyline-first 原則 — chart 是論點的可視化，不是裝飾。一張無 beat 的 chart 是噪音。

### R3: Homogeneity (同框 = 同 axes = 同 metric)

在同一個 chart 物件（同 axes）內：

- **不可混 metric**（例：溫度 °C 不能跟流量 L/min 同一個 y 軸）。非畫不可 → dual-axis，且兩軸 label 都明標單位 + 警告 reader
- **不可混時間粒度**（per-second + per-day 不能同框 — 解析度撐爆軸）
- **不可混對象族群**（顧客 + 員工 數字不能同框，除非語義上同 metric — e.g. NPS）
- **不可混單位制**（kWh + Wh 必須換算到同單位才畫）

打破這條 → 拆兩張圖 + 用連接線/比較表/小倍數 (small multiples) 說明關係。

### R4: Type-to-Structure (反「線性流程畫成象限」)

**先指認 data 的結構，再選 chart 類型**，不是反過來。

| Data structure | 對的 | 禁用 |
|---|---|---|
| 線性流程 / 時序步驟 (sequential, ordered) | flowchart / timeline / sankey | 2×2 / bar / 多欄 table / radar |
| 二維 qualitative positioning (2 dims) | 2×2 matrix / scatter+quadrant | flowchart |
| 趨勢 (over time, continuous) | line | bar（除非 N 離散點） |
| 對比 N ≤ 8 離散項 | vertical bar；N > 6 用 horizontal | line / pie |
| 對比 N > 8 離散項 | sorted table | bar / pie |
| 占比 part-of-whole (≤ 5 parts) | stacked bar / treemap；pie 慎用 | radar |
| 分佈 (distribution) | histogram / box / violin | line / bar |
| 關聯 / 相關 | scatter / heatmap | bar |
| 階層 hierarchy | tree / sunburst / treemap | flat table |
| N 維評分（同單位、≤ 6 dims） | radar — **僅此情境** | line |

完整反例集與每類細則見對應 sub-file。

---

## Pre-Generation Must-Check

**全勾才能進生成**：

- [ ] **R2 narrative beat** 已寫（對應 storyline 哪句、要 argue 什麼、觀眾記得什麼）
- [ ] **R4 chart type** 已查 mapping 表並標註對應 data-structure
- [ ] **Data 清洗完成**（numeric 型別確定、NaN/null 策略明確、單位一致）
- [ ] **Axis range / log-linear / truncation 決定**（避免 misleading；不刻意截軸放大差異）
- [ ] **Style file 已 load**（讀 `styles/<style-name>.md`，無對應 → 用 `styles/example.md` 並警告用戶）
- [ ] **Triage 已完成**（這支圖屬於 data / business / system 哪一類，sub-file 已讀）

任一項打 ✗ → 回頭補，**不要往下做**。

---

## Post-Generation Must-Check

**全勾才能交付**：

- [ ] **R1 canvas bbox 量測** — `fill ≥ 0.80`、`edge padding ≤ 0.08`、`center offset ≤ 0.05`
- [ ] **R3 同 axes 不混 metric / 時間粒度 / 對象族群 / 單位制**
- [ ] **Visual diff 可讀** — 不同 data 點是否能被肉眼看出差異（1% 差距不該看起來一樣）
- [ ] **Legend / axis label 完整不遮擋** — 不被 chart body / data points 覆蓋；過長 label 用斷行或縮寫並加註
- [ ] **Narrative beat 進 speaker notes / caption** — beat 不能只在 storyline 裡；caption 一行寫清楚這張圖 argue 什麼
- [ ] **對比 reference deck** — 同 client 上一頁的色盤、字型、grid 風格、margin 一致

任一項打 ✗ → 修正或砍掉重做，**不要交付半成品**。

### 機械化檢查（HTML 圖檔必跑）

R1 和「沒切版／沒 wrap／字級夠大」三題不靠肉眼估，跑腳本拿診斷：

```bash
node skills/docs/chart-design/references/check-html-figure.mjs <fig.html> \
  --width 1600 --height 900 --screenshot /tmp/check.png
# 直式捲動報告圖（如 qa-dataflow 功能關係圖）用 --height auto
```

每條診斷有 `code / subject / evidence / suggestion`，照 suggestion 修，改完再跑。
**兩輪沒讓錯誤數創新低就停**，把未解的診斷照實列出，不要第三輪 +1px 微調（重複 feedback = 方向錯）。
PNG / matplotlib 類圖表沒有 DOM，跳過這步，只做下面的肉眼審視。

### 交付收據（三種宣稱分開寫）

交付訊息附這段，欄位不准互相冒充：機械檢查過 ≠ 看過截圖，看過截圖 ≠ 機械檢查過。

```text
output: <絕對路徑>
mechanical_check: 0 errors, N warnings @1600×900 | skipped（非 HTML）
screenshot: <png 路徑> | skipped
visual_review: passed | failed（寫出看到的缺陷） | skipped（沒有影像讀取能力）
correction_rounds: 0 | 1 | 2
```

`visual_review: passed` 只能在 **Read 過截圖之後**寫；沒 Read 就寫 `skipped`。
`correction_rounds` 上限 2，超過代表 layout 選錯，回 Triage 重選圖型。

---

## Style Files

每個專案/客戶/品牌的風格存於 `styles/`：

```
skills/docs/chart-design/styles/
├── example.md          # 模板，新專案 copy 改名
├── richwave.md         # 立積電 (pending — 用 excalidraw / mermaid / 力成 HTML 為 baseline)
├── powertech.md        # 力成 (pending — 用其 HTML deck 為 baseline)
├── pitch-deck.md       # 投資人 BP 通用 (pending)
└── iot-factory.md      # IoT/廠務報告通用 (pending)
```

Style file 內容規格：色盤 hex、字型 family + sizes、grid 規則、margin、axis style、legend position、reference deck path。範例見 `styles/example.md`。

**沒對應 style file** → 用 `example.md` fallback **並警告**「這版 chart 沒鎖風格，下次請建立 `styles/<專案>.md`」。**禁止在 chart code 內 hardcode 顏色/字型** — style 是 SSOT。

---

## Triage 後 → 跳對應 sub-file

依 triage 結果讀對應 sub-file（**只讀對的那個**，避免 context 浪費）：

- **Data analysis** → `Read skills/docs/chart-design/data-analysis.md`
- **Business** → `Read skills/docs/chart-design/business.md`
- **System architecture** → `Read skills/docs/chart-design/system-architecture.md`

---

## Workflow Summary

```
1. Triage          → 三選一（data / business / system）
2. Load sub-file   → 讀對應 *.md
3. Load style file → 讀 styles/<name>.md，無 → fallback example.md + 警告
4. R2 narrative gate → 三題填完
5. Pre-check (6 題) → 全勾才生成
6. Generate         → 用 sub-file 指定的工具預設
7. Post-check (6 題) → 全勾才交付
8. 寫 caption + speaker notes（含 narrative beat）
```

---

## Anti-Patterns

| 不要 | 要 |
|------|---|
| 沒寫 narrative beat 就開始畫圖 | R2 gate：先回答三題 |
| 同一個 chart 混 metric 圖示「比較全貌」 | R3：拆兩張 + small multiples |
| 把「step 1 → step 2 → step 3」畫成 2×2 象限 | R4：流程用 flowchart / timeline |
| 為了「視覺平衡」截軸放大差異 | 標明 broken axis 或不截 |
| 大量留白「看起來高級」 | R1：≥ 80% fill、無 > 8% 空白帶 |
| 用 pie chart 比 > 5 個項目 | 改 stacked bar / sorted table |
| 不查 reference deck 就調色 | Style file 是 SSOT，不在 chart 裡 hardcode |
| 一張圖塞 7 條 line 比較 | 拆 small multiples |
| 表格只是 data dump 沒 argue | 每張表也適用 R2 — 不能說一句話 argue 什麼 → 砍 |
| 「補空白」加裝飾元素 | 留白合規（≤ 8%）就讓它留白，不塞圖示 |
