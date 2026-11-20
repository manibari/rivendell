---
name: manual-writer
loop: shared
pdca: do
description: >
  Write or rewrite an end-user 操作手冊 in Traditional Chinese to the Microsoft documentation
  standard: one topic type for each article, one action for each step, screen names in [ ],
  numbered screenshot callouts, and a lint script before hand-off.
  TRIGGER when: "寫操作手冊", "操作手冊", "使用手冊", "使用者手冊", "手冊章節", "更新手冊", "user manual", "help article".
  SKIP: developer docs, README, API reference (gstack-document-generate); SOW (sow-writer);
  internal notice (internal-comms); a .docx layout (office-docx); the 開發中心 pages (spine-dev-center).
tags: [docs, writing, manual]
version: 1.0.0
user_invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Manual Writer

A manual is a set of **tasks**: things the reader wants to get done on the screen.
Each article has one **topic type**, and each step is one action at one place on the screen.
The standard is the Microsoft Writing Style Guide plus the Microsoft zh-TW Style Guide.
Each rule in the references names its source, or says that it is a rivendell choice.

Files of this skill:

| File | Read it |
|---|---|
| [references/zh-tw-style.md](references/zh-tw-style.md) | Before you write the first line (step 4) |
| [references/article-templates.md](references/article-templates.md) | When you pick topic types (step 3) |
| [references/screenshots.md](references/screenshots.md) | Before you add or recapture a screenshot (step 5) |
| [references/review-checklist.md](references/review-checklist.md) | In step 6 |
| `scripts/check_manual.py` | Lint for the form, in step 6 |
| `scripts/annotate-shot.mjs` | Screenshot with numbered callouts, in step 5 |

## Step 1: Read the manual home

1. Find the manual folder of the project, for example `docs/manual/`. Read its `README.md`.
2. Write down four facts: the folder, the file format (frontmatter fields), the link form, and whether the page renderer shows images.
3. To find the image fact, read the renderer's list of allowed HTML tags. Look for `img`.
4. The project decides the file format. This skill decides the writing style.
5. If the project README has a style rule that disagrees with `zh-tw-style.md`, tell the user. Propose a README change. Do not pick one in silence.

Done when: you can state the four facts, and each disagreement is reported to the user.

## Step 2: List the tasks from the live screen

1. Open the app as each role that the manual covers.
2. For each task, record: role, goal, start screen, each label exactly as the screen shows it, and the result.
3. If the app cannot run, read the screen code. Mark each such task `未核對畫面`.

Done when: each task in scope has all five fields, and each label comes from the screen or is marked `未核對畫面`.

## Step 3: Give each article one topic type

Types: 快速入門, 操作說明, 概念, 參考, 疑難排解. Read `article-templates.md` for each shape.

- One 操作說明 article covers one user goal.
- A procedure of more than 12 steps becomes two or more tasks.
- An idea that a procedure needs goes to a 概念 article. The procedure links to it.

Done when: each article has exactly one type, and each task from step 2 is in exactly one 操作說明 article.

## Step 4: Write

Read `zh-tw-style.md` first. The rules that writers break most often:

```markdown
若要建立報價，請使用下列步驟。

1. 在 [報價] 頁面，選取 [新增報價]。
2. 在 [商機] 清單中，選取要報價的商機。
3. 輸入數量和單價，然後選取 [儲存]。

   畫面會顯示 [報價詳情]，狀態為 [草稿]。
```

- The location comes before the action. A step has one action, or short actions at one place.
- Screen names go in half-width `[ ]`, with no bold. Use `「」` for quotes and error messages only.
- The verb is `選取` for buttons, links, tabs, and list values. Use `輸入` for typed values.
- Address the reader as `您`. Use full-width punctuation. Put one space between Chinese and English, digits, `( )`, or `[ ]`.
- Use demo data only, for example 示範科技股份有限公司, 陳業務, Q-DEMO-001.

Set the `updated` date (or the project's date field) to the day that you checked the article against the screen.

Done when: each article from step 3 has text, and each step uses labels from the step 2 list.

## Step 5: Add screenshots

Read `screenshots.md`. Capture with:

```bash
node ~/.claude/skills/manual-writer/scripts/annotate-shot.mjs --spec-dir docs/manual-shots
```

If the renderer has no `img` tag (step 1), do not add image syntax. List each planned screenshot in the hand-off, and propose a renderer ticket to the user.

Done when: each image has alt text, a spec file, and badge numbers that match the step numbers. Or the renderer gap is in the hand-off.

## Step 6: Check

1. Run the lint. Fix each `E`. For each `W`, fix it or write the reason to keep it.

   ```bash
   python3 ~/.claude/skills/manual-writer/scripts/check_manual.py docs/manual
   ```

   Add `--no-h1` when the page shows the title by itself.
2. Go through `review-checklist.md`, item by item. The lint cannot judge these items.

Done when: the lint exits 0, and each checklist item has 通過 or a reason.

## Step 7: Hand off

Report to the user in Traditional Chinese:

- The articles that you added or changed, with the topic type of each.
- The screenshots that you captured, and the planned ones that the renderer cannot show yet.
- Each task marked `未核對畫面`.
- Each disagreement with the project README, and the change that you propose.
- Each `W` from the lint that you kept, with the reason.

## Gotchas

- **ChimesERP renderer (checked 2026-11-20).** `backend/app/platform/markdown.py` `ALLOWED_TAGS` has no `img`, so images do not show. Its frontmatter parser rejects unknown keys. Do not add a `type:` field for the topic type.
- **ChimesERP manuals use `「」` for screen names.** They were written before this skill. Convert an article to `[ ]` when you rewrite it, and change the rule in `docs/manual/README.md` in the same change.
- **`[label](` becomes a link in Markdown.** The spacing rule puts a space after `]`, so `選取 [儲存] (右上角)` stays plain text. Write `[儲存]` and `(` with a space between them.
- **zh-TW Microsoft Support pages use bold and brackets together.** Their markup is often broken. The written zh-TW guide says brackets only. This skill follows the guide.
- **Labels in code are not labels on the screen.** An i18n file or a constant can differ from what the screen shows. Copy from the screen.
- **Zero lint errors does not mean a good article.** The lint checks form. The checklist checks whether a reader can do the task.
