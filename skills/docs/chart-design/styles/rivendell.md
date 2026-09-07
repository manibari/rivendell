# Chart Style: rivendell

> Source of truth for any figure that goes into rivendell's own docs or dashboard.
> Derived from `dashboard-next/DESIGN.md` (forest-green accent, sequential greens,
> differentiate by label not color). Do not hardcode these in chart code — read here.

## Brand / Project

| 欄位 | 值 |
|------|-----|
| Project | rivendell（skills library + dashboard） |
| Use case | docs/ 內嵌圖、dashboard 圖表、README 圖 |
| Reference | `dashboard-next/DESIGN.md`、`dashboard-next/src/app/globals.css` |
| Last updated | 2026-09-07 |
| Notes | 語義靠標籤與形狀，顏色只分「層級／狀態」，不做彩虹 |

## Color Palette

```
accent        : #2d4a3e   /* 主色：主線、強調框 */
accent-soft   : #5b7a6a   /* 次強調、連線 */
accent-bg     : #e8efea   /* 主色淡底（pastel，配深字） */
seq-2         : #a3bbb1   /* 次級層 */
seq-3         : #dfe7e3   /* 最淡層 */
ink           : #0a0a0a
ink-muted     : #6b7280
ink-subtle    : #9ca3af
canvas        : #fafafa
surface       : #ffffff
border        : #e5e7eb
border-strong : #d1d5db
status-ok     : #10b981
status-warn   : #f59e0b   /* 缺環、待補 */
status-err    : #ef4444
```

## Mermaid classDef（直接貼）

每個 classDef 都設 fill / stroke / color（深淺模式都可讀，見 mermaid-theme.md §1）。

```
classDef tier fill:#e8efea,stroke:#2d4a3e,color:#0a0a0a
classDef tierSoft fill:#dfe7e3,stroke:#5b7a6a,color:#0a0a0a
classDef artifact fill:#ffffff,stroke:#d1d5db,color:#374151
classDef gap fill:#fff7e6,stroke:#f59e0b,color:#8a5a00,stroke-dasharray:5 4
classDef done fill:#e8efea,stroke:#10b981,color:#0a0a0a
classDef lost fill:#fdf5f5,stroke:#ef4444,color:#7f1d1d
classDef once fill:#2d4a3e,stroke:#2d4a3e,color:#ffffff
```

## Typography

- 圖內字型跟 renderer 走（GitHub / mmdc 預設），不設 `%%{init}%%`
- 節點主標 ≤ 6 個中文字或 3 個英文詞；副標用 `<br/>` 一行

## Layout

- 流程圖 `flowchart LR` 為主，分層用 `subgraph`
- 每張 ≤ 12 節點；超過就拆
- 交接物（檔案）畫成獨立節點放在邊上，不塞進箭頭標籤
