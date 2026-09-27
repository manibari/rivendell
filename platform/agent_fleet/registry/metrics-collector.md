---
schema_version: 2
name: metrics-collector
kind: service
project: rivendell
entry: bin/sk-metrics-collector
schedule:
  type: keepalive
  value: "-"
log_dir: logs
---

System monitor history: samples CPU (per core), GPU, temperatures, fans, power
and battery every 5 s into `system-metrics.db` (5 s kept 7 days, 1 m kept 90
days, 1 h kept forever). Read by `/api/health/metrics/history` and the
dashboard's 系統監控 page.

Also records the top 10 CPU-consuming processes per 5 s tick (`procs_5s`,
kept 14 days; CPU-time delta, command lines redacted), read by
`/api/health/processes?range=15m`. Use it to answer "who caused that spike".
