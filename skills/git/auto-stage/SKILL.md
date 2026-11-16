---
name: auto-stage
loop: platform
pdca: do
description: >
  PostToolUse hook — auto git-stages files after Claude Edit/Write.
  Skips .env, node_modules. Catalog visibility only; no slash invocation.
tags: [git, hook, automation]
version: 1.0.0
source: harvest-hooks-research
user_invocable: false
---

# auto-stage

PostToolUse hook that runs after every Edit/Write tool call. Automatically stages the modified file so it's ready for commit.

## What It Does

- After Claude edits or creates a file → `git add <file>`
- Finds the correct git root for the file
- Silently skips files outside git repos

## What It Skips

| Pattern | Reason |
|---------|--------|
| `.env`, `.env.local` | Contains secrets |
| `node_modules/` | Dependencies |
| `__pycache__/`, `*.pyc` | Build artifacts |
| `.git/` | Git internals |
| `.DS_Store` | macOS metadata |

## Installation

This is a project hook, not a global hook. rivendell registers it in its own
`.claude/settings.json` (committed), so it runs only in rivendell sessions:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/skills/git/auto-stage/scripts/auto-stage-hook.sh"
          }
        ]
      }
    ]
  }
}
```

To use it in another repo, add the same block to that repo's `.claude/settings.json`
with the command `~/.claude/skills/auto-stage/scripts/auto-stage-hook.sh`. Do not add it
to `~/.claude/settings.json`: it would stage edits in every repo, including repos where
the user stages by hand.

## Notes

- Non-blocking: always exits 0, never interrupts Claude's workflow
- Works across multiple repos (finds git root per-file)
- Does NOT auto-commit — just stages for your review
