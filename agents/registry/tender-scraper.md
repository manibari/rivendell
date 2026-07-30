---
schema_version: 2
name: tender-scraper
kind: script
project: sales-assistant
entry: scripts/tender-scraper.sh
schedule:
  type: calendar
  value: "8:30"
log_dir: materials/tenders
label: com.sk.agent.sales.tender-scraper
---

sales-assistant 已宣告退役（遷移 chimesflow）。純機械搬移保留 enabled:true 不打斷現跑 agent；待 chimesflow ready 再單獨 commit 改 enabled:false。
