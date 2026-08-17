---
date: 2026-07-24
type: ssot-drift
total_drift: 1
status: drift-detected
---

# SSOT Drift Report — 2026-07-24

Daily check by `bin/sk-ssot-drift-cron` (03:00). Compares `agents/agents.conf`
(agent identity SSOT) with `~/.claude/projects.json` (project metadata SSOT).
See README "Agent SSOT vs project metadata" section.

## Summary

```
[0;36m=== SSOT Drift Check ===[0m
agents.conf:   /Users/manibari/code/rivendell/agents/agents.conf
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
