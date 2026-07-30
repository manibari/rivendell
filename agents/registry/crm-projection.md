---
schema_version: 2
name: crm-projection
kind: script
project: sales-assistant
entry: scripts/crm-projection.sh
schedule:
  type: calendar
  value: "7:00"
log_dir: materials/clients
label: com.sk.agent.sales.crm-projection
---

sales-assistant 已宣告退役（遷移 chimesflow）。純機械搬移保留 enabled:true 不打斷現跑 agent；待 chimesflow ready 再單獨 commit 改 enabled:false。
