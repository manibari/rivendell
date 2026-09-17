#!/usr/bin/env bash
# install.sh — wire (or remove) the context-journal hooks into a Claude Code
# settings.json. Idempotent: safe to run repeatedly; never clobbers other hooks.
#
# Global scope is ALSO covered by rivendell's manifest (data/global-hooks.json →
# `sk hooks install`), and both write the same deploy-symlink command strings, so
# running either one is enough and running both is harmless.
#
# Usage:
#   install.sh install [--project]   # default target: ~/.claude/settings.json
#   install.sh uninstall [--project]
#   install.sh status [--project]
#
#   --project → target ./.claude/settings.json (this repo only) instead of global.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY="$HOME/.claude/skills/context-journal/scripts"

ACTION="${1:-status}"
SCOPE="global"
[ "${2:-}" = "--project" ] && SCOPE="project"

# Global hooks must survive a repo move, so they reference the ~/.claude/skills
# deploy symlink rather than wherever the repo happens to live today. Project
# hooks stay pinned to the checkout they belong to.
if [ "$SCOPE" = "global" ] && [ -e "$DEPLOY/journal-stop-hook.sh" ]; then
  PREFIX="~/.claude/skills/context-journal/scripts"
else
  PREFIX="$HERE"
  [ "$SCOPE" = "global" ] && \
    echo "NOTE: ~/.claude/skills/context-journal not deployed — falling back to repo paths. Run \`sk deploy\` then re-run for a move-proof install." >&2
fi

STOP_CMD="$PREFIX/journal-stop-hook.sh"
SS_CMD="$PREFIX/journal-sessionstart-hook.sh"
UPS_CMD="$PREFIX/journal-compact-reminder-hook.sh"
SS_MATCHER="startup|resume|compact"

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
    jq --arg stop "$STOP_CMD" --arg ss "$SS_CMD" --arg ups "$UPS_CMD" --arg ssm "$SS_MATCHER" '
      .hooks //= {} |
      .hooks.Stop //= [] |
      .hooks.SessionStart //= [] |
      .hooks.UserPromptSubmit //= [] |
      (if any(.hooks.Stop[]?.hooks[]?; .command == $stop) then .
       else .hooks.Stop += [{hooks: [{type: "command", command: $stop}]}] end) |
      (if any(.hooks.SessionStart[]?.hooks[]?; .command == $ss)
       then
         # Already registered — repair the matcher of pre-handoff installs,
         # which only listened for compact|resume and so missed `startup`.
         .hooks.SessionStart |= map(
           if any(.hooks[]?; .command == $ss) then .matcher = $ssm else . end)
       else .hooks.SessionStart += [{matcher: $ssm, hooks: [{type: "command", command: $ss}]}] end) |
      (if any(.hooks.UserPromptSubmit[]?.hooks[]?; .command == $ups) then .
       else .hooks.UserPromptSubmit += [{hooks: [{type: "command", command: $ups}]}] end)
    ' "$SETTINGS" > "$tmp"
    mv "$tmp" "$SETTINGS"
    echo "INSTALLED → $SETTINGS"
    echo "  Stop             → $STOP_CMD"
    echo "  SessionStart     → $SS_CMD  (matcher: $SS_MATCHER)"
    echo "  UserPromptSubmit → $UPS_CMD  (two-tier nudge)"
    echo "  Restart Claude Code to load them."
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
    TM=$(jq -r --arg c "$SS_CMD" 'first(.hooks.SessionStart[]? | select(any(.hooks[]?; .command==$c)) | .matcher // "-") // "-"' "$SETTINGS" 2>/dev/null || echo "-")
    U=$(jq -r --arg c "$UPS_CMD" '[.hooks.UserPromptSubmit[]?.hooks[]? | select(.command==$c)] | length' "$SETTINGS" 2>/dev/null || echo 0)
    echo "  Stop hook (log):          $([ "$S" -gt 0 ] && echo installed || echo 'not installed')"
    echo "  SessionStart (re-inject): $([ "$T" -gt 0 ] && echo "installed (matcher: $TM)" || echo 'not installed')"
    echo "  UserPromptSubmit (nudge): $([ "$U" -gt 0 ] && echo installed || echo 'not installed')"
    if [ "$T" -gt 0 ]; then
      case "$TM" in
        *startup*) : ;;
        *) echo "  WARNING: matcher lacks 'startup' — handoff notes will NOT be injected. Re-run: install.sh install" ;;
      esac
    fi
    TOP=$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")
    SLUG=$(basename "$TOP" | tr -cd 'a-zA-Z0-9._-')
    H="$HOME/.claude/session-logs/$SLUG/HANDOFF.md"
    echo "  Pending handoff:          $([ -f "$H" ] && echo "yes → $H" || echo 'none')"
    ;;
  *)
    echo "Usage: install.sh {install|uninstall|status} [--project]" >&2
    exit 1
    ;;
esac
