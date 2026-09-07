#!/usr/bin/env bash
# storyline-gate-hook.sh — PreToolUse hook (Bash|Write) that makes slide-workflow
# Gate 0 real: while a project has a storyline.md that is NOT `status: signed-off`,
# deck generation is blocked until /slide-office-hours signs it off.
#
# Deliberately narrow, so it does not over-fire (see rivendell .claude/CLAUDE.md
# "Storyline-first is a hard gate"):
#   - fires only on deck-generation actions: an html2pptx run, or writing a .pptx
#   - fires only when a storyline.md exists in the project (draft found);
#     a project with no storyline at all is left to prompt routing
#   - escape hatch: SK_SKIP_STORYLINE_GATE=1 or a `.storyline-gate-off` file
#
# Input: hook JSON on stdin. Exit 0 = allow, 2 = block (reason on stderr).

INPUT="$(cat 2>/dev/null)" || true
[ -z "$INPUT" ] && exit 0
[ "${SK_SKIP_STORYLINE_GATE:-}" = "1" ] && exit 0
command -v jq >/dev/null 2>&1 || exit 0

TOOL="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')"
CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // empty')"
[ -z "$CWD" ] && CWD="$PWD"

case "$TOOL" in
  Bash)
    CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' | head -c 600)"
    # html2pptx.js run, or a node/python script that writes a .pptx
    printf '%s' "$CMD" | grep -qE 'html2pptx|\.pptx' || exit 0
    # editing an existing deck is not generation
    printf '%s' "$CMD" | grep -qE 'office-pptx/scripts/(inventory|thumbnail|replace|rearrange)' && exit 0
    ;;
  Write)
    FP="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')"
    case "$FP" in *.pptx) ;; *) exit 0 ;; esac
    ;;
  *) exit 0 ;;
esac

ROOT="$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$CWD")"
[ -f "$ROOT/.storyline-gate-off" ] && exit 0

# Nearest storyline.md: cwd first, then up to 3 levels under the repo root.
STORY="$(find "$CWD" -maxdepth 1 -name storyline.md 2>/dev/null | head -1)"
[ -z "$STORY" ] && STORY="$(find "$ROOT" -maxdepth 3 -name storyline.md -not -path '*/node_modules/*' 2>/dev/null | head -1)"
[ -z "$STORY" ] && exit 0   # no storyline anywhere → not this hook's call

STATUS="$(awk '/^---$/{c++; next} c==1 && /^status:/{sub(/^status:[ \t]*/,""); print; exit}' "$STORY" | tr -d '"'"'" )"
if [ "$STATUS" = "signed-off" ]; then
  exit 0
fi

printf '{"decision":"block","reason":"storyline gate: %s 的 status 是「%s」，不是 signed-off。先跑 /slide-office-hours 紅隊完簽核，再生成 deck。（跳過：SK_SKIP_STORYLINE_GATE=1）"}\n' \
  "${STORY#$ROOT/}" "${STATUS:-缺 status}" >&2
exit 2
