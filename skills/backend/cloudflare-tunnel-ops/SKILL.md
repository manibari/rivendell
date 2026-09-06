---
name: cloudflare-tunnel-ops
loop: dev
pdca: act
description: >
  Operate, move, and troubleshoot an EXISTING Cloudflare Tunnel for a dockerized app —
  deploy to a new host (copy creds, no re-provision), debug error 1033 / dead container,
  fix DNS proxied/grey-cloud, rotate credentials, and reason about locally-managed vs
  dashboard-managed config.
  TRIGGER when: "tunnel is down / error 1033", site behind cloudflared returns 502/timeout,
  moving an app+tunnel to a new VM or host, cloudflared container won't connect, or the
  domain stopped resolving through the tunnel.
  DO NOT TRIGGER when: creating a brand-new tunnel + DNS from scratch (use
  cloudflare-tunnel-provision), or for app-layer 307/CORS issues (use tunnel-proxy-deploy).
tags: [backend, deploy, cloudflare, tunnel, troubleshooting, docker]
version: 1
source: family-fiscal + chimesflow deployments (2026-06)
user_invocable: true
---

# Operate & Troubleshoot an Existing Cloudflare Tunnel

For tunnels already created by `[[cloudflare-tunnel-provision]]`. The tunnel id, secret,
and DNS record persist on Cloudflare — most "ops" tasks are about the **local
cloudflared container + config**, not re-creating anything.

## Deploy / move a tunnel to a new host (no re-provision)

This is the ChimesFlow GCP-VM pattern: the tunnel + DNS already exist; you only move
the credentials. **Never re-create the tunnel just to run it elsewhere** — a tunnel can
run from any host that has its `<id>.json`.

```bash
# 1. copy the credentials JSON to the new host (it is gitignored, so scp it)
scp ./cloudflared/<TUNNEL_ID>.json <vm>:~/<project>/cloudflared/

# 2. on the new host: provide config.yml (commit a config.yml.example to copy from)
cp cloudflared/config.yml.example cloudflared/config.yml

# 3. start it
docker compose up -d cloudflared
docker compose logs --tail=20 cloudflared   # expect: "Registered tunnel connection"
```

Running the same tunnel from two hosts at once is allowed (Cloudflare load-balances the
connections) — but for a single-origin app, stop the old host's cloudflared after cutover.

## Quick diagnosis order

```bash
docker compose ps cloudflared                         # is it even up?
docker compose logs --tail=50 cloudflared             # connection errors / config parse
curl -s http://<service>:<port> -o /dev/null -w '%{http_code}\n'   # from a sibling container
curl -sL https://<host> -o /dev/null -w '%{http_code}\n'           # external, through the edge
dig +short <host>                                     # CNAME -> <id>.cfargotunnel.com ?
```

## Symptom → cause → fix

| Symptom | Cause | Fix |
|---------|-------|-----|
| Browser `error 1033` ("Argo Tunnel error") | cloudflared not connected to the edge | Container down / crash-looping, or bad creds. `docker compose up -d cloudflared`; check logs for "Unauthorized" → wrong `<id>.json`. |
| 502 / timeout through the tunnel, but app is up | `ingress.service` wrong | Must be the **compose service name + port** (`http://frontend:3010`), reachable on the compose network — not `localhost` (that's the cloudflared container itself). |
| DNS resolves but bypasses the tunnel / cert errors | CNAME is **grey-cloud** (not proxied) | Set the record `proxied: true` (orange cloud). |
| `<id>.cfargotunnel.com` not found | DNS record deleted or wrong tunnel id | Recreate CNAME `<host> → <id>.cfargotunnel.com` proxied (see provision step 5). |
| cloudflared logs "config parse" / starts then exits | `config.yml` not mounted or malformed | Volume must be `./cloudflared:/etc/cloudflared:ro`; `credentials-file` path must be the **in-container** path `/etc/cloudflared/<id>.json`. |
| Works locally, dies after `git pull` redeploy | creds/config got wiped or were never on this host | They're gitignored — they must exist on the host out-of-band; don't expect git to carry them. |
| Need to invalidate a leaked secret | Locally-managed secret can't be rotated in place | Delete the tunnel (`DELETE /accounts/<acct>/cfd_tunnel/<id>`) and re-run `[[cloudflare-tunnel-provision]]` — it issues a fresh secret + updates the CNAME. |

## Locally-managed vs dashboard-managed (don't mix)

Our tunnels are **locally-managed** (`config_src: local`): the `config.yml` on the host
is the source of truth for ingress. If you also edit ingress in the Cloudflare dashboard,
it's ignored (or conflicts). Keep all ingress changes in `cloudflared/config.yml` and
restart the container: `docker compose restart cloudflared`.

## Useful one-liners

```bash
# list tunnels on the account
curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/<acct>/cfd_tunnel?is_deleted=false" \
  | python3 -m json.tool

# show a tunnel's current connections (is it actually up on the edge?)
curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/<acct>/cfd_tunnel/<id>/connections" \
  | python3 -m json.tool
```

## Related

- `[[cloudflare-tunnel-provision]]` — create a tunnel + DNS from scratch.
- `[[tunnel-proxy-deploy]]` — app-layer issues once the tunnel works (307, CORS, rewrites).
