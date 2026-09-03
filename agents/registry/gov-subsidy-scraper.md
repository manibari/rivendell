---
schema_version: 2
name: gov-subsidy-scraper
kind: script
project: sales-assistant
entry: scripts/subsidy-scraper.sh
schedule:
  type: calendar_multi
  value: "1:8:00,4:8:00"
log_dir: materials/subsidies
label: com.sk.agent.sales.gov-subsidy-scraper
---

sales-assistant 已宣告退役（遷移 chimesflow）。純機械搬移保留 enabled:true 不打斷現跑 agent；待 chimesflow ready 再單獨 commit 改 enabled:false。
