# Sales Material Assembler — Assembly Workflow

## Pre-flight

Before assembling, verify required materials exist:

```
1. Glob materials/company/profile.md → must exist
2. Glob materials/company/capabilities.md → must exist
3. Glob reports/customer-intel/{client}*.md → warn if missing
4. Glob materials/case-studies/*.md → warn if none
5. Glob materials/solutions/**/*.md → warn if none
```

If company profile/capabilities are empty (only TODO placeholders), warn the user:
"公司資料尚未填入，簡報會缺少公司介紹。要先填寫 materials/company/ 嗎？"

## Assembly Pipeline

### 1. Collect Materials

```python
materials = {
    "company": read("materials/company/profile.md"),
    "capabilities": read("materials/company/capabilities.md"),
    "team": read("materials/company/team.md"),
    "methodology": read("materials/company/methodology.md"),
    "differentiators": read("materials/company/differentiators.md"),
    "intel": read("reports/customer-intel/{client}_{date}.md"),
    "cases": matched_cases,      # from matching.md
    "solutions": matched_solutions,  # from matching.md
    "subsidies": matched_subsidies,  # from matching.md
}
```

### 2. Build Slide Content

For each slide in the deck structure:

1. **Extract** relevant content from the source material
2. **Condense** into slide-appropriate length (bullets, not paragraphs)
3. **Localize** — all slide text in Traditional Chinese
4. **Format** as HTML using the blueprint from slide-blueprints.md

### 3. Generate HTML Files

Create one HTML file per slide in a temp directory:

```
/tmp/sales-pptx-{client}/
├── slide-01-cover.html
├── slide-02-agenda.html
├── slide-03-about-us.html
├── ...
└── slide-14-contact.html
```

Each HTML file follows the html2pptx constraints:
- `width: 720pt; height: 405pt` for 16:9
- All text in `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>`
- No `<br>` tags
- Web-safe fonts only
- Hex colors WITHOUT `#` prefix in PptxGenJS calls

### 4. Convert to PPTX

Follow the office-pptx html2pptx workflow:

```javascript
// slide-gen.js
const { html2pptx } = require('/path/to/html2pptx.js');
const pptxgen = require('pptxgenjs');
const pres = new pptxgen();

// For each slide HTML file:
const slide = pres.addSlide();
await html2pptx(slide, './slide-01-cover.html');
// ... repeat for all slides

pres.writeFile({ fileName: 'output.pptx' });
```

### 5. Validate

After generating:
1. Check file exists and size > 0
2. Report slide count
3. Show output path

### 6. Save

Move final PPTX to:
```
materials/presentations/{client-slug}_{YYYY-MM-DD}.pptx
```

## Customization Points

The user may request variations:

| Request | Action |
|---------|--------|
| "不要放補助" | Skip slide 10 |
| "加強技術面" | Add methodology slide, expand solution architecture |
| "簡短版" | Only slides 1, 5, 6, 8, 13, 14 |
| "英文版" | Translate slide content to English |
| "多加一個案例" | Add slide 9 with second case study |

Always confirm the deck structure with the user before generating.
