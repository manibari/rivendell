---
name: Workflow Retro
loop: platform
pdca: act
description: >
  Weekly retrospective for rivendell skills+agents — reads telemetry, surfaces
  next workflow bottleneck. Outputs reports/workflow-retro-YYYY-WW.md + 1-3 actions.
  TRIGGER: /workflow-retro, "weekly retro", "本週回顧", or Sunday/Monday agent fire.
  SKIP: per-session candidates (session-harvest); single-error log (self-improving-agent);
  commit-history retro (gstack-retro).
version: 1.0.0
tags: [meta, observability, retro, workflow, weekly]
languages: all
---

# Workflow Retro

Weekly retrospective on the rivendell automation system itself. Three questions,
one page, 1-3 actions. The point is not to produce reading material — it's to
surface the next thing worth fixing.

**Announce at start:** "正在拉本週的 skill / agent / learnings 數據，產出 workflow retro..."

## Why this exists

Rivendell already has reactive observability: `.learnings/` catches mistakes after
they happen, `session-harvest` catches skill candidates after a session ends. What's
missing is the layer above — *is the system as a whole getting healthier or noisier
week over week?* Reactive tools can't answer that because each one only sees its
own slice.

A weekly retro merges all the slices into one read. If the read keeps producing the
same finding ("nobody triggers the X skill we built last month"), that finding
becomes an action ("retire X" or "rewrite its description"). If it keeps producing
nothing, the retro itself can be retired — it's not load-bearing yet.

## The Three Axes

### 1. 使用度 (Usage)
Who is actually getting used, who is dead weight.

- **Skill firing frequency** this week → `GET http://localhost:8000/api/skills/usage`
  Group by skill, count entries with `date` in the last 7 days.
- **Skill never fired in 30 days** → same endpoint, no entries with date >= today-30d.
  These are candidates for retirement, not because they're bad but because either
  the description doesn't trigger or the use case never came up. Both are signals.
- **Agent execution status** → `launchctl list | grep com.sk` then per-agent
  `GET /api/agents/{label}/runs` for exit-code history.
  Note `0` = success, `1+` = failure, `-` = never ran (suspicious if the agent is
  scheduled and the schedule has passed).

### 2. 重複痛點 (Recurring Pain)
Themes that show up 3+ times in `.learnings/LEARNINGS.md` or recent harvest reports.
Repetition is the signal — a one-off bug is noise; a pattern that surfaces three
weeks in a row is a workflow gap.

- **Source A**: `.learnings/LEARNINGS.md` — scan section headers for repeated
  topics (e.g., "next.js build", "launchd plist", "TCC permission").
- **Source B**: `reports/harvest-*.md` from the last 14 days — look for the same
  skill candidate being suggested across multiple reports without being built.
- **Source C**: `reports/skill-audit-*.md` issue counts — issues that persist
  week to week without count dropping.

For each repeated theme, identify whether it's:
- **Mechanical** (can be agent-ed away — e.g., symlink drift)
- **Editorial** (needs a documentation/skill update — e.g., recurring ambiguity
  about which skill to use)
- **Architectural** (needs a real fix — e.g., recurring outage class)

### 3. 集中度 (Concentration)
Where time, tokens, or failures are concentrating.

- **Token / cost by project** → `GET http://localhost:8000/api/tokens` plus
  `/api/tokens/filtered` for last-7-day breakdown. Highlight any project taking
  >40% of weekly cost — concentration that high deserves a "is this the right tool
  for the job" question.
- **Failing agents** → from axis 1's run history, list agents whose exit-1 rate
  is non-trivial (≥1 failure / week of scheduled runs).
- **Watchdog log** → `reports/watchdog.log` — non-empty means dashboard restarts
  happened. Multiple restarts in a week is a trend worth naming.

## Data Sources Quick Reference

| Source | What it gives |
|--------|---------------|
| `GET /api/skills/usage` | Per-skill firing dates and counts |
| `GET /api/agents` | All registered agents + load/exit status |
| `GET /api/agents/{label}/runs` | Exit-code history per agent |
| `GET /api/tokens` and `/api/tokens/filtered` | Daily and per-project cost |
| `reports/skill-audit-*.md` | Structural skill health snapshots |
| `reports/test-*.md` | Daily structural validation results |
| `reports/harvest-*.md` | Past skill-candidate decisions |
| `reports/watchdog.log` | Dashboard restart events |
| `.learnings/LEARNINGS.md` | Manual fixes / corrections / best practices |

If the dashboard API is down (`curl` fails), fall back to file-based sources only —
flag the API outage as itself a finding for axis 3.

## Report Structure

Always write to `reports/workflow-retro-YYYY-WW.md` where `WW` is the ISO week
number (`date +%G-W%V`). One file per week — overwrite if rerun mid-week.

```markdown
---
date: YYYY-MM-DD
iso_week: YYYY-WW
period: YYYY-MM-DD to YYYY-MM-DD (last 7 days)
source: workflow-retro
---

# Workflow Retro — YYYY-WW

## TL;DR
One-paragraph summary. What changed this week vs last? Most important finding?

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+ this week) | ... | ... |
| 低頻 (1-4 this week) | ... | ... |
| 沉寂 (30+ days) | ... | ... |

Brief interpretation — anything surprising? Anything to retire?

## 重複痛點

(For each theme appearing 3+ times)
### Theme name
- **頻率**: N occurrences across [sources]
- **類別**: Mechanical / Editorial / Architectural
- **代表性事件**: One-line example
- **建議**: Concrete next step

If no themes meet the threshold, write "本週無重複痛點 — 系統穩定" and move on.

## 集中度

- **Token 集中**: Top project + % of weekly cost
- **失敗集中**: Agents with ≥1 non-zero exit this week
- **Dashboard 健康**: Watchdog restart count

## 下週 Actions (max 3, prioritized)

1. **[Action]** — Why now, est. effort, expected impact
2. ...
3. ...

If there are no clear actions, write "本週系統健康度良好，無明確優化項目"
rather than padding with weak suggestions. The retro's value comes from
restraint — three real actions beat ten speculative ones.

## 對照上週
(skip on first run)
- 上週 actions 完成度: X / Y
- 上週指標 → 本週指標的變化
```

## Heuristics for Quality

- **Actionability over completeness.** Don't list every skill with low usage if
  three of them are deprecated by design. Mention only those whose low usage is
  surprising or actionable.
- **Three is a real threshold.** A theme appearing twice could be coincidence.
  Three times is the minimum for "pattern." Be honest if nothing crosses it.
- **Surface the meta.** If the retro's own findings keep being ignored week over
  week, that's the most important finding — name it explicitly.
- **No padding.** "Empty" is a valid section. A 200-word retro that tells the
  truth beats a 2000-word retro that hedges.

## Integration with Other Skills

| Other skill | Relationship |
|-------------|--------------|
| `session-harvest` | Per-session, finds skill candidates. Retro consumes its output (the harvest reports) as one of its sources. |
| `self-improving-agent` | Captures individual learnings. Retro reads `.learnings/` to find themes across many learnings. |
| `gstack-retro` | Commit-history retro from the gstack repo. Complementary, not duplicative — one looks at code shipped, one looks at automation health. Run them together for a full picture. |
| `skill-creator` | Hand off here when retro identifies a skill that should be built. |

## When to Skip a Week

If less than 5 sessions happened in the last 7 days, the data is too sparse for
meaningful trend reading. Write a 3-line "low activity week, skipped retro" entry
and move on. Forced retros on idle data produce noise that erodes trust in the
report.
