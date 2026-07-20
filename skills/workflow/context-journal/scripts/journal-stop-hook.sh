#!/usr/bin/env bash
# journal-stop-hook.sh — Claude Code Stop hook.
# Appends one compact work-log entry per turn so the durable record lives on
# disk, not in context. This makes /compact (and built-in auto-compact) safe:
# the preceding transcript can be dropped and this log survives to be read back.
#
# Wired via ~/.claude/settings.json hooks.Stop (see install.sh).
# A hook must NEVER break the session: swallow every error, always `exit 0`.
#
# stdin (JSON): { session_id, transcript_path, cwd, hook_event_name, stop_hook_active }

set -uo pipefail

INPUT=$(cat 2>/dev/null || true)

_jq() { printf '%s' "$INPUT" | jq -r "$1" 2>/dev/null || true; }

SESSION_ID=$(_jq '.session_id // "unknown"')
TRANSCRIPT=$(_jq '.transcript_path // empty')
CWD=$(_jq '.cwd // empty')

[ -n "$CWD" ] && cd "$CWD" 2>/dev/null || true

# Project slug from git toplevel (fallback: cwd basename).
TOP=$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")
SLUG=$(basename "$TOP" 2>/dev/null | tr -cd 'a-zA-Z0-9._-')
[ -z "$SLUG" ] && SLUG="unknown"

LOG_DIR="$HOME/.claude/session-logs/$SLUG"
mkdir -p "$LOG_DIR" 2>/dev/null || true
LOG="$LOG_DIR/${SESSION_ID}.md"

BRANCH=$(git branch --show-current 2>/dev/null || echo "n/a")

# --- pull the last turn's request + response from the tail of the transcript ---
# Read only the tail (each JSONL line is one record) to stay O(1)-ish per turn.
PROMPT=""
SUMMARY=""
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  TAIL=$(tail -n 500 "$TRANSCRIPT" 2>/dev/null || true)
  PROMPT=$(printf '%s' "$TAIL" \
    | jq -rs '[.[] | select(.type=="last-prompt") | .lastPrompt] | last // ""' 2>/dev/null \
    | perl -CSD -0pe 's/\s+/ /g; $_=substr($_,0,160)' 2>/dev/null || true)
  SUMMARY=$(printf '%s' "$TAIL" \
    | jq -rs '[.[] | select(.type=="assistant") | .message.content[]? | select(.type=="text") | .text] | last // ""' 2>/dev/null \
    | perl -CSD -0pe 's/\s+/ /g; $_=substr($_,0,320)' 2>/dev/null || true)
fi

# Only record what changed THIS turn: diff current `git status` against the
# snapshot from the previous entry, so entries stay lean instead of repeating
# the whole dirty tree every turn.
SNAP="$LOG_DIR/.snapshot-${SESSION_ID}"
[ -f "$SNAP" ] || : > "$SNAP" 2>/dev/null || true
NOW=$(git status --short 2>/dev/null || true)
CHANGES=$(printf '%s\n' "$NOW" | grep -vxF -f "$SNAP" 2>/dev/null | grep -v '^$' | head -20 || true)
printf '%s\n' "$NOW" > "$SNAP" 2>/dev/null || true

# Skip trivial turns: no new file changes AND a near-empty assistant reply.
if [ -z "$CHANGES" ] && [ "${#SUMMARY}" -lt 40 ]; then
  exit 0
fi

# Header on first write for this session.
if [ ! -f "$LOG" ]; then
  {
    echo "# 工作日誌 · $SLUG"
    echo "session: \`$SESSION_ID\`"
    echo "started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "> compaction 前的操作/調整逐回合紀錄。compact 後由 SessionStart hook 自動讀回尾段。"
    echo ""
  } >> "$LOG" 2>/dev/null || true
fi

{
  echo "## $(date '+%m-%d %H:%M:%S') · \`$BRANCH\`"
  [ -n "$PROMPT" ]  && echo "- 觸發: $PROMPT"
  if [ -n "$CHANGES" ]; then
    echo "- 改動:"
    printf '%s\n' "$CHANGES" | sed 's/^/    /'
  else
    echo "- 改動: 無新增檔案異動"
  fi
  [ -n "$SUMMARY" ] && echo "- 摘要: $SUMMARY"
  echo ""
} >> "$LOG" 2>/dev/null || true

exit 0
