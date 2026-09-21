---
schema_version: 2
name: token-snapshot
kind: script
project: rivendell
entry: bin/sk-token-snapshot
schedule:
  type: calendar
  value: "2:30"
log_dir: reports
---

Migrated from agents.conf (script worker).
