#!/usr/bin/env bash
# Check if task_plan.md has incomplete phases. Used as Stop hook.
set -euo pipefail

PLAN="task_plan.md"

if [ ! -f "$PLAN" ]; then
  exit 0
fi

incomplete=$(grep -ciE 'in_progress|not_started|pending|TODO' "$PLAN" 2>/dev/null || true)

if [ "$incomplete" -gt 0 ]; then
  echo "[planning-with-files] ⚠ task_plan.md has $incomplete incomplete item(s)."
  echo "  Consider updating phase statuses before ending the session."
fi
