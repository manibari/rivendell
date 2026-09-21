---
schema_version: 2
name: ssot-drift
kind: script
project: rivendell
entry: bin/sk-ssot-drift-cron
schedule:
  type: calendar
  value: "3:00"
log_dir: reports
---

Migrated from agents.conf (script worker).
