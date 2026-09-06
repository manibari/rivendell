---
name: resolving-merge-conflicts
loop: dev
pdca: do
description: >
  Resolve an in-progress git merge or rebase conflict by recovering each side's
  intent from its primary sources, then proving the result with the project's own
  checks rather than by reading the diff.
  TRIGGER when: a merge or rebase has stopped with conflicts, the user says
  "解衝突", "merge conflict", "衝突怎麼處理", "rebase 卡住", or a branch has
  diverged far enough that merging needs a plan.
  SKIP when: no merge is in progress (this is not a "should I merge" advisor), or
  the task is reviewing a finished diff (use gstack-review).
when_to_use: a git merge/rebase is halted on conflicts and each side's changes need reconciling
version: 1.0.0
tags: [git, merge, conflict, integration]
languages: all
user_invocable: true
---

# Resolving Merge Conflicts

1. **See the current state** of the merge/rebase. Check git history, and the conflicting files.

2. **Find the primary sources** for each conflict. Understand deeply why each change was made,
   and what the original intent was. Read the commit messages, check the PRs, check original
   issues/tickets.

3. **Resolve each hunk.** Preserve both intents where possible. Where incompatible, pick the one
   matching the merge's stated goal and note the trade-off. Do **not** invent new behaviour.
   Always resolve; never `--abort`.

4. Discover the project's **automated checks** and run them — typically typecheck, then tests,
   then format. Fix anything the merge broke.

5. **Finish the merge/rebase.** Stage everything and commit. If rebasing, continue the rebase
   process until all commits are rebased.

## Try the merge somewhere disposable first

`git worktree add --detach <tmp> <branch>` and merge there. The conflict list, the resolution,
and the test run all happen without touching the working tree, and a bad attempt is `rm -rf`
rather than `git merge --abort` against live files. Push with `git push origin HEAD:<branch>`
when it passes — that lands the result without disturbing anyone's uncommitted work.

## What only testing finds

Step 4 is not a formality. These survive a careful reading of every hunk and were each caught by
running something (rivendell, 2026-08-03):

- **A fix on one side that the other side's code never received.** The same bug pattern existed in
  both branches; only one branch fixed it, and the fix could not reach the lines that arrived from
  the other. Grep the *merged* file for the pattern the fix targeted.
- **Identity derived from a path.** `basename $PWD`-style self-detection silently changes meaning
  in a worktree or a renamed checkout, and the failure mode is a silent skip, not an error.
- **A file that moved on one side and was edited on the other.** Git records two files, not a
  rename, so both survive. Check for duplicate basenames after resolving.
- **A consumer of something the merge deleted.** If one branch removed a generated file, grep for
  every reader of it; the ones nobody thought of report "0 items" instead of failing.

Compare against a known-good baseline before blaming the merge — an environment artifact
(no `node_modules`, services not installed) reads exactly like a regression in a test report.

<!-- Ported from: https://github.com/mattpocock/skills (MIT) by skill-scout.
     Steps 1-5 are Matt Pocock's, verbatim. The two sections below are rivendell's,
     added from the origin/main × chore/skill-quality merge on 2026-08-03. -->
