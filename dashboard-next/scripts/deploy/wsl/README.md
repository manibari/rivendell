# Dashboard on WSL — self-host deploy (A2b)

Run the rivendell dashboard on the always-on **WSL** host so 部署管理 becomes the
**prod deployment monitor**. On WSL the dashboard sees the real prod containers
(`docker ps` natively) and reaches each app's health endpoint on `localhost` —
the two things the mac copy can't do for WSL-hosted apps.

> ⚠️ **Untested from the mac.** This scaffolding mirrors the mac launchd setup +
> ChimesFlow's proven `scripts/deploy/wsl/` git-poll pattern, but the WSL-specific
> steps (systemd-in-WSL, lingering, docker-under-systemd) must be verified on the
> host. Treat the first run as a smoke test.

## Why native processes, not a container

The dashboard's value here depends on host-local access:
- **`/api/ports` docker overlay** shells out to `docker ps` / `docker inspect`.
- **Deployment health** curls each app's health URL, several on `localhost`
  (e.g. family-fiscal `localhost:8020`).

Running the dashboard as plain processes on the WSL host (the same `start-api.sh`
/ `start-web.sh` the mac uses) gets both for free. Containerising it would mean
mounting the docker socket + host networking + a docker CLI in the image — more
moving parts, no benefit here.

## Prerequisites

- Node ≥ 20, Python ≥ 3.11, `docker` usable from your WSL shell (`docker ps` works).
- `~/code/rivendell` cloned on the WSL host (this repo), **checked out to the
  deploy branch**. The /ports → 部署管理 work currently lives on
  `chore/skill-quality` (not yet merged to main — a parallel session is finishing
  related port-map work). So: `git checkout chore/skill-quality`, and the
  `crontab.sample` sets `DASHBOARD_DEPLOY_BRANCH=chore/skill-quality`. Once that
  work lands on main, flip both back to main.
- `~/projects/ops/monitors.toml` present (the shared health SoT; clone `manibari/ops`).
- WSL **systemd enabled** — `/etc/wsl.conf`:
  ```
  [boot]
  systemd=true
  ```
  then `wsl --shutdown` from Windows and reopen. Verify: `systemctl --user status`.

## Install

```bash
cd ~/code/rivendell/dashboard-next/scripts/deploy/wsl

# 1. user services
mkdir -p ~/.config/systemd/user
cp systemd/rivendell-dashboard-*.service ~/.config/systemd/user/

# 2. health keys (for keyed apps; chmod 600, never in git)
mkdir -p ~/.config/rivendell-dashboard
cat > ~/.config/rivendell-dashboard/env <<'EOF'
OPS_KEY_FAMILY_FISCAL=<same value as family-fiscal backend HEALTH_KEY>
EOF
chmod 600 ~/.config/rivendell-dashboard/env

# 3. keep user services running without an active login session
loginctl enable-linger "$USER"

# 4. enable + start
systemctl --user daemon-reload
systemctl --user enable --now rivendell-dashboard-api rivendell-dashboard-web

# 5. smoke test
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/api/ports   # expect 200
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/ports        # expect 200

# 6. git-poll auto-deploy
chmod +x dashboard-redeploy.sh
crontab crontab.sample
```

## What you should see

On WSL, 部署管理 now lists the **prod** containers (chimesflow / family-fiscal /
…) with their source folder, and a **health badge** per project that reflects a
real probe: family-fiscal turns from `unknown` (on the mac) to `healthy` here,
because `localhost:8020/api/health` is reachable. A failed redeploy writes `ERR:`
to `~/rivendell-dashboard-redeploy.log`, which the health check surfaces.

## WSL gotchas (read before "it's not working")

- **systemd user services need lingering.** Without `loginctl enable-linger`,
  `systemctl --user` units stop when you close the WSL shell. Step 3 fixes it.
- **docker under systemd.** Confirm `docker ps` works in the unit's environment,
  not just your interactive shell (Docker Desktop WSL-integration vs native
  dockerd differ). If empty under the service but fine interactively, start/expose
  docker before the units.
- **CRLF.** If these scripts were touched on Windows and you get `\r: command not
  found`, run `sed -i 's/\r$//' dashboard-redeploy.sh`.
- **`.next` is atomic.** `dashboard-redeploy.sh` does `rm -rf .next && npm run
  build` (never a partial delete) — keep it that way.
- **Don't also run the mac copy against the same data.** This is a separate prod
  instance; it monitors WSL. The mac launchd copy keeps monitoring the mac.
- **Tunnel / cross-machine access just works.** The web app calls `/api/*` on its
  own origin; `next.config.ts` proxies that to the backend server-side. So opening
  the WSL dashboard from another machine through a tunnel needs **no** config — no
  `NEXT_PUBLIC_API_URL` (which would have pinned the client to loopback). Only set
  `API_PROXY_TARGET` if the FastAPI backend is NOT on `127.0.0.1:8000` of the same
  host as the web process.
