---
schema_version: 2
name: research-agent
kind: script
project: news_stock
entry: scripts/research-agent.sh
extra_args: daily
schedule:
  type: calendar
  value: "7:30"
log_dir: reports
---

Migrated from agents.conf (script worker).
