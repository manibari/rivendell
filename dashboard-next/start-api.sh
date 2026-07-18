#!/usr/bin/env bash
# start-api.sh — Start the FastAPI backend for rivendell.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$DIR/api/.venv"

# Ensure venv exists
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# Install deps only when requirements.txt changes. `pip install` on every start
# means every boot (and every crash-loop restart under Restart=always) hits the
# network — so if the service starts before the network is up, pip fails, the
# script exits under `set -e`, and systemd just restarts into the same failure.
# Gating on a hash of requirements.txt makes steady-state startup fully offline;
# the network is only touched when the deps genuinely changed.
REQ="$DIR/api/requirements.txt"
STAMP="$VENV_DIR/.requirements.sha256"
want="$(sha256sum "$REQ" | cut -d' ' -f1)"
if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP" 2>/dev/null)" != "$want" ]; then
    "$VENV_DIR/bin/pip" install -q -r "$REQ"
    echo "$want" > "$STAMP"
fi

exec "$VENV_DIR/bin/uvicorn" server:app \
    --host 127.0.0.1 \
    --port 8000 \
    --app-dir "$DIR/api"
