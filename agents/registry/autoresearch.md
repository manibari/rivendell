---
schema_version: 2
name: autoresearch
kind: script
enabled: false
project: sales-assistant
entry: sk-autoresearch-wrapper.sh
schedule:
  type: calendar
  value: "0:2:00"
log_dir: reports
label: com.sk.agent.sales.autoresearch
---

Autoresearch — 原 conf 註解停用，遷為 enabled:false。待啟用時翻 true。
