# Screenshots and callouts

Read this file before you add or recapture a screenshot.

## When to add a screenshot

Add a screenshot only when one of these is true:

- The reader must find one control among many on a busy screen.
- The article introduces a screen, and its layout is the subject.
- The result of a task is hard to describe in words, for example a chart or a status badge.

Do not add a screenshot for each step. A screenshot that shows only one button adds no information.

## Rules for each screenshot

1. Use demo data only. Mask real names, email addresses, phone numbers and ID numbers.
2. Capture at the fixed viewport in the spec (default 1440 x 900, scale 2). Use the same viewport in one manual.
3. Crop to the area that the steps use. Keep enough context for the reader to find that area on the full screen.
4. Put one numbered badge on each target control. The badge number is the step number that uses the control.
5. Write alt text that tells what the image shows, in 150 characters or fewer. Start with `螢幕擷取畫面`. Example: `螢幕擷取畫面顯示 [報價] 頁面的 [新增報價] (1) 與 [狀態] (2)。`
6. Put the image after the step that it supports, not before the procedure.
7. Name the file `<article-slug>-<nn>.png`. `nn` starts at `01` in each article.

## Capture with the script

`scripts/annotate-shot.mjs` opens the page, draws the badges and outline boxes, and saves the PNG.
It uses the Playwright that the target project installs.
Run it from the target project directory.

```bash
node ~/.claude/skills/manual-writer/scripts/annotate-shot.mjs --spec docs/manual-shots/quotes-contracts-01.json
```

Spec file:

```json
{
  "url": "http://localhost:3000/quotes",
  "viewport": { "width": 1440, "height": 900 },
  "storageState": ".auth/demo-user.json",
  "waitFor": "role=heading[name=\"報價\"]",
  "clip": "main",
  "mask": ["[data-pii]"],
  "callouts": [
    { "n": 1, "selector": "role=button[name=\"新增報價\"]" },
    { "n": 2, "selector": "role=combobox[name=\"狀態\"]" }
  ],
  "out": "docs/manual/img/quotes-contracts-01.png"
}
```

- The script draws a 2 px outline and a round numbered badge in `#D13438` at the top-left of each control.
  Microsoft publishes no rule for highlight color or width (checked 2026-11-20); this is a rivendell choice.
  Put no other text in the image. Labels stay in the article text, where an editor can change them.
- Find controls by role and visible label. When a label changes, the capture fails. This failure tells you that the article text is out of date too.
- Keep spec files outside the published manual folder. A product image can copy the manual folder, and the spec holds local URLs.
- Keep login state files out of Git. Make sure that `.gitignore` excludes them.

## Recapture

When a screen changes, run every spec that captures that screen.
Then read each step that cites a badge number. A moved control can change the step order.
