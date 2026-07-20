#!/usr/bin/env bash
# journal-sessionstart-hook.sh — Claude Code SessionStart hook.
# After a compaction (source=="compact"), read back the tail of this session's
# work-log and inject it into the fresh context so continuity survives even
# though the preceding transcript was dropped. This closes the loop: Stop hook
# writes the log, this hook reads it back.
#
# Wired via ~/.claude/settings.json hooks.SessionStart (see install.sh).
# Emits hookSpecificOutput.additionalContext (stdout) for Claude to consume.
# Always exit 0.
#
# stdin (JSON): { session_id, cwd, source, hook_event_name }
#   source ∈ startup | resume | clear | compact

set -uo pipefail

INPUT=$(cat 2>/dev/null || true)
_jq() { printf '%s' "$INPUT" | jq -r "$1" 2>/dev/null || true; }

SOURCE=$(_jq '.source // empty')
SESSION_ID=$(_jq '.session_id // empty')
CWD=$(_jq '.cwd // empty')

# Only inject on compaction and resume — startup/clear begin fresh on purpose.
case "$SOURCE" in
  compact|resume) : ;;
  *) exit 0 ;;
esac

[ -n "$CWD" ] && cd "$CWD" 2>/dev/null || true
TOP=$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")
SLUG=$(basename "$TOP" 2>/dev/null | tr -cd 'a-zA-Z0-9._-')
[ -z "$SLUG" ] && SLUG="unknown"

LOG="$HOME/.claude/session-logs/$SLUG/${SESSION_ID}.md"
[ -f "$LOG" ] || exit 0

# Inject the last ~5KB of the log (recent turns matter most).
BODY=$(tail -c 5000 "$LOG" 2>/dev/null || true)
[ -z "$BODY" ] && exit 0

HEADER="[context-journal] compaction 前的工作日誌（供接續，不必重讀被壓縮的前文）:"
jq -n --arg h "$HEADER" --arg b "$BODY" \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: ($h + "\n\n" + $b)}}' \
  2>/dev/null || true

exit 0
