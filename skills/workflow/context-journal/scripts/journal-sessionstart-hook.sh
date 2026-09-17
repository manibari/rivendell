#!/usr/bin/env bash
# journal-sessionstart-hook.sh — Claude Code SessionStart hook.
#
# Two jobs, picked by `source`:
#
#   compact | resume → the transcript was dropped or reloaded mid-session. Read
#                      back the tail of THIS session's work-log so continuity
#                      survives without re-reading the compacted prefix.
#
#   startup          → a brand-new session. Inject HANDOFF.md if one was written
#                      recently and not yet consumed, so "close this session and
#                      open a fresh one" is a real handoff rather than amnesia.
#                      Consumed handoffs are archived, never re-injected — a new
#                      session with no pending handoff starts clean, on purpose.
#
# Wired via ~/.claude/settings.json hooks.SessionStart (matcher startup|resume|compact).
# Emits hookSpecificOutput.additionalContext (stdout) for Claude to consume.
# Always exit 0.
#
# stdin (JSON): { session_id, cwd, source, hook_event_name }
#   source ∈ startup | resume | clear | compact
#
# Config: ~/.claude/session-logs/.handoff-ttl-min   # handoff freshness, minutes (default 240)

set -uo pipefail

INPUT=$(cat 2>/dev/null || true)
_jq() { printf '%s' "$INPUT" | jq -r "$1" 2>/dev/null || true; }

SOURCE=$(_jq '.source // empty')
SESSION_ID=$(_jq '.session_id // empty')
CWD=$(_jq '.cwd // empty')

case "$SOURCE" in
  compact|resume|startup) : ;;
  *) exit 0 ;;   # `clear` begins fresh on purpose
esac

[ -n "$CWD" ] && cd "$CWD" 2>/dev/null || true
TOP=$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")
SLUG=$(basename "$TOP" 2>/dev/null | tr -cd 'a-zA-Z0-9._-')
[ -z "$SLUG" ] && SLUG="unknown"
DIR="$HOME/.claude/session-logs/$SLUG"

_emit() { # _emit <header> <body>
  jq -n --arg h "$1" --arg b "$2" \
    '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: ($h + "\n\n" + $b)}}' \
    2>/dev/null || true
}

if [ "$SOURCE" = "startup" ]; then
  HANDOFF="$DIR/HANDOFF.md"
  [ -f "$HANDOFF" ] || exit 0

  TTL=$(cat "$HOME/.claude/session-logs/.handoff-ttl-min" 2>/dev/null || echo 240)
  case "$TTL" in ''|*[!0-9]*) TTL=240 ;; esac

  MTIME=$(stat -f %m "$HANDOFF" 2>/dev/null || stat -c %Y "$HANDOFF" 2>/dev/null || echo 0)
  case "$MTIME" in ''|*[!0-9]*) exit 0 ;; esac
  AGE_MIN=$(( ( $(date +%s) - MTIME ) / 60 ))
  # Stale handoff: leave it on disk for manual reading, but never auto-inject.
  [ "$AGE_MIN" -gt "$TTL" ] && exit 0

  BODY=$(cat "$HANDOFF" 2>/dev/null || true)
  [ -z "$BODY" ] && exit 0

  # Consume it: archive so the next new session starts clean.
  mkdir -p "$DIR/handoff-archive" 2>/dev/null || true
  mv "$HANDOFF" "$DIR/handoff-archive/HANDOFF-$(date +%Y%m%d-%H%M%S)-${SESSION_ID:-unknown}.md" 2>/dev/null || true

  _emit "[context-journal] 上一個 session 的交接單（${AGE_MIN} 分鐘前寫的，已消費並歸檔）。照它接續，不要重問使用者已經決定的事：" "$BODY"
  exit 0
fi

# compact | resume — same session, read back its own log tail.
LOG="$DIR/${SESSION_ID}.md"
[ -f "$LOG" ] || exit 0
BODY=$(tail -c 5000 "$LOG" 2>/dev/null || true)
[ -z "$BODY" ] && exit 0

_emit "[context-journal] compaction 前的工作日誌（供接續，不必重讀被壓縮的前文）:" "$BODY"
exit 0
