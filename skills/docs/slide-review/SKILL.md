---
name: slide-review
loop: sales
pdca: check
description: >
  Per-slide layout check for a deck before export. Runs the chart-design figure
  checker on every slide HTML file at the slide's own canvas, then Claude reads each
  screenshot for the rules a script cannot see (separate concepts in separate boxes,
  one main label per card). Fix loop with a stop rule: iteration 1 fixes small
  defects, a defect that comes back needs a structural change the user approves,
  iteration 3 still failing goes to the user. Writes review.md, which the deck
  pre-flight (`sk deck-preflight`) reads before a deck becomes final.
  TRIGGER: "/slide-review", "檢查簡報排版", "簡報截圖檢查", "逐頁檢查簡報",
  slide-workflow Gate 6.5.
  SKIP: one chart or figure page (chart-design runs its checker directly); storyline
  review (slide-office-hours); overall design taste (gstack-design-review).
tags: [docs, slides, qa, review]
version: 1.0.1
user_invocable: true
allowed-tools: "Read, Edit, Write, Bash, Glob, AskUserQuestion"
---

# Slide Review

Check every slide of a deck before export. A script measures what it can. Claude
reads each screenshot for the rest. A failure gets at most three iterations.

This skill holds the slide layout rules. Until 2026-07-27 they were in the global
CLAUDE.md ("Diagram & Slide Output Defaults"). That section is gone, so this file is
now the source. Background: GitHub issue #2 (2026-06-03), plan
`docs/plans/2026-10-20-slide-storyline-review-deck-index.md`.

## Rules

| Rule | Meaning | Checked by |
|---|---|---|
| R1 Canvas | Each slide has a fixed canvas: its body box (html2pptx: `720pt x 405pt`). Nothing goes outside it. Content fills at least 80% of it, with no empty band over 8% (chart-design R1). | Script: `figure/overflow`, `figure/canvas-fill`, `figure/empty-band` |
| R2 Font size | No text under 0.75% of the canvas width (12px on 1600, 7.2px on 960). The title is clearly the largest, then section header, card title, body. | Script: `figure/small-font`. Claude: the size order |
| R3 Separate concepts | Different concepts (network zones, inside and outside, phases, owners) sit in fully separate boxes with different colour families. A shared border with a gap is not separate. | Claude |
| R4 No clipping, no wrapped titles | A title stays on one line. Text does not overlap. When content does not fit, split the slide. Do not shrink the font. | Script: `figure/text-wrap`, `figure/text-overlap`, `figure/overflow` |
| R5 Main label first | A card shows one main label on one line and at most one sub-label. Five or more sub-labels on one slide means the layout is wrong. | Claude |
| R6 Repeat means structure | The same defect on the same slide in two iterations needs a structural change, not a 1px tweak. The user approves it first. | Script marks `repeat`; Claude marks visual repeats |

## Hard rules

1. **Write `status: passed` only when every slide passed both the script and the
   screenshot read in the last iteration.** A slide the script could not read
   (`unread`) is not a pass.
2. **Read every screenshot**, also for slides the script passed. R3 and R5 are
   visual only.
3. **Do not fix with `overflow: hidden` or a smaller font.** Cut content, change
   spacing, or split the slide.
4. **Colours and fonts change in the template `:root` variables**, not inline
   (slide-workflow Gate 6).
5. **The user may export without a pass.** Then `review.md` stays
   `failed-needs-user`, and the deck pre-flight (`sk deck-preflight`, where rivendell's
   `sk` is installed) blocks the move to the final folder.
   Say this once. Do not argue.

## Procedure

### Step 0: Pre-flight

1. Find the slides folder: one HTML file for each slide. Usual names: `slides/`,
   `build/`, `pptx-build/slides/` under the deck's `cache/`.
2. Find the deck's `storyline.md` (deck folder or its `cache/`). Not signed off:
   stop and send the user to slide-workflow Gate 0.
3. The script needs the Node packages of the repo root and Google Chrome. If it
   prints `playwright not found`, run `npm install` once in the repo root:
   `cd -P "${CLAUDE_SKILL_DIR}/../../.." && npm install`.

### Step 1: Iteration 1, script

```bash
node "${CLAUDE_SKILL_DIR}/scripts/review-deck.mjs" <slides-dir>
```

Output: `<slides-dir>/review/iter-1/report.json` and one annotated PNG for each
slide (red = error, amber = warning). The canvas comes from each slide's body. If
the script says `未判讀：量不到畫布大小`, rerun with `--canvas 960x540` (or the real
size) and say so in the report.

### Step 2: Screenshot read

Read every PNG in `iter-1/`. For each slide, judge R2 (size order), R3 and R5. Write
one line for each defect: slide, rule, what is wrong, the smallest fix.

### Step 3: Fix, then iteration 2

Fix only the failing elements in the slide HTML. Then:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/review-deck.mjs" <slides-dir> --iter 2
```

Read the screenshots again.

### Step 4: Repeats (R6)

A defect is a repeat when the script marks it `"repeat": true`, or when your
screenshot read finds the same rule failing on the same slide again. For each
repeat, propose one structural change: a larger title, no sub-labels, less padding,
or a split into two slides. Ask with AskUserQuestion before you apply it. Approved:
apply it and run `--iter 3`. Declined: go to Step 6 with `failed-needs-user`.

### Step 5: Iteration 3

All slides pass: go to Step 6 with `passed`. Any slide still fails: stop. Do not
start iteration 4. Go to Step 6 with `failed-needs-user`.

### Step 6: Write review.md

Write `review.md` in the folder that holds `storyline.md`:

```markdown
---
review_skill: slide-review
checked_at: 2026-10-20T15:30:00+08:00
status: passed            # or failed-needs-user
iterations: 2
slides: 18
canvas: 960x540
report: cache/build/review/iter-2/report.json
---

# 排版檢查紀錄

| 頁 | 規則 | 問題 | 第幾輪發現 | 處理 |
|---|---|---|---|---|
| s05-portfolio | R4 | 標題換成兩行 | 1 | 縮短標題，第 2 輪通過 |
```

List warnings that remain under the table. They do not block.

### Step 7: Report to the user

Result first: passed, or which slides failed and why. Then the iterations, the
fixes applied, and the path of the last screenshots.

## Files

- `scripts/review-deck.mjs`: runs `chart-design/references/check-html-figure.mjs`
  on every slide, writes `review/iter-<n>/report.json`, marks repeats.
- `scripts/review-lib.mjs`: the pure functions (sort, canvas, font rule, repeats,
  summary). Tests: `node --test scripts/`.
