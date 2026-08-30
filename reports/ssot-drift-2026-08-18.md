---
date: 2026-08-18
type: ssot-drift
total_drift: 16
status: drift-detected
---

# SSOT Drift Report — 2026-08-18

Daily check by `bin/sk-ssot-drift-cron` (03:00). Compares `agents/agents.conf`
(agent identity SSOT) with `~/.claude/projects.json` (project metadata SSOT).
See README "Agent SSOT vs project metadata" section.

## Summary

```
[0;36m=== SSOT Drift Check ===[0m
agents.conf:   /home/manibari/projects/rivendell/agents/agents.conf
projects.json: /home/manibari/.claude/projects.json

[0;33magents.conf has, but projects.json lacks metadata:[0m
  news_stock / research-agent
  news_stock / research-agent-weekly
  rivendell / disk-monitor
  rivendell / doctor
  rivendell / harvest
  rivendell / janitor
  rivendell / maintain
  rivendell / ssot-drift
  rivendell / symlink-fix
  rivendell / tester
  rivendell / token-snapshot
  rivendell / workflow-retro
  sales-assistant / crm-projection
  sales-assistant / material-health
  sales-assistant / subsidy-scraper
  sales-assistant / tender-scraper

[0;31mTotal drift: 16[0m
```

## Raw JSON

```json
{"total_drift":16,"agents_conf_only":[{"project":"news_stock","agent":"research-agent"},{"project":"news_stock","agent":"research-agent-weekly"},{"project":"rivendell","agent":"disk-monitor"},{"project":"rivendell","agent":"doctor"},{"project":"rivendell","agent":"harvest"},{"project":"rivendell","agent":"janitor"},{"project":"rivendell","agent":"maintain"},{"project":"rivendell","agent":"ssot-drift"},{"project":"rivendell","agent":"symlink-fix"},{"project":"rivendell","agent":"tester"},{"project":"rivendell","agent":"token-snapshot"},{"project":"rivendell","agent":"workflow-retro"},{"project":"sales-assistant","agent":"crm-projection"},{"project":"sales-assistant","agent":"material-health"},{"project":"sales-assistant","agent":"subsidy-scraper"},{"project":"sales-assistant","agent":"tender-scraper"}],"projects_json_only":[]}
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
