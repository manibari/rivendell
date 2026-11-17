#!/bin/bash
# token-waste-watch: collect -> Gemini -> report, every N minutes until END.
#
# Usage: watch.sh <start> <end> [every_min]
#   start, end  local time, YYYY-MM-DDTHH:MM (for example 2026-11-17T18:00 2026-11-18T09:00)
#   every_min   minutes between reports (default 60). An end in the past gives one report.
# Report:    ${TOKEN_WATCH_REPORT_DIR:-<repo>/reports}/token-watch-<end day>-<host>.md (overwritten each round)
# Snapshots: ~/.local/state/sk/token-watch/<end day>/snap-HHMM.json
set -u
SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd -P)"
START="${1:?start time, YYYY-MM-DDTHH:MM}"
END="${2:?end time, YYYY-MM-DDTHH:MM}"
EVERY_MIN="${3:-60}"

end_epoch=$(date -j -f '%Y-%m-%dT%H:%M' "$END" +%s 2>/dev/null) || { echo "bad end time: $END" >&2; exit 2; }
date -j -f '%Y-%m-%dT%H:%M' "$START" +%s >/dev/null 2>&1 || { echo "bad start time: $START" >&2; exit 2; }

HOST_TAG=$(hostname -s | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-' | sed 's/-\{1,\}$//')
DAY="${END%%T*}"
REPORT_DIR="${TOKEN_WATCH_REPORT_DIR:-$REPO_ROOT/reports}"
REPORT="$REPORT_DIR/token-watch-${DAY}-${HOST_TAG}.md"
SNAPS="$HOME/.local/state/sk/token-watch/$DAY"
mkdir -p "$SNAPS" "$REPORT_DIR"
echo "report: $REPORT"

while :; do
  now_epoch=$(date +%s)
  if [ "$now_epoch" -ge "$end_epoch" ]; then upto="$END"; else upto="$(date '+%Y-%m-%dT%H:%M')"; fi
  snap="$SNAPS/snap-$(date '+%H%M').json"
  if python3 -I "$SCRIPT_DIR/collect.py" "$START" "$upto" > "$snap"; then
    python3 -I "$SCRIPT_DIR/analyze.py" "$snap" "$REPORT" 2>&1 | sed "s/^/[$(date '+%H:%M')] /"
  else
    echo "[$(date '+%H:%M')] collect failed"
  fi
  [ "$now_epoch" -ge "$end_epoch" ] && break
  left=$(( end_epoch - now_epoch ))
  step=$(( EVERY_MIN * 60 ))
  sleep $(( step < left ? step : left ))
done
echo "done: $REPORT"
