# Data Analysis Charts (數據分析圖表)

> Read this after triage. 主檔 `SKILL.md` 的 R1–R4 + pre/post must-check 依然全套適用。本檔只補上 data-driven viz 的工具預設、軸規則、配色規則、每類 chart 的細節規則跟反例。

---

## Tool Defaults

| 用途 | 工具 | 為什麼 |
|------|------|--------|
| 靜態 PNG → 嵌 PPTX / Google Slides | **matplotlib**（or seaborn for one-liners） | 排版可控、輸出穩定、跟 iot-factory-report 同棧 |
| 互動 / drill-down / 多頁 dashboard | **plotly** | hover / zoom / export 一條龍 |
| HTML deck 內嵌 | **Chart.js** or **ECharts** | 跟 slide-workflow / pitch-deck 的 HTML template CSS 共用 |
| 學術風 / paper figure | **matplotlib + seaborn** with serif font | 自帶 publication theme |

**不要混用** — 一份 deck 內 chart library 只能一套（同 deck 多種 library = 視覺漂移）。

---

## Per-Chart-Type Rules

### Line Chart (趨勢)

- Max **6** lines。超過 → 拆 small multiples 或 highlight one focus + 其他 grey out
- 線條 **endpoint 必須有 label**（不靠 legend；legend 是備援不是主檢索）
- **不要平滑化**（moving average 之外）除非有明確 narrative beat（用 raw + MA 雙線示意）
- x 軸是時間 → **連續 datetime axis**，不要 categorical（不然 gap 看不出來）
- gap / 缺資料 → 用點+斷線，不要直接連過去（misleading）

### Bar Chart (對比)

- **預設 sorted by value（desc）**，除非語義要求順序（時間、流程）
- N ≤ 6 → vertical bar；6 < N ≤ 8 → horizontal bar；N > 8 → sorted table
- **不要 3D bar**，**不要漸層填色**（除非真的有第三維 data）
- Stacked bar：最多 4 個 segment；超過 → 改 streamgraph 或拆圖
- Bar width / gap 比例：bar 佔 60–70%，gap 30–40%（密集易讀）

### Scatter Plot (關聯)

- 點數 > 500 → 用 `alpha=0.3` 顯示密度 or 改 heatmap / 2D histogram
- **標 outlier**（z > 2.5 標 label，z > 3 加 annotation 解釋）
- 加 trend line **只有在有實際 fit** 的時候 — 不要為了「看起來有相關」硬加
- x/y 軸應有**對等的視覺權重**（若 x range 是 0–100、y 是 0–1，scale 視覺要平均 — 用 `set_aspect`）

### Histogram / Distribution

- Bin 數用 Sturges (`int(np.log2(n)+1)`) 或 Freedman-Diaconis；**不要用 default 10**
- 高度 skew → 用 log-y 或畫 ECDF 取代
- 多個 distribution 對比 → violin / box，不要疊 histogram
- **必標 N**（樣本數）在 caption 或 corner

### Heatmap

- 配色 sequential（單向）vs diverging（有中心點）— **不能搞錯**
- 軸 label 多 → 旋轉 45° or 縮寫 + tooltip
- 加 colorbar **必標單位**
- 不要把名目資料當數值畫 heatmap（要 categorical → 用 categorical colormap）

### Time-Series Special Rules

- Sampling interval **必須一致** — 不一致 → resample 後標明
- 異常點用獨立 marker（如紅圓點 + outline），不混在主線上
- 多 series 同框 → 確認 R3（同單位、同時間粒度）
- Long range（>1 year）→ 加 minor ticks 跟 zoom panel

---

## Axis Rules

- **預設 zero-based**（bar、area、stacked 強制）
- Line / scatter 在 range 很窄、語義上 zero 無意義時，可以 non-zero — 但**標 broken axis** 或在 caption 警告
- **Log scale** 用條件：range > 2 個數量級、或 distribution 高度 skewed。標 caption 寫明
- Truncation 絕對禁止為了「放大差異」— 視為 misleading
- Date axis 用 ISO format（`2026-05-18`），不要 `5/18/26`

---

## Color Rules

### Categorical (區分類別)

- **最多 6 色**（再多 → 拆圖 / small multiples）
- 用 colorblind-safe palette：`tab10` 是底線，更好的是 Okabe-Ito 或 ColorBrewer Set2
- **不要用紅 + 綠** 表達二類別對比（色盲不可讀）— 改藍/橘

### Sequential (單向程度)

- viridis / cividis / magma — 不要 jet / rainbow
- 一定要有 colorbar + 單位

### Diverging (有中心值)

- RdBu / BrBG / PiYG — 中心點明確（通常是 0 或 baseline）
- 兩端飽和度要對等

### Style file 覆蓋

- `styles/<name>.md` 若指定 brand colors → **照用 brand 不用預設**（brand colors 要先檢查 colorblind-safe；若不行，配 pattern fill 補強）

---

## Data Cleaning Pre-Check (R2 上層補充)

生成前必確認：

- [ ] Numeric 型別正確（不是 string 偽裝成數字）
- [ ] NaN / null 策略：drop / fill 哪個？標 caption
- [ ] 單位一致（公斤 vs 公克、°C vs °F、kWh vs Wh 都要先換算）
- [ ] Outlier 已決定處理（保留標 outlier / winsorize / drop + 標 caption）
- [ ] 時序資料 interval 一致或已 resample
- [ ] 如果是 ratio / percentage，分母明確（per-population vs per-event）

---

## Anti-Patterns (此類專屬)

| 不要 | 要 |
|------|---|
| 為了讓兩條 line 看起來分得開，截 y 軸 | 用真實 zero-based or 標 broken axis |
| 7 條 line 一張圖比較 | small multiples / highlight 1 focus |
| Pie chart 比 8 個產品市占 | sorted bar / treemap |
| 用 rainbow colormap 表示連續值 | viridis / cividis |
| 紅線 + 綠線表達 good/bad | 藍/橘 + 圖示輔助 |
| Histogram 用 default bin 數 | 用 Sturges / FD 估算 |
| Scatter 1000 點不加 alpha | `alpha=0.3` 或 heatmap |
| Heatmap 沒 colorbar | 必加 + 標單位 |
| Stacked bar 6+ segment 想看趨勢 | streamgraph 或拆 line chart |
| 缺資料直接連線過去 | 斷線 + 點標 missing |
