---
name: slide-template-extractor
loop: sales
pdca: plan
description: >
  Extract design system from existing PPTX/Google Slides → locked HTML slide template
  with CSS variables. Stops style drift across deck generations.
  TRIGGER: "把這份簡報的風格做成 template", "extract slide design", "鎖定簡報風格".
  SKIP: create from scratch (pitch-deck / sales-material); edit existing PPTX (office-pptx).
tags: [docs, workflow]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep, WebFetch"
---

# Slide Template Extractor

Convert an existing brand deck → locked HTML template that pitch-deck and sales-material can reuse.

## Output Location

By default, save extracted templates to `mockups/slide-templates/{name}.html` in the current project, or to a project-specific location if the user specifies one.

---

## Phase 1: Identify Source

Ask the user (or detect from context):
- **Source type**: Local .pptx file? Google Slides URL? Google Drive file?
- **Target name**: e.g. `chimes-ai`, `cht-corporate`, `sabre-2026`
- **Brand context**: What client/company is this for?

---

## Phase 2: Download / Access

### Local PPTX
Already accessible — skip to Phase 3.

### Google Drive PPTX upload
URL pattern `/presentation/d/{ID}/edit?slide=id.p1` (long ID with dashes/underscores) usually = .pptx upload.

```python
# Use mcp__google-drive__downloadFile
fileId = "<extracted from URL>"
localPath = "/tmp/source-template.pptx"
```

If `getGoogleSlidesContent` returns "operation not supported", it confirms .pptx upload — use `downloadFile` instead.

### Native Google Slides
URL pattern `/presentation/d/{ID}/edit` where `getGoogleSlidesContent` works.

```python
# Use mcp__google-drive__getGoogleSlidesContent for text + structure
# Use mcp__google-drive__exportSlideThumbnail for visual reference
```

If `downloadFile` fails with `exportSizeLimitExceeded` (large native Slides), use `getGoogleSlidesContent` + multiple thumbnails instead.

---

## Phase 3: Extract Design Tokens

### From .pptx (preferred — most accurate)

```bash
# Unzip
cd /tmp && rm -rf source-pptx && unzip -q source-template.pptx -d source-pptx

# Theme colors (in order: dk1, lt1, dk2, lt2, accent1-6)
grep -o 'srgbClr val="[0-9A-F]*"' source-pptx/ppt/theme/theme1.xml | sort -u

# Theme fonts
grep -o 'typeface="[^"]*"' source-pptx/ppt/theme/theme1.xml | sort -u
```

```python
# Inspect each slide's text + actual colors used
from pptx import Presentation
p = Presentation('/tmp/source-template.pptx')
print(f'Slides: {len(p.slides)}')
print(f'Slide size: {p.slide_width.inches}x{p.slide_height.inches} in')

for i, slide in enumerate(p.slides[:5]):   # first 5 slides usually enough
    print(f'=== Slide {i+1} ===')
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            run = shape.text_frame.paragraphs[0].runs[0] if shape.text_frame.paragraphs[0].runs else None
            if run:
                size = run.font.size.pt if run.font.size else '?'
                color = ''
                try:
                    if run.font.color.rgb:
                        color = f'#{run.font.color.rgb}'
                except: pass
                font = run.font.name or '(default)'
                text = shape.text_frame.text.strip().replace(chr(10), ' | ')[:60]
                print(f'  "{text}" {font} {size}pt {color}')
```

### From Google Slides (when .pptx not available)

```python
# Get title slide visual + text
mcp__google-drive__exportSlideThumbnail(presentationId, slideObjectId="p", size="LARGE")
# Then WebFetch the thumbnail URL with vision prompt OR
# Read the saved binary from the tool-results dir as an image

mcp__google-drive__getGoogleSlidesContent(presentationId)  # text content + structure
```

---

## Phase 4: Catalog What You Found

Build a tokens table before writing any HTML:

```markdown
## Design tokens (extracted)
- **Primary color**: #215CA0 (cover title)
- **Accent**: #036AFB (highlights)
- **Navy**: #002060 (section dividers)
- **Body text**: #3F3F3F
- **Font**: Noto Sans TC
- **Aspect ratio**: 16:9 (1280×720)
- **Logo position**: top-left, 36px from top
- **Brand line**: "中華電信 / 企業客戶分公司 · 資信通信處"

## Slide types observed
1. Cover (large title + subtitle + section info)
2. Section divider (giant number + label)
3. 3-step process (numbered cards)
4. AS-IS / TO-BE comparison
5. Data table
6. Metrics (large numbers)
```

---

## Phase 5: Build Locked HTML Template

Use this skeleton — every template MUST have:

```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>{Brand} Template</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap" rel="stylesheet">
<style>
  /* ── Locked Tokens (DO NOT modify per slide) ──── */
  :root {
    --primary: #...;
    --accent: #...;
    --navy: #...;
    --text-primary: #...;
    --text-secondary: #...;
    --bg: #...;
    --font: 'Noto Sans TC', sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #ddd; padding: 40px 20px; }

  /* 1280×720 = 16:9 — STANDARD, do not change */
  .slide {
    width: 1280px; height: 720px;
    background: var(--bg);
    margin: 0 auto 40px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
  }

  /* Brand mark, page-num, footer — consistent across all slides */
  .brand-mark { position: absolute; top: 36px; left: 56px; ... }
  .page-num { position: absolute; bottom: 28px; right: 56px; ... }
</style>
</head>
<body>
  <!-- Each slide variant: cover, section, content, comparison, metrics, table -->
</body>
</html>
```

**Required slide variants** (build these even if source only has cover):
1. **Cover** — large title + subtitle + brand mark + meta line
2. **Section divider** — giant number + section label + main heading
3. **Content cards** — 3 cards with icon + title + body
4. **Comparison** — AS-IS / TO-BE two-column with checkmark contrast
5. **Metrics** — 3 large numbers + label + description
6. **Data table** — header row + alternating rows + highlight column

---

## Phase 6: Verify & Hand Off

1. Save to `mockups/slide-templates/{name}.html`
2. Open in browser: `open mockups/slide-templates/{name}.html`
3. Show user the file path and ask for visual approval
4. If they request tweaks, edit ONLY the `:root` tokens or specific slide variants

Then update the user's slide-generating skills to use this template:
> 已建立 `mockups/slide-templates/{name}.html`。
> 未來生成 {brand} 的簡報時，pitch-deck / sales-material 應該優先讀這個檔案的 tokens 和 layout，
> 不要自己發明新風格。

---

## Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| Theme colors don't match what you see in slides | Theme has defaults but slides override per-shape | Inspect actual `run.font.color.rgb` per shape via python-pptx |
| Font shows as `(default)` everywhere | python-pptx returns None when font is inherited from layout | Read `slideLayouts/slideLayout1.xml` for inherited fonts |
| Images embedded as raster, can't extract logo | PPTX media is in `ppt/media/imageN.png` | `cp source-pptx/ppt/media/image1.png mockups/slide-templates/{name}-logo.png` |
| Google Slides downloadFile fails | Native Slides too large to export | Use `getGoogleSlidesContent` + multiple thumbnails instead |
| Title is cut off in template | Source uses non-standard slide size (e.g. 21.98×12.36 in) | Compute aspect ratio, scale to 1280×720 |
| CJK characters render with wrong glyphs | Font fallback chain missing CJK font | Always include `'Noto Sans TC'` or `'PingFang TC'` first in font stack |

---

## Reference Examples

Already-extracted templates (read these to see the output format):
- `mockups/slide-templates/chimes-ai.html` — dark navy + cream cards (Tukey AutoML deck)
- `mockups/slide-templates/cht-corporate.html` — white + CHT blue (智慧製造產品介紹)
