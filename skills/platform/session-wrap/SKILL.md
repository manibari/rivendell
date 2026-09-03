---
name: session-wrap
loop: platform
pdca: do
description: >
  End-of-session cleanup: auto-commit uncommitted changes, archive learnings,
  and update progress.md. Run this before closing a session to ensure nothing
  is lost. TRIGGER when: user says "/wrap", "收工", "session 結束", "整理 session",
  "打包收工", "結束工作", "wrap up", "session close".
  DO NOT TRIGGER when: user is in the middle of work and just pausing.
tags: [workflow, meta]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Session Wrap

End-of-session cleanup. Run all 3 steps in order, report results.

## Step 1: Auto-Commit Uncommitted Changes

```bash
git status --short
```

If there are uncommitted changes:

1. Run `git diff --stat` to see what changed
2. Run `git log --oneline -3` to check recent commit style
3. Stage relevant files (skip `.env`, `node_modules`, `*.pyc`, `.DS_Store`)
4. Write a commit message summarizing the session's work
5. Commit with `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`

If working tree is clean → skip, report "No uncommitted changes."

**Important**: Do NOT push automatically. Just commit locally. User decides when to push.

## Step 2: Learnings Archive

Check if any learnings were captured during the session:

```bash
cat .learnings/LEARNINGS.md 2>/dev/null | tail -30
cat .learnings/ERRORS.md 2>/dev/null | tail -20
cat .learnings/FEATURE_REQUESTS.md 2>/dev/null | tail -10
```

For each file that exists and has content:
- Confirm entries from this session are saved (check dates)
- If there are learnings in conversation context that weren't saved to files, save them now

Quick self-check questions:
- Did any command fail this session? → `.learnings/ERRORS.md`
- Did the user correct my approach? → `.learnings/LEARNINGS.md` (category: correction)
- Did I discover a better pattern? → `.learnings/LEARNINGS.md` (category: best_practice)
- Was there a knowledge gap? → `.learnings/LEARNINGS.md` (category: knowledge_gap)

## Step 3: Progress Update

```bash
ls task_plan.md progress.md findings.md 2>/dev/null
```

If planning files exist (from `planning-with-files`):
1. Read `task_plan.md` — find phases marked `[in_progress]`
2. Update status: mark completed phases as `[complete]`, note what's left
3. Read `progress.md` — append today's session summary
4. If ALL phases are complete, note "All phases complete" in progress.md

If no planning files exist → skip, report "No active planning session."

## Output Format

After all 3 steps, print a summary:

```
## Session Wrap 完成

| 項目 | 狀態 |
|------|------|
| Git commit | ✅ committed: "{message}" / ⏭ clean |
| Learnings | ✅ {N} entries archived / ⏭ none |
| Progress | ✅ updated (Phase {N} complete) / ⏭ no planning files |

下次 session 可以用 `context-recovery` 或讀 `task_plan.md` 接續。
```

## What This Does NOT Do

- ❌ **Push to remote** — user decides when to push
- ❌ **Run session-harvest** — harvest is a separate, heavier operation; use `/session-harvest` if you want that too
- ❌ **Delete planning files** — they persist for the next session to pick up
