#!/usr/bin/env bash
# journal-compact-reminder-hook.sh — Claude Code UserPromptSubmit hook.
# Reads the exact current context occupancy from the last assistant message's
# usage (input + cache_read + cache_creation) and nudges the user to /compact
# once it crosses a configurable threshold. Because context-journal keeps a
# durable on-disk log, compacting early is lossless — so an early nudge is safe
# and saves tokens on every subsequent turn.
#
# Built-in auto-compact only fires very late (near the model's context limit);
# this gives an earlier, tunable reminder.
#
# Emits a `systemMessage` (shown to the user, NOT injected into context).
# Never blocks the prompt; always exit 0.
#
# stdin (JSON): { session_id, transcript_path, cwd, hook_event_name, prompt }
#
# Config:
#   ~/.claude/session-logs/.compact-threshold   # first-nudge token count (default 300000)
#   ~/.claude/session-logs/.compact-step         # re-nudge every N more tokens (default 100000)

set -uo pipefail

INPUT=$(cat 2>/dev/null || true)
_jq() { printf '%s' "$INPUT" | jq -r "$1" 2>/dev/null || true; }

SESSION_ID=$(_jq '.session_id // "unknown"')
TRANSCRIPT=$(_jq '.transcript_path // empty')
CWD=$(_jq '.cwd // empty')

[ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] || exit 0
[ -n "$CWD" ] && cd "$CWD" 2>/dev/null || true

CFG_DIR="$HOME/.claude/session-logs"
mkdir -p "$CFG_DIR" 2>/dev/null || true
THRESHOLD=$(cat "$CFG_DIR/.compact-threshold" 2>/dev/null || echo 300000)
STEP=$(cat "$CFG_DIR/.compact-step" 2>/dev/null || echo 100000)
case "$THRESHOLD" in ''|*[!0-9]*) THRESHOLD=300000 ;; esac
case "$STEP" in ''|*[!0-9]*) STEP=100000 ;; esac

# Exact current context occupancy from the last assistant usage record.
CUR=$(tail -n 120 "$TRANSCRIPT" 2>/dev/null \
  | jq -rs '[.[] | select(.type=="assistant") | .message.usage] | map(select(.!=null)) | last
            | ((.input_tokens // 0) + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0))' 2>/dev/null || true)
case "$CUR" in ''|*[!0-9]*) exit 0 ;; esac

[ "$CUR" -lt "$THRESHOLD" ] && exit 0

# Cooldown: remind once, then only again after +STEP more tokens.
TOP=$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")
SLUG=$(basename "$TOP" 2>/dev/null | tr -cd 'a-zA-Z0-9._-'); [ -z "$SLUG" ] && SLUG="unknown"
STATE="$CFG_DIR/$SLUG/.compact-remind-${SESSION_ID}"
mkdir -p "$CFG_DIR/$SLUG" 2>/dev/null || true
LAST=$(cat "$STATE" 2>/dev/null || echo 0)
case "$LAST" in ''|*[!0-9]*) LAST=0 ;; esac
[ "$CUR" -lt "$((LAST + STEP))" ] && exit 0
printf '%s' "$CUR" > "$STATE" 2>/dev/null || true

CUR_K=$(( CUR / 1000 ))
THR_K=$(( THRESHOLD / 1000 ))
MSG="⚠️ 前文約 ${CUR_K}k tokens（門檻 ${THR_K}k）。context-journal 已備份本 session，/compact 為無損 —— 現在壓縮可省下後續每回合重載前文的 token。調門檻：echo 400000 > ~/.claude/session-logs/.compact-threshold"

jq -n --arg m "$MSG" '{systemMessage: $m}' 2>/dev/null || true
exit 0
