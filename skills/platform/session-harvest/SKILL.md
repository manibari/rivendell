---
name: Session Harvest
loop: platform
pdca: check
description: >
  Review the current session and extract reusable skill candidates — analyzes tool
  patterns, multi-step workflows, domain knowledge.
  TRIGGER: /session-harvest, "harvest skills", "extract skills", "告一段落", "收割".
  SKIP: creating a known skill (skill-creator); error logging (self-improving-agent);
  code review.
version: 1.0.0
tags: [meta, skills, harvest, session-review]
languages: all
---

# Session Harvest

Review what happened in the current session and identify work patterns worth turning into reusable skills. The goal is to grow the skills library organically from real usage rather than speculative design.

**Announce at start:** "正在檢視這次 session 的工作內容，尋找可以變成 skill 的模式..."

## What Makes a Good Skill Candidate

Not everything is worth a skill. Look for patterns that are:

1. **Repeatable** — The same workflow will likely happen again in future sessions
2. **Non-trivial** — Takes 3+ steps or requires domain knowledge that isn't obvious
3. **Generalizable** — Works across projects, not just this specific codebase
4. **Not already covered** — Check existing skills before suggesting duplicates

Patterns that are NOT good skill candidates:
- One-off fixes for a specific bug
- Simple operations Claude already handles well without guidance
- Workflows that are too project-specific to generalize

## Two Modes

### Single-session mode (default)
Review only the current session's tool calls and conversation. Use this when invoked as `session-harvest` without arguments.

### Cross-session mode ("harvest all" / "其他 session")
Read past harvest reports from `reports/harvest-*.md`, filter out skills that have already been built, and integrate all unimplemented Strong/Moderate candidates into a single prioritized list.

```bash
# 1. List historical reports
ls reports/harvest-*.md 2>/dev/null | sort -r

# 2. Extract candidate names from each report (Strong/Moderate sections)
for f in reports/harvest-*.md; do
  echo "=== $(basename $f) ==="
  grep -E "Strong|Moderate|🟢|🟡|★★★|★★" "$f" 2>/dev/null
done

# 3. Cross-reference with currently installed skills
ls ~/.claude/skills/

# 4. Frequency-rank unimplemented candidates (more reports = stronger signal)
```

Trigger cross-session mode when user says: "harvest all", "skills harvest all", "其他 session 也 harvest", "整合過去的 harvest", or asks about "未實作的候選".

Present results as **frequency-ranked unimplemented candidates** — the more reports mention a pattern, the stronger the signal it should be built.

---

## How to Harvest

### Step 1: Reconstruct the Session

Review the conversation to understand what was accomplished. Focus on:

- **Tool call sequences** — What tools were used in what order? Repeated sequences suggest a workflow.
- **Multi-step problem solving** — Where did you take 5+ steps to accomplish something? Could a skill have guided you through it faster?
- **Domain knowledge applied** — Did you use specialized knowledge (API quirks, framework conventions, pricing models, deployment patterns)?
- **User corrections** — Where did the user redirect you? This reveals implicit knowledge that should be codified.
- **Research patterns** — Did you read multiple files, search docs, or web search to figure something out? That research could be pre-baked into a skill.

### Step 2: Identify Candidates

For each candidate, assess:

| Criterion | Question |
|-----------|----------|
| Frequency | Will this pattern come up again? How often? |
| Complexity | How many steps / how much knowledge is involved? |
| Generality | Does this apply to other projects or just this one? |
| Existing coverage | Is there already a skill that handles this? |
| Value | How much time/effort would the skill save per use? |

Score each candidate as: **strong** (definitely create), **moderate** (worth discussing), or **weak** (probably not worth it).

### Step 3: Present Findings

Output a structured report:

```markdown
# Session Harvest Report

## Session 概要
- **日期**: YYYY-MM-DD
- **主要工作**: One-line summary
- **涉及技術**: Key technologies used

## Skill 候選清單

### 🟢 Strong: [Skill Name]
- **用途**: What it would do
- **觸發時機**: When it would activate
- **涵蓋步驟**: The workflow it would encode
- **分類建議**: Which category (meta/workflow/quality/frontend/backend/docs/git)
- **來源**: What happened in this session that surfaced this pattern
- **現有相似**: Any existing skill that partially overlaps (and how this differs)

### 🟡 Moderate: [Skill Name]
...

### 🔴 Weak: [Skill Name] (not recommended)
- **原因**: Why this isn't worth a skill
```

### Step 4: Cross-Reference

Before finalizing, check the existing skills library:

1. Read the skills list from the project's README or run `./bin/sk list`
2. For each candidate, verify it doesn't duplicate an existing skill
3. If a candidate overlaps with an existing skill, suggest **enhancing** the existing skill instead of creating a new one

### Step 5: Next Steps

For each strong candidate, offer:

> **要建立 [skill name] 嗎？** 我可以用 skill-creator 來產生完整的 SKILL.md。
> 或者先記錄到 `.learnings/FEATURE_REQUESTS.md`，之後再處理。

If the user wants to proceed, hand off to the `skill-creator` skill with a pre-filled brief.

## Example: What a Harvest Looks Like

Suppose in a session you:
1. Built a Streamlit dashboard that reads Claude Code stats
2. Parsed JSONL session files for token usage
3. Estimated costs using per-model pricing
4. Added date range filtering

The harvest might identify:
- **Strong**: "claude-data-reader" — A skill for parsing Claude Code's data files (stats-cache.json, JSONL sessions, settings.json). Encodes the file formats, field names, and common aggregation patterns.
- **Moderate**: "streamlit-dashboard" — Patterns for building Streamlit management dashboards with Chinese UI. Might be too project-specific.
- **Weak**: "date-range-filter" — Adding date pickers to Streamlit. Too simple, Claude already handles this well.

## Integration with Self-Improving Agent

Session Harvest complements the self-improving-agent skill:
- **self-improving-agent** captures _mistakes_ and _corrections_ (reactive)
- **session-harvest** captures _successful patterns_ and _workflows_ (proactive)

If during harvest you notice corrections that weren't logged, suggest logging them via self-improving-agent too.
