---
name: tunnel-proxy-deploy
loop: dev
pdca: act
description: >
  Deploy FastAPI + Next.js behind Cloudflare Tunnel. Covers reverse proxy pitfalls,
  trailing slash redirects, CORS, port mapping, and end-to-end QA checklist.
  TRIGGER when: deploying FastAPI/Next.js behind Cloudflare Tunnel or any reverse proxy,
  debugging 307 redirects, CORS errors, or blank pages behind tunnel/nginx/caddy.
  DO NOT TRIGGER when: local development without reverse proxy.
tags: [backend, deploy, cloudflare, fastapi, nextjs]
version: 1
source: incident-2026-03-15
user_invocable: false
---

# Deploying FastAPI + Next.js Behind Cloudflare Tunnel

## Architecture

```
Browser → Cloudflare CDN → Tunnel → Next.js (:8503)
                                        ↓ rewrite /api/*
                                    FastAPI (:8001)
                                        ↓
                                    SQLite / Postgres
```

## Critical Issue: FastAPI 307 Trailing Slash Redirect

### Problem

FastAPI defaults to `redirect_slashes=True`. When a request hits `/api/nx/clients` (no trailing slash), FastAPI returns:

```
HTTP/1.1 307 Temporary Redirect
Location: http://127.0.0.1:8001/api/nx/clients/
```

This **breaks** behind a reverse proxy because:
1. The 307 redirect exposes the internal URL (`127.0.0.1:8001`) to the client browser
2. Browser tries to connect directly to `127.0.0.1:8001` over HTTPS — SSL fails
3. Result: all API calls fail silently, frontend shows blank/empty data

### Symptoms
- Pages load (HTML renders) but all data sections are empty
- Browser DevTools shows `net::ERR_CONNECTION_REFUSED` or SSL errors
- `curl -sL` from the server works fine (localhost), but external URL fails
- Redirect chain: `https://sales.phyra.uk/api/nx/clients` → 307 → `https://127.0.0.1:8001/api/nx/clients/` → SSL error

### Solution: TrailingSlashMiddleware

```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request

app = FastAPI(redirect_slashes=False)  # Disable built-in redirect

class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """Internally add trailing slash so routes match without 307 redirect."""
    async def dispatch(self, request: Request, call_next):
        path = request.scope["path"]
        if path.startswith("/api/") and not path.endswith("/") and "." not in path.split("/")[-1]:
            request.scope["path"] = path + "/"
        return await call_next(request)

app.add_middleware(TrailingSlashMiddleware)
```

Key points:
- `redirect_slashes=False` — prevents FastAPI from issuing 307
- Middleware internally rewrites the path — no HTTP redirect sent
- Skip paths with file extensions (`.json`, `.html`) to avoid breaking static files

### Why Not Just Fix the Frontend?

The frontend (`nexus-api.ts`) uses paths like `/api/nx/clients/` (with slash), but Next.js rewrite strips or doesn't preserve trailing slashes consistently. Fixing it at the backend middleware level is more robust.

## CORS Configuration for Tunnel

Always include the tunnel domain in CORS origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # local dev
        "http://localhost:8503",      # Next.js prod
        "https://sales.phyra.uk",    # tunnel domain
        "https://api.phyra.uk",      # API domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Next.js Rewrite Configuration

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8001/api/:path*",
      },
    ];
  },
};
```

- Use `127.0.0.1` instead of `localhost` to avoid IPv6 issues
- The rewrite is server-side (Next.js server proxies to FastAPI)
- Build (`next build`) is required after changing `next.config.ts`

## Cloudflare Tunnel Config

```yaml
# ~/.cloudflared/config.yml
ingress:
  - hostname: sales.phyra.uk
    service: http://localhost:8503    # Next.js (frontend + API proxy)
  - hostname: api.phyra.uk
    service: http://localhost:8001    # FastAPI (direct API access)
```

## Environment Variables

FastAPI won't auto-load `.env` files. Two options:

```bash
# Option 1: Source before starting (recommended for launchd/systemd)
set -a && source .env && set +a
uvicorn backend.main:app --host 0.0.0.0 --port 8001

# Option 2: Add python-dotenv to the app
from dotenv import load_dotenv
load_dotenv()
```

## Python Version Compatibility

- `list[str] | None` syntax requires Python 3.10+
- If deploying on older machines, install Python 3.12 via Homebrew:
  ```bash
  brew install python@3.12
  /opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv
  ```
- Always verify venv Python version matches: `.venv/bin/python3 --version`
- After recreating venv, kill old processes — they may hold the old port

## Node.js Version

- Next.js 15+ requires Node.js >= 18.18.0
- Install via Homebrew: `brew install node@22`
- Use full path: `/opt/homebrew/opt/node@22/bin/npx next build`

## QA Checklist for Tunnel Deploy

Run this checklist after every deploy:

```bash
# 1. Backend API (direct)
curl -s http://localhost:8001/api/nx/clients -w "\nHTTP: %{http_code}\n"

# 2. Frontend proxy (local)
curl -sL http://localhost:8503/api/nx/clients -w "\nHTTP: %{http_code}\n"

# 3. External via tunnel
curl -sL https://sales.phyra.uk/api/nx/clients -w "\nHTTP: %{http_code}\n"

# 4. Check no 307 redirects
curl -sv https://sales.phyra.uk/api/nx/clients 2>&1 | grep "< HTTP"
# Should show 200, NOT 307

# 5. Verify correct process on port
lsof -i :8503 -sTCP:LISTEN  # Should be node, not python
lsof -i :8001 -sTCP:LISTEN  # Should be python

# 6. Test all dashboard API endpoints
for ep in clients deals "deals/?view=urgency" "calendar/reminders" "tbd" "subsidies"; do
  echo "$ep: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/api/nx/$ep)"
done
```

## Common Gotchas

| Symptom | Cause | Fix |
|---------|-------|-----|
| Page loads but data is empty | API 307 redirect exposes localhost | Add TrailingSlashMiddleware |
| `TELEGRAM_BOT_TOKEN not set` | `.env` not loaded | `set -a && source .env` before uvicorn |
| `Port XXXX is not available` | Old process still running | `lsof -i :PORT -t \| xargs kill` |
| Wrong app on port (e.g. NBA instead of CRM) | Stale Python 3.9 process | Kill old process, rebuild venv with correct Python |
| `error 1033` on Cloudflare | Tunnel process died | Restart cloudflared; deeper tunnel ops → `[[cloudflare-tunnel-ops]]` |
| Next.js build fails | Wrong Node.js version | Use `/opt/homebrew/opt/node@22/bin/npx` |

## Related

This skill covers the **app layer** (307 / CORS / rewrites). For the tunnel itself:

- `[[cloudflare-tunnel-provision]]` — create a tunnel + DNS for a new domain from scratch (Cloudflare API, docker-compose).
- `[[cloudflare-tunnel-ops]]` — operate / move / troubleshoot an existing tunnel (error 1033, host migration, creds).
