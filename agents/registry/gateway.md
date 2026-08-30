---
schema_version: 2
name: gateway
kind: service
project: rivendell
entry: gateway/start-gateway.sh
schedule:
  type: keepalive
  value: "-"
log_dir: logs
label: com.sk.gateway
---

Ported from origin/main agents.conf (2026-08 merge): personal-assistant
gateway service (keepalive).
