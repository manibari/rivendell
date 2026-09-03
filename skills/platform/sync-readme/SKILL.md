---
name: sync-readme
loop: platform
pdca: do
description: >
  Keep README.md sections in sync with code structure across repos.
  TRIGGER when: a new skill/feature/route/command is added or renamed, and the README
  has a corresponding catalog or reference section that needs updating.
  Also triggers via hook automatically when SKILL.md files are modified in the skills library.
  DO NOT TRIGGER when: editing README prose/explanations, or changes that don't affect
  catalogued items (e.g. internal refactors, bug fixes in non-catalogued logic).
tags: [meta]
version: 1
user_invocable: true
trigger_label: 自動 + hook
---

# sync-readme

Keep README.md sections automatically in sync with the codebase.

## How It Works

### For This Skills Library (rivendell)

A PostToolUse hook detects edits to `skills/*/*/SKILL.md` and auto-runs
`scripts/generate-readme-catalog.py`, which:

1. Scans all `SKILL.md` frontmatter files
2. Preserves existing Chinese descriptions for known skills
3. Auto-generates descriptions for new skills from their `description` field
4. Detects trigger mode via `trigger_label` frontmatter or pattern matching
5. Replaces the `## Skills Catalog` section in `README.md` in-place

You can also run it manually: `./bin/sk readme`

### For Other Repos (Generic Protocol)

Mark README sections with HTML comment anchors:

```markdown
<!-- sync-readme:start:SECTION_NAME -->
... auto-managed content ...
<!-- sync-readme:end:SECTION_NAME -->
```

Common section types by project:

| Project Type | Tracked Files | README Section Name |
|---|---|---|
| FastAPI / Flask | `routes/*.py`, `api/*.py` | `api-reference` |
| Next.js | `app/**/page.tsx`, `pages/**` | `pages` |
| CLI tool | `commands/*.py`, `src/commands/` | `commands` |
| Skills library | `skills/*/*/SKILL.md` | `catalog` |
| Any project | `CHANGELOG.md` | `changelog` |

## When Claude Should Update

When you add or modify a tracked file, Claude will:
1. Identify which README section corresponds to the change
2. Find the `<!-- sync-readme:start:NAME -->` anchor
3. Regenerate the content between the anchors

## Adding sync-readme to a New Repo

**Step 1** — Add section anchors to README.md:

```markdown
## API Reference
<!-- sync-readme:start:api-reference -->
| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
<!-- sync-readme:end:api-reference -->
```

**Step 2** — Add PostToolUse hook to `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/skills/sync-readme/scripts/sync-readme-hook.sh"
      }]
    }]
  }
}
```

**Step 3** — Run `/sync-readme` once to do an initial sync.

## Frontmatter Fields (Skills Library)

Add to `SKILL.md` for precise control:

| Field | Purpose | Example |
|---|---|---|
| `trigger_label` | Override auto-detected trigger mode | `自動 + hook` |
| `summary` | Override auto-generated short description | `短描述文字` |

## Manual Trigger

```bash
# Regenerate rivendell catalog
./bin/sk readme

# Or via Claude
/sync-readme
```
