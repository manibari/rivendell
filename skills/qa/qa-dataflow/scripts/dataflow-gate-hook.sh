#!/usr/bin/env bash
# dataflow-gate-hook.sh — PreToolUse hook (Edit|Write|Bash) for schema changes.
#
# The rule (~/.claude/CLAUDE.md): touching data writes / cross-module hand-off /
# a new store is a HARD GATE for qa-dataflow. A hook cannot judge intent, so it
# enforces the one thing it can see — the 功能關係主表 is maintained:
#   - a migration is being written (alembic/versions, migrations/, prisma migrate,
#     makemigrations, alembic revision/upgrade)
#   - the repo HAS a qa-dataflow map (docs/**/dataflow-*.{md,html}) → require the
#     newest one to be ≤ SK_DATAFLOW_MAX_AGE_DAYS (default 30) old, else BLOCK
#   - the repo has NO map → allow, but say so (stdout is shown to the model)
# Escape hatch: SK_SKIP_DATAFLOW_GATE=1 or a `.dataflow-gate-off` file.
#
# Input: hook JSON on stdin. Exit 0 = allow, 2 = block (reason on stderr).

INPUT="$(cat 2>/dev/null)" || true
[ -z "$INPUT" ] && exit 0
[ "${SK_SKIP_DATAFLOW_GATE:-}" = "1" ] && exit 0
command -v jq >/dev/null 2>&1 || exit 0

TOOL="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')"
CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // empty')"
[ -z "$CWD" ] && CWD="$PWD"

case "$TOOL" in
  Edit|Write)
    FP="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')"
    printf '%s' "$FP" | grep -qE '(alembic/versions/[^/]+\.py|/migrations/[^/]+\.(py|sql)|prisma/migrations/)' || exit 0
    ;;
  Bash)
    CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' | head -c 600)"
    printf '%s' "$CMD" | grep -qE 'alembic (revision|upgrade|downgrade)|prisma migrate|makemigrations|migrate_schema' || exit 0
    ;;
  *) exit 0 ;;
esac

ROOT="$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$CWD")"
[ -f "$ROOT/.dataflow-gate-off" ] && exit 0

MAX_AGE="${SK_DATAFLOW_MAX_AGE_DAYS:-30}"
NEWEST="$(find "$ROOT/docs" -type f \( -name 'dataflow-*.md' -o -name 'dataflow-*.html' \) -not -path '*/node_modules/*' 2>/dev/null | xargs -I{} stat -f '%m %N' {} 2>/dev/null | sort -rn | head -1)"

if [ -z "$NEWEST" ]; then
  # No map: cannot demand maintenance of what does not exist. Leave a trace.
  echo "dataflow gate: 這個 repo 沒有 qa-dataflow 功能關係主表（docs/**/dataflow-*）。這次動到 schema，建議先跑 /qa-dataflow 畫主表，之後改 schema 前先改主表。"
  exit 0
fi

MTIME="${NEWEST%% *}"; MAP="${NEWEST#* }"
NOW="$(date +%s)"
AGE_DAYS=$(( (NOW - MTIME) / 86400 ))
if [ "$AGE_DAYS" -le "$MAX_AGE" ]; then
  exit 0
fi

printf '{"decision":"block","reason":"dataflow gate: 主表 %s 已 %s 天沒更新（上限 %s 天）。規矩是先改主表再改 schema：跑 /qa-dataflow 更新 %s，或 SK_SKIP_DATAFLOW_GATE=1 跳過。"}\n' \
  "${MAP#$ROOT/}" "$AGE_DAYS" "$MAX_AGE" "$(basename "$MAP")" >&2
exit 2
