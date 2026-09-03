---
name: audit-fix
loop: platform
pdca: check
description: >
  Analyze `sk audit` reports and fix project permission issues automatically.
  TRIGGER when: an audit report exists with project issues (one-off commands,
  colon-style patterns, missing configs), or user asks to clean up project permissions.
  DO NOT TRIGGER when: no audit report exists, or all projects already pass audit.
tags: [meta]
version: 1
source: manual
user_invocable: false
---

# audit-fix

Analyze `./bin/sk audit` reports and automatically fix project permission issues across all managed projects.

## Instructions

When invoked, follow this five-phase flow:

### Phase 1: Audit

1. Run `./bin/sk audit` (or read the latest report in `reports/skill-audit-*.md`)
2. Extract all **project issues** — categorized as:
   - `one-off`: Hardcoded path commands (`git -C /Users/...`, `find /Users/...`, `sed -n '...'`)
   - `colon-style`: Old format patterns (`Bash(cmd:*)` instead of `Bash(cmd *)`)
   - `commit-msg`: Full commit message commands (`git commit -m "$(cat..."`)
   - `global-dup`: Entries already covered by `~/.claude/settings.json` global baseline
   - `missing-config`: Project lacks `.claude/CLAUDE.md` or `.claude/settings.local.json`
   - `git-dirty`: Uncommitted changes (info only, no action)
3. Also note any **git status** warnings (dirty files, unpushed commits) — report but do NOT act on these

### Phase 2: Classify

For each project's `.claude/settings.local.json`, classify every entry:

| Category | Action | Examples |
|----------|--------|---------|
| **one-off** | DELETE | `Bash(git -C /full/path commit -m "...")`, `Bash(find /Users/... -name ...)` |
| **colon-style** | FIX → space-style | `Bash(git add:*)` → `Bash(git add *)` |
| **commit-msg** | DELETE | `Bash(git commit -m "$(cat <<'EOF'...")` with embedded message |
| **global-dup** | DELETE | `Bash(ls:*)`, `Bash(grep:*)`, `Bash(git push)` if global has `Bash(git *)` |
| **project-tool** | KEEP | `Bash(pnpm --filter @pkg/name *)` only if not covered by global `Bash(pnpm *)` |
| **webfetch-work** | KEEP | `WebFetch(domain:...)` relevant to the project's domain (finance, marketing, etc.) |
| **webfetch-noise** | DELETE | Game wikis, academic guides, one-off research domains |
| **hooks** | KEEP | Any `hooks` configuration key — never modify |
| **mcp** | KEEP | Any MCP-related permissions |

### Phase 3: Plan

For each project, generate a change plan:

```
Project: ~/Documents/Projects/<name>
  DELETE (N entries):
    - Bash(git -C /Users/.../project commit -m "...")  [one-off]
    - Bash(ls:*)  [global-dup]
    - WebFetch(domain:eu4cheats.com)  [webfetch-noise]
  FIX (M entries):
    - Bash(git add:*) → Bash(git add *)  [colon-style]
  KEEP (K entries):
    - WebFetch(domain:ai.google.dev)  [webfetch-work]
    - hooks: {...}  [hooks]
```

Present the plan to the user before executing. If `missing-config` issues exist, plan to create minimal configs.

### Phase 4: Execute

For each project:

1. Read the current `.claude/settings.local.json`
2. Apply deletions and fixes per the plan
3. Write the cleaned file
4. Validate JSON: `python3 -c "import json; json.load(open('<path>'))"` — if invalid, fix immediately
5. For `missing-config` projects:
   - Create `.claude/CLAUDE.md` with project name and detected tech stack
   - Run `./bin/sk permissions <project-path>` to generate `settings.local.json`

**Safety rules:**
- NEVER modify `~/.claude/settings.json` (global baseline)
- NEVER run git commands in other projects (no commit, push, checkout)
- NEVER delete `.claude/settings.local.json` files — write empty permissions instead
- NEVER modify `hooks` configuration in any settings file
- NEVER modify MCP server configurations
- Always preserve the `deny` array (even if empty)

### Phase 5: Verify

1. For each modified file, validate JSON syntax:
   ```bash
   python3 -c "import json; json.load(open('<path>'))"
   ```
2. Re-run `./bin/sk audit` and confirm:
   - Project issues count decreased (ideally to 0, or only `git-dirty` info items remain)
   - No new issues introduced
3. Report final summary:
   ```
   Audit Fix Summary
   ─────────────────
   Projects cleaned: 5
   Entries removed:  142
   Entries fixed:    23
   Entries kept:     8

   Remaining issues: 3 (all git-dirty, info only)
   ```
