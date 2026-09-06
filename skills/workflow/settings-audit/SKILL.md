---
name: settings-audit
loop: platform
pdca: check
description: >
  Audit and clean up .claude/settings.local.json — remove invalid permissions,
  fix JSON syntax, and validate format. Detects one-time Bash commands that
  got saved as permanent permissions and cleans them out.
  TRIGGER when: settings.local.json is malformed or skipped by Claude Code,
  user reports permission issues, or periodic maintenance.
  Also trigger when user says "清理 settings" / "permission 問題".
  DO NOT TRIGGER when: adding new permissions (use update-config skill),
  or debugging hook issues.
version: 1.0.0
tags: [workflow, maintenance, claude-code]
languages: [json, bash]
---

## Problem
Claude Code silently skips malformed `settings.local.json` — no error, just ignores it. Common causes:
- One-time Bash approvals saved as permanent permission entries (e.g. `Bash(git commit -m "fix: ...")`)
- Missing commas between array elements
- Mixed valid glob patterns with full bash commands

## Audit Steps

### 1. Validate JSON
```bash
python3 -c "import json; json.load(open('.claude/settings.local.json'))" 2>&1
```
If this fails, the file is broken and Claude Code is ignoring ALL permissions.

### 2. Identify Invalid Permissions
Valid patterns:
- `Bash(npm *)`, `Bash(npx *)` — glob patterns
- `Read(/path/**)` — path patterns
- `WebFetch(domain:example.com)` — domain patterns
- `mcp__server__tool` — MCP tool names

Invalid patterns (one-time commands that leaked in):
- `Bash(git commit -m "..."` — full commands with arguments
- `Bash(python3 -c "..."` — inline scripts
- `Bash(find /path -type f ...)` — full find commands
- Any permission entry > 80 characters is suspicious

### 3. Clean Up
Keep only reusable glob patterns. Remove one-time commands.

### 4. Fix JSON Syntax
- Ensure commas between array elements
- Validate with `python3 -m json.tool`

## Prevention
- Periodically run this audit (monthly)
- When approving a Bash command, consider if it needs to be permanent
- Prefer glob patterns (`Bash(npm *)`) over specific commands

## Quick Fix Script
```bash
python3 -c "
import json
with open('.claude/settings.local.json') as f:
    data = json.load(f)
perms = data.get('permissions', {}).get('allow', [])
clean = [p for p in perms if len(p) < 80 and not any(x in p for x in ['git commit', 'python3 -c', 'find /', 'for p in', 'echo \"'])]
data['permissions']['allow'] = clean
with open('.claude/settings.local.json', 'w') as f:
    json.dump(data, f, indent=2)
print(f'Cleaned: {len(perms)} → {len(clean)} permissions')
"
```
