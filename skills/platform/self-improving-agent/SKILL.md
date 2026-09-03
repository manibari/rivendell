---
name: Self-Improving Agent
loop: platform
pdca: act
description: Captures learnings, errors, and corrections to enable continuous improvement. Routes generic learnings to ~/.claude/learnings/, project-specific ones to <project>/.learnings/, and promotes valuable rules to CLAUDE.md.
when_to_use: when a command fails, user corrects you, you discover outdated knowledge, a better approach is found, user requests missing capability, or before starting major tasks (review past learnings)
version: 2.0.0
tags: [meta, quality, learning, continuous-improvement, hook]
languages: all
---

# Self-Improving Agent

Log learnings and errors to markdown files for continuous improvement. Important learnings get promoted to project memory (CLAUDE.md / AGENTS.md), and recurring patterns get extracted into reusable skills.

## Vault Routing — pick the right destination

This skill writes to one of THREE vaults depending on scope:

| Scope | Vault | When |
|-------|-------|------|
| 🌍 Generic | `~/.claude/learnings/` | macOS, git, shell, JS/Python framework gotchas, common APIs — anything that would apply if you switched to a totally different project tomorrow |
| 🏛️ Platform-meta | `<repo>/.claude/CLAUDE.md` (rule) or `<repo>/.learnings/` (history) | Specific to a platform you maintain (rivendell, gstack) — applies across multiple projects via that platform but tied to its toolchain |
| 🏠 Project-specific | `<current-project>/.learnings/` | Schemas, file paths, business logic, domain quirks of ONE codebase |

**Routing test**: "Would I want this rule when working in a totally different project tomorrow?" Yes → global. No → project-local.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Command/operation fails | Log to `<vault>/ERRORS.md` |
| User corrects you | Log to `<vault>/LEARNINGS.md` with category `correction` |
| User wants missing feature | Log to `<project>/.learnings/FEATURE_REQUESTS.md` (always project) |
| API/external tool fails (generic API) | Log to `~/.claude/learnings/ERRORS.md` |
| Knowledge was outdated | Log to `<vault>/LEARNINGS.md` with category `knowledge_gap` |
| Found better approach | Log to `<vault>/LEARNINGS.md` with category `best_practice` |
| Similar to existing entry | Link with `**See Also**`, consider priority bump |
| Recurring 2+ times in global vault | Distill to one-line rule, promote to `~/.claude/CLAUDE.md`, archive original |
| Broadly applicable platform-meta | Promote to `<platform-repo>/.claude/CLAUDE.md` |

## Setup

Vaults are created on demand:

```bash
# Global vault (shared across all projects)
mkdir -p ~/.claude/learnings

# Project vault (per-codebase)
mkdir -p .learnings
```

## Logging Format

### Learning Entry

Append to `.learnings/LEARNINGS.md`:

```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
One-line description of what was learned

### Details
Full context: what happened, what was wrong, what's correct

### Suggested Action
Specific fix or improvement to make

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file.ext
- Tags: tag1, tag2
- See Also: LRN-20250110-001 (if related to existing entry)

---
```

### Error Entry

Append to `.learnings/ERRORS.md`:

```markdown
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601 timestamp
**Priority**: high
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
Brief description of what failed

### Error
```
Actual error message or output
```

### Context
- Command/operation attempted
- Input or parameters used
- Environment details if relevant

### Suggested Fix
If identifiable, what might resolve this

### Metadata
- Reproducible: yes | no | unknown
- Related Files: path/to/file.ext
- See Also: ERR-20250110-001 (if recurring)

---
```

### Feature Request Entry

Append to `.learnings/FEATURE_REQUESTS.md`:

```markdown
## [FEAT-YYYYMMDD-XXX] capability_name

**Logged**: ISO-8601 timestamp
**Priority**: medium
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Requested Capability
What the user wanted to do

### User Context
Why they needed it, what problem they're solving

### Complexity Estimate
simple | medium | complex

### Suggested Implementation
How this could be built, what it might extend

### Metadata
- Frequency: first_time | recurring
- Related Features: existing_feature_name

---
```

## ID Generation

Format: `TYPE-YYYYMMDD-XXX`
- TYPE: `LRN` (learning), `ERR` (error), `FEAT` (feature)
- YYYYMMDD: Current date
- XXX: Sequential number or random 3 chars (e.g., `001`, `A7B`)

Examples: `LRN-20250115-001`, `ERR-20250115-A3F`, `FEAT-20250115-002`

## Resolving Entries

When an issue is fixed, update the entry:

1. Change `**Status**: pending` to `**Status**: resolved`
2. Add resolution block after Metadata:

```markdown
### Resolution
- **Resolved**: 2025-01-16T09:00:00Z
- **Commit/PR**: abc123 or #42
- **Notes**: Brief description of what was done
```

Other status values:
- `in_progress` - Actively being worked on
- `wont_fix` - Decided not to address (add reason in Resolution notes)
- `promoted` - Elevated to CLAUDE.md or AGENTS.md
- `promoted_to_skill` - Extracted as a reusable skill

## Promoting to Project Memory

When a learning is broadly applicable (not a one-off fix), promote it to permanent memory. The destination depends on scope.

### When to Promote

- Learning has recurred 2+ times (across same or different projects)
- Knowledge any contributor (human or AI) should know
- Prevents recurring mistakes
- Documents project-specific conventions

### Promotion Targets

| Target | What Belongs There |
|--------|-------------------|
| `~/.claude/CLAUDE.md` | Cross-project engineering rules (auto-loaded every session — token-bounded, keep dense) |
| `<repo>/.claude/CLAUDE.md` | Platform-specific rules (rivendell, gstack — loaded only in that repo) |
| Project `CLAUDE.md` | Project facts, conventions, gotchas for all Claude interactions in that codebase |
| Project `AGENTS.md` | Agent-specific workflows, tool usage patterns, automation rules |

### Periodic Promotion Sprint

Roughly monthly (or when `~/.claude/learnings/LEARNINGS.md` exceeds ~30 entries):

1. Read all per-project `.learnings/` + `~/.claude/learnings/`
2. Classify each entry: 🌍 generic / 🏛️ platform-meta / 🏠 project-specific / 🗑️ stale
3. Generic entries → distill into dense rules in `~/.claude/CLAUDE.md`, archive originals
4. Platform-meta → promote to `<platform-repo>/.claude/CLAUDE.md`
5. Save a classification report (e.g. `reports/learnings-promotion-sprint-YYYY-MM-DD.md`) for history

See `~/Documents/Projects/rivendell/reports/learnings-promotion-sprint-2026-05-13.md` for the seed-sprint template.

### How to Promote

1. **Distill** the learning into a concise rule or fact
2. **Add** to appropriate section in target file (create file if needed)
3. **Update** original entry:
   - Change `**Status**: pending` to `**Status**: promoted`
   - Add `**Promoted**: CLAUDE.md` or `AGENTS.md`

### Promotion Examples

**Learning** (verbose):
> Project uses pnpm workspaces. Attempted `npm install` but failed.
> Lock file is `pnpm-lock.yaml`. Must use `pnpm install`.

**In CLAUDE.md** (concise):
```markdown
## Build & Dependencies
- Package manager: pnpm (not npm) - use `pnpm install`
```

**Learning** (verbose):
> When modifying API endpoints, must regenerate TypeScript client.
> Forgetting this causes type mismatches at runtime.

**In AGENTS.md** (actionable):
```markdown
## After API Changes
1. Regenerate client: `pnpm run generate:api`
2. Check for type errors: `pnpm tsc --noEmit`
```

## Recurring Pattern Detection

If logging something similar to an existing entry:

1. **Search first**: `grep -r "keyword" .learnings/`
2. **Link entries**: Add `**See Also**: ERR-20250110-001` in Metadata
3. **Bump priority** if issue keeps recurring
4. **Consider systemic fix**: Recurring issues often indicate:
   - Missing documentation (promote to CLAUDE.md)
   - Missing automation (add to AGENTS.md)
   - Architectural problem (create tech debt ticket)

## Periodic Review

Review `.learnings/` at natural breakpoints:

### When to Review
- Before starting a new major task
- After completing a feature
- When working in an area with past learnings
- Weekly during active development

### Quick Status Check
```bash
# Count pending items
grep -h "Status\*\*: pending" .learnings/*.md | wc -l

# List pending high-priority items
grep -B5 "Priority\*\*: high" .learnings/*.md | grep "^## \["

# Find learnings for a specific area
grep -l "Area\*\*: backend" .learnings/*.md
```

### Review Actions
- Resolve fixed items
- Promote applicable learnings
- Link related entries
- Escalate recurring issues

## Detection Triggers

Automatically log when you notice:

**Corrections** (learning with `correction` category):
- "No, that's not right..."
- "Actually, it should be..."
- "You're wrong about..."
- "That's outdated..."

**Feature Requests** (feature request):
- "Can you also..."
- "I wish you could..."
- "Is there a way to..."
- "Why can't you..."

**Knowledge Gaps** (learning with `knowledge_gap` category):
- User provides information you didn't know
- Documentation you referenced is outdated
- API behavior differs from your understanding

**Errors** (error entry):
- Command returns non-zero exit code
- Exception or stack trace
- Unexpected output or behavior
- Timeout or connection failure

## Priority Guidelines

| Priority | When to Use |
|----------|-------------|
| `critical` | Blocks core functionality, data loss risk, security issue |
| `high` | Significant impact, affects common workflows, recurring issue |
| `medium` | Moderate impact, workaround exists |
| `low` | Minor inconvenience, edge case, nice-to-have |

## Area Tags

Use to filter learnings by codebase region:

| Area | Scope |
|------|-------|
| `frontend` | UI, components, client-side code |
| `backend` | API, services, server-side code |
| `infra` | CI/CD, deployment, Docker, cloud |
| `tests` | Test files, testing utilities, coverage |
| `docs` | Documentation, comments, READMEs |
| `config` | Configuration files, environment, settings |

## Best Practices

1. **Log immediately** - context is freshest right after the issue
2. **Be specific** - future agents need to understand quickly
3. **Include reproduction steps** - especially for errors
4. **Link related files** - makes fixes easier
5. **Suggest concrete fixes** - not just "investigate"
6. **Use consistent categories** - enables filtering
7. **Promote aggressively** - if in doubt, add to CLAUDE.md
8. **Review regularly** - stale learnings lose value

## Hook Integration

Enable automatic reminders through Claude Code hooks. This is **opt-in** - you must explicitly configure hooks.

### Quick Setup

Add to `.claude/settings.json` in your project:

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/skills/self-improving-agent/scripts/activator.sh"
      }]
    }]
  }
}
```

This injects a learning evaluation reminder after each prompt (~50-100 tokens overhead).

### Full Setup (With Error Detection)

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/skills/self-improving-agent/scripts/activator.sh"
      }]
    }],
    "PostToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/skills/self-improving-agent/scripts/error-detector.sh"
      }]
    }]
  }
}
```

### Available Hook Scripts

| Script | Hook Type | Purpose |
|--------|-----------|---------|
| `scripts/activator.sh` | UserPromptSubmit | Reminds to evaluate learnings after tasks |
| `scripts/error-detector.sh` | PostToolUse (Bash) | Triggers on command errors |

## Automatic Skill Extraction

When a learning is valuable enough to become a reusable skill, extract it.

### Skill Extraction Criteria

A learning qualifies for skill extraction when ANY of these apply:

| Criterion | Description |
|-----------|-------------|
| **Recurring** | Has `See Also` links to 2+ similar issues |
| **Verified** | Status is `resolved` with working fix |
| **Non-obvious** | Required actual debugging/investigation to discover |
| **Broadly applicable** | Not project-specific; useful across codebases |
| **User-flagged** | User says "save this as a skill" or similar |

### Extraction Workflow

1. **Identify candidate**: Learning meets extraction criteria
2. **Create skill**: Create `~/.claude/skills/<skill-name>/SKILL.md`
3. **Fill template**: Use YAML frontmatter (name, description, when_to_use, version, tags, languages) and write skill content
4. **Update learning**: Set status to `promoted_to_skill`, add `Skill-Path`
5. **Verify**: Read skill in fresh session to ensure it's self-contained

### Extraction Detection Triggers

Watch for these signals that a learning should become a skill:

**In conversation:**
- "Save this as a skill"
- "I keep running into this"
- "This would be useful for other projects"
- "Remember this pattern"

**In learning entries:**
- Multiple `See Also` links (recurring issue)
- High priority + resolved status
- Category: `best_practice` with broad applicability
- User feedback praising the solution

### Skill Quality Gates

Before extraction, verify:

- [ ] Solution is tested and working
- [ ] Description is clear without original context
- [ ] Code examples are self-contained
- [ ] No project-specific hardcoded values
- [ ] Follows skill naming conventions (lowercase, hyphens)

## Gitignore Options

**Keep learnings local** (per-developer):
```gitignore
.learnings/
```

**Track learnings in repo** (team-wide):
Don't add to .gitignore - learnings become shared knowledge.

**Hybrid** (track templates, ignore entries):
```gitignore
.learnings/*.md
!.learnings/.gitkeep
```

## Integration with Other Skills

This skill works with:
- skills/systematic-debugging - Log errors discovered during debugging
- skills/post-change-qa - Log issues found during QA
- skills/code-reviewer - Log patterns found during review
