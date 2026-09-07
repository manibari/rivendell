#!/usr/bin/env bash
# task-tag.sh — record the task object for an INTERACTIVE session.
#
# Scheduled runs get role/job/stage via `sk run --job 4a --stage plan` and land
# in agent_runs. Interactive sessions have no such row, so task-brief Step 1
# calls this once it has located the task; the dashboard role view reads the
# file and can then say "4a Plan ran 3 times, last 2026-09-07" instead of
# guessing from docs.
#
# Usage: task-tag.sh --job 4a --stage plan [--role 4] "one-line task"
# Writes: ~/.claude/session-logs/<repo-slug>/tasks.jsonl (one JSON per line)
set -euo pipefail

ROLE="" JOB="" STAGE="" NOTE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --role)  ROLE="$2"; shift 2 ;;
    --job)   JOB="$2"; shift 2 ;;
    --stage) STAGE="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) NOTE="$*"; break ;;
  esac
done
[ -z "$JOB" ] && { echo "task-tag: --job is required (e.g. 4a)" >&2; exit 1; }
case "$STAGE" in plan|do|check|act) ;; *) echo "task-tag: --stage must be plan|do|check|act" >&2; exit 1 ;; esac
[ -z "$ROLE" ] && ROLE="${JOB%%[a-z]*}"

TOP="$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")"
SLUG="$(basename "$TOP" | tr -cd 'a-zA-Z0-9._-')"
DIR="$HOME/.claude/session-logs/${SLUG:-unknown}"
mkdir -p "$DIR"

python3 - "$DIR/tasks.jsonl" "$ROLE" "$JOB" "$STAGE" "$NOTE" "$TOP" <<'EOF'
import json, sys, datetime, os
path, role, job, stage, note, top = sys.argv[1:7]
rec = {
    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    "role": role, "job": job, "stage": stage,
    "note": note[:200], "project": os.path.basename(top),
    "session": os.environ.get("CLAUDE_SESSION_ID", ""),
}
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(f"task-tag: {job} {stage} → {path}")
EOF
