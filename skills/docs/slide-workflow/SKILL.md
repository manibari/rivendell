---
name: slide-workflow
description: >
  Gated presentation workflow: purpose → style → outline → content → Codex visual
  assets → generate → review → export. Prevents jumping to generation with no
  outline or missing visual briefs.
  TRIGGER: "做簡報", "做 deck", "準備提案", "幫我做 slides", "簡報流程".
  SKIP: complete outline + locked template + "直接生成".
tags: [docs, workflow]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Slide Workflow

Gated workflow + a pre-flight router. Each gate requires user confirmation before proceeding. Never skip a gate unless the user explicitly says to.

> 上層 routing 邏輯（哪一類 deck → 哪個 skill 接手）見 `~/.claude/CLAUDE.md` 的 `### Slide / Deck Building` flow。本 SKILL.md 是該 flow 的 D 路徑（通用流程）的執行細節。

## Pre-flight: Deck-Type Routing

確認 `slide-workflow` 是否真的是這次 deck 的主 skill。先問：

> 哪一類 deck？
> A. 投資人 BP / 募資簡報              → 交給 `/pitch-deck`（含 discovery interview，自己跑完整流程）
> B. 客戶客製提案                      → 交給 `/sales-material`（從素材庫組裝）
> C. IoT / 廠務分析報告                → 交給 `/iot-factory-report`（時序資料 → PPTX）
> D. B2B 首次拜訪 / 高階主管簡介 / 通用 → 由 slide-workflow 接手 → 繼續 Gate 0 ↓

判斷：

| 答案 | 動作 |
|------|------|
| A / B / C | STOP — 「請用 `/pitch-deck`（或對應 skill）」，結束 slide-workflow。不要重複跑流程。 |
| D | 進 Gate 0 |
| 用戶明說「不要那個 skill，就用 slide-workflow」 | 進 Gate 0（強制走 D） |

> 等待用戶選擇後才進入 Gate 0。

---

## Gate 0: storyline.md preflight

**這道 gate 是 2026-05-03 加上的，原因：cd63836f session（光泉 deck）浪費 5 個 edit cycle 在「邊做邊發現 storyline 薄弱點」。沒簽核 storyline 就動工 = 浪費時間。**

```bash
ls -la storyline.md 2>/dev/null
```

判斷：

| 狀況 | 動作 |
|------|------|
| 存在 + frontmatter `status: signed-off` | 進 Gate 1 |
| 存在但 status 是 `draft` 或缺漏 | STOP — 「找到 storyline.md 但還沒簽核。先跑 `/slide-office-hours` red-team 完才能進來。」 |
| 不存在 | STOP — 「沒找到 storyline.md。deck 沒 storyline 動工會浪費時間（參見 cd63836f 教訓）。從 `/slide-office-hours` 開始，會給你 template。」 |

**Override**: 用戶說「跳過 storyline gate」/「我知道，直接做」/「--skip-storyline」 — warn once：
> ⚠️ 跳過 storyline gate。如果中途發現結構/猜題/事實要改，那不是 bug，是這個決定的後果。

然後進 Gate 1。

**例外免 storyline 的場景**（自動跳過 Gate 0，不需 override）：
- 純內部 deck（不對外）
- 用戶明確說這是 quick mode + 「我已經想好了」

> 等待 storyline 簽核或 override 後才進入 Gate 1。

---

## Gate 1: 確認目的與受眾

Ask these (skip those already answered):

| 問題 | 為什麼問 |
|------|---------|
| 這份簡報的**目的**是什麼？ | 決定走哪條路徑（pitch-deck / sales-material / 技術報告） |
| **受眾**是誰？ | 決定語言、深度、專業術語程度 |
| **場景**？（面對面 / email 附件 / 線上會議） | 決定頁數和資訊密度 |
| **時間**？（10 分鐘 / 30 分鐘 / 無限制閱讀） | 決定 slide 數量 |

### 路徑對應

| 目的 | 主力 Skill | 預期頁數 |
|------|-----------|---------|
| 投資人 / 募資 | `pitch-deck` | 10-16 |
| 客戶提案 / BD | `sales-material` | 8-15 |
| 技術報告 / 分析 | 手動 + locked template | 5-20 |
| 公司介紹 / 形象 | `pitch-deck` (simplified) | 6-10 |
| 內部報告 | 手動 + minimal template | 3-8 |

**Gate 1 輸出**: 確認目的、受眾、場景、預期頁數。

> 等待用戶確認後才進入 Gate 2。

---

## Gate 2: 確認品牌風格

```bash
# 列出可用的 locked templates
ls mockups/slide-templates/*.html 2>/dev/null
ls ../*/mockups/slide-templates/*.html 2>/dev/null
```

展示選項給用戶：

| Template | 風格 | 適用 |
|----------|------|------|
| `chimes-ai.html` | 深海軍藍 + 幾何 accent + 奶油色 title card | Chimes AI / 詠鋐智能品牌簡報 |
| `cht-corporate.html` | 白底 + CHT 藍 + 企業風 | 中華電信合作簡報 |
| （其他） | ... | ... |

如果沒有匹配的 template，依「起點」選工具：

| 起點 | 動作 | Skill |
|------|------|-------|
| 客戶有寄參考 PPTX / Google Slides | 抽出設計系統 → 鎖定 HTML template | `/slide-template-extractor` |
| 沒有參考檔，要從零做品牌 | 設計色盤、字型、版面 | `/ui-ux-pro-max` + `/gstack-design-consultation` |
| 已有 mockups/slide-templates/*.html 但要微調 | 改 `:root` CSS variables（顏色/字型）即可 | manual edit |
| 預算/時間不夠，先用最接近的 | 用 neutral template + 換 logo | manual |

**Gate 2 輸出**: 確認使用哪個 template（檔案名稱）。

> 等待用戶確認後才進入 Gate 3。

---

## Gate 3: 確認大綱

這是最關鍵的一步。**不確認大綱就不動手生成任何 slide。**

**標題規則**：每頁標題只放主張或名詞短語，不掛解釋性子句或修辭前綴
（❌「光泉：三天後訂購量預測，整條迴路已經在跑」→ ✅「光泉：三天後訂購量預測」）；
解釋放「核心訊息」欄或 slide subtitle。

產出一份大綱表：

```markdown
## 簡報大綱

| # | Slide 類型 | 標題 | 核心訊息（1 句話） | 數據/素材來源 | Visual mode |
|---|-----------|------|-------------------|-------------|-------------|
| 1 | Cover | {title} | — | brand logo | image-heavy |
| 2 | Agenda | 目錄 | 3 個 section | — | native |
| 3 | Problem | {pain point} | 量化痛點 | discovery data | hybrid |
| 4 | Solution | {product/service} | 1 flow 或 3 步驟 | product info | hybrid |
| 5 | How it works | {demo/arch} | 技術示意 | screenshot/diagram | native |
| 6 | Traction | {metrics} | 數字說話 | CRM / 報告 | native |
| 7 | Case study | {client name} | before → after | case study doc | hybrid |
| 8 | Team | {key people} | 相關經歷 | bios | hybrid |
| 9 | Ask / Next steps | {CTA} | 明確行動 | — | hybrid |
```

### 大綱原則
- **每張 slide 只有一個核心訊息**
- 核心訊息用 1 句話寫完（如果需要 2 句，拆成 2 張 slide）
- Cover / Agenda / Closing 不算在「核心 slides」裡
- 數據 slide 必須標明數據來源
- 每張 slide 必須標明 visual mode：`native`、`hybrid`、`image-heavy`
- 如果有 demo / screenshot / generated hero image，標明「需要準備 image」
- `hybrid` / `image-heavy` 必須在 Gate 4.5 產生 visual brief，不可直接進 HTML

**Gate 3 輸出**: 用戶確認大綱表（可能修改順序、增刪 slides、調整核心訊息）。

> 等待用戶確認後才進入 Gate 4。

---

## Gate 4: 蒐集內容

依大綱逐張蒐集素材。根據「數據/素材來源」欄位決定工具：

| 來源 | 工具 |
|------|------|
| 客戶情報 | `sales-customer-intel` / `tw-company-lookup` |
| CRM 數據 | `sales-crm-projection` |
| 案例庫 | `sales-material` (match case studies) |
| 補助資料 | `gov-subsidy-scraper` output |
| 網路研究 | `autoresearch` / `WebSearch` |
| 既有文件 | Read local files |
| 需要用戶提供 | 列出清單請用戶補充 |

**如果有素材缺口**（用戶需要提供但還沒有的），**在這裡停下來要求**，不要等到生成時才發現缺。

**Gate 4 輸出**: 所有 slide 的素材已就位（或用戶確認「先用 placeholder」）。

> 等待用戶確認後才進入 Gate 4.5。

---

## Gate 4.5: Codex 視覺圖片資產

這道 gate 只處理 `hybrid` 和 `image-heavy` slides。目標是把圖片生成變成正式素材供應鏈，而不是在做 PPTX 時臨場補洞。

### 先分類

| Visual mode | 處理方式 |
|-------------|----------|
| `native` | 不生成圖片；用 template 元件、圖表、表格、icon、diagram |
| `hybrid` | 產生背景/情境/產品脈絡圖片，再用原生文字與標註覆蓋 |
| `image-heavy` | 產生全版主視覺，保留 safe area 給原生標題/副標 |

### Codex handoff

圖片資產由 Codex 的 image generation 能力產生。若目前正在 Claude Code 中執行，先輸出 `visual_briefs.md`，交給 Codex 生成圖片後再回到本流程；不要讓 Claude Code 用 CSS 漸層、抽象裝飾、假 stock 圖或圖片內文字替代。

### Visual brief

每張圖用這個格式：

```markdown
## slide-03-problem-bg
- slide purpose:
- audience/tone:
- image role: hero | background | concept visual | customer scene | product context
- visual subject:
- composition:
- aspect ratio: 16:9
- safe area:
- template palette/style constraints:
- negative constraints: no visible text, no logos, no fake UI, no watermarks, no tiny details
- output path: assets/generated/slide-03-problem-bg.png
```

保存規則：
- 圖片放在 `{output-dir}/assets/generated/` 或 `assets/generated/`
- brief/prompt 與圖片同名保存，方便重生
- 檔名包含 slide 編號與角色，例如 `slide-01-cover-hero.png`
- 同步建立 `visual_assets.json`，讓 `office-pptx` 不用從 markdown 猜圖檔與 placement

`visual_assets.json` 最小格式：

```json
{
  "deck_id": "client-deck",
  "assets": [
    {
      "slide_id": "slide-03",
      "slide_number": 3,
      "mode": "hybrid",
      "role": "background",
      "brief_path": "visual_briefs.md#slide-03-problem-bg",
      "image_path": "assets/generated/slide-03-problem-bg.png",
      "prompt_path": "assets/generated/slide-03-problem-bg.prompt.md",
      "status": "briefed",
      "safe_area": "right 35% clear for title and metrics",
      "placement": {"fit": "cover", "focal_point": "left center", "overlay": "dark 30%"}
    }
  ]
}
```

狀態規則：
- `briefed`: 已寫 brief，尚未產圖
- `generated`: 已產圖，尚未人工/縮圖確認
- `approved`: 可進 final PPTX
- `draft-placeholder`: 只允許內部草稿或用戶明確接受低保真交付

禁止用圖片生成的內容：
- 真實 logo、精確 UI screenshot、架構圖文字、財務圖表、KPI 數字、法規文字、小字密集頁
- 這些內容用原生 slide 元素或來源素材處理

**Gate 4.5 輸出**: 所有 `hybrid` / `image-heavy` slides 都有 `approved` 圖片資產；或用戶明確確認這次只輸出 draft/internal 版本。

> 等待圖片資產確認後才進入 Gate 5。

---

## Gate 5: 生成 HTML Slides

**必須使用 Gate 2 確認的 locked template**。

1. Read the template file → 提取 `:root` CSS variables + slide component classes
2. 依 Gate 3 大綱逐張生成 HTML，並使用 Gate 4.5 的 generated assets
3. 每張 slide 使用 template 裡對應的 slide 類型（cover / section / cards / comparison / metrics / table）
4. 如果大綱有 template 未提供的 slide 類型，用最接近的 slide 類型改造
5. 存檔：`{output-dir}/{client}-deck.html`

**注意 CJK 字型**：如果 template 的 font stack 有 `Noto Sans TC`，確認 Google Fonts link 存在。

**圖片分層規則**：
- 圖片只承擔背景、情境、產品脈絡或主視覺
- 標題、副標、註解、數據、logo、CTA 都用 HTML/PPT 原生元素
- 不拉伸圖片；用 cover/crop/position 保持比例
- 背景圖片加 overlay 或遮罩，確保文字對比足夠

**Gate 5 輸出**: HTML 檔案路徑 → 請用戶在瀏覽器打開確認。

```bash
open {output-dir}/{client}-deck.html
```

> 等待用戶看完確認後才進入 Gate 6。

---

## Gate 6: 審閱與修改

用戶會說哪些 slides 需要改。常見修改：

| 修改類型 | 處理方式 |
|---------|---------|
| 文字修改 | Edit HTML content only |
| 順序調整 | 搬動 `<div class="slide">` block |
| 刪除 slide | 移除整個 block |
| 新增 slide | 複製最近的同類型 block，換內容 |
| 顏色/字型 | **不改** — 回去改 template 的 `:root` variables |
| 版面結構 | 換成 template 裡另一個 slide 類型 |

**反覆循環** Gate 5-6 直到用戶滿意。

> 用戶說「OK」或「可以了」後進入 Gate 6.5。

---

## Gate 6.5: 文字打磨 + 視覺一致性（recommended，可省略）

| 動作 | 工具 | 何時跳過 |
|------|------|---------|
| 移除 AI slop / 檢查繁中口吻（「值得注意的是」「進一步」「綜上所述」） | `/de-slopify` | 內部 deck 不對外 |
| 視覺一致性檢查（行距、對齊、色彩濫用） | `/gstack-design-review` | 已用 locked template 且只動文字 |
| 撰寫講者備註 | manual or `/office-pptx` speaker notes API | 純閱讀型 deck |

> 確認後進入 Gate 7。

---

## Gate 7: 輸出

依交付場景選格式：

| 格式 | 適用 | Skill |
|------|------|-------|
| **PPTX**（客戶交付 / 高階主管 / 公司模板） | 大多數 B2B 場景 | `/office-pptx`（html2pptx） |
| **Google Slides**（多人協作編輯） | 客戶要邊看邊改 | `/gdoc-report-builder` |
| **HTML deck**（線上分享 / 不要 PPTX 重量） | webinar / blog 內嵌 | `/gstack-design-html` |
| **PDF**（email 附件 / 鎖定不能改） | 法務 / 投標附件 | print-to-PDF from HTML or PPTX export |

存檔慣例：`{output-dir}/{client}-deck.{ext}`

交付後確認：
> 簡報已匯出：`{path}`
> 需要其他格式嗎？

---

## Quick Mode

如果用戶說「跳過流程，直接做」，仍然**至少確認 3 件事**：

1. 用哪個 template？（如果不確認 → 風格漂移）
2. 幾張 slides？（如果不確認 → 頁數失控）
3. 核心訊息是什麼？（如果不確認 → 內容空洞）

這 3 個是 non-negotiable，即使 quick mode 也不跳。

---

## Anti-Patterns

| 不要 | 要 |
|------|---|
| 沒確認 template 就開始寫 HTML | Gate 2 先選 template |
| 沒確認大綱就開始填 slide 內容 | Gate 3 先確認每張 slide 的 1 句話核心訊息 |
| `hybrid` / `image-heavy` 沒 visual brief / `visual_assets.json` 就做 HTML | Gate 4.5 先讓 Codex 產生圖片資產 |
| 讓圖片生成出現標題、數字、logo、UI 字 | 圖片只當主視覺，所有文字與資料用原生元素 |
| 在 HTML 裡硬寫顏色/字型 | 使用 template 的 `:root` CSS variables |
| 一次生成 20 張 slides | 先做 3-5 張讓用戶確認風格對不對，再做剩下的 |
| 發現缺素材時用 placeholder 蒙混 | Gate 4 就列出缺口，請用戶補 |
| 改完不讓用戶看就直接輸出 PPTX | Gate 6 的 HTML review 是必要的 |
