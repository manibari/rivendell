---
date: 2026-08-30
type: ssot-drift
total_drift: 12
status: drift-detected
---

# SSOT Drift Report — 2026-08-30

Daily check by `bin/sk-ssot-drift-cron` (03:00). Compares `agents/agents.conf`
(agent identity SSOT) with `~/.claude/projects.json` (project metadata SSOT).
See README "Agent SSOT vs project metadata" section.

## Summary

```
[0;36m=== SSOT Drift Check ===[0m
agents.conf:   /home/manibari/projects/rivendell/agents/agents.conf
projects.json: /home/manibari/.claude/projects.json

[0;33magents.conf has, but projects.json lacks metadata:[0m
  rivendell / disk-monitor
  rivendell / doctor
  rivendell / facts
  rivendell / harvest
  rivendell / janitor
  rivendell / mail-triage
  rivendell / maintain
  rivendell / ssot-drift
  rivendell / symlink-fix
  rivendell / tester
  rivendell / token-snapshot
  rivendell / workflow-retro

[0;31mTotal drift: 12[0m
```

## Raw JSON

```json
{"total_drift":12,"agents_conf_only":[{"project":"rivendell","agent":"disk-monitor"},{"project":"rivendell","agent":"doctor"},{"project":"rivendell","agent":"facts"},{"project":"rivendell","agent":"harvest"},{"project":"rivendell","agent":"janitor"},{"project":"rivendell","agent":"mail-triage"},{"project":"rivendell","agent":"maintain"},{"project":"rivendell","agent":"ssot-drift"},{"project":"rivendell","agent":"symlink-fix"},{"project":"rivendell","agent":"tester"},{"project":"rivendell","agent":"token-snapshot"},{"project":"rivendell","agent":"workflow-retro"}],"projects_json_only":[]}
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
