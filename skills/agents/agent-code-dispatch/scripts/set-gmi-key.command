#!/bin/bash
# Store the GMI API key in the macOS Keychain for `sk code` (qwen executor).
# Open this file in Finder or Terminal: it needs a TTY to hide the input,
# so it does not work through Claude Code's `!` prefix.
set -euo pipefail
SERVICE="sk-gmi-api-key"
printf 'Paste the GMI API key (input is hidden): '
read -rs KEY
echo
if [ -z "$KEY" ]; then
  echo "Empty input. Nothing stored."
  exit 1
fi
security add-generic-password -U -s "$SERVICE" -a "$USER" -w "$KEY"
unset KEY
echo "Stored in Keychain as '$SERVICE'."
read -rp "Press Enter to close."
