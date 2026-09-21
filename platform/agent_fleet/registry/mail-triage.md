---
schema_version: 2
name: mail-triage
kind: script
project: rivendell
entry: bin/sk-mail-triage-cron
schedule:
  type: calendar
  value: "7:45"
log_dir: reports
---

Ported from origin/main agents.conf (2026-08 merge): morning mail triage.
