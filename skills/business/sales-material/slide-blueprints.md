# Slide Blueprints — HTML Templates

Each slide type has an HTML template. All templates follow html2pptx constraints:
- Dimensions: `width: 720pt; height: 405pt` (16:9)
- Text must be in `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>` (NOT bare `<div>`)
- Web-safe fonts only (Arial, Verdana, Georgia, etc.)
- No `<br>` tags — use separate elements
- No CSS gradients — pre-rasterize as PNG if needed

## 1. Cover Slide

```html
<div style="width: 720pt; height: 405pt; background: #1a1a2e; display: flex; flex-direction: column; justify-content: center; padding: 60pt;">
  <h1 style="font-family: Arial; font-size: 28pt; color: #ffffff; margin-bottom: 10pt;">
    {client_name}
  </h1>
  <h2 style="font-family: Arial; font-size: 18pt; color: #e0e0e0; margin-bottom: 30pt;">
    {proposal_title}
  </h2>
  <p style="font-family: Arial; font-size: 12pt; color: #aaaaaa;">
    {our_company_name} | {date}
  </p>
</div>
```

## 2. Agenda Slide

```html
<div style="width: 720pt; height: 405pt; background: #ffffff; padding: 40pt;">
  <h1 style="font-family: Arial; font-size: 24pt; color: #1a1a2e; margin-bottom: 20pt;">
    議程
  </h1>
  <ol style="font-family: Arial; font-size: 14pt; color: #333333; line-height: 2;">
    <li>關於我們</li>
    <li>了解您的挑戰</li>
    <li>建議方案</li>
    <li>成功案例</li>
    <li>補助機會</li>
    <li>時程與預算</li>
    <li>下一步</li>
  </ol>
</div>
```

## 3. About Us (公司介紹)

```html
<div style="width: 720pt; height: 405pt; background: #ffffff; padding: 40pt;">
  <h1 style="font-family: Arial; font-size: 24pt; color: #1a1a2e; margin-bottom: 15pt;">
    關於我們
  </h1>
  <p style="font-family: Arial; font-size: 12pt; color: #555555; margin-bottom: 15pt;">
    {company_intro_paragraph}
  </p>
  <ul style="font-family: Arial; font-size: 11pt; color: #333333;">
    <li>{service_1}: {description}</li>
    <li>{service_2}: {description}</li>
    <li>{service_3}: {description}</li>
  </ul>
</div>
```

## 5. Pain Points (了解您的挑戰)

```html
<div style="width: 720pt; height: 405pt; background: #f8f8fc; padding: 40pt;">
  <h1 style="font-family: Arial; font-size: 24pt; color: #1a1a2e; margin-bottom: 20pt;">
    了解您的挑戰
  </h1>
  <p style="font-family: Arial; font-size: 11pt; color: #666666; margin-bottom: 15pt;">
    根據我們的調研，{client_name} 目前面臨以下關鍵挑戰：
  </p>
  <ul style="font-family: Arial; font-size: 12pt; color: #333333; line-height: 1.8;">
    <li><strong>{pain_point_1}</strong></li>
    <li><strong>{pain_point_2}</strong></li>
    <li><strong>{pain_point_3}</strong></li>
  </ul>
</div>
```

## 6. Proposed Solution (建議方案)

```html
<div style="width: 720pt; height: 405pt; background: #ffffff; padding: 40pt;">
  <h1 style="font-family: Arial; font-size: 24pt; color: #1a1a2e; margin-bottom: 15pt;">
    建議方案：{solution_name}
  </h1>
  <p style="font-family: Arial; font-size: 11pt; color: #555555; margin-bottom: 15pt;">
    {solution_overview}
  </p>
  <ul style="font-family: Arial; font-size: 11pt; color: #333333;">
    <li>{deliverable_1}</li>
    <li>{deliverable_2}</li>
    <li>{deliverable_3}</li>
  </ul>
</div>
```

## 8. Case Study (成功案例)

```html
<div style="width: 720pt; height: 405pt; background: #ffffff; padding: 40pt;">
  <h1 style="font-family: Arial; font-size: 22pt; color: #1a1a2e; margin-bottom: 10pt;">
    成功案例：{case_client}
  </h1>
  <p style="font-family: Arial; font-size: 10pt; color: #888888; margin-bottom: 15pt;">
    {case_industry} | {case_duration} | {case_year}
  </p>
  <p style="font-family: Arial; font-size: 11pt; color: #555555; margin-bottom: 10pt;">
    挑戰：{challenge_summary}
  </p>
  <p style="font-family: Arial; font-size: 11pt; color: #555555; margin-bottom: 10pt;">
    方案：{solution_summary}
  </p>
  <p style="font-family: Arial; font-size: 16pt; color: #2d6a4f; font-weight: bold;">
    {outcome}
  </p>
</div>
```

## 10. Subsidy Opportunities (補助機會)

```html
<div style="width: 720pt; height: 405pt; background: #f0f7f4; padding: 40pt;">
  <h1 style="font-family: Arial; font-size: 24pt; color: #1a1a2e; margin-bottom: 20pt;">
    可申請補助
  </h1>
  <div class="placeholder" style="position: absolute; left: 40pt; top: 90pt; width: 640pt; height: 250pt;"></div>
</div>
```

Use PptxGenJS table for subsidy data:

```javascript
slide.addTable([
  [{ text: "補助名稱", options: { bold: true }}, { text: "補助金額" }, { text: "截止日期" }],
  ["{subsidy_1_name}", "{subsidy_1_amount}", "{subsidy_1_deadline}"],
  ["{subsidy_2_name}", "{subsidy_2_amount}", "{subsidy_2_deadline}"],
], { x: 0.5, y: 1.2, w: 9, fontSize: 11, color: "333333" });
```

## 11. Timeline & Budget (時程與預算)

```html
<div style="width: 720pt; height: 405pt; background: #ffffff; padding: 40pt;">
  <h1 style="font-family: Arial; font-size: 24pt; color: #1a1a2e; margin-bottom: 20pt;">
    時程與預算
  </h1>
  <div class="placeholder" style="position: absolute; left: 40pt; top: 90pt; width: 640pt; height: 260pt;"></div>
</div>
```

Use PptxGenJS table:

```javascript
slide.addTable([
  [{ text: "階段" }, { text: "期間" }, { text: "交付物" }],
  ["{phase_1}", "{duration_1}", "{deliverable_1}"],
  ["{phase_2}", "{duration_2}", "{deliverable_2}"],
  ["{phase_3}", "{duration_3}", "{deliverable_3}"],
], { x: 0.5, y: 1.2, w: 9, fontSize: 11 });
```

Budget note below table:
```javascript
slide.addText("預估投資：{budget_range}（含補助可降至 {budget_after_subsidy}）",
  { x: 0.5, y: 5.5, fontSize: 12, color: "2d6a4f" });
```

## 13. Next Steps (下一步)

```html
<div style="width: 720pt; height: 405pt; background: #1a1a2e; padding: 40pt;">
  <h1 style="font-family: Arial; font-size: 24pt; color: #ffffff; margin-bottom: 20pt;">
    下一步
  </h1>
  <ol style="font-family: Arial; font-size: 14pt; color: #e0e0e0; line-height: 2;">
    <li>{next_step_1}</li>
    <li>{next_step_2}</li>
    <li>{next_step_3}</li>
  </ol>
</div>
```

## 14. Contact (聯繫方式)

```html
<div style="width: 720pt; height: 405pt; background: #1a1a2e; display: flex; flex-direction: column; justify-content: center; align-items: center;">
  <h1 style="font-family: Arial; font-size: 28pt; color: #ffffff; margin-bottom: 10pt;">
    Thank You
  </h1>
  <p style="font-family: Arial; font-size: 14pt; color: #e0e0e0; margin-bottom: 5pt;">
    {contact_name} | {contact_title}
  </p>
  <p style="font-family: Arial; font-size: 12pt; color: #aaaaaa;">
    {email} | {phone}
  </p>
</div>
```

## Design Notes

- **Color palette**: Dark navy (#1a1a2e) + white + green accent (#2d6a4f)
- **Font**: Arial throughout for safety
- **Contrast**: Dark slides for bookends (cover, next steps, contact), white for content
- Adjust colors per client brand if known from customer-intel
