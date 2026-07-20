#!/usr/bin/env bash
# install.sh — wire (or remove) the context-journal hooks into a Claude Code
# settings.json. Idempotent: safe to run repeatedly; never clobbers other hooks.
#
# Usage:
#   install.sh install [--project]   # default target: ~/.claude/settings.json
#   install.sh uninstall [--project]
#   install.sh status [--project]
#
#   --project → target ./.claude/settings.json (this repo only) instead of global.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STOP_CMD="$HERE/journal-stop-hook.sh"
SS_CMD="$HERE/journal-sessionstart-hook.sh"
UPS_CMD="$HERE/journal-compact-reminder-hook.sh"

ACTION="${1:-status}"
SCOPE="global"
[ "${2:-}" = "--project" ] && SCOPE="project"

if [ "$SCOPE" = "project" ]; then
  SETTINGS="$(pwd)/.claude/settings.json"
else
  SETTINGS="$HOME/.claude/settings.json"
fi

mkdir -p "$(dirname "$SETTINGS")"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"

command -v jq >/dev/null 2>&1 || { echo "ERROR: jq required" >&2; exit 1; }

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

case "$ACTION" in
  install)
    jq --arg stop "$STOP_CMD" --arg ss "$SS_CMD" --arg ups "$UPS_CMD" '
      .hooks //= {} |
      .hooks.Stop //= [] |
      .hooks.SessionStart //= [] |
      .hooks.UserPromptSubmit //= [] |
      (if any(.hooks.Stop[]?.hooks[]?; .command == $stop) then .
       else .hooks.Stop += [{hooks: [{type: "command", command: $stop}]}] end) |
      (if any(.hooks.SessionStart[]?.hooks[]?; .command == $ss) then .
       else .hooks.SessionStart += [{matcher: "compact|resume", hooks: [{type: "command", command: $ss}]}] end) |
      (if any(.hooks.UserPromptSubmit[]?.hooks[]?; .command == $ups) then .
       else .hooks.UserPromptSubmit += [{hooks: [{type: "command", command: $ups}]}] end)
    ' "$SETTINGS" > "$tmp"
    mv "$tmp" "$SETTINGS"
    echo "INSTALLED → $SETTINGS"
    echo "  Stop             → $STOP_CMD"
    echo "  SessionStart     → $SS_CMD  (matcher: compact|resume)"
    echo "  UserPromptSubmit → $UPS_CMD  (compact reminder)"
    ;;
  uninstall)
    jq --arg stop "$STOP_CMD" --arg ss "$SS_CMD" --arg ups "$UPS_CMD" '
      if .hooks then
        (if .hooks.Stop then
          .hooks.Stop |= (map(.hooks |= map(select(.command != $stop))) | map(select((.hooks | length) > 0)))
        else . end) |
        (if (.hooks.Stop? // [] | length) == 0 then del(.hooks.Stop) else . end) |
        (if .hooks.SessionStart then
          .hooks.SessionStart |= (map(.hooks |= map(select(.command != $ss))) | map(select((.hooks | length) > 0)))
        else . end) |
        (if (.hooks.SessionStart? // [] | length) == 0 then del(.hooks.SessionStart) else . end) |
        (if .hooks.UserPromptSubmit then
          .hooks.UserPromptSubmit |= (map(.hooks |= map(select(.command != $ups))) | map(select((.hooks | length) > 0)))
        else . end) |
        (if (.hooks.UserPromptSubmit? // [] | length) == 0 then del(.hooks.UserPromptSubmit) else . end) |
        (if (.hooks | length) == 0 then del(.hooks) else . end)
      else . end
    ' "$SETTINGS" > "$tmp"
    mv "$tmp" "$SETTINGS"
    echo "UNINSTALLED from $SETTINGS (log files under ~/.claude/session-logs/ kept)"
    ;;
  status)
    echo "Target: $SETTINGS"
    S=$(jq -r --arg c "$STOP_CMD" '[.hooks.Stop[]?.hooks[]? | select(.command==$c)] | length' "$SETTINGS" 2>/dev/null || echo 0)
    T=$(jq -r --arg c "$SS_CMD" '[.hooks.SessionStart[]?.hooks[]? | select(.command==$c)] | length' "$SETTINGS" 2>/dev/null || echo 0)
    U=$(jq -r --arg c "$UPS_CMD" '[.hooks.UserPromptSubmit[]?.hooks[]? | select(.command==$c)] | length' "$SETTINGS" 2>/dev/null || echo 0)
    echo "  Stop hook (log):          $([ "$S" -gt 0 ] && echo installed || echo 'not installed')"
    echo "  SessionStart (re-inject): $([ "$T" -gt 0 ] && echo installed || echo 'not installed')"
    echo "  UserPromptSubmit (nudge): $([ "$U" -gt 0 ] && echo installed || echo 'not installed')"
    ;;
  *)
    echo "Usage: install.sh {install|uninstall|status} [--project]" >&2
    exit 1
    ;;
esac
