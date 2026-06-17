---
name: concurrent-session-git
description: >
  Git hygiene when multiple Claude sessions (or a human + an agent) share ONE
  working tree and collide — your commit sweeps another session's uncommitted
  WIP, or a stale local base bundles unpushed commits into a PR. Covers:
  pathspec-only commits, byte-exact un-bundling of mixed changes, base-drift
  detection before branching/PR, and when to isolate via worktree vs pause the
  other session.
  TRIGGER when: two sessions edit the same repo at once; a commit's diffstat is
  bigger than your change; "撞車"; a PR bundles commits you didn't make; before
  committing on a repo another session/agent is also touching.
  SKIP when: you're the only writer in the repo; spawning fresh parallel agents
  on independent problems (use dispatching-parallel-agents — it isolates up front;
  this skill is for recovering when sharing already collided).
tags: [git, concurrency, hygiene, multi-session]
version: 1.0.0
source: manual
---

# concurrent-session-git

When two Claude sessions (or your hand-opened terminal + a background agent) share
one checkout, the working tree is shared state. One session's `git commit` can
capture another's half-finished edits, and a stale local base can smuggle unpushed
commits into a PR. This skill is the discipline that keeps each session's work
clean and recoverable. Even a solo dev hits this — *you* are the other session.

## Rules (the discipline)

1. **Commit by pathspec, only your files** — `git commit -m "…" -- path1 path2`.
   NEVER `git add -A`, `git add .`, or `git commit -a` on a shared tree. The
   auto-stage hook stages everything Edit/Write touches, so pathspec at commit
   time is your only real protection.
2. **Check the diffstat after every commit** — if `N files / +X / -Y` is bigger
   than your change, you bundled someone else's WIP. Stop and un-bundle (below).
3. **Check base-drift before branching / PR** — `git log origin/<base>..<base>`.
   If local base is ahead (unpushed commits), a squash-merge bundles them into
   your PR. Branch from `origin/<base>`, or push the local commits first.
4. **Don't `reset --hard` a shared tree** — it destroys the other session's
   uncommitted WIP. Use byte-exact un-bundle or `git stash` instead.
5. **Stop auto-committing a contended tree** — if a second session is actively
   editing, isolate (worktree) or pause it. Repeated per-step commits on a shared
   tree keep stealing the other's WIP.

## Byte-exact un-bundle (you already committed mixed changes)

When one file holds your change + another session's uncommitted change, and you
committed both:

```bash
cp path /tmp/bundled                 # 1. preserve everything (yours + theirs)
git reset --soft <parent>            # 2. undo the bundled commit, keep changes
git checkout <parent> -- path        # 3. restore the CLEAN base of that file
# 4. re-apply ONLY your change to the clean file (Edit, or extract your hunk
#    from /tmp/bundled if your region is disjoint from theirs)
git commit -m "…" -- path            # 5. commit your change alone
cp /tmp/bundled path                 # 6. restore the bundle → git diff now shows
                                     #    ONLY their change, back as uncommitted WIP
```

This works cleanly when your edit and theirs touch **disjoint regions** of the
file (verify with `git diff HEAD -- path | grep '^@@'` — no overlap with your
lines). If they overlap, you can't auto-split; pause the other session and
coordinate.

## Worktree isolation (prevent it entirely)

```bash
git worktree add ../<repo>-mywork <branch>   # your own working dir, shared .git
```

Edit/commit there; your tree is no longer shared, so no collision. Caveat: you
can't check out the same branch in two worktrees, and switching the main tree's
branch disrupts the other session — coordinate before moving it.

## Gotchas

- **Solo dev is not immune**: two of your own sessions on one checkout collide
  exactly like two people. The "other session" is still you.
- **`git checkout origin/main -- <file>`** pulls a clean version into the working
  tree + index — handy for step 3 above and for grabbing a file your stale branch
  base lacks.
- **Surface it, don't silently bundle**: committing another session's WIP under
  your message (even on a solo repo) misattributes and can prematurely land their
  unfinished work. Disclose it; let the owner decide.
- **PR diffs by content, not commits**: if `origin/main` already contains your
  stale base's commits' *content* (via an earlier squash), a PR from that base
  shows only the net-new diff — the old commits cancel out. Reassuring, but
  confirm with `git diff origin/main..HEAD`.
