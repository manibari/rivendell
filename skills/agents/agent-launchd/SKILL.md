---
name: LaunchD Agent
description: >
  Create / debug / manage macOS launchd LaunchAgents — plist generation, scheduling,
  launchctl lifecycle, troubleshooting, portable multi-agent fleet.
  TRIGGER: scheduled task on macOS, plist/launchctl/LaunchAgent, "排程", "定時執行", "引繼".
  SKIP: Linux (cron/systemd); CI pipelines (ci-pipeline); cloud deploy (deploy).
version: 2.0.0
tags: [workflow, macos, launchd, scheduling, automation, portability]
languages: [bash, python, c]
---

# LaunchD Agent Management

Guide for creating and managing macOS LaunchAgents — the macOS equivalent of cron jobs, but with richer scheduling, logging, and lifecycle control.

## Quick Reference

| Task | Command |
|------|---------|
| Load agent | `launchctl load ~/Library/LaunchAgents/<label>.plist` |
| Unload agent | `launchctl unload ~/Library/LaunchAgents/<label>.plist` |
| Run immediately | `launchctl start <label>` |
| Check status | `launchctl list <label>` |
| See all agents | `launchctl list \| grep <prefix>` |

## Plist Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.example.my-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/script.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/path/to/working/dir</string>
    <key>StandardOutPath</key>
    <string>/path/to/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

## Scheduling Patterns

### Single schedule (daily at 9:00)
```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
</dict>
```

### Multiple schedules (9:00 and 18:00)
Use an **array** of dicts — this is a common gotcha:
```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key><integer>9</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key><integer>18</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
</array>
```

### Weekly (every Monday at 9:00)
Weekday: 0=Sunday, 1=Monday, ..., 6=Saturday
```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
</dict>
```

### Interval-based (every 5 minutes)
```xml
<key>StartInterval</key>
<integer>300</integer>
```

### Run at load
Add `RunAtLoad` to also run when the agent is first loaded:
```xml
<key>RunAtLoad</key>
<true/>
```

## Available Calendar Keys

| Key | Type | Range | Notes |
|-----|------|-------|-------|
| Month | integer | 1-12 | |
| Day | integer | 1-31 | Day of month |
| Weekday | integer | 0-6 | 0=Sunday |
| Hour | integer | 0-23 | |
| Minute | integer | 0-59 | |

Omitted keys mean "any" — a dict with only `Minute: 0` runs every hour at :00.

## Installation Flow

The correct sequence for installing/updating an agent:

```bash
# 1. If already loaded, unload first (avoids error 5)
launchctl unload ~/Library/LaunchAgents/com.example.plist 2>/dev/null

# 2. Copy/generate the plist (replace template vars if needed)
sed "s|REPO_PATH|$PWD|g" template.plist > ~/Library/LaunchAgents/com.example.plist

# 3. Load the agent
launchctl load ~/Library/LaunchAgents/com.example.plist

# 4. Verify it's loaded
launchctl list com.example
```

The unload-before-load pattern is important because `launchctl load` on an already-loaded agent returns error 5 ("Input/output error").

## Reading Plist in Python

```python
import plistlib
from pathlib import Path

plist_path = Path.home() / "Library/LaunchAgents/com.example.plist"
with open(plist_path, "rb") as f:
    data = plistlib.load(f)

# Schedule can be dict (single) or list (multiple)
schedule = data.get("StartCalendarInterval", {})
if isinstance(schedule, dict):
    schedule = [schedule]
# Now schedule is always a list of dicts
```

## Modifying Schedule Programmatically

```python
import plistlib

with open(plist_path, "rb") as f:
    data = plistlib.load(f)

# Set multiple schedules
data["StartCalendarInterval"] = [
    {"Hour": 9, "Minute": 0},
    {"Hour": 18, "Minute": 0, "Weekday": 1},
]

with open(plist_path, "wb") as f:
    plistlib.dump(data, f)

# Must unload + load to apply changes
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `load` returns error 5 | Agent already loaded | Unload first, then load |
| Agent doesn't run | PATH not set in plist | Add `EnvironmentVariables` with PATH |
| Agent runs but script fails | Working directory wrong | Set `WorkingDirectory` in plist |
| `launchctl list` shows exit code 78 | Configuration error | Check plist syntax with `plutil -lint` |
| Agent not in `launchctl list` | Not loaded or wrong path | Ensure plist is in `~/Library/LaunchAgents/` |
| Agent runs at wrong time | Schedule timezone | launchd uses system timezone |

## Common Gotchas

1. **PATH is minimal** — launchd agents run with a very limited PATH (`/usr/bin:/bin:/usr/sbin:/sbin`). Always set PATH explicitly or use absolute paths in scripts.

2. **Single vs array schedule** — A single `StartCalendarInterval` dict vs an array of dicts. Python's `plistlib` handles both, but your code must check `isinstance(schedule, dict)`.

3. **Changes need reload** — Editing a plist file does nothing until you `unload` + `load` the agent.

4. **User agents only** — `~/Library/LaunchAgents/` runs as the current user and only while logged in. For system-wide agents that run at boot, use `/Library/LaunchDaemons/` (requires root).

5. **Log rotation** — launchd doesn't rotate logs. Use dated log paths (e.g., `agent-$(date +%F).log`) or set up a separate rotation mechanism.

6. **TCC / Full Disk Access** — launchd agents accessing `~/Documents/`, `~/Desktop/`, or `~/Downloads/` need the executable to have Full Disk Access (FDA). `/bin/bash` does NOT have FDA by default. See the Portable Fleet Pattern below for the solution.

7. **Cross-project `source` causes EDEADLK (exit 78)** — When a launchd script sources a lib from a *different* project directory (e.g., `source ~/Documents/OtherProject/bin/lib.sh`), macOS TCC can intermittently return "Resource deadlock avoided" (errno 78). Under `set -euo pipefail` this silently aborts the entire script. Wrap the `source` defensively:

   ```bash
   # Bad — aborts script on TCC failure
   source "$OTHER_PROJECT/bin/sk-exec-lib"

   # Good — TCC failure is non-fatal; main task continues
   set +e; source "$OTHER_PROJECT/bin/sk-exec-lib" 2>/dev/null || true; set -e
   ```

   This applies especially when the sourced lib is optional (e.g., dashboard telemetry). If the lib is mandatory, log the failure and exit cleanly rather than proceeding silently.

---

## Portable Multi-Agent Fleet Pattern

When managing multiple launchd agents across machines, hardcoded absolute paths make plists non-portable. This pattern solves it with three components:

### Architecture

```
project/
├── agents/
│   ├── agents.conf          # Declarative agent definitions
│   └── sk-agent-run.c       # Compiled launcher (gets FDA)
└── bin/
    └── sk-setup-agents      # Bootstrap: detect PATH → compile → generate plists → load
```

New machine setup: `./bin/sk-setup-agents` → grant FDA → done.

### 1. Declarative Config (`agents.conf`)

All agents defined in one file — no plist editing needed:

```
# LABEL | PROJECT_REL | SCRIPT | SCHEDULE_TYPE | SCHEDULE_VALUE | LOG_DIR | EXTRA_ARGS
#
# SCHEDULE_TYPE: interval | calendar | calendar_multi | keepalive
# SCHEDULE_VALUE:
#   interval       → seconds (28800 = 8h)
#   calendar       → H:MM or W:H:MM (W=weekday 0-6)
#   calendar_multi → W1:H:MM,W2:H:MM
#   keepalive      → - (always running)

com.example.daily-task   | my-project | scripts/task.sh   | calendar       | 7:30         | logs
com.example.weekly-task  | my-project | scripts/weekly.sh | calendar       | 0:10:00      | logs | weekly
com.example.twice-weekly | my-project | scripts/scrape.sh | calendar_multi | 1:8:00,4:8:00 | logs
com.example.web-server   | my-project | scripts/start.sh  | keepalive      | -            | logs
```

### 2. Compiled Launcher (`sk-agent-run.c`)

A tiny C program that `cd`s into the project dir and execs the script. Compiled during setup so it can receive FDA — `/bin/bash` cannot.

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: sk-agent-run <project_dir> <script> [args...]\n");
        return 1;
    }
    if (chdir(argv[1]) != 0) { perror("chdir"); return 1; }

    int new_argc = argc - 1;
    char **new_argv = malloc((new_argc + 1) * sizeof(char *));
    new_argv[0] = "/bin/bash";
    for (int i = 2; i < argc; i++) new_argv[i - 1] = argv[i];
    new_argv[new_argc] = NULL;

    execv("/bin/bash", new_argv);
    perror("execv"); return 1;
}
```

Why not just a shell script? macOS TCC blocks `/bin/bash` from accessing `~/Documents/` when launched by launchd. A compiled binary can be granted FDA individually.

### 3. Bootstrap Script (`sk-setup-agents`)

Key responsibilities:
1. **Auto-detect PATH** — scans for conda, homebrew, npm global, ~/.local/bin
2. **Compile launcher** — `cc -O2 -o ~/.local/bin/sk-agent-run agents/sk-agent-run.c`
3. **Generate plists** — reads agents.conf, expands `$HOME`-relative paths
4. **Load into launchd** — unload-then-load each agent

```bash
# PATH detection pattern — finds tools regardless of install location
detect_path() {
  local parts="/usr/local/bin:/usr/bin:/bin"
  [ -d "/opt/homebrew/bin" ] && parts="/opt/homebrew/bin:$parts"
  for conda_bin in "$HOME/miniconda3/bin" "$HOME/anaconda3/bin" \
    "/opt/homebrew/Caskroom/miniconda/base/bin"; do
    [ -d "$conda_bin" ] && { parts="$conda_bin:$parts"; break; }
  done
  local npm_bin="$(npm config get prefix 2>/dev/null)/bin"
  [ -d "$npm_bin" ] && parts="$parts:$npm_bin"
  parts="$parts:$HOME/.local/bin"
  echo "$parts"
}
```

### FDA Setup (one-time per machine)

After running `sk-setup-agents`:

1. Open **System Settings → Privacy & Security → Full Disk Access**
2. Click **+**, navigate to `~/.local/bin/sk-agent-run`
3. Toggle ON

Without FDA, agents accessing `~/Documents/` will fail with "Operation not permitted" (exit 126).

### 4. Auto-Heal Script (`sk-agent-doctor`)

Diagnoses failing agents by reading stderr/stdout logs and applies known fixes:

| Pattern | Auto-Fix |
|---------|----------|
| `command not found` | Re-run `sk-setup-agents` (regenerate PATH) |
| `No module named 'X'` | `pip3 install X` (with name mapping) |
| `EADDRINUSE` / `address already in use` | Kill stale process, restart agent |
| `ENOTEMPTY .next` | Remove stale build cache |
| `Operation not permitted` | Report: grant FDA (manual) |
| `OAuth token has expired` | Report: `claude login` (manual) |
| `Push failed` | Report: check git remote (manual) |
| `ENOTFOUND` / API unreachable | Report: check network (manual) |

```bash
./bin/sk-agent-doctor            # diagnose + auto-fix
./bin/sk-agent-doctor --check    # diagnose only (dry run)
```

Integrates with `sk-tester-cron` — tester auto-triggers doctor when agent health check fails.

### Cron-Script Conventions (rivendell flavor)

Every cron-style script under `bin/sk-*-cron` (or any `bin/sk-*` invoked by a
launchd agent) follows the same shape. Following these conventions means the
fleet behaves predictably — anomalies surface naturally and re-runs are safe.

```bash
#!/usr/bin/env bash
# sk-<name> — <one-line purpose>
#
# <2-3 line explanation of what it does and what failure mode it solves>
set -euo pipefail

# Resolve repo root from script location, NOT from $PWD — launchd's cwd is unreliable
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="$REPO_DIR/reports"
STATE_FILE="$STATE_DIR/.<name>-state"   # gitignored runtime state
LOG_FILE="$STATE_DIR/<name>.log"

mkdir -p "$STATE_DIR"

# Optional: hook into dashboard observability
set +e; source "$REPO_DIR/bin/sk-exec-lib" 2>/dev/null || true; set -e

# ... do the work ...

# Always exit 0 for maintenance scripts; failures live in the log, not the
# launchd exit code. Use exit 1 only when the script itself broke (config
# missing, prerequisite absent), not when "nothing was wrong to fix".
exit 0
```

**Five conventions worth treating as load-bearing:**

1. **Silent on healthy.** Only write to `LOG_FILE` when something actually
   changed (`FIXED`, `RESTART`, `ARCHIVED`). A healthy fleet produces empty
   logs, which makes anomalies obvious. A noisy log buries the signal.

2. **State in `reports/.<name>-state`.** Hidden file, gitignored. Format is
   plain text, parseable by `grep`/`cut`. Anything stateful (last-run timestamp,
   counters) goes here. Examples in this repo: `.watchdog-state`,
   `.harvest-state`, `.harvest-done`.

3. **Pipefail trap defense.** With `set -euo pipefail`, a `grep` that finds no
   match returns 1 and kills the whole script. Wrap risky pipelines:
   ```bash
   { grep "^$key:" "$STATE_FILE" 2>/dev/null | cut -d: -f2-; } || true
   ```
   The `{ ...; } || true` catches the pipeline's exit and gives back 0. Common
   trap when reading state files that may be empty on first run.

4. **Idempotent re-run.** Running the script twice in a row on already-clean
   state must be a no-op. Validate this manually before deploying the agent:
   ```bash
   ./bin/sk-<name>; echo "first: $?"
   ./bin/sk-<name>; echo "second: $?"   # both 0, no log change between them
   ```
   This is what makes `launchctl kickstart` safe and lets the cron's interval
   be tuned freely.

5. **`exit 0` always for maintenance.** Maintenance scripts are not health
   checks. If you exit 1 when "nothing needed fixing", launchd will retry
   aggressively and `launchctl list` will show alarming failure counts that
   mean nothing. Reserve non-zero exit codes for "the script itself broke."

**See live examples:** `bin/sk-watchdog`, `bin/sk-deploy-symlink-fix`,
`bin/sk-reports-janitor`, `bin/sk-workflow-retro-cron`. All follow this shape.

### Debugging the Fleet

```bash
# All agents at a glance
launchctl list | grep com.sk | awk '{printf "%-50s exit=%s pid=%s\n", $3, $2, $1}'

# Common exit codes
#   0   = success
#   1   = script error (check stderr log)
#   126 = permission denied (grant FDA)
#   127 = command not found (check PATH in plist)
#   256 = script exited 1 (launchd multiplies by 256)

# Reload a single agent after config change
launchctl unload ~/Library/LaunchAgents/com.example.plist
launchctl load ~/Library/LaunchAgents/com.example.plist

# Reload all
./bin/sk-setup-agents

# Unload all
./bin/sk-setup-agents --unload

# Preview without installing
./bin/sk-setup-agents --dry-run
```
