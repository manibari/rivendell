---
schema_version: 2
name: token-analysis
kind: script
project: rivendell
entry: bin/sk-token-analysis-cron
schedule:
  type: calendar
  value: "23:45"
log_dir: reports
---

Migrated from agents.conf (script worker).
