---
name: Learnings Promotion Sprint
loop: platform
pdca: act
description: >
  Periodic cross-project `.learnings/` distillation. Sweeps every project's
  `.learnings/` + `~/.claude/learnings/`, classifies entries into generic /
  platform-meta / project-specific / drop, distills recurring patterns into
  dense rules in the right CLAUDE.md, and leaves an audit trail.
  TRIGGER: "整理 learnings", "learnings 太多", "跨專案整理", "promotion sprint",
  /learnings-promotion-sprint, or whenever `~/.claude/learnings/LEARNINGS.md`
  exceeds ~30 entries, or cross-project `.learnings/` accumulate ≥ 80 entries.
  SKIP: single-entry write (use `self-improving-agent`); single-project weekly
  retro (use `workflow-retro`); git history retro (use `gstack-retro`).
version: 1.0.0
tags: [meta, learning, distillation, cross-project, monthly]
languages: all
---

# Learnings Promotion Sprint

Periodic distillation pass over the whole `.learnings/` graveyard. Reads every
project's local `.learnings/` plus the global `~/.claude/learnings/`, then
**promotes** the patterns that recur across projects into dense rules in the
appropriate `CLAUDE.md` so future sessions see them automatically.

**Announce at start:** "開始 learnings promotion sprint — 掃 N projects、M entries → 委派分類 → 寫入 CLAUDE.md。"

## Why this exists

`self-improving-agent` is great at *capturing* — every correction, every error,
every "wait, that's not how it works" gets logged. But the captured entries
pile up in three places (project vaults, global vault, ERRORS files), and the
real value is buried until someone reads them. Two specific failure modes:

- **Duplication across projects.** The same "pnpm vs npm" trap fires in
  3 projects, each logging it locally. Until the third one notices, the rule
  isn't load-bearing — every future project trips on it again.
- **Global vault entropy.** `~/.claude/learnings/LEARNINGS.md` grows linearly;
  past ~30 entries, the signal-to-noise drops and entries stop being read.

This skill is the **periodic compaction pass**. Distinct from
`self-improving-agent` (writes one entry at a time) and `workflow-retro`
(reads one project's signals weekly). This one runs roughly monthly, looks at
**all** projects at once, and produces dense rules — not more entries.

## When to fire

| Trigger | Source |
|---------|--------|
| User says "整理 learnings", "跨專案 distillation", "promotion sprint" | conversation |
| `wc -l ~/.claude/learnings/LEARNINGS.md` > ~600 lines (≈ 30 entries) | size |
| `find ~/Documents/Projects -name LEARNINGS.md -path '*/.learnings/*' \| xargs wc -l \| tail -1` > 2000 | aggregate size |
| `workflow-retro` flags "same theme in 3+ projects' `.learnings/`" | retro signal |
| It's been > 30 days since last `reports/learnings-promotion-sprint-*.md` | calendar |

## Workflow — six steps

### Step 1 — Scan & dump

Run the bundled helper. It enumerates every `.learnings/` (project-local
+ global), captures size + entry count, and dumps every entry into one
flat file the next step can hand to a subagent.

```bash
bash skills/platform/learnings-promotion-sprint/scripts/dump-learnings.sh
```

Outputs:
- `/tmp/learnings-sweep/inventory.tsv` — `project<TAB>path<TAB>lines<TAB>entries`
- `/tmp/learnings-sweep/all.txt` — all entries concatenated, each prefixed with
  `### [<project>] <original-heading>` so the classifier knows where each came from
- prints a summary table to stdout

**Why a bundled script:** the previous manual sprint (2026-05-13) repeated
this find/cat/wc dance ~8 times. Codifying it removes a class of foot-guns
(missing a project, double-counting, stale `/tmp` dirs).

### Step 2 — Delegate classification to a subagent

This is the critical move: the classification phase reads thousands of lines.
Doing it in the main context burns budget and pollutes future reasoning. Use
`general-purpose` Agent so the bulk reading stays out of the main thread.

Prompt the agent (verbatim template):

> Read `/tmp/learnings-sweep/all.txt`. Each entry is prefixed with
> `### [<project>] <heading>`. Classify every entry into exactly one of four
> buckets:
>
> - **🌍 Generic** — would apply if you switched to a totally different
>   project tomorrow (macOS, git, shell, Node/Python framework gotchas,
>   common APIs). Promotion target: `~/.claude/CLAUDE.md`.
> - **🏛️ Platform-meta** — tied to one toolchain the user maintains
>   (rivendell, gstack, etc.) but applies across that platform's projects.
>   Promotion target: `<repo>/.claude/CLAUDE.md`.
> - **🏠 Project-specific** — schemas, paths, business logic of ONE codebase.
>   Stays in the original `.learnings/`.
> - **🗑️ Drop** — stale, already-fixed, or too narrow to be load-bearing.
>
> For Generic and Platform-meta, **merge duplicates** — when 2+ entries
> describe the same trap, fuse them into ONE proposed rule. The rule must:
> (a) be dense (1–4 lines), (b) explain the *why* in one phrase, (c) name
> the concrete command or check the future-agent should run.
>
> Output to `/tmp/learnings-sweep/classified.md` using the template in
> `skills/platform/learnings-promotion-sprint/assets/classified-template.md`
> (or, if that file does not exist, follow the structure of
> `reports/learnings-promotion-sprint-2026-05-13.md`).
>
> Report counts: `Generic: N (→ M merged rules)`, `Platform-meta: N`,
> `Project-specific: N`, `Drop: N`. Total must equal the entry count in
> `/tmp/learnings-sweep/inventory.tsv`.

**Routing test** (give this to the subagent, but useful to know yourself):
"Would I want this rule when working in a totally different project
tomorrow?" Yes → Generic. No, but yes across all my rivendell projects →
Platform-meta. No, only this codebase → Project-specific.

### Step 3 — Review the classification (main context, fast)

Read `/tmp/learnings-sweep/classified.md`. Spot-check:

- Counts add up to `inventory.tsv`'s total entry count.
- No proposed Generic rule is actually project-specific (a misclass here
  pollutes `~/.claude/CLAUDE.md` permanently).
- No rule duplicates an existing entry in `~/.claude/CLAUDE.md` — `grep` the
  proposed rule's key phrase against the live file before promoting.
- Each proposed rule has a *why* — if a rule reads as "do X" without
  explaining why X matters, it will be ignored at use time. Ask the agent
  to revise, or revise inline.

If anything looks off, send corrections back to the same subagent rather
than re-reading the dump yourself — keeps the main context clean.

### Step 4 — Promote into the right CLAUDE.md

For each accepted rule:

**Generic** → append to `~/.claude/CLAUDE.md`'s `## Engineering Gotchas`
section (or create the section if absent). Keep the section ordered by
**recency of last promotion** so old rules drift to the top and new rules
sit at the bottom — makes review easier next sprint.

**Platform-meta** → append to `<repo>/.claude/CLAUDE.md` under a section
named after the platform (e.g. `## Rivendell Operations`).

Insertion pattern:

```markdown
- **<one-line rule>**: <terse spec including the command to run>. Reason: <one-phrase why>. <optional: pointer to original learning entry>
```

Example (from 2026-05-13 sprint):

```markdown
- **`.next/` is atomic**: Never partially delete (`rm -rf .next/dev`, `rm -rf .next/cache`). Turbopack leaves dangling refs → `Cannot find module ../chunks/ssr/[turbopack]_runtime.js`. Only safe path: kill next-server → `mv .next .next.broken-$(date +%s)` → fresh `npm run build`.
```

### Step 5 — Stamp the originals

For each `.learnings/LEARNINGS.md` whose entries got promoted, prepend a
header note so future readers (and the next sprint) know those entries
already paid out:

```markdown
> **Promotion sprint 2026-MM-DD:** Entries below this line were swept and
> classified. Generic patterns were distilled into `~/.claude/CLAUDE.md`;
> platform rules into `<repo>/.claude/CLAUDE.md`. See
> `reports/learnings-promotion-sprint-2026-MM-DD.md` for the classification
> report. New entries below this header are eligible for the next sprint.
```

Do NOT delete the original entries — they remain the historical record.
The header just signals "already harvested, no need to re-read on the next
pass for entries above it."

### Step 6 — Save the classification report

Copy `/tmp/learnings-sweep/classified.md` to
`<this-project>/reports/learnings-promotion-sprint-YYYY-MM-DD.md`. This is
the audit trail — next sprint will diff against it to see what's new vs.
already-distilled.

If you're running this from a project that doesn't have a `reports/`
directory, default to the rivendell repo (`~/Documents/Projects/rivendell/reports/`)
since rivendell hosts the meta-tooling.

## Output checklist

When done, the user should see:

- [ ] N rules added to `~/.claude/CLAUDE.md` (Generic)
- [ ] M rules added to `<platform>/.claude/CLAUDE.md` (Platform-meta)
- [ ] K project `.learnings/LEARNINGS.md` files stamped with promotion header
- [ ] One report at `reports/learnings-promotion-sprint-YYYY-MM-DD.md`
- [ ] Summary line: `Swept N projects / X entries → Y promoted rules (G generic + P platform) / D dropped`

## Cross-skill boundaries

| Skill | Role |
|-------|------|
| `self-improving-agent` | Writes single entries into `.learnings/`. The producer this skill consumes from. |
| `workflow-retro` | Weekly single-project read; if it sees the *same* theme repeat across multiple projects' `.learnings/`, it should flag for the next sprint of this skill. |
| `gstack-retro` | Reads git history, not `.learnings/`. Orthogonal. |
| `session-harvest` | Per-session skill candidate discovery; doesn't touch `.learnings/`. |

The two-skill design (`self-improving-agent` writes one-by-one;
`learnings-promotion-sprint` distills in bulk) is intentional. Single-entry
promotion is a different cognitive job than mass classification: the first
is a fast inline judgment in the middle of work; the second wants the whole
corpus in front of you so duplicates collapse.

## Reference: 2026-05-13 seed sprint

The 2026-05-13 manual run is the canonical example of what this skill
codifies. Stats from that sprint:

- 11 projects swept (`~/Documents/Projects/*/.learnings/`) + global vault
- 125 entries classified
- 24 generic → 14 distilled rules into `~/.claude/CLAUDE.md`
- 17 platform-meta → 6 rules into `rivendell/.claude/CLAUDE.md`
- 67 project-specific → stayed put
- 17 dropped (stale / already-fixed / too narrow)

Read `~/Documents/Projects/rivendell/reports/learnings-promotion-sprint-2026-05-13.md`
to see the full output structure — section ordering, merge notation, "Why
generic" justification per rule, and the per-project stamping at the end.

## Failure modes to avoid

- **Skipping the subagent delegation.** Reading 100+ entries in the main
  context is a guaranteed way to lose track of the *current* task. The
  bulk read MUST go through a subagent.
- **Promoting too eagerly.** A rule that only fired once is not load-bearing
  yet — it should stay in `.learnings/` until a second project hits the
  same trap. The merge-2+ heuristic in Step 2 enforces this.
- **Forgetting the *why*.** Rules without justification get ignored at
  use time. Every promoted rule needs a `Reason:` or `Why:` phrase.
- **Editing rules in-place across sprints.** If a previously-promoted rule
  needs updating, leave the old line and append a follow-up note rather
  than rewriting — `git blame` on `CLAUDE.md` is one of the better signals
  for "is this rule still trusted?"
