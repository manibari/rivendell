#!/usr/bin/env bash
# session-handoff.sh — write the handoff note that lets you close a fat session
# and continue in a fresh one without losing the thread.
#
# Division of labour: this script gathers only the MECHANICAL facts (branch,
# uncommitted files, recent commits, work-log tail). The semantic part — what we
# are actually doing, what is decided, what is next — is left as TODO markers for
# Claude to fill in, because only the session itself knows that.
#
# The note lands at ~/.claude/session-logs/<project>/HANDOFF.md, where the
# SessionStart hook picks it up on the next `startup` (within .handoff-ttl-min,
# default 240) and archives it after injecting.
#
# Usage:
#   session-handoff.sh seed     # (default) write the skeleton, print the path
#   session-handoff.sh path     # print the target path only
#   session-handoff.sh show     # print the current note
#   session-handoff.sh clear    # drop a pending note (archives it)

set -uo pipefail

ACTION="${1:-seed}"

TOP=$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")
SLUG=$(basename "$TOP" 2>/dev/null | tr -cd 'a-zA-Z0-9._-'); [ -z "$SLUG" ] && SLUG="unknown"
DIR="$HOME/.claude/session-logs/$SLUG"
HANDOFF="$DIR/HANDOFF.md"

case "$ACTION" in
  path) printf '%s\n' "$HANDOFF"; exit 0 ;;
  show)
    [ -f "$HANDOFF" ] || { echo "no pending handoff at $HANDOFF" >&2; exit 1; }
    cat "$HANDOFF"; exit 0 ;;
  clear)
    [ -f "$HANDOFF" ] || { echo "nothing to clear"; exit 0; }
    mkdir -p "$DIR/handoff-archive" 2>/dev/null || true
    mv "$HANDOFF" "$DIR/handoff-archive/HANDOFF-cleared-$(date +%Y%m%d-%H%M%S).md"
    echo "cleared (archived under $DIR/handoff-archive/)"; exit 0 ;;
  seed) : ;;
  *) echo "Usage: session-handoff.sh {seed|path|show|clear}" >&2; exit 1 ;;
esac

mkdir -p "$DIR" 2>/dev/null || true

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "-")
STATUS=$(git status --short 2>/dev/null | head -40)
[ -z "$STATUS" ] && STATUS="(working tree clean)"
COMMITS=$(git log -5 --format='%h %ad %s' --date=short 2>/dev/null || true)
[ -z "$COMMITS" ] && COMMITS="(no commits)"

# Tail of the most recent work-log for this project, if the Stop hook is running.
LOGTAIL=""
NEWEST=$(ls -t "$DIR"/*.md 2>/dev/null | grep -v '/HANDOFF\.md$' | head -1 || true)
[ -n "$NEWEST" ] && LOGTAIL=$(tail -c 2500 "$NEWEST" 2>/dev/null || true)

{
  echo "# Session handoff — $SLUG"
  echo
  echo "寫於 $(date '+%Y-%m-%d %H:%M')　branch: \`$BRANCH\`"
  echo
  echo "## 在做什麼"
  echo "TODO(claude): 一兩句話。這個 session 的目標，以及為什麼在做。"
  echo
  echo "## 已經決定 / 已完成"
  echo "TODO(claude): 條列。把已經拍板的決定寫進來，新 session 才不會重問。"
  echo
  echo "## 下一步"
  echo "TODO(claude): 條列，具體到新 session 可以直接動手。"
  echo
  echo "## 雷區"
  echo "TODO(claude): 試過但行不通的做法、踩過的坑。沒有就寫「無」。"
  echo
  echo "## 關鍵檔案"
  echo "TODO(claude): path:line 形式，只列真的要再打開的。"
  echo
  echo "---"
  echo
  echo "## 機械現況（自動產生，勿手改）"
  echo
  echo '```'
  echo "git status --short:"
  printf '%s\n' "$STATUS"
  echo
  echo "recent commits:"
  printf '%s\n' "$COMMITS"
  echo '```'
  if [ -n "$LOGTAIL" ]; then
    echo
    echo "<details><summary>work-log 尾段（$(basename "$NEWEST")）</summary>"
    echo
    printf '%s\n' "$LOGTAIL"
    echo
    echo "</details>"
  fi
} > "$HANDOFF"

echo "$HANDOFF"
