#!/usr/bin/env bash
# deploy.sh — Pull latest code from GitHub and restart the dashboard.
# Run this on the remote machine. Can be triggered by cron, launchd, or GitHub webhook.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
VENV_DIR="$REPO_DIR/.venv"
DASHBOARD_DIR="$REPO_DIR/apps/dashboard-legacy"
LOG_FILE="$REPO_DIR/deploy.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

cd "$REPO_DIR"

# Pull latest changes
log "Pulling latest from origin..."
git fetch origin
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    log "Already up to date ($LOCAL). Skipping."
    exit 0
fi

git pull origin main
log "Updated: $LOCAL → $REMOTE"

# Set up or update venv
if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

log "Installing dependencies..."
"$VENV_DIR/bin/pip" install -q -r "$DASHBOARD_DIR/requirements.txt"

# Restart Streamlit
log "Restarting Streamlit..."
pkill -f "streamlit run $DASHBOARD_DIR/app.py" 2>/dev/null || true
sleep 1
nohup "$VENV_DIR/bin/streamlit" run "$DASHBOARD_DIR/app.py" \
    >> "$REPO_DIR/streamlit.log" 2>&1 &
DASHBOARD_PID=$!
log "Dashboard started (PID=$DASHBOARD_PID)"
log "Deploy complete."
