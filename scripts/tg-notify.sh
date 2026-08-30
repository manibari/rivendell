#!/usr/bin/env bash
# tg-notify.sh — one-way Telegram push for dispatch/triage results.
# Reads RIVENDELL_TG_BOT_TOKEN / RIVENDELL_TG_CHAT_ID from
# ~/.config/rivendell/secrets.env. Silently exits 0 when unconfigured —
# notification is best-effort and must never block the main flow.
# Usage: tg-notify.sh "message"   or   echo "message" | tg-notify.sh
set -uo pipefail

SECRETS="$HOME/.config/rivendell/secrets.env"
[ -f "$SECRETS" ] || exit 0

token=$(grep -E '^RIVENDELL_TG_BOT_TOKEN=' "$SECRETS" | head -1 | cut -d= -f2-)
chat_id=$(grep -E '^RIVENDELL_TG_CHAT_ID=' "$SECRETS" | head -1 | cut -d= -f2-)
[ -n "$token" ] && [ -n "$chat_id" ] || exit 0

if [ $# -ge 1 ]; then
    text="$*"
else
    text="$(cat)"
fi
[ -n "$text" ] || exit 0

curl -sf --max-time 10 "https://api.telegram.org/bot${token}/sendMessage" \
    --data-urlencode "chat_id=${chat_id}" \
    --data-urlencode "text=${text}" \
    > /dev/null || exit 1
exit 0
