---
schema_version: 2
name: sales-material-health
kind: script
project: sales-assistant
entry: scripts/material-health.sh
schedule:
  type: calendar
  value: "0:9:00"
log_dir: materials
label: com.sk.agent.sales.sales-material-health
---

sales-assistant 已宣告退役，未來由 ChimesERP 接手（owner 2026-11-16；原本寫遷移 chimesflow）。保留 enabled:true 不打斷現跑 agent；ChimesERP 接手後再單獨 commit 改 enabled:false。
