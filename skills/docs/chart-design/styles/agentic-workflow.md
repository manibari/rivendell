# Chart Style: Agentic-Workflow 研究

| 欄位 | 值 |
| --- | --- |
| Project | AIOS 與 Dify 平台研究 |
| Use case | 內部工程文件、架構說明 |
| Reference deck path | 無（本專案為 Markdown 工程文件） |
| Last updated | 2026-09-19 |
| Notes | 風格由助理暫定，未對齊詠鋐既有簡報樣式。對外簡報前應重新指定。 |

## Color Palette

```
brand-primary    : #2F5BEA   /* AIOS 主色，取自平台登入鈕藍 */
brand-secondary  : #7C3AED   /* metavision 紫 */
ink              : #1F2937
ink-muted        : #6B7280
canvas           : #FFFFFF
panel            : #F3F4F6
positive         : #10B981   /* 已驗證 */
negative         : #EF4444   /* 風險 / 未開放 */
warning          : #F59E0B   /* 推論未證實 */
neutral          : #9CA3AF
```

## 線條語義（本專案專用，重要）

| 樣式 | 意義 |
| --- | --- |
| 實線 `-->` | 已實地觀察到的關係 |
| 虛線 `-.->` | 依設定頁語意或說明文字推論，未直接驗證 |
| 粗線 `==>` | 主要資料路徑 |

**規則：任何未經實機驗證的元件或連線一律用虛線，並在圖說標明。**
本研究未取得後端原始碼，模組內部切分屬推論。

## 圖型預設

內部工程文件用 Mermaid。對外簡報改用 Excalidraw 或 HTML/CSS。
