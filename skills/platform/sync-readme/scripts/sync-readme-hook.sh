#!/usr/bin/env bash
# sync-readme-hook.sh — PostToolUse hook
#
# Input:  JSON on stdin: {"tool_name":"Edit","tool_input":{"file_path":"..."},...}
# Behavior:
#   - If SKILL.md modified in rivendell → auto-regenerate README catalog
#   - If a "README-trackable" file changed in any other repo → print reminder
# Exit: 0 always (non-blocking)

set -euo pipefail

INPUT="$(cat)"

# Extract file path from hook payload
if command -v jq &>/dev/null; then
  FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)"
else
  FILE_PATH="$(echo "$INPUT" | python3 -c \
    "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" \
    2>/dev/null || true)"
fi

[ -z "$FILE_PATH" ] && exit 0

# Resolve rivendell root (env override or canonical location)
RIVENDELL_PATH="${RIVENDELL_PATH:-$HOME/Documents/Projects/rivendell}"
CATALOG_SCRIPT="$RIVENDELL_PATH/scripts/generate-readme-catalog.py"

# ── Case 1: SKILL.md modified in rivendell ─────────────────────────────────
if [[ "$FILE_PATH" == "$RIVENDELL_PATH/skills/"*"/SKILL.md" ]]; then
  if [ -f "$CATALOG_SCRIPT" ]; then
    if python3 "$CATALOG_SCRIPT" 2>/dev/null; then
      echo "[sync-readme] README.md catalog regenerated automatically"
    else
      echo "[sync-readme] WARNING: catalog regeneration failed — run 'sk readme' manually"
    fi
  fi
  exit 0
fi

# ── Case 2: README-trackable files in other repos ──────────────────────────
# Only check if the file has a corresponding README.md in the project root
PROJECT_ROOT=""
if command -v git &>/dev/null; then
  PROJECT_ROOT="$(git -C "$(dirname "$FILE_PATH")" rev-parse --show-toplevel 2>/dev/null || true)"
fi
[ -z "$PROJECT_ROOT" ] && exit 0
[ "$PROJECT_ROOT" = "$RIVENDELL_PATH" ] && exit 0  # already handled above
[ ! -f "$PROJECT_ROOT/README.md" ] && exit 0

# Patterns that often need README updates when changed
TRACKED_PATTERNS=(
  "/routes/"
  "/api/"
  "/commands/"
  "/pages/"
  "/app/.*page\."
  "package\.json$"
  "pyproject\.toml$"
  "Makefile$"
  "CHANGELOG"
)

for pattern in "${TRACKED_PATTERNS[@]}"; do
  if [[ "$FILE_PATH" =~ $pattern ]]; then
    RELATIVE="${FILE_PATH#$PROJECT_ROOT/}"
    echo "[sync-readme] $RELATIVE changed — README.md may need updating. Run /sync-readme if needed."
    exit 0
  fi
done

exit 0
