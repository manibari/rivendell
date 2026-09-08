---
date: 2026-09-07
type: ssot-drift
total_drift: 11
status: drift-detected
---

# SSOT Drift Report — 2026-09-07

Daily check by `bin/sk-ssot-drift-cron` (03:00). Compares the agent registry
(`agents/registry/*.md`, the identity SSOT that generates agents.conf) with
`~/.claude/projects.json` (project metadata SSOT), plus registry validation.
See README "Agent SSOT vs project metadata" section.

## Registry Validation (0 FAIL)

```
validated 25 agent(s): 0 FAIL, 0 WARN
```

## Summary

```
[0;36m=== SSOT Drift Check ===[0m
agents.conf:   /var/folders/_7/b47kjvx506s_zl1r2wxjx6d40000gn/T/sk-agents-conf.XXXXXX.qvNBB2QYeK
projects.json: /Users/manibari/.claude/projects.json

[0;33magents.conf has, but projects.json lacks metadata:[0m
  rivendell / facts
  rivendell / mail-triage
  rivendell / token-analysis
  sales-assistant / gov-subsidy-scraper
  sales-assistant / gov-tender-scraper
  sales-assistant / sales-crm-projection
  sales-assistant / sales-material-health

[0;33mprojects.json claims agent, but agents.conf doesn't define it:[0m
  sales-assistant / crm-projection
  sales-assistant / material-health
  sales-assistant / subsidy-scraper
  sales-assistant / tender-scraper

[0;31mTotal drift: 11[0m
```

## Raw JSON

```json
{"total_drift":11,"agents_conf_only":[{"project":"rivendell","agent":"facts"},{"project":"rivendell","agent":"mail-triage"},{"project":"rivendell","agent":"token-analysis"},{"project":"sales-assistant","agent":"gov-subsidy-scraper"},{"project":"sales-assistant","agent":"gov-tender-scraper"},{"project":"sales-assistant","agent":"sales-crm-projection"},{"project":"sales-assistant","agent":"sales-material-health"}],"projects_json_only":[{"project":"sales-assistant","agent":"crm-projection"},{"project":"sales-assistant","agent":"material-health"},{"project":"sales-assistant","agent":"subsidy-scraper"},{"project":"sales-assistant","agent":"tender-scraper"}]}
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
