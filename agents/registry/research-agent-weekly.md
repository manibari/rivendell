---
schema_version: 2
name: research-agent-weekly
kind: script
project: news_stock
entry: scripts/research-agent.sh
extra_args: weekly
schedule:
  type: calendar
  value: "0:10:00"
log_dir: reports
---

Migrated from agents.conf (script worker).
