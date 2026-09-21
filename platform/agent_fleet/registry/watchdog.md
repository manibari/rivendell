---
schema_version: 2
name: watchdog
kind: script
project: rivendell
entry: bin/sk-watchdog
schedule:
  type: interval
  value: "60"
log_dir: reports
label: com.sk.dashboard.watchdog
---

Migrated from agents.conf (script worker).
