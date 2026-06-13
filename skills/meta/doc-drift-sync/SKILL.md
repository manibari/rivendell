---
name: doc-drift-sync
description: >
  Keep a project's living docs aligned when version or state moves — detect and fix
  drift across CHANGELOG.md, ROADMAP.md, CLAUDE.md, and progress.md so they stop
  contradicting each other (roadmap "done" items actually appear in the changelog,
  progress reflects the roadmap, version numbers match across files and git).
  Also owns the project's ITERATION CYCLE: a weekly cadence (anchored to
  workflow-retro) on which these docs are reviewed and bumped, so they drift on
  purpose, not by neglect.
  TRIGGER when: bumping a version, finishing an iteration/sprint, "更新文件", "版本對齊",
  "文件漂移", "sync changelog/roadmap", "對齊 roadmap", or when CHANGELOG's latest entry
  disagrees with git tags / package.json / the roadmap. Make sure to reach for this
  whenever the user mentions version bumps, release prep, roadmap/changelog updates,
  or an iteration / retro cadence — even if they never say the word "drift".
  SKIP when: authoring a brand-new document from scratch (use doc-coauthoring), or
  regenerating the README skills catalog from SKILL.md frontmatter (use sync-readme).
metadata:
  type: meta
  tags: [docs, versioning, roadmap, changelog, iteration, maintenance]
---

# doc-drift-sync

## Why this exists

Solo / small-team projects accumulate **living docs** that are supposed to agree
with each other but quietly fall out of sync: a feature lands in `CHANGELOG.md`
but the `ROADMAP.md` still lists it under "Next"; `progress.md` claims something
is done that the roadmap never marked; the version in `package.json` is ahead of
the newest `CHANGELOG` heading. Each file is edited in isolation, so the drift is
invisible until someone trusts the wrong one.

This skill does two things:

1. **Detect & fix drift** across the canonical doc set in one pass.
2. **Define the iteration cycle** — the recurring rhythm on which the docs get
   reviewed — so alignment is a scheduled habit, not a heroic cleanup.

It does NOT author new docs (that's `doc-coauthoring`) and does NOT regenerate the
README catalog from skill frontmatter (that's `sync-readme`).

## The canonical doc set

Per project, these four are the source of truth and must agree:

| File | Owns | Drift smell |
|------|------|-------------|
| `CHANGELOG.md` | What shipped, by version/date | newest heading < git tag / package version |
| `ROADMAP.md` | What's planned: Now / Next / Later / Done | "Done" item missing from CHANGELOG |
| `progress.md` | Current working state / in-flight | claims done but roadmap says Next |
| `CLAUDE.md` (+AGENTS.md) | Rules, structure, counts | stale counts, dead paths, renamed things |

Not every project has all four — sync whichever exist. If a project clearly needs
one it lacks (e.g. ships versions but has no CHANGELOG), flag it; don't silently
fabricate history.

## Drift-detection workflow

1. **Read all that exist** in one pass — don't trust file mtime, read the content.
2. **Establish ground truth for version**: read `git tag --list | sort -V | tail`,
   `package.json`/`pyproject.toml` version, and the newest `CHANGELOG` heading.
   The highest real, shipped state wins; reconcile the others to it.
3. **Cross-check the alignment rules** (below). List every contradiction with a
   file:line pointer — evidence, not assertion.
4. **Fix forward, never invent backward**: add the missing CHANGELOG line for a
   shipped roadmap item; move the roadmap item to Done; correct the stale count.
   If a fact can't be verified from git history or the other docs, write `待補`
   rather than guessing what "must have" happened.
5. **Report** the diff you made and any residual `待補` so the user can fill gaps.

## Alignment rules (the cross-checks)

- Every `ROADMAP` **Done** item has a matching `CHANGELOG` entry (and vice-versa:
  a shipped CHANGELOG line should not still sit under roadmap Now/Next).
- `progress.md`'s "current focus" is consistent with roadmap **Now** — not ahead
  of it, not behind.
- Version appears identically in: newest CHANGELOG heading, `package.json`/
  manifest, the latest git tag (if the project tags), and any doc that cites it.
- `CLAUDE.md` structural claims (skill counts, directory tree, file paths) match
  reality — re-derive counts, don't trust the written number.

## The iteration cycle

Docs only stay aligned if review is on a cadence. Anchor it to whatever recurring
rhythm the project already has rather than inventing a new ceremony.

- **Default cadence: weekly, ISO week** (e.g. `2026-W24`). In rivendell this rides
  the existing **`workflow-retro`** (fires Sunday/Monday). One iteration =
  one retro = one doc-alignment pass.
- **Each iteration**: retro surfaces what changed → move `ROADMAP` items between
  Now/Next/Done → append a `CHANGELOG` entry for the week → run this skill's
  cross-checks → fix drift.
- **Versioning**: prefer the project's existing scheme. If none, ISO-week tags
  (`2026-W24`) suit an internal platform better than semver — they map 1:1 to the
  retro cadence. Apps with external consumers should use semver instead.
- A `CHANGELOG` `[Unreleased]` section collects changes mid-iteration; it's
  promoted to a dated/versioned heading at the iteration close.

## Output

A short report: (a) drift found (file:line), (b) edits applied, (c) any `待補`
left for the user, (d) whether this iteration's CHANGELOG/ROADMAP were advanced.
Then prompt whether to commit (per the user's git habit), staging ONLY the doc
files — never sweep in unrelated generated artifacts (e.g. `reports/*`).
