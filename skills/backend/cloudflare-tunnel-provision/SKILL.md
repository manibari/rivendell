---
name: cloudflare-tunnel-provision
description: >
  Stand up a brand-new public domain for a self-hosted dockerized app behind a
  Cloudflare Tunnel, from scratch, via the Cloudflare API — no dashboard clicking.
  Covers API token scopes, creating a locally-managed tunnel, writing credentials +
  config.yml, the DNS CNAME → cfargotunnel.com record, and wiring the cloudflared
  container into docker-compose.
  TRIGGER when: exposing a new subdomain (e.g. foo.phyra.uk) for a docker-compose app,
  "set up a cloudflare tunnel / domain for <project>", adding cloudflared to a stack,
  or scripting tunnel+DNS provisioning.
  DO NOT TRIGGER when: the tunnel + DNS already exist and you only need to deploy/move/
  debug it (use cloudflare-tunnel-ops), or for app-layer proxy bugs like 307/CORS
  (use tunnel-proxy-deploy).
tags: [backend, deploy, cloudflare, tunnel, dns, docker]
version: 1
source: family-fiscal + chimesflow deployments (2026-06)
user_invocable: true
---

# Provision a Cloudflare Tunnel + Domain for a Dockerized App

Stand up `https://<host>.<zone>` → Cloudflare Tunnel → your `cloudflared` container →
sibling app container, end to end. Reference implementation:
`~/bin/family-fiscal-tunnel-setup.sh` (one-shot, idempotent). This skill generalizes it.

## Architecture (what you're building)

```
Browser → Cloudflare edge (proxied DNS) → Tunnel (<id>.cfargotunnel.com)
            → cloudflared container → http://<service>:<port> (compose network)
```

Two host patterns seen in practice:
- **WSL self-host** (Family-Fiscal): everything provisioned by API script on the box.
- **GCP VM** (ChimesFlow): tunnel + DNS created once, then only credentials are copied
  to the VM and the container started. See `cloudflare-tunnel-ops` for that path.

## Prerequisites

- A zone already on Cloudflare (e.g. `phyra.uk`). All our apps share **one account**
  (account tag `50483b2af2b0b1926e69332ce7be4717`) and the `phyra.uk` zone.
- An **API token** with exactly these scopes — nothing more:
  - `Account → Cloudflare Tunnel → Edit`
  - `Zone → DNS → Edit` (scoped to the target zone)
  Export it as `CF_API_TOKEN`. The script verifies `/user/tokens/verify` returns
  `"status":"active"` before doing anything.

## Steps

The reference script `references/provision-tunnel.sh` does all of this idempotently.
Parameterize it with `HOST`, `TUNNEL_NAME`, `PROJ`, and the upstream `SERVICE:PORT`.

1. **Verify token** → `GET /user/tokens/verify` (`"status":"active"`).
2. **Resolve IDs** → account id from `GET /accounts`, zone id from
   `GET /zones?name=<zone>`.
3. **Create a locally-managed tunnel** → `POST /accounts/<acct>/cfd_tunnel` with
   `{"name","tunnel_secret","config_src":"local"}`. The secret is
   `base64(random 32 bytes)` — generate once and **keep it** (see Gotchas).
4. **Write credentials + config** into `<proj>/cloudflared/`:
   - `<tunnel-id>.json` → `{"AccountTag","TunnelID","TunnelSecret"}`
   - `config.yml`:
     ```yaml
     tunnel: <tunnel-id>
     credentials-file: /etc/cloudflared/<tunnel-id>.json
     ingress:
       - hostname: <host>            # e.g. family-fiscal.phyra.uk
         service: http://frontend:3010   # compose SERVICE name + port, NOT localhost
       - service: http_status:404
     ```
5. **Create the DNS record** → CNAME `<host>` → `<tunnel-id>.cfargotunnel.com`,
   **`proxied: true`** (orange cloud — mandatory for tunnels). PUT if it exists, POST
   if not (idempotent).
6. **Wire `cloudflared` into docker-compose** (see Compose snippet) and bring it up:
   `docker compose up -d cloudflared`.
7. **Verify** → `docker compose logs cloudflared` shows "Registered tunnel connection";
   `curl -sL https://<host> -o /dev/null -w '%{http_code}'` returns 200.

## Compose snippet (committed to the repo)

```yaml
  cloudflared:
    image: cloudflare/cloudflared:latest
    restart: unless-stopped
    depends_on:
      - frontend
    command: tunnel --config /etc/cloudflared/config.yml --no-autoupdate run
    volumes:
      - ./cloudflared:/etc/cloudflared:ro
```

The `ingress.service` host (`frontend:3010`, `chimesflow `frontend:8080`) is the
**compose service name**, resolved over the compose network — cloudflared runs in its
own container, so `localhost` would point at the cloudflared container itself, not your app.

## Secrets hygiene (do this or you'll leak the tunnel)

`cloudflared/<id>.json` contains `TunnelSecret` — anyone with it can run your tunnel.
Both projects gitignore the live files and commit only an example:

```gitignore
cloudflared/*.json
cloudflared/config.yml
```

Commit `cloudflared/config.yml.example` (no secret) so the layout is documented; keep
the real `config.yml` and `<id>.json` local-only.

## Gotchas

| Symptom | Cause | Fix |
|---------|-------|-----|
| Re-running "create tunnel" by name returns no id | A tunnel with that name already exists | You **cannot recover the original secret**. Either reuse the existing `<id>.json` you kept, or delete the old tunnel (`DELETE /cfd_tunnel/<id>`) and recreate. The script aborts on secret mismatch rather than writing a broken creds file. |
| `error 1033` in browser | Tunnel not connected / origin unreachable | `cloudflared` container down, wrong `service:port`, or app container not up. See `cloudflare-tunnel-ops`. |
| DNS resolves but 5xx/timeout | DNS record not **proxied** | Set `proxied: true` (orange cloud) — a grey-cloud CNAME bypasses the tunnel. |
| `localhost`/`127.0.0.1` in ingress doesn't reach the app | cloudflared is a separate container | Use the compose **service name**, not localhost. |
| Page loads but API data empty (307 / CORS) | App-layer reverse-proxy issue | Out of scope here → use `[[tunnel-proxy-deploy]]`. |

## Related

- `[[tunnel-proxy-deploy]]` — app-layer pitfalls once the tunnel is up (307 trailing
  slash, CORS, Next.js rewrites, QA checklist).
- `[[cloudflare-tunnel-ops]]` — deploy/move/rotate/debug an existing tunnel.
