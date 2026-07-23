---
name: agent-observability
description: >
  Make any script-based agent visible in rivendell: execution history,
  live log streaming, and timeline events. Step-by-step guide for integrating
  exec-lib, progress logging, and dashboard log discovery.
  TRIGGER when: building a new scraper/script agent, user asks why agent
  has no execution history, dashboard shows "等待輸出" or empty timeline,
  or user says "看不到 agent 的執行狀況".
  DO NOT TRIGGER when: building Claude headless agents (use headless-agent),
  or working on dashboard UI itself (use frontend-design).
version: 1.0.0
tags: [workflow, dashboard, observability, agents]
languages: [bash, python]
---

## Overview

Non-Claude agents (Python scrapers, shell scripts) don't produce stream-json. This skill covers the 3 layers needed to make them visible in the dashboard.

## Layer 1: Execution History (exec-lib)

Shell wrapper pattern:

```bash
# At top of wrapper script
export SK_EXEC_REPO_DIR="$HOME/Documents/Projects/rivendell"
if [ -f "$SK_EXEC_REPO_DIR/bin/sk-exec-lib" ]; then
  source "$SK_EXEC_REPO_DIR/bin/sk-exec-lib"
fi

start_epoch=$(date +%s)

# ... run your agent ...
python3 scripts/my_agent.py && run_exit=0 || run_exit=$?

end_epoch=$(date +%s)

# Record to dashboard DB
if type _sk_exec_record_run &>/dev/null; then
  _sk_exec_record_run "project-name" "agent-name" \
    "$start_epoch" "$end_epoch" "$run_exit" "" "" "" "" "" ""
fi
exit "$run_exit"
```

Key rules:

- MUST use `export` before source (not inline `VAR=val source`)
- Guard with `if [ -f ]` so script works without rivendell
- Agent name should match the launchd label suffix

## Layer 2: Progress Logging (Python)

Use `[step N/M]` prefixes for dashboard progress indicator:

```python
logger.info("[step 1/5] Fetching data...")
logger.info("[step 2/5] (%d/%d) Processing %s", idx, total, item_name)
logger.error("[step 3/5] Failed: %s", error)
```

The dashboard `/timeline` endpoint converts Python logging format into events:

- `INFO` → log event
- `ERROR` → log_error event
- `WARNING` → log_warn event

Dated log files (`scraper-YYYY-MM-DD.log`) are matched to runs by timestamp.

## Layer 3: Dashboard Log Discovery

The dashboard finds logs via two methods:

1. `reports/{agent-name}-stdout.log` (default)
2. plist `StandardOutPath` (for non-standard log dirs)

If your agent logs to a custom directory (e.g. `materials/tenders/`), no code changes needed — the dashboard reads the path from the plist automatically.

For the `/files` endpoint to list your log files, name them with the agent name prefix or `scraper-` prefix.

## Checklist

| Step | What | Verify |
|------|------|--------|
| 1 | Shell wrapper with exec-lib | Run once → check DB: `SELECT * FROM agent_runs WHERE agent_name='...'` |
| 2 | Python `[step N/M]` logging | Run → check log file has step prefixes |
| 3 | Plist StandardOutPath correct | `plutil -p ~/Library/LaunchAgents/com.sk.agent.*.plist \| grep StandardOutPath` |
| 4 | Dashboard shows history | Visit /agents/{label} → 執行歷史 should have rows |
| 5 | Dashboard shows timeline | Click a run → should show log events, not "無時間線資料" |
| 6 | Live monitoring works | Click "立即執行" → should stream output in real-time |

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 執行歷史空白 | No exec-lib in wrapper | Add source + record_run |
| "等待輸出..." forever | Log path mismatch | Check plist StandardOutPath matches actual log |
| "無時間線資料" | No dated log file | Ensure `scraper-YYYY-MM-DD.log` or agent log exists |
| Timeline all same type (no colors) | Python not using logging module | Use `logging.error()` not `print("ERROR")` |
