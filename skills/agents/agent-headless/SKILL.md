---
name: Headless Agent
loop: platform
pdca: do
description: Pattern for running Claude Code as an automated, non-interactive agent with scheduling, structured logging, and output management.
when_to_use: when setting up Claude Code to run unattended — scheduled tasks, automated research, periodic code maintenance, or any headless/batch workflow
version: 1.0.0
tags: [automation, scheduling, infrastructure]
languages: [bash, python]
user_invocable: true
---

# Headless Agent

## Overview

Run Claude Code as a headless agent — no human in the loop. The agent receives a prompt, executes autonomously, and writes structured output.

**Use cases:**
- Scheduled research/analysis (e.g. daily investment reports)
- Automated code maintenance (e.g. dependency updates, lint fixes)
- Periodic data processing and ETL
- Automated monitoring and alerts

**Core components:**
1. Runner script (bash) — invokes Claude with the right flags
2. Log parser (python) — converts stream-json to structured JSONL
3. Scheduler (launchd/cron/systemd) — triggers runs on schedule

## Runner Script Template

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/path/to/project"
REPORTS_DIR="$PROJECT_DIR/reports"
TODAY="$(date '+%Y-%m-%d')"
LOG_FILE="$REPORTS_DIR/agent-${TODAY}.log"

mkdir -p "$REPORTS_DIR"

PROMPT="Your task prompt here..."

echo "=== Agent Run — $TODAY ===" | tee "$LOG_FILE"
echo "Start: $(date)" | tee -a "$LOG_FILE"

cd "$PROJECT_DIR"

claude -p \
  --dangerously-skip-permissions \
  --output-format stream-json \
  --max-turns 30 \
  "$PROMPT" \
  2>>"$REPORTS_DIR/agent-stderr.log" \
  | python3 /path/to/parse-agent-log.py \
      --output "$REPORTS_DIR/agent-${TODAY}.structured.jsonl" \
  | tee -a "$LOG_FILE"

echo "End: $(date)" | tee -a "$LOG_FILE"
```

### Key Flags

| Flag | Purpose |
|------|---------|
| `-p` / `--print` | Non-interactive mode: pass prompt as argument, no REPL |
| `--dangerously-skip-permissions` | Skip all permission prompts (required for headless) |
| `--output-format stream-json` | Structured JSON output for machine parsing |
| `--max-turns N` | Limit agent iterations to prevent runaway execution |
| `--model MODEL` | Optionally specify model (default: your configured model) |
| `--verbose` | Include debug info in stderr |
| `--allowedTools "..."` | Restrict which tools the agent can use (safer alternative to full skip-permissions) |
| `--permission-mode auto` | Auto-approve tools in allowedTools list only (alternative to --dangerously-skip-permissions) |

**Permission strategy choice:**
- `--dangerously-skip-permissions` — approves everything, simplest for trusted prompts
- `--allowedTools + --permission-mode auto` — whitelist specific tools, safer for broader prompts

**Output plumbing:**
- stdout carries stream-json, piped through parser
- stderr is redirected to a separate file for error diagnosis
- Parser emits plain text to stdout (for tee/log) and structured JSONL to --output file

## Log Parser

The log parser (`parse-agent-log.py`) reads Claude's `stream-json` output from stdin and produces:

**To stdout** — plain text (assistant text blocks) for human-readable logs
**To --output file** — structured JSONL with event types:

| Event type | Content |
|-----------|---------|
| `thinking` | Extended thinking block (preview + character length) |
| `tool` | Tool call (name + input) |
| `text` | Assistant text block |
| `result` | Token usage summary with cost estimate |

Each event includes a timestamp (`ts` field).

The parser from `scripts/parse-agent-log.py` (in the rivendell repo) can be used directly or copied into your project.

## macOS Scheduling (launchd)

### Plist Template

Save to `~/Library/LaunchAgents/com.user.agent-name.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.user.agent-name</string>
  <key>ProgramArguments</key>
  <array>
    <string>/path/to/runner.sh</string>
    <string>daily</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>7</integer>
    <key>Minute</key><integer>30</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>/path/to/logs/launchd-stdout.log</string>
  <key>StandardErrorPath</key>
  <string>/path/to/logs/launchd-stderr.log</string>
  <key>WorkingDirectory</key>
  <string>/path/to/project</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    <key>HOME</key>
    <string>/Users/username</string>
  </dict>
</dict>
</plist>
```

### Management Commands

```bash
# Load (enable)
launchctl load ~/Library/LaunchAgents/com.user.agent-name.plist

# Unload (disable)
launchctl unload ~/Library/LaunchAgents/com.user.agent-name.plist

# Check status
launchctl list | grep agent-name

# Run immediately (for testing)
launchctl start com.user.agent-name
```

### launchd Gotchas

- **PATH must be set explicitly.** launchd provides a minimal PATH (`/usr/bin:/bin:/usr/sbin:/sbin`). Claude Code, Homebrew tools, and python3 will not be found without setting PATH.
- **HOME must be set.** Claude Code reads config from `~/.claude/`, which requires HOME to resolve correctly.
- **WorkingDirectory** sets cwd for the script — use this instead of `cd` in the plist.
- **StartCalendarInterval** for cron-like scheduling (specific times). **StartInterval** for fixed-interval in seconds.
- **Weekday** key: 0 = Sunday, 1 = Monday, ..., 6 = Saturday. Use an array of dicts for multiple days.

## Linux Scheduling (cron / systemd)

### cron

```bash
# Edit crontab
crontab -e

# Run daily at 07:30
30 7 * * * /path/to/runner.sh daily >> /path/to/logs/cron.log 2>&1

# Run weekly on Sunday at 10:00
0 10 * * 0 /path/to/runner.sh weekly >> /path/to/logs/cron.log 2>&1
```

Ensure PATH is set at the top of crontab:
```
PATH=/usr/local/bin:/usr/bin:/bin:/home/user/.local/bin
```

### systemd Timer

Service file (`~/.config/systemd/user/agent.service`):
```ini
[Unit]
Description=Headless Claude Agent

[Service]
Type=oneshot
ExecStart=/path/to/runner.sh daily
WorkingDirectory=/path/to/project
Environment=PATH=/usr/local/bin:/usr/bin:/bin
```

Timer file (`~/.config/systemd/user/agent.timer`):
```ini
[Unit]
Description=Run agent daily

[Timer]
OnCalendar=*-*-* 07:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl --user enable --now agent.timer
systemctl --user status agent.timer
journalctl --user -u agent.service
```

## Output Management

### File Organization

```
reports/
  agent-2026-03-11.log              # Human-readable execution log
  agent-2026-03-11.structured.jsonl  # Machine-parseable events
  agent-stderr.log                   # Claude stderr (errors, debug)
  daily-2026-03-11.md                # Agent-generated report
  state.json                         # Persistent state across runs
```

### Strategies

- **Log rotation**: date-stamped files (`agent-YYYY-MM-DD.log`) — no rotation config needed
- **Structured JSONL**: for cost tracking, tool usage analysis, performance monitoring
- **Plain text log**: for quick human review via `tail -f`
- **stderr separation**: isolate Claude internal errors from agent output
- **Persistent state**: JSON file read at start, updated at end — carries context between runs

## Multi-Mode Pattern

Support different run modes via script arguments:

```bash
MODE="${1:-daily}"

case "$MODE" in
  daily)
    PROMPT="Quick health check. Read state.json, check conditions, write brief report."
    MAX_TURNS=20
    ;;
  weekly)
    PROMPT="Full weekly analysis. Deep research, compare alternatives, write detailed report."
    MAX_TURNS=50
    ;;
  full)
    PROMPT="Complete pipeline from scratch. Initialize state, run all steps, produce full output."
    MAX_TURNS=80
    ;;
  *)
    echo "Usage: $0 [daily|weekly|full]"
    exit 1
    ;;
esac

claude -p \
  --dangerously-skip-permissions \
  --output-format stream-json \
  --max-turns "$MAX_TURNS" \
  "$PROMPT" \
  2>>"$REPORTS_DIR/agent-stderr.log" \
  | python3 "$PARSER" --output "$STRUCTURED_LOG" \
  | tee -a "$LOG_FILE"
```

Adjust `--max-turns` per mode — daily checks need fewer turns than full research runs.

## Best Practices

1. **Always set `--max-turns`.** Without it, a confused agent can loop indefinitely, burning tokens.
2. **Use `--dangerously-skip-permissions` only for trusted prompts on your own machine.** For shared environments, use `--allowedTools` to whitelist specific tools.
3. **Keep prompts in the script** (not separate files) for auditability — you can see exactly what the agent was told in `git log`.
4. **Set explicit PATH** in launchd/cron. This is the most common cause of "works manually, fails when scheduled."
5. **Monitor stderr** for unexpected errors — agent output on stdout may look normal while stderr contains critical failures.
6. **Use structured JSONL** to track cost over time. Token usage accumulates fast with daily runs.
7. **Test manually before scheduling.** Run the script by hand, verify output, then add the schedule.
8. **Pre-run data collection** can run before Claude starts (e.g. refresh a database, pull latest data). Put these steps in the runner script before the `claude` invocation.

## Security Considerations

- **`--dangerously-skip-permissions` means the agent can run ANY command** — shell commands, file writes, network requests, all without confirmation.
- Only run on machines you control, with prompts you wrote.
- Consider restricting capabilities in the prompt itself (e.g. "Do not modify any code, only write reports").
- Use `--allowedTools` when possible to limit the blast radius.
- Monitor logs regularly for unexpected tool usage.
- Do not commit runner scripts with sensitive prompts to public repositories.
- Do not expose the runner script or its output directory to untrusted users.

## Agent Git Operations

`sk_exec` supports automatic git operations after a successful agent run via environment variables:

### Auto-commit (reports, data)

```bash
SK_EXEC_AUTO_COMMIT=1              # Enable auto-commit after successful run
SK_EXEC_AUTO_PUSH=1                # Push after commit
SK_EXEC_COMMIT_SCOPE="reports/*.md reports/*.html data/*.jsonl"  # Glob patterns to stage
SK_EXEC_GIT_SIGNOFF="agent-name"   # Signature in commit message
```

Only files matching `SK_EXEC_COMMIT_SCOPE` are staged. Commit only happens if the agent exits 0.

### Path filtering (safety)

```bash
SK_EXEC_ALLOWED_PATHS="src/**:config/**"     # Colon-separated globs (empty = all)
SK_EXEC_FORBIDDEN_PATHS=".env*:*.db:.claude/**"  # Always blocked
SK_EXEC_MAX_FILES=5                          # Max files per commit (0 = unlimited)
```

### QA gate

```bash
SK_EXEC_QA_CHECK=off     # "off" (default), "auto" (detect pytest/vitest/swift), or script path
```

When `auto`, detects pytest/vitest/swift test and runs before committing. Failure → unstage + skip commit.

### Branch workflow (for code changes)

```bash
SK_EXEC_MERGE_STRATEGY=pr          # "auto" = commit to main, "pr" = branch + PR
SK_EXEC_BRANCH_PREFIX="agent/"     # Branch name prefix
SK_EXEC_CREATE_PR=1                # Create PR via gh after push
```

Branch workflow: creates `agent/{name}/{date}-{sha}` branch → commit → push → PR.

### agents.json schema

Define git and QA config per-agent in `.claude/agents.json`:

```json
{
  "agents": {
    "maintainer": {
      "type": "claude-dev",
      "script": "scripts/maintainer.sh",
      "schedule": { "type": "daily", "hour": 4, "minute": 0 },
      "git": {
        "merge_strategy": "auto",
        "allowed_paths": ["src/**", "config/**"],
        "forbidden_paths": [".env*", "*.db"],
        "max_files_changed": 5
      },
      "qa": { "pre_commit": "auto" }
    }
  }
}
```

### Multi-role agents

| Role | Scope | Merge strategy | Human review |
|------|-------|---------------|-------------|
| **maintainer** | stability, efficiency | `auto` → main | No |
| **tester** | tests, coverage reports | `auto` → main | No |
| **developer** | features, UI/UX | `pr` → branch + PR | Yes |

### Manual commands

```bash
sk agent run research-agent --project news_stock         # Run immediately
sk agent run research-agent --project news_stock weekly   # Specify mode
sk agent commit research-agent --project news_stock       # Commit accumulated output
```

## Integration with Other Skills

This skill provides the infrastructure layer. Combine with domain-specific skills for the agent's actual task:
- **autoresearch** skill for autonomous iteration loops (modify → verify → keep/discard)
- Investment research skill for financial analysis agents
- Systematic debugging skill for automated bug triage agents
- Any custom skill that defines the agent's domain knowledge and workflow

When building a new headless agent, always ask: **does this task have a measurable metric?** If yes, consider wrapping it in an autoresearch loop (`sk-autoresearch`) instead of a one-shot runner. The autoresearch pattern turns any agent from "run once and report" into "iterate until optimal."

## Dashboard Integration

### exec-lib for Run Recording

To record execution history to the dashboard DB, source `sk-exec-lib` from rivendell and call `_sk_exec_record_run` at the end of your runner script.

```bash
# Must export BEFORE sourcing — not inline
export SK_EXEC_REPO_DIR="$HOME/Documents/Projects/rivendell"

# Guard so the script still works without rivendell installed
if [ -f "$SK_EXEC_REPO_DIR/bin/sk-exec-lib" ]; then
  source "$SK_EXEC_REPO_DIR/bin/sk-exec-lib"
fi

# After the agent run completes:
_sk_exec_record_run "project" "agent-name" "$start_epoch" "$end_epoch" "$run_exit" ...
```

Key points:
- `SK_EXEC_REPO_DIR` **must be exported** before the `source` line — an inline `VAR=x source ...` does not propagate to the library's functions.
- The `if [ -f ... ]` guard ensures the script degrades gracefully on machines where rivendell is not checked out.
- Call `_sk_exec_record_run` with positional args: project name, agent name, start/end epoch timestamps, exit code, and any extra metadata fields.

### Dashboard Log Discovery

The dashboard API reads the `StandardOutPath` value from each agent's launchd plist to locate log files. If your agent writes logs to a non-standard directory (somewhere other than `reports/`), no code changes are needed — the dashboard resolves the path from the plist automatically. Just ensure your plist's `StandardOutPath` points to the correct log file.

### Live Monitoring

The `/live` endpoint polls the agent's stdout log for real-time output. For non-Claude agents (Python scripts, etc.), plain text logging works out of the box.

Tips for better visibility:
- Use `[step N/M]` progress prefixes in your log lines — the dashboard renders these as a progress indicator.
- The `/timeline` endpoint auto-converts Python logging format (`YYYY-MM-DD HH:MM:SS LEVEL message`) into timeline events, so standard `logging.info(...)` output works without any adapter.

## Portability

Hardcoded paths in launchd plists break when moving to a new machine. For managing multiple agents portably, see the **Portable Multi-Agent Fleet Pattern** in the `agent-launchd` skill, which provides:
- Declarative `agents.conf` — all agents in one file
- Auto-detect PATH (conda, homebrew, npm)
- Compiled C launcher with FDA for `~/Documents/` access
- One-command bootstrap: `./bin/sk-setup-agents`
