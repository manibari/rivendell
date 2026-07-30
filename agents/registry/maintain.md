---
schema_version: 2
name: maintain
kind: script
project: rivendell
entry: bin/sk-maintain-cron
schedule:
  type: calendar
  value: "22:00"
log_dir: reports
---

Migrated from agents.conf (script worker).
