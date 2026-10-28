---
name: slide-template-extractor
loop: sales
pdca: plan
description: >
  Extract design system from existing PPTX/Google Slides → locked HTML slide template
  with CSS variables. Stops style drift across deck generations. When the client has no
  deck, take the brand colors and logo from the client's website or from a system we built
  for the client, and check each color's contrast before it holds text.
  TRIGGER: "把這份簡報的風格做成 template", "extract slide design", "鎖定簡報風格",
  "簡報模板", "做一個 X 的簡報模板".
  SKIP: writing a deck's content (pitch-deck / sales-material); edit existing PPTX (office-pptx).
tags: [docs, workflow]
version: 1.1.0
user_invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep, WebFetch"
---

# Slide Template Extractor

Convert an existing brand deck → locked HTML template that pitch-deck and sales-material can reuse.

## Output Location

- If the owner's template folder `~/Work/ChimesAI/範本/presentations/` exists, save
  `{name}-pitch.html` and `{name}-pitch-sample.png` there. Add one row to the "HTML 風格"
  table of its `README.md`: style, file, use, the source of the tokens, the colors that are
  decoration only (with their contrast), the sample file and the date.
- Else save to `mockups/slide-templates/{name}.html` in the current project, or to the
  place the user names.

---

## Phase 1: Identify Source

Ask the user (or detect from context):
- **Source type**: Local .pptx file? Google Slides URL? Google Drive file? No deck at all
  (go to Phase 2b)?
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

## Phase 2b: No deck to extract from

When the client has no deck, take the brand from these sources, in this order:

1. **A system that we built for the client.** Its theme file and logo files hold the exact
   values (2026-10-28 example: `~/Code/Rightek-CRM/frontend/src/lib/theme.ts` and
   `public/rightek-logo-*.svg`).
2. **The client's website.** Read the CSS custom properties and the computed colors of the
   header, the buttons and the links. Take the logo from the site header; SVG first.
3. **The user**, for each value that is still missing. Do not invent a brand color.

Write the source of each token in a comment next to it in `:root`.

Then check each color before it holds text:

1. Compute its contrast ratio against each background where it can hold text (white, the
   page background, the dark background).
2. 4.5:1 or more: the color can hold text. For text of 24px or more, 3:1 is enough.
3. Less: the color is decoration only (bars, icons, chart fills). Mark it in `:root`
   (「淺底上不放字」). Add a text variant for the dark background when needed
   (`--accent-on-dark`).

(2026-10-28, Rightek: the teal accent `#28C2B6` has 2.21:1 on white, so it is decoration
only. Text uses the dark teal `#03515D`.)

Then go to Phase 4 with these tokens. Phase 3 needs a source deck.

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

1. Save the template (see Output Location).
2. Check every page type with the slide-review script. Do not write a second checker.
   - Split the template into one HTML file per `.slide` section, each with the same
     `<head>`, in a scratch folder `pages/`. Add
     `<style>body{padding:0;background:none}.slide{margin:0;box-shadow:none}</style>` to
     each `<head>`. Without it, the preview padding of the template moves the page off the
     canvas, and each page gets a false `figure/overflow` error.
   - Run the script. It finds text outside the page, wrapped titles and text below the
     smallest font size, and writes one annotated PNG per page:
     ```bash
     S="$(cd -P "${CLAUDE_SKILL_DIR}" && pwd)"
     node "$S/../../docs/slide-review/scripts/review-deck.mjs" <scratch>/pages --canvas 1280x720
     ```
     If it prints `playwright not found`, do slide-review Step 0, item 3.
   - Fix the template, not the split files. Then split and run again.
3. Put the page PNGs together in one overview image, 2 columns. Read it yourself, then
   show it to the user. Save it next to the template as `{name}-pitch-sample.png`.
4. Ask for visual approval. A tweak changes ONLY the `:root` tokens or one page type.
5. Register the template (see Output Location).

Then update the user's slide-generating skills to use this template:
> 已建立 `{template path}`。
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
- `~/Work/ChimesAI/範本/presentations/rightek-pitch.html` — no source deck; brand from the
  client's website through its CRM theme file; warm white + dark teal, teal as decoration
  only; 7 page types; sample `rightek-pitch-sample.png` (2026-10-28)
