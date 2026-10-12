# Chart Style: ChimesERP

> Style file for chart-design. Source: the Chimes AI Design System of chimes-people-ops
> (`app/styles/tokens.css`), chosen by the owner for ChimesERP on 2026-10-12.
> Do not hardcode other colors or fonts in ChimesERP figures.

---

## Brand / Project

| 欄位 | 值 |
|------|-----|
| Project / Client | ChimesERP (Chimes AI 詠鋐智能, internal ERP) |
| Use case | Design documents (SA/SD, business scope map), mockups, internal reports |
| Reference | `~/Code/ChimesERP/docs/mockups/2026-10-12-apps-page.html` (same tokens) |
| Last updated | 2026-10-12 |
| Notes | Light theme for documents. Brand marks come from chimes-people-ops `public/mark-*.svg`; do not redraw or recolor them |

---

## Color Palette

### Primary

```
brand-primary    : #046AFB   /* accent, core-domain group, key arrows */
brand-secondary  : #1E3A8A   /* deep blue, titles on light tint */
brand-tertiary   : #EFF6FF   /* primary tint, group fill */
```

### Neutrals

```
ink              : #09090B   /* text */
ink-muted        : #71717A   /* secondary text, captions */
canvas           : #F6F7FA   /* figure background */
panel            : #FFFFFF   /* boxes, cards */
border           : #DBDDE0   /* box borders, dividers */
edge             : #3F3F46   /* arrows */
```

### Semantic

```
positive         : #16A34A   /* success; supporting-domain group */
negative         : #DC2626   /* error, risk */
warning          : #D97706   /* attention */
neutral          : #52525B   /* generic-domain group, baseline */
```

### Categorical Palette (≤ 6)

```
cat-1: #046AFB
cat-2: #16A34A
cat-3: #D97706
cat-4: #1E40AF
cat-5: #DC2626
cat-6: #52525B
```

Pair with shape or label when more than 3 categories share one chart.

---

## Typography

```
family : -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif
title  : 28px / 600
box    : 18px / 600 title, 14px body, 12px code names
label  : 13px on arrows, white label chip behind the text
min    : 12px (never smaller)
```

---

## Shapes and Lines (system-architecture figures)

- Radius: box 14px, group frame 18px, chip 6px.
- Group frame: dashed 1.5px border in the group color, fill = group tint (brand-tertiary, #F0FDF4, #FFFFFF with #F6F7FA canvas).
- Arrows: solid = synchronous call or read; dashed = event or asynchronous push. Arrowhead size 8px.
- Return paths (退回、回覆) are drawn on the outside and dashed.
- Canvas 1600 × 900 for slide-like figures.
