# Chart Style: <PROJECT_NAME>

> Template for chart-design skill style files. Copy to `styles/<project-slug>.md`
> and fill in. Each project / client / brand gets ONE file; chart-design loads it
> before any generation. **Source of truth — do NOT hardcode colors / fonts in
> chart code.**

---

## Brand / Project

| 欄位 | 值 |
|------|-----|
| Project / Client | <name, e.g. 立積電 / Richwave Technology> |
| Use case | <e.g. B2B presales decks, IoT factory reports, investor BP> |
| Reference deck path | <relative path to canonical PDF / PPTX / HTML> |
| Last updated | <YYYY-MM-DD> |
| Notes | <free-form, e.g. "client requested no red — competitor color"> |

---

## Color Palette

### Primary (主色)

```
brand-primary    : #______   <hex>   /* main accent, line color, key fills */
brand-secondary  : #______           /* secondary accent */
brand-tertiary   : #______           /* tertiary, rarely used */
```

### Neutrals

```
ink              : #______           /* axis lines, labels, text */
ink-muted        : #______           /* gridlines, secondary text */
canvas           : #______           /* chart background — usually white or off-white */
panel            : #______           /* container / card bg */
```

### Semantic

```
positive         : #______           /* up trend, success,我方 */
negative         : #______           /* down trend, alert, 競品 */
warning          : #______           /* attention, threshold breach */
neutral          : #______           /* baseline, "no change" */
```

### Categorical Palette (≤ 6 colors)

For multi-series line / bar / scatter. **Colorblind-safe required.** If brand colors aren't safe, pair with pattern fill or marker shape.

```
cat-1: #______
cat-2: #______
cat-3: #______
cat-4: #______
cat-5: #______
cat-6: #______
```

Suggested fallbacks (if no brand spec): Okabe-Ito (`#000000 #E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7`).

### Sequential / Diverging

```
sequential       : <viridis | cividis | brand-custom-gradient>
diverging        : <RdBu | brand-custom>
```

---

## Typography

```
font-family-base  : "<font name>", system-ui, sans-serif
font-family-mono  : "<font name>", monospace
font-family-cjk   : "Noto Sans TC", "PingFang TC", sans-serif    /* if CJK content */

font-size-title       : __ px    /* chart title */
font-size-axis-label  : __ px    /* x/y axis labels */
font-size-tick        : __ px    /* axis tick values */
font-size-legend      : __ px
font-size-annotation  : __ px    /* outlier labels, callouts */
font-size-caption     : __ px    /* below chart */

font-weight-title     : 600
font-weight-body      : 400
```

---

## Grid & Axes

```
grid-style        : <none | horizontal-only | full | minor-only>
grid-color        : <ink-muted at 0.3 opacity, or specific hex>
grid-stroke       : __ px

axis-line         : <show | hide>
axis-tick-length  : __ px
axis-label-rotate : <0 | 45 | 90>   /* default for long labels */
zero-baseline     : <always-show | hide-if-non-zero-range>
```

---

## Margin / Padding / Layout

```
chart-margin-top    : __ %  of canvas height
chart-margin-bottom : __ %
chart-margin-left   : __ %
chart-margin-right  : __ %

panel-padding       : __ px   /* between chart and container border */
panel-radius        : __ px   /* card border radius if framed */
panel-border        : <none | __px solid {ink-muted}>
panel-shadow        : <none | subtle | strong>
```

Remember R1: 主元素 ≥ 80% fill, no edge band > 8%. These margins are an upper bound.

---

## Legend

```
legend-position    : <top | bottom | right | inline-endpoint | none>
legend-orientation : <horizontal | vertical>
legend-marker      : <line | box | circle>
```

Preferred: **inline-endpoint labels** (label at end of each line) for line charts; legend only as fallback.

---

## Markers / Lines / Bars

```
line-width-default  : __ px
line-width-emphasis : __ px   /* for highlighted series */
marker-size         : __ px
marker-shape-set    : <circle, square, triangle, diamond, ...>   /* for monochrome distinction */

bar-width-ratio     : __ (0.6-0.7 typical)
bar-radius          : __ px (top-corner rounding)
```

---

## Business Chart Defaults (if applicable)

```
matrix-cell-padding   : __ px
matrix-quadrant-label-style : <H1 | H2 | tag>
timeline-marker-shape : <circle | diamond | line>
table-header-bg       : {brand-primary}
table-row-alt-bg      : {panel}
table-highlight-bg    : {positive}   /* for 我方 / recommended tier */
```

---

## System Architecture Defaults (if applicable)

```
box-fill-default    : {panel}
box-fill-frontend   : {brand-primary}
box-fill-backend    : {brand-secondary}
box-fill-data       : {brand-tertiary}
box-fill-external   : {neutral}
box-border          : __px solid {ink}
arrow-color         : {ink}
arrow-sync-style    : solid
arrow-async-style   : dashed
boundary-fill       : {brand-primary} with low opacity
boundary-border     : dashed
```

---

## Reference Decks / Anchors

When in doubt, eyeball-compare against:

- `<path/to/reference-deck-1.pdf>` page X — for chart style baseline
- `<path/to/reference-deck-2.html>` slide Y — for table / matrix style

---

## Notes / Conventions

- <e.g. "客戶習慣看 vertical bar，不要用 horizontal"
- <e.g. "Trend 一定要附 30-day MA 虛線"
- <e.g. "Avoid 紅色 — 競品色，會被誤解">
