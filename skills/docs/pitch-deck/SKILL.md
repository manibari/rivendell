---
name: pitch-deck
description: >
  Pitch decks / investor presentations with strategic storytelling — discovery interview,
  narrative planning, Codex-generated visual asset briefs, HTML slide generation,
  PPTX export.
  TRIGGER: "做 BP", "投資人 deck", "pitch deck", "募資簡報", "investor presentation".
  SKIP: technical docs or internal status (office-pptx).
tags: [docs, workflow]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep, WebSearch"
---

# Pitch Deck

Strategic business presentation — from blank page to final PPTX.

## Phase 1: Discovery Interview

Ask these questions before writing any slide. Skip those already answered in context.

**Company & Product**
- 公司/產品名稱是什麼？一句話描述它做什麼？
- 解決什麼問題？目前的解法為何（現狀 / 痛點）？
- 你們的解法為何更好？（差異化/護城河）

**Market**
- 目標客戶是誰？（B2B / B2C / B2G）
- 市場規模估計（TAM/SAM/SOM）？有沒有參考數據？
- 主要競爭對手？

**Traction & Team**
- 目前進展？（用戶數、MRR、客戶名單、POC 等）
- 創辦團隊背景（1-2 句）？

**The Ask**
- 這份 deck 的目的？（種子輪募資、BD 提案、競賽、內部報告）
- 募資金額 / 期望成果？

---

## Phase 2: Narrative Structure

Map answers to slides. Standard investor pitch flow:

| # | Slide | 核心訊息 | 1 sentence hook | Visual mode |
|---|-------|---------|-----------------|-------------|
| 1 | Cover | 公司名 + tagline | 讓人想繼續看 | image-heavy |
| 2 | Problem | 痛點有多真實 | 觀眾點頭認同 | hybrid |
| 3 | Solution | 你怎麼解決 | 簡單直覺 | hybrid |
| 4 | How It Works | 產品邏輯 | 1 flow 或 3 步驟 | native |
| 5 | Market | 機會多大 | TAM → SAM → SOM funnel | native |
| 6 | Traction | 你已證明什麼 | 數字說話 | native |
| 7 | Business Model | 怎麼賺錢 | 清晰的收費邏輯 | native |
| 8 | Competition | 為何你贏 | 2×2 matrix 或 feature table | native |
| 9 | Team | 為何你們能做到 | 相關經歷背書 | hybrid |
| 10 | Ask | 你要什麼 | 明確的數字與用途 | hybrid |

> Adjust slide count based on deck type:
> - **Seed (≤12 slides)**: skip Competition if market is new
> - **Series A (12-16 slides)**: add Financial Projections, Roadmap
> - **BD/Sales deck**: replace Ask with Next Steps + CTA
> - **Competition deck**: add Demo slide, shorten Team

---

## Phase 2.5: Codex Visual Asset Strategy

For polished external decks, decide the visual mode for every slide before writing
HTML. Use images for emotional framing and scene-setting; keep text, charts,
tables, logos, diagrams, numbers, and labels as native slide elements.

### Visual modes

| Mode | Use when | How to build |
|------|----------|--------------|
| `native` | Data, charts, tables, process diagrams, architecture, dense claims | PPT/HTML shapes, text, icons, charts |
| `hybrid` | Needs a hero/background/product context but must stay editable | Codex-generated image plus native title, labels, callouts |
| `image-heavy` | Cover, section divider, vision slide, customer scene, strategic concept | Full-bleed Codex-generated image with native overlay text |

### Codex image generation rule

If a slide is `hybrid` or `image-heavy`, create a visual brief and use Codex with
image generation to produce the raster asset. If the current runtime cannot
generate images, write the briefs to `visual_briefs.md` and hand them to Codex
before final slide generation. Do not let Claude Code substitute CSS blobs,
generic gradients, fake stock photos, or text drawn into an image for this step.

### Visual brief format

Create one brief per visual slide:

```markdown
## slide-01-cover-hero
- slide purpose:
- audience/tone:
- image role: hero | background | concept visual | customer scene | product context
- visual subject:
- composition:
- aspect ratio: 16:9
- safe area: e.g. left 42% clear for title
- style constraints: inherit locked template palette; no visible text
- negative constraints: no logos, no fake UI, no watermarks, no tiny text, no dark muddy crop
- output path: assets/generated/slide-01-cover-hero.png
```

Store generated assets in `assets/generated/` or `{output-dir}/assets/generated/`
and save the prompt/brief beside the image. The filename must include the slide
number and role so `office-pptx` can place it deterministically.

Also create or update `visual_assets.json` beside `visual_briefs.md` so the PPTX
step can consume image placement deterministically:

```json
{
  "deck_id": "company-pitch",
  "assets": [
    {
      "slide_id": "slide-01",
      "slide_number": 1,
      "mode": "image-heavy",
      "role": "hero",
      "brief_path": "visual_briefs.md#slide-01-cover-hero",
      "image_path": "assets/generated/slide-01-cover-hero.png",
      "prompt_path": "assets/generated/slide-01-cover-hero.prompt.md",
      "status": "briefed",
      "safe_area": "left 42% clear for title",
      "placement": {"fit": "cover", "focal_point": "right center", "overlay": "dark 35%"}
    }
  ]
}
```

Use `status: approved` only after the generated image is visually checked. For
external decks, unresolved or placeholder generated assets block final PPTX
export unless the user explicitly accepts draft quality.

### When not to generate an image

Do not use image generation for financial charts, KPI numbers, exact UI
screenshots, real logos, product screens that must be accurate, architecture
labels, legal/compliance claims, or any small text. Use native slide elements or
provided source assets instead.

---

## Phase 3: HTML Slides

### CRITICAL: Use a Locked Template First

**Before writing any HTML**, check for locked brand templates:

```bash
ls mockups/slide-templates/*.html 2>/dev/null
ls ../*/mockups/slide-templates/*.html 2>/dev/null
```

If a template matching the client/brand exists (e.g. `chimes-ai.html`, `cht-corporate.html`), **read it and reuse its `:root` CSS tokens, slide layouts, and component classes**. Do NOT invent a new style. Only the slide *content* (text, numbers, list items) changes — colors, fonts, spacing, and slide structure stay locked to the template.

If no template exists for this brand, ask:
> 沒有找到鎖定的品牌 template。要不要先用 `slide-template-extractor` 從一份既有簡報抽出 template？或要我先建一個臨時版本？

**Why this rule exists**: Without a locked template, slide style drifts every session — sometimes good, sometimes bad. Locked templates make output deterministic.

### Generate slides

Generate one HTML file per 3-4 slides, or a single-file multi-slide deck using a scroll or nav structure.

### Slide design principles
- One main idea per slide — supporting content is secondary
- Max 5 bullet points; prefer visuals (Codex images, charts, icons, diagrams) over text
- Brand color: **always inherit from the locked template's `:root` variables**, never invent
- Font: Inter or Geist Sans (load from Google Fonts if HTML)
- Generated images are visual assets only: overlay all copy, callouts, data labels,
  and logos as native HTML/PPT elements so the deck remains editable and readable.

### HTML slide template

```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>[Company] Pitch Deck</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', sans-serif; background: #0f0f1a; color: #fff; }
    .slide {
      width: 1280px; height: 720px;
      display: flex; flex-direction: column;
      justify-content: center; align-items: flex-start;
      padding: 80px; page-break-after: always;
      background: #0f0f1a; border: 1px solid #222;
      margin-bottom: 40px;
    }
    .slide-number { position: absolute; bottom: 24px; right: 32px;
      font-size: 12px; color: rgba(255,255,255,0.3); }
    h1 { font-size: 52px; font-weight: 700; line-height: 1.1; margin-bottom: 24px; }
    h2 { font-size: 36px; font-weight: 600; margin-bottom: 16px; color: #4ecdc4; }
    p, li { font-size: 22px; line-height: 1.6; color: rgba(255,255,255,0.85); }
    .tagline { font-size: 28px; color: #4ecdc4; margin-top: 12px; }
    .metric { font-size: 64px; font-weight: 800; color: #4ecdc4; }
    .metric-label { font-size: 18px; color: rgba(255,255,255,0.6); margin-top: 4px; }
  </style>
</head>
<body>
  <!-- Slides go here -->
</body>
</html>
```

### Visual components to use

- **Problem**: quote/story from a real user, then stats
- **Cover / section**: Codex-generated full-bleed image with safe area for title
- **Solution**: Codex-generated context image or real product screenshot plus native 3-step flow
- **Market**: TAM/SAM/SOM concentric circles or bar chart
- **Traction**: metric cards (`<div class="metric">`)
- **Competition**: 2×2 positioning matrix (CSS grid)
- **Team**: headshot placeholder + name + 1-line bio

---

## Phase 4: Export to PPTX

After HTML is finalized, hand off to `office-pptx` skill:

> "HTML slides 已完成。現在用 office-pptx 將這些 slides 轉換成 PPTX 格式，
> 保持相同的設計風格與品牌色。每個 HTML slide 對應一頁 PPTX。"

Or if user needs editable PPTX directly (without HTML preview first):
Use `office-pptx` skill with the narrative structure above to generate PPTX directly.

---

## Slide Copy Principles

- **Problem slide**: lead with a relatable story or shocking stat, not abstract description
- **Solution slide**: show the product in 1 image or 3-step flow; avoid feature lists
- **Traction slide**: only metrics that prove demand (revenue, users, NPS, pilots); omit vanity metrics
- **Ask slide**: specific amount + specific use of funds (not "grow the team") + timeline
- **Team slide**: relevance over prestige — connect past experience directly to this problem
