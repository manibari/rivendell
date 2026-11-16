---
schema_version: 2
name: gov-tender-scraper
kind: script
project: sales-assistant
entry: scripts/tender-scraper.sh
schedule:
  type: calendar
  value: "8:30"
log_dir: materials/tenders
label: com.sk.agent.sales.gov-tender-scraper
---

sales-assistant 已宣告退役，未來由 ChimesERP 接手（owner 2026-11-16；原本寫遷移 chimesflow）。保留 enabled:true 不打斷現跑 agent；ChimesERP 接手後再單獨 commit 改 enabled:false。
