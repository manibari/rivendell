#!/usr/bin/env bash
# journal-compact-reminder-hook.sh — Claude Code UserPromptSubmit hook.
# Reads the exact current context occupancy from the last assistant message's
# usage (input + cache_read + cache_creation) and nudges the user in TWO TIERS:
#
#   tier 1 (>= .compact-threshold)  → suggest /compact
#   tier 2 (>= .restart-threshold)  → suggest a handoff note + a FRESH session
#
# Why two tiers: /compact is a lossy summary AND it invalidates the whole prompt
# cache, so past a point it stops paying for itself — a clean session seeded with
# a short handoff note starts at ~5k tokens where a compacted one often keeps 50k+
# of summary residue. Because context-journal keeps a durable on-disk log, both
# moves are safe; this hook only picks which one to recommend.
#
# The model cannot compact or close its own session — those are harness actions.
# This hook therefore only SPEAKS: it emits a `systemMessage` (shown to the user,
# NOT injected into context). Never blocks the prompt; always exit 0.
#
# stdin (JSON): { session_id, transcript_path, cwd, hook_event_name, prompt }
#
# Config (all under ~/.claude/session-logs/):
#   .compact-threshold   # tier-1 nudge, token count (default 300000)
#   .restart-threshold   # tier-2 nudge, token count (default 600000)
#   .compact-step        # re-nudge only after N more tokens (default 100000)

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
_cfg() { # _cfg <file> <default>
  local v; v=$(cat "$CFG_DIR/$1" 2>/dev/null || echo "$2")
  case "$v" in ''|*[!0-9]*) v="$2" ;; esac
  printf '%s' "$v"
}
THRESHOLD=$(_cfg .compact-threshold 300000)
RESTART=$(_cfg .restart-threshold 600000)
STEP=$(_cfg .compact-step 100000)

# Exact current context occupancy from the last assistant usage record.
CUR=$(tail -n 120 "$TRANSCRIPT" 2>/dev/null \
  | jq -rs '[.[] | select(.type=="assistant") | .message.usage] | map(select(.!=null)) | last
            | ((.input_tokens // 0) + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0))' 2>/dev/null || true)
case "$CUR" in ''|*[!0-9]*) exit 0 ;; esac

# Which tier are we in? 0 = quiet.
TIER=0
[ "$CUR" -ge "$THRESHOLD" ] && TIER=1
[ "$CUR" -ge "$RESTART" ] && TIER=2
[ "$TIER" -eq 0 ] && exit 0

TOP=$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")
SLUG=$(basename "$TOP" 2>/dev/null | tr -cd 'a-zA-Z0-9._-'); [ -z "$SLUG" ] && SLUG="unknown"
STATE="$CFG_DIR/$SLUG/.compact-remind-${SESSION_ID}"
mkdir -p "$CFG_DIR/$SLUG" 2>/dev/null || true

# State: "<tier> <tokens>". Older installs wrote a bare integer (tier 1).
LAST_RAW=$(cat "$STATE" 2>/dev/null || echo "0 0")
LAST_TIER=$(printf '%s' "$LAST_RAW" | awk '{print ($2=="") ? 1 : $1}')
LAST_TOK=$(printf '%s' "$LAST_RAW" | awk '{print ($2=="") ? $1 : $2}')
case "$LAST_TIER" in ''|*[!0-9]*) LAST_TIER=0 ;; esac
case "$LAST_TOK" in ''|*[!0-9]*) LAST_TOK=0 ;; esac

# Escalating to a higher tier always speaks; otherwise honour the cooldown.
if [ "$TIER" -le "$LAST_TIER" ] && [ "$CUR" -lt "$((LAST_TOK + STEP))" ]; then
  exit 0
fi
printf '%s %s' "$TIER" "$CUR" > "$STATE" 2>/dev/null || true

CUR_K=$(( CUR / 1000 ))
if [ "$TIER" -ge 2 ]; then
  RST_K=$(( RESTART / 1000 ))
  MSG="⚠️ 前文約 ${CUR_K}k tokens（換手門檻 ${RST_K}k）。到這個量級 /compact 已不划算 —— 它是有損摘要，而且會讓整份 prompt cache 失效。建議改成換手：跑 \`/context-journal handoff\` 產交接單，然後關掉這個 session 另開一個（新 session 啟動時會自動把交接單讀回來）。調門檻：echo 800000 > ~/.claude/session-logs/.restart-threshold"
else
  THR_K=$(( THRESHOLD / 1000 ))
  MSG="⚠️ 前文約 ${CUR_K}k tokens（門檻 ${THR_K}k）。context-journal 已備份本 session，/compact 為無損 —— 現在壓縮可省下後續每回合重載前文的 token。調門檻：echo 400000 > ~/.claude/session-logs/.compact-threshold"
fi

jq -n --arg m "$MSG" '{systemMessage: $m}' 2>/dev/null || true
exit 0
