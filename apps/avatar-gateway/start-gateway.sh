#!/usr/bin/env bash
# start-gateway.sh — Start the avatar-gateway (persona chat brain) on :8200.
# Pattern mirrors dashboard-next/start-api.sh: venv + requirements sha256 stamp
# so steady-state startup is fully offline (Restart=always safe).
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

REQ="$DIR/requirements.txt"
STAMP="$VENV_DIR/.requirements.sha256"
if command -v sha256sum >/dev/null 2>&1; then
    want="$(sha256sum "$REQ" | cut -d' ' -f1)"
elif command -v shasum >/dev/null 2>&1; then
    want="$(shasum -a 256 "$REQ" | cut -d' ' -f1)"
else
    want="always"
fi
have="$(cat "$STAMP" 2>/dev/null || true)"
if [ "$want" != "$have" ]; then
    "$VENV_DIR/bin/pip" install -q -r "$REQ"
    printf '%s' "$want" > "$STAMP"
fi

# claude / codex live under the user's local bins — systemd units may get a
# minimal PATH. Never pin a node version: pick up every nvm bin dir present.
export PATH="$HOME/.local/bin:$PATH"
for nvm_bin in "$HOME"/.nvm/versions/node/*/bin; do
    [ -d "$nvm_bin" ] && PATH="$nvm_bin:$PATH"
done
export PATH

exec "$VENV_DIR/bin/uvicorn" server:app --host 127.0.0.1 --port 8310 --app-dir "$DIR"
