# Chart Style: 光泉 A批訂購量預測 BI (kuangchuan-bi)

> 色票與字型**不是為圖表新訂的**，是實查 `frontend/styles.css` 的 `:root` CSS 變數
> 抄回來的（該檔又沿用 2026-05-29 PoC 看板）。圖表跟產品畫面同一套，才不會
> 文件裡的架構圖看起來像另一個系統的。改色請先改 `frontend/styles.css`，再同步這裡。

---

## Brand / Project

| 欄位 | 值 |
|------|-----|
| Project / Client | 光泉（中華電 presales）/ kuangchuan-bi |
| Use case | 內部工程文件（SA/SD、資料流圖、QA 落差圖）＋ 看板內嵌圖表 |
| Reference | `frontend/styles.css` `:root`（SSOT）、`docs/design-reference/poc-dashboard-v1.html` |
| Last updated | 2026-09-16 |
| Notes | 無框架、無 build chain；看板僅一個外部相依（Leaflet）。圖表不要引入新的圖表函式庫 |

---

## Color Palette

### Primary (主色)

```
brand-primary    : #215CA0   /* --cover  標題、主結構框線 */
brand-secondary  : #297FD5   /* --accent 強調邊、選中態 */
brand-tertiary   : #002060   /* --navy   最深層，頁首與帶標題 */
```

### Neutrals

```
ink              : #1a2233   /* --ink   文字 */
ink-muted        : #7b8b9c   /* --gray  副標、格線 */
canvas           : #ffffff   /* --card  圖面底 */
panel            : #f4f6fa   /* --bg    容器底 */
line             : #e3e8f0   /* --line  分隔線、方框邊 */
tint             : #EDF2FD   /* --tint  帶底色（半透明群組框用這個）*/
```

### Semantic

```
positive         : #3FB984   /* --green 有防護 ✓ / 正常 */
negative         : #D9534F   /* --red   無防護 ✗ / 高風險 */
warning          : #E8A33D   /* --amber 只做一半 ◐ / 需覆核 */
neutral          : #7b8b9c   /* --gray  基準線、無變化 */
```

三態關卡標示（qa-dataflow / SD §7 專用，語義固定不可換色）：
`✓ positive` · `✗ negative` · `◐ warning`

### Categorical Palette (≤ 6 colors)

```
cat-1: #215CA0
cat-2: #3FB984
cat-3: #E8A33D
cat-4: #297FD5
cat-5: #FF8379   /* --coral */
cat-6: #7b8b9c
```

不是 colorblind-safe（cat-3 琥珀 vs cat-5 珊瑚在 deuteranopia 下會靠近）。
**多序列圖一律同時用標記形狀或圖樣填充區分**，不要只靠顏色。

### Sequential / Diverging

```
sequential       : #EDF2FD → #002060（tint→navy 單色階）
diverging        : #D9534F ← #f4f6fa → #3FB984（紅-灰-綠，用於誤差正負）
```

---

## Typography

```
font-family-base  : "PingFang TC", "Microsoft JhengHei", Arial, sans-serif
font-family-mono  : "SF Mono", Menlo, monospace
font-family-cjk   : 同 base（本專案全中文，不分離 CJK stack）
```

字級下限（圖內，1600 寬）：節點標題 15px、節點副標 12px、邊標籤 12px、帶標題 17px。
低於此值在 PNG 縮圖裡會讀不出來。

---

## Grid / Layout

- 架構圖固定 1600×900；直式資料流圖用 `--height auto`
- 群組／帶用**虛線框 + `tint` 半透明底**，不用實線（會跟節點邊界混淆）
- 節點方框 `border-radius: 8px`、`1px solid line`、底 `canvas`
- 邊標籤加**白底標籤片**壓在線上，否則短間距會疊到方框
- 箭頭語義：實線 = 同步呼叫／主幹；虛線 = 唯讀旁掛或 async；外側繞行 = 回頭路
