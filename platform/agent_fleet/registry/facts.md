---
schema_version: 2
name: facts
kind: script
project: rivendell
entry: bin/sk-facts-cron
schedule:
  type: calendar
  value: "21:30"
log_dir: reports
---

Ported from origin/main agents.conf (2026-08 merge): daily durable-facts
extraction into the knowledge-graph (`scripts/kg.py`).
