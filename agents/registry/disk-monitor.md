---
schema_version: 2
name: disk-monitor
kind: script
project: rivendell
entry: bin/sk-disk-monitor-cron
schedule:
  type: calendar
  value: "3:30"
log_dir: reports
---

Migrated from agents.conf (script worker).
