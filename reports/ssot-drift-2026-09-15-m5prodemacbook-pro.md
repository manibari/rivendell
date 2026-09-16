---
date: 2026-09-15
type: ssot-drift
total_drift: 9
status: drift-detected
---

# SSOT Drift Report — 2026-09-15

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
agents.conf:   /var/folders/sy/yh0krb_s3h73twxlk2zjv5080000gn/T/sk-agents-conf.XXXXXX.XABVjCKPWr
projects.json: /Users/m5pro/.claude/projects.json

[0;33magents.conf has, but projects.json lacks metadata:[0m
  news_stock / research-agent
  news_stock / research-agent-weekly
  rivendell / facts
  rivendell / mail-triage
  rivendell / token-analysis
  sales-assistant / gov-subsidy-scraper
  sales-assistant / gov-tender-scraper
  sales-assistant / sales-crm-projection
  sales-assistant / sales-material-health

[0;31mTotal drift: 9[0m
```

## Raw JSON

```json
{"total_drift":9,"agents_conf_only":[{"project":"news_stock","agent":"research-agent"},{"project":"news_stock","agent":"research-agent-weekly"},{"project":"rivendell","agent":"facts"},{"project":"rivendell","agent":"mail-triage"},{"project":"rivendell","agent":"token-analysis"},{"project":"sales-assistant","agent":"gov-subsidy-scraper"},{"project":"sales-assistant","agent":"gov-tender-scraper"},{"project":"sales-assistant","agent":"sales-crm-projection"},{"project":"sales-assistant","agent":"sales-material-health"}],"projects_json_only":[]}
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
