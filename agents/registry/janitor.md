---
schema_version: 2
name: janitor
kind: script
project: rivendell
entry: bin/sk-reports-janitor
schedule:
  type: calendar
  value: "0:3:00"
log_dir: reports
---

Migrated from agents.conf (script worker).
