#!/usr/bin/env bash
# start-web.sh — Build (if needed) and start the Next.js frontend.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Resolve node fresh each launch. The service unit's PATH is written once and
# survives reboots, so baking in a versioned nvm dir (…/v24.13.0/bin) means the
# next `nvm install` silently deletes node out from under a running service. If
# node isn't already on PATH, load nvm — which prepends whatever `default`
# points at — so the toolchain tracks the user's current node, not a frozen one.
if ! command -v node >/dev/null 2>&1; then
    export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
    # shellcheck disable=SC1091
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" --no-use && nvm use --silent default
fi

# Install deps if node_modules missing
if [ ! -d "node_modules" ]; then
    npm install
fi

# Rebuild if the build sentinel is missing or any source/config is newer.
# The sentinel is touched only after `npm run build` exits 0, so a build that
# was interrupted (SIGKILL, OOM, Ctrl-C, disk full) leaves no sentinel and we
# rebuild on next launch. `BUILD_ID` alone is not enough — Next can write it
# before all chunks are flushed, leading to "Cannot find module" 500s.
SENTINEL=".next/.build-complete"
if [ ! -f "$SENTINEL" ] || [ -n "$(find src next.config.ts package.json -newer "$SENTINEL" 2>/dev/null)" ]; then
    rm -rf .next
    npm run build
    touch "$SENTINEL"
fi

exec npx next start -p 3000
