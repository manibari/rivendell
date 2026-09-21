#!/usr/bin/env bash
# Stable entry for the legacy Streamlit deployment.
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$REPO_DIR/platform/deployment/legacy-streamlit-deploy.sh" "$@"
