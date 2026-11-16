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

sales-assistant 已宣告退役，未來由 ChimesERP 接手（owner 2026-11-16；原本寫遷移 chimesflow）。保留 enabled:true 不打斷現跑 agent；ChimesERP 接手後再單獨 commit 改 enabled:false。
