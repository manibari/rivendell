---
name: docker-compose-setup
loop: dev
pdca: do
description: >
  Set up Docker Compose for multi-service projects (Next.js + FastAPI + Postgres/Redis).
  Generates Dockerfiles, docker-compose.yml (dev + prod), .env.example, .dockerignore,
  and healthchecks. TRIGGER when: user says "用 docker 包裝", "一鍵啟動", "containerize",
  "docker-compose", "幫我加 Docker", "打包成 container", "docker 部署", "Docker 設定".
  DO NOT TRIGGER when: user is asking about cloud deployment platforms (use deploy skill)
  or GitHub Actions CI/CD (use ci-pipeline skill).
tags: [backend, deploy]
version: 2.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Docker Compose Setup

Multi-service containerization for local dev and production.

## Step 1: Detect Project Stack

```bash
# Find services
ls */package.json */pyproject.toml */requirements.txt 2>/dev/null
grep -r "next\|react\|vue\|nuxt" */package.json 2>/dev/null | head -3
grep -r "fastapi\|flask\|django\|express" */pyproject.toml */requirements.txt */package.json 2>/dev/null | head -3
```

Map each detected service to a Dockerfile pattern:
| Stack | Dockerfile pattern |
|-------|--------------------|
| Next.js | Multi-stage: deps -> builder -> runner (node:22-alpine) |
| FastAPI / Python | Multi-stage: builder (uv) -> runner (python:3.12-slim) |
| Express / Node | Multi-stage: deps -> builder -> runner (node:22-alpine) |
| Postgres | Use official image, no custom Dockerfile |
| Redis | Use official image, no custom Dockerfile |

---

## Step 2: Dockerfiles

### Multi-Stage Build Decision Tree

```
Need to build/compile code in the container?
  YES --> Use multi-stage (builder + runtime)
  NO  --> Does the image include dev dependencies or build tools?
    YES --> Use multi-stage to separate them
    NO  --> Single stage MAY be acceptable for simple runtime images

Choosing the final stage base:
  Static binary (Go CGO_ENABLED=0, Rust musl)?
    YES --> scratch or distroless/static-debian12
    NO  --> Need a shell? --> alpine or *-slim variant
            No shell needed? --> distroless/base-debian12
```

### Image Size Impact (multi-stage vs single-stage)

| Language | Without Multi-Stage | With Multi-Stage | Reduction |
|----------|-------------------|-----------------|-----------|
| Go | ~800 MB | ~7 MB (alpine) | 99% |
| Node.js | ~1.1 GB | ~180 MB (slim) | 83% |
| Python | ~1.0 GB | ~150 MB (slim) | 85% |

### Next.js (multi-stage)

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* yarn.lock* package-lock.json* ./
RUN corepack enable 2>/dev/null || true && \
    if [ -f pnpm-lock.yaml ]; then pnpm install --frozen-lockfile; \
    elif [ -f yarn.lock ]; then yarn --frozen-lockfile; \
    else npm ci; fi

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN corepack enable 2>/dev/null || true && \
    if [ -f pnpm-lock.yaml ]; then pnpm build; \
    elif [ -f yarn.lock ]; then yarn build; \
    else npm run build; fi

FROM node:22-alpine AS runner
WORKDIR /app
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
USER 1001:1001
EXPOSE 3000
ENV NODE_ENV=production PORT=3000 HOSTNAME="0.0.0.0"
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1
CMD ["node", "server.js"]
```

### FastAPI / Python (uv)

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-slim AS runner
WORKDIR /app
RUN groupadd -r -g 1001 appgroup && \
    useradd --no-log-init -r -u 1001 -g appgroup appuser
COPY --from=builder /app/.venv ./.venv
COPY . .
USER 1001:1001
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

> For `requirements.txt` projects: replace `uv sync` with `pip install -r requirements.txt --target /app/.venv/lib`.

---

## Step 3: docker-compose.yml

```yaml
# docker-compose.yml  (production)
services:
  web:
    build:
      context: ./frontend          # adjust to actual dir
      target: runner
    ports:
      - "${WEB_PORT:-3000}:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000
    depends_on:
      api:
        condition: service_healthy
    read_only: true
    tmpfs:
      - /tmp:size=64m
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges=true
    restart: unless-stopped

  api:
    build:
      context: ./backend           # adjust to actual dir
      target: runner
    ports:
      - "${API_PORT:-8000}:8000"
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REPORTS_DIR=/data/reports
    volumes:
      - reports:/data/reports
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s
    read_only: true
    tmpfs:
      - /tmp:size=64m
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges=true
    deploy:
      resources:
        limits:
          memory: 512m
          cpus: "1.5"
          pids: 200
    restart: unless-stopped

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-myapp}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
      - FOWNER
      - DAC_READ_SEARCH
    security_opt:
      - no-new-privileges=true
    deploy:
      resources:
        limits:
          memory: 256m
          cpus: "1.0"
    restart: unless-stopped

volumes:
  pgdata:
  reports:
```

### docker-compose.dev.yml (override for local dev)

```yaml
# docker-compose.dev.yml
services:
  web:
    build:
      target: deps          # use deps stage for hot reload
    volumes:
      - ./frontend:/app
      - /app/node_modules   # keep container node_modules
    environment:
      - NODE_ENV=development
      - WATCHPACK_POLLING=true   # required for file watching on macOS Docker
    command: npm run dev
    read_only: false
    cap_drop: []
    deploy: {}

  api:
    volumes:
      - ./backend:/app      # live reload via uvicorn --reload
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    read_only: false
    cap_drop: []
    deploy: {}
```

Run dev: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`

---

## Step 4: .env.example

```bash
# Auto-generate from docker-compose.yml env references
grep -oP '\$\{[A-Z_]+[^}]*\}' docker-compose.yml | sort -u | \
  sed 's/\${\([^:}]*\)[^}]*}/\1=/' > .env.example
```

Always include these at minimum:
```
POSTGRES_DB=myapp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
WEB_PORT=3000
API_PORT=8000
```

---

## Step 5: .dockerignore

```
# Version control
.git
.gitignore
.gitattributes

# Dependencies (rebuilt inside container)
node_modules
__pycache__
*.pyc
.venv

# Build artifacts
.next
dist
coverage
.pytest_cache

# Docker files (not needed in build context)
Dockerfile*
docker-compose*.yml
.dockerignore

# Environment and secrets
.env
.env.*
*.pem
*.key

# IDE and OS files
.vscode
.idea
*.swp
.DS_Store

# Documentation
*.md
LICENSE
docs/

# Test and CI
.github
tests/
```

---

## Step 6: Verify

```bash
# Validate compose file first (ALWAYS do this)
docker compose config -q

# Build and start
docker compose build --no-cache
docker compose up -d

# Check all services healthy
docker compose ps

# Spot-check API
curl http://localhost:${API_PORT:-8000}/health

# View logs
docker compose logs -f api
```

---

## Security Hardening Checklist

Apply to EVERY production container:

### Dockerfile Security (MUST)

- [ ] Non-root USER with explicit UID/GID (ALWAYS use `USER 1001:1001`)
- [ ] No secrets in ENV, ARG, or COPY layers (use `--mount=type=secret` for build-time secrets)
- [ ] Pinned base image tags (consider digest pinning for critical services)
- [ ] `# syntax=docker/dockerfile:1` as first line (enables BuildKit features)
- [ ] HEALTHCHECK instruction defined
- [ ] Exec form for ENTRYPOINT/CMD (NOT shell form -- shell form breaks signal handling)

### Compose Security (MUST)

- [ ] `cap_drop: ALL` on every service (add back only what is needed)
- [ ] `security_opt: no-new-privileges=true` on every service
- [ ] `read_only: true` with `tmpfs` for writable paths
- [ ] `depends_on` with `condition: service_healthy` (NEVER use bare `depends_on`)
- [ ] Resource limits: `memory`, `cpus`, `pids`

### Compose Security (SHOULD)

- [ ] `NEVER` use `--privileged` (use specific `--cap-add` instead)
- [ ] `NEVER` use `latest` tag in production
- [ ] `NEVER` store secrets in environment variables for passwords/tokens (use Docker secrets or mounted files)
- [ ] `NEVER` use `container_name` on services you intend to scale

---

## Anti-Pattern Catalog

### Dockerfile Anti-Patterns

| Anti-Pattern | Why It Is Bad | Correct Pattern |
|---|---|---|
| `COPY . .` before `RUN npm install` | ANY file change invalidates cache, forces full reinstall | Copy lockfile first, install deps, THEN copy source |
| Separate `RUN apt-get update` and `RUN apt-get install` | Cached `update` layer becomes stale | ALWAYS combine: `RUN apt-get update && apt-get install -y pkg` |
| No `.dockerignore` file | Entire context (`.git/`, `node_modules/`) sent to builder | ALWAYS create `.dockerignore` -- see Step 5 |
| `ENTRYPOINT /usr/bin/app` (shell form) | App runs under `/bin/sh -c`, does NOT receive SIGTERM | Use exec form: `ENTRYPOINT ["/usr/bin/app"]` |
| Installing curl/vim in production image | Increases attack surface | Keep debug tools in a separate `--target debug` stage |
| `RUN pip install` without `--no-cache-dir` | pip cache bloats image layer | Use `--mount=type=cache` or `--no-cache-dir` |
| Running as root (no USER instruction) | Compromised process can escalate to host root | ALWAYS add `USER 1001:1001` |
| Using `docker commit` for production images | Unreproducible, undocumented images | ALWAYS use Dockerfiles |

### Compose Anti-Patterns

| Anti-Pattern | Why It Is Bad | Correct Pattern |
|---|---|---|
| `version: "3.8"` in compose file | Deprecated and ignored by Compose v2 | Remove `version:` entirely |
| Bare `depends_on: [db]` | Only waits for container start, NOT readiness | Use `depends_on: db: condition: service_healthy` |
| Hardcoded container IPs | IPs change on restart | Use service names for DNS resolution |
| `--link` for service communication | Legacy, deprecated | Use user-defined networks (Compose default) |
| Port `-p` for container-to-container communication | Unnecessary, adds exposure | Containers on same network reach all ports directly |
| No resource limits in production | Container can consume all host resources | ALWAYS set memory, cpus, pids limits |
| `COMPOSE_PROFILES` not used for optional services | Debug/admin tools start in production | Use `profiles: [debug]` to gate optional services |

---

## Build Optimization

### Cache Mount Patterns

Cache mounts persist package manager caches across builds -- only new/changed packages download:

```dockerfile
# npm
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

# pnpm
COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.local/share/pnpm/store pnpm install --frozen-lockfile

# pip / uv
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

# apt-get (ALWAYS use sharing=locked)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends curl
```

### Instruction Ordering (Critical for Cache Efficiency)

Order from LEAST to MOST frequently changed:

```
FROM base-image                    (rarely changes)
RUN install system packages        (rarely changes)
COPY package.json / pyproject.toml (dep changes)
RUN install dependencies           (dep changes)
COPY . .                           (every commit)
RUN build application              (every commit)
CMD / ENTRYPOINT                   (rarely changes)
```

**Rule:** Once ANY layer's cache is invalidated, ALL subsequent layers MUST rebuild.

### CI/CD Cache Backend

```yaml
# GitHub Actions
- uses: docker/build-push-action@v7
  with:
    push: true
    tags: user/app:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

ALWAYS use `mode=max` in CI to cache ALL intermediate layers.

---

## Compose Watch (Hot Reload Alternative)

Modern alternative to volume mounts for dev -- built into Compose v2.22+:

```yaml
services:
  web:
    build: ./frontend
    develop:
      watch:
        - action: sync
          path: ./frontend/src
          target: /app/src
          ignore:
            - node_modules/
        - action: rebuild
          path: ./frontend/package.json

  api:
    build: ./backend
    develop:
      watch:
        - action: sync+restart
          path: ./backend
          target: /app
          ignore:
            - __pycache__/
            - .venv/
```

| Action | When to Use |
|--------|-------------|
| `sync` | Source code changes (interpreted languages, hot-reload frameworks) |
| `rebuild` | Dependency changes (package.json, pyproject.toml) |
| `sync+restart` | Config file changes (needs process restart) |

Run: `docker compose up --watch`

---

## Error Diagnostic Decision Tree

### Compose File Won't Parse

```
docker compose config fails
+-- YAML syntax error?
|   +-- Check indentation (spaces only, NEVER tabs)
|   +-- Check colons have space after them
|   +-- Check strings with special chars are quoted
+-- Variable interpolation error?
|   +-- Unset variable? --> Use ${VAR:-default} or set in .env
|   +-- Dollar sign in value? --> Escape with $$ (e.g., $$HOME)
+-- Unknown attribute?
    +-- Check spelling and indentation level
```

### Services Won't Start

```
docker compose up fails
+-- Port conflict?
|   +-- "port is already allocated" --> lsof -i :PORT
+-- Dependency failure?
|   +-- "dependency failed to start" --> Check dependent service logs
|   +-- Healthcheck timeout --> Increase interval/retries/start_period
+-- Build failure?
|   +-- "build path does not exist" --> Check context path
|   +-- "file not found in build context" --> Check .dockerignore
+-- Exit code 137?
|   +-- OOMKilled=true --> Increase memory limit
|   +-- OOMKilled=false --> Check docker events + stop timeout
+-- Exit code 127?
    +-- Binary not found --> Check CMD path, verify binary exists in image
```

### Container Runtime Issues

| Exit Code | Meaning | Common Cause |
|-----------|---------|--------------|
| 0 | Success / premature exit | Process daemonized instead of running in foreground |
| 1 | Application error | Missing env vars, config errors -- check `docker logs` |
| 125 | Docker daemon error | Invalid config, missing image |
| 126 | Command not executable | Permission denied on entrypoint |
| 127 | Command not found | Binary missing, wrong PATH, typo in CMD |
| 137 | SIGKILL (OOM or forced stop) | Memory limit exceeded or `docker stop` timeout |
| 143 | SIGTERM (graceful stop) | Normal `docker stop` behavior |

---

## Networking Patterns

### Rule: ALWAYS use service names for DNS

Containers on the same Compose network resolve each other by service name automatically.
NEVER hardcode IPs. NEVER use `--link`.

### Isolated Backend Network

```yaml
services:
  web:
    networks:
      - frontend
      - backend
  api:
    networks:
      - backend
  db:
    networks:
      - backend  # NOT accessible from frontend

networks:
  frontend:
  backend:
    internal: true  # no external internet access
```

### Container Cannot Connect to Another Service

```
Check: Are they on the same network?
  NO  --> Add both to the same network in compose
  YES --> Is the target listening on 0.0.0.0?
    NO  --> Fix: NEVER bind to 127.0.0.1 inside a container
    YES --> Is the target healthy?
      NO  --> Check logs: docker compose logs <service>
      YES --> DNS issue: docker compose exec <svc> nslookup <target>
```

---

## Common Issues

| Issue | Fix |
|-------|-----|
| Port already in use | Check `port-map.html`, change `WEB_PORT`/`API_PORT` in `.env` |
| `Path(__file__).parent*N` wrong in container | Use env var: `Path(os.environ.get("REPORTS_DIR", fallback))` |
| node_modules conflict | Mount override: `- /app/node_modules` in volumes |
| Hot reload not working | Ensure dev override is loaded; check `WATCHPACK_POLLING=true` for Docker on macOS |
| DB connection refused | Add `depends_on: db: condition: service_healthy`; verify `pg_isready` healthcheck |
| `exec format error` | Architecture mismatch -- build for correct platform: `docker buildx build --platform linux/amd64` |
| `Read-only file system` | Add `tmpfs` for writable paths or mount a volume for data dirs |
| Container exits immediately (code 0) | Main process runs in background -- run in foreground mode |
| `no space left on device` | Run `docker system prune`. Write data to volumes, not container layer |
| Stale apt cache in layers | ALWAYS combine `apt-get update && apt-get install` in one RUN |

---

## Environment Variable Precedence (Highest to Lowest)

| Priority | Source |
|----------|--------|
| 1 (highest) | `docker compose run -e` CLI flag |
| 2 | Shell/interpolation in `environment` |
| 3 | `environment` attribute in compose.yaml |
| 4 | `env_file` attribute files |
| 5 (lowest) | Image `ENV` directive |

### Interpolation Syntax

| Syntax | Behavior |
|--------|----------|
| `${VAR:-default}` | Use `default` if VAR is unset or empty |
| `${VAR-default}` | Use `default` only if VAR is unset |
| `${VAR:?error}` | Error if VAR is unset or empty |
| `$$` | Literal `$` sign (escape) |

---

## References

See [references/security-hardening.md](references/security-hardening.md) for the full security checklist.
See [references/anti-patterns.md](references/anti-patterns.md) for expanded anti-pattern catalog with exploit scenarios.
See [references/build-optimization.md](references/build-optimization.md) for CI/CD cache backends and advanced cache strategies.

### Official Sources

- https://docs.docker.com/build/building/best-practices/
- https://docs.docker.com/compose/compose-file/
- https://docs.docker.com/engine/security/
- https://docs.docker.com/build/cache/
- https://docs.docker.com/compose/how-tos/file-watch/
- https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/
