---
schema_version: 2
name: workflow-retro
kind: script
project: rivendell
entry: bin/sk-workflow-retro-cron
schedule:
  type: calendar
  value: "0:23:00"
log_dir: reports
---

Migrated from agents.conf (script worker).
