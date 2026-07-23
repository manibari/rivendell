#!/usr/bin/env bash
# Initialize planning files in the current project directory from templates.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/../templates"

files=("task_plan.md" "findings.md" "progress.md")
created=0

for f in "${files[@]}"; do
  if [ -f "$f" ]; then
    echo "[planning-with-files] $f already exists, skipping."
  else
    cp "$TEMPLATE_DIR/$f" "$f"
    echo "[planning-with-files] Created $f"
    created=$((created + 1))
  fi
done

if [ "$created" -eq 0 ]; then
  echo "[planning-with-files] All planning files already exist."
else
  echo "[planning-with-files] Initialized $created file(s)."
fi
