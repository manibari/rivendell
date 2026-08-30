---
date: 2026-08-04
type: ssot-drift
total_drift: 1
status: drift-detected
---

# SSOT Drift Report — 2026-08-04

Daily check by `bin/sk-ssot-drift-cron` (03:00). Compares the agent registry
(`agents/registry/*.md`, the identity SSOT that generates agents.conf) with
`~/.claude/projects.json` (project metadata SSOT), plus registry validation.
See README "Agent SSOT vs project metadata" section.

## Registry Validation (0 FAIL)

```
validated 22 agent(s): 0 FAIL, 0 WARN
```

## Summary

```
[0;36m=== SSOT Drift Check ===[0m
agents.conf:   /var/folders/_7/b47kjvx506s_zl1r2wxjx6d40000gn/T/sk-agents-conf.XXXXXX.l8qGomIwwG
projects.json: /Users/manibari/.claude/projects.json

[0;33magents.conf has, but projects.json lacks metadata:[0m
  rivendell / token-analysis

[0;31mTotal drift: 1[0m
```

## Raw JSON

```json
{"total_drift":1,"agents_conf_only":[{"project":"rivendell","agent":"token-analysis"}],"projects_json_only":[]}
```

## How to fix

- **agents.conf has, projects.json lacks**: agent exists but project metadata
  is incomplete. Add the agent to `projects.json`'s `agents` array, or
  remove it from `agents.conf` if obsolete.
- **projects.json claims, agents.conf doesn't**: project metadata references
  an agent that no-longer runs. Remove from `projects.json` or add a matching
  row to `agents.conf`.

## Next reports

Re-runs daily at 03:00. To suppress until next-run, fix the underlying drift
or hide this report (will be regenerated tomorrow if drift persists).
