---
schema_version: 2
name: api
kind: service
project: rivendell
entry: dashboard-next/start-api.sh
schedule:
  type: keepalive
  value: "-"
log_dir: logs
label: com.sk.dashboard.api
---

Migrated from agents.conf (service worker).
