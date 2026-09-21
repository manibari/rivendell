---
schema_version: 2
name: doctor
kind: script
project: rivendell
entry: bin/sk-agent-doctor
schedule:
  type: calendar
  value: "7:00"
log_dir: reports
---

Migrated from agents.conf (script worker).
