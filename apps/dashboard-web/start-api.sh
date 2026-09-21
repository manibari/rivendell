#!/usr/bin/env bash
# Stable entry used by existing service definitions.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/api/start.sh" "$@"
