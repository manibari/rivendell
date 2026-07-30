---
schema_version: 2
name: material-health
kind: script
project: sales-assistant
entry: scripts/material-health.sh
schedule:
  type: calendar
  value: "0:9:00"
log_dir: materials
label: com.sk.agent.sales.material-health
---

sales-assistant 已宣告退役（遷移 chimesflow）。純機械搬移保留 enabled:true 不打斷現跑 agent；待 chimesflow ready 再單獨 commit 改 enabled:false。
