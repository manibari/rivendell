#!/usr/bin/env bash
# rivendell dashboard redeploy — FOR WSL SELF-HOST ONLY.
#
# Pulls origin/main, rebuilds the Next web bundle, restarts the two systemd user
# services. Single-flight via flock. Emits "ERR:" lines on failure so ops/check.sh
# (or another dashboard) can surface a broken deploy — same convention as
# ~/code/ChimesFlow/scripts/deploy/wsl/chimesflow-redeploy.sh.
#
# Run it from cron (see crontab.sample) for git-poll auto-deploy.
set -uo pipefail

REPO="${RIVENDELL_DIR:-$HOME/code/rivendell}"
LOG="${DASHBOARD_REDEPLOY_LOG:-$HOME/rivendell-dashboard-redeploy.log}"
LOCK="/tmp/rivendell-dashboard-redeploy.lock"
# Which branch prod tracks. Defaults to main; set DASHBOARD_DEPLOY_BRANCH to a
# feature branch while its work hasn't landed on main yet (e.g. chore/skill-quality
# until the port-map parallel work is merged). The local checkout must be ON this
# branch — see README.
BRANCH="${DASHBOARD_DEPLOY_BRANCH:-main}"

exec 9>"$LOCK"
flock -n 9 || { echo "SKIP: another redeploy is in progress"; exit 0; }

ts()  { date '+%F %T'; }
log() { echo "$(ts) $*" | tee -a "$LOG"; }

cd "$REPO" || { log "ERR: cannot cd $REPO"; exit 1; }

if [ -n "$(git status --porcelain --untracked-files=no 2>/dev/null)" ]; then
  log "ERR: working tree dirty — refusing to deploy. Resolve on the host, then re-run."
  exit 1
fi

before=$(git rev-parse HEAD 2>/dev/null || echo "")
git fetch --quiet origin "$BRANCH" || { log "ERR: git fetch failed ($BRANCH)"; exit 1; }
git merge --ff-only "origin/$BRANCH" || { log "ERR: ff-only merge failed — local checkout not on $BRANCH, or diverged"; exit 1; }
after=$(git rev-parse HEAD 2>/dev/null || echo "")

if [ "$before" = "$after" ]; then
  log "no change ($after) — nothing to redeploy"
  exit 0
fi
log "redeploying $before -> $after"

# Clean rebuild of the Next web (.next is atomic — never partially delete).
if ! ( cd dashboard-next && rm -rf .next && npm ci --silent && npm run build ) >>"$LOG" 2>&1; then
  log "ERR: web build failed — leaving the running services up on the old build"
  exit 1
fi

# Restart both user services (api has no build step; web now has a fresh .next).
if ! systemctl --user restart rivendell-dashboard-api rivendell-dashboard-web; then
  log "ERR: systemctl --user restart failed"
  exit 1
fi

log "redeploy OK ($after)"
