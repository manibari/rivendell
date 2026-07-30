---
schema_version: 2
name: web
kind: service
project: rivendell
entry: dashboard-next/start-web.sh
schedule:
  type: keepalive
  value: "-"
log_dir: logs
label: com.sk.dashboard.web
---

Migrated from agents.conf (service worker).
