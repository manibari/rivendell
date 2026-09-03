---
name: skill-apply
loop: platform
pdca: do
description: >
  Turn a skill you have imported but not installed into a review of your own codebase — read an
  external skill repo (matt-skills and the like) off disk, pick the lenses that fit, and run them
  target by target until each one lands a durable artifact in the repo under review.
  TRIGGER when: the user names an external skill collection and a thing of their own to judge —
  "用 matt-skills 檢查這個專案", "基於 [外部 skill] 看一下 X 有沒有偷吃步", "拿 grill-me 審我的架構",
  "apply domain-modeling to these modules", "run their code-review checklist over my repo"; also
  right after skill-scout finishes importing, when the next request is to evaluate something.
  DO NOT TRIGGER when: importing or comparing skills without applying them (skill-scout), writing or
  editing a skill (skill-creator, writing-great-skills), or auditing a repo with rivendell's own
  scoring (github-repo-audit) — this skill's whole point is that the judgement comes from someone
  else's skill, not ours.
when_to_use: an imported external skill needs to be pointed at your own project and produce findings
version: 1.0.0
tags: [meta, skills, review, architecture]
languages: all
user_invocable: true
---

# skill-apply

Someone else wrote a good review skill. It sits in a cloned repo, uninstalled. This skill closes the
gap between having it and having been judged by it.

The judgement is **borrowed** — the standards come from the external skill, not from you and not
from rivendell. Your job is to carry them faithfully to a target and record the verdict where it
will still be found in six months.

Grounded in two real runs (2026-08-03 ChimesFlow architecture, 190 messages; 2026-08-05 PTI-ARES
five-board audit, 683 messages). What went wrong in those runs is why several steps below exist.

## Step 1 — Read the source, because you cannot call it

An imported skill repo is almost never deployed. `matt-skills` is cloned at
`~/code/matt-skills` and has **no symlink** in `~/.claude/skills/` — and 24 of its 41 skills carry
`disable-model-invocation: true`, which strips their description so no other skill can reach them
even when they are installed.

So there is nothing to invoke. You **read the SKILL.md as text and execute it yourself**.

```bash
REPO=~/code/matt-skills                      # or wherever the user cloned it
find "$REPO/skills" -name SKILL.md | sed "s|$REPO/skills/||"
```

Read the candidate skills in full, including their sibling files — the review skills keep their
teeth there. `domain-modeling/` carries `ADR-FORMAT.md` and `CONTEXT-FORMAT.md`;
`improve-codebase-architecture/` carries `HTML-REPORT.md`; several carry an `agents/` directory.
Skipping those is how a run ends up inventing an output format that the skill already specified.

**Done when** you can state, for each lens you plan to use, what it looks for and what it emits.

## Step 2 — Name the target, and name it concretely

A **lens** is one external skill applied to one **target**. Both must be concrete before any
reviewing starts, because "review the project" has no completion criterion and will drift.

Targets seen so far: one whole architecture (ChimesFlow), and a set of five boards whose handling
code was suspected of shortcuts (PTI-ARES). Both are legitimate — a target is anything you can
finish having an opinion about.

Lay out the grid and get it agreed before spending a single review turn:

| | domain-modeling | code-review | diagnosing-bugs |
|---|---|---|---|
| pb0009 | ✓ | ✓ | — |
| PB0015 | ✓ | — | — |

The 683-message run applied 4 lenses to 5 targets in one session and **the user interrupted it
twice**. Twenty cells is not a session, it is a project. Confirm the grid, then commit to a small
number of cells for this round — the rest are the next round's work, not this one's.

## Step 3 — Run one cell at a time

Work one cell to completion, write its artifact, then start the next. The grid is the checkpoint:
an interrupted run resumes by looking at which cells already have artifacts, so nothing depends on
the session surviving.

**Keep the external skill's interaction rhythm.** The grill family works by asking one question at
a time, offering a recommended answer, and refusing to proceed without agreement — that is the
mechanism, not the packaging. The 683-message run used `AskUserQuestion` 14 times and was right to.
Compressing an interview into a single batched verdict produces a confident review of a project you
never actually understood; when a lens interviews, interview.

Evidence comes from the repo under review — files read, commands run, counts taken. A borrowed lens
sharpens what you look for; it cannot tell you what is true here.

**Done when** the cell's verdict is one you could defend with specific lines and numbers.

## Step 4 — Land the artifact in the repo under review

The artifact goes in the **target's** repo, in the format the applied skill specifies — not in
rivendell, not in chat. That is what makes this different from an opinion.

The two runs differ instructively on exactly this point:

- **Survived** — `domain-modeling` writes `docs/adr/NNNN-slug.md`, sequential, per its
  `ADR-FORMAT.md`. PTI-ARES still has all four
  (`0001-three-packages-one-repo.md` … `0004-one-distribution-three-versions.md`), committed,
  readable a week later.
- **Gone** — the ChimesFlow run produced a standalone HTML report. The 08-03 harvest names the file;
  it is no longer anywhere on disk. 190 messages of review, unrecoverable.

A generated report that nobody commits is a chat message with extra steps. Prefer the format that
lands *in the source tree* next to what it judges, and commit it in the same breath. Where a lens
does specify a rich standalone format, write it into the repo and commit it — the format is not the
problem, the orphaning is.

When a lens specifies no format, a findings file beside the code beats a chat message. Record what
you looked at, what you found, and what was decided — a reader in six months needs the reasoning,
not the score.

Cite the lens and its commit: `domain-modeling @ matt-skills 2ab9580`. External skills move, and a
verdict whose standard has since changed should be re-readable as history rather than mistaken for
current policy.

**Done when** every agreed cell has a committed artifact.

## Step 5 — Order the work

Reviews produce more findings than anyone will act on. Close with a short ordered list — what to fix
first and why that one first. Ordering is the deliverable; an unordered list of twelve problems is
another thing to triage, not a decision.

## Notes

- **Anchored on matt-skills.** Both runs used the same source, so that is the only collection this
  skill has been verified against. Another collection with a different structure — skills that
  assume installation, or that bundle executable scripts — may need Step 1 adapted. Widen this
  section once a second source has actually been through it.
- **The user is the standard's owner.** A borrowed lens can be wrong about your project: the 08-05
  run rejected a `pti-core` shared package on grounds specific to a solo developer, which no generic
  checklist would have known. When a lens's recommendation collides with the project's reality, say
  so in the artifact and record why the standard was declined. Declining with a reason is a finding.
- **Neighbours.** `skill-scout` gets the repo onto disk; this skill starts once it is there.
  `github-repo-audit` judges with rivendell's own rubric; this one deliberately does not.
