---
schema_version: 2
name: harvest
kind: script
project: rivendell
entry: bin/sk-harvest-cron
schedule:
  type: interval
  value: "28800"
log_dir: reports
---

Migrated from agents.conf (script worker).
