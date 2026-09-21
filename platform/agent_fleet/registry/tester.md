---
schema_version: 2
name: tester
kind: script
project: rivendell
entry: bin/sk-tester-cron
schedule:
  type: calendar
  value: "6:00"
log_dir: reports
---

Migrated from agents.conf (script worker).
