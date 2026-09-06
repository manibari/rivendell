---
name: deploy
loop: dev
pdca: act
description: >
  Recommend deployment platform and generate deploy config (Dockerfile, fly.toml, vercel.json, CD workflow).
  TRIGGER when: user asks to deploy, asks "how to deploy", or wants to set up continuous deployment.
  DO NOT TRIGGER when: purely local development, plan mode, or user is only asking about CI (use ci-pipeline instead).
tags: [meta]
version: 1
source: manual
user_invocable: false
---

# Deploy Configuration Generator

Recommend deployment platform based on project type and generate deployment configs + CD workflow.

## Instructions

### Step 1: Detect Project Type and Recommend Platform

Scan the project to determine its type, then recommend the best deployment target:

| Project Type | Indicators | Recommended Platform | Config Files |
|-------------|-----------|---------------------|-------------|
| Next.js (SSR) | `next` in deps, no `output: 'export'` | Vercel | `vercel.json` |
| Next.js (static) | `next` + `output: 'export'` in next.config | Vercel or Cloudflare Pages | `vercel.json` or `wrangler.toml` |
| Nuxt | `nuxt` in deps | Vercel or Cloudflare Pages | `vercel.json` |
| Python API (FastAPI) | `fastapi` / `uvicorn` in deps | Fly.io or Railway | `fly.toml` + `Dockerfile` |
| Streamlit | `streamlit` in deps | Streamlit Cloud or Fly.io | — or `fly.toml` |
| Docker Compose | `docker-compose.yml` present | VPS or Railway | `docker-compose.prod.yml` |
| iOS app | `*.xcodeproj` / `Package.swift` | TestFlight / App Store Connect | Fastlane `Fastfile` |
| Firebase Functions | `firebase.json` with functions | Firebase Hosting | CI `firebase deploy` |
| Static site | HTML/CSS only, or SSG output | Cloudflare Pages or Netlify | — |

If the project is full stack (e.g., Python API + Next.js frontend), recommend separate deploy targets for each component.

Present the recommendation to the user and confirm before generating configs.

### Step 2: Security Checks (Before Generating)

Run these checks and fix issues before generating deploy configs:

1. **`.gitignore` check**: Ensure `.env`, `.env.local`, `.env.production` are in `.gitignore`
2. **Hardcoded secrets scan**: Grep for patterns like API keys, passwords, tokens in source code. Flag any findings.
3. **CORS / Allowed hosts**: If the project has CORS or allowed hosts config, remind the user to update for production domain
4. **Database URLs**: Ensure database connection strings use environment variables, not hardcoded values

### Step 3: Generate Deployment Configs

#### Vercel (Next.js / Nuxt / static)

Generate `vercel.json` if non-trivial config is needed:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "nextjs",
  "buildCommand": "pnpm build",
  "installCommand": "pnpm install --frozen-lockfile"
}
```

For most Next.js projects, Vercel auto-detects — only generate `vercel.json` if there are custom rewrites, headers, or env vars.

#### Fly.io (Python API / Streamlit)

Generate `fly.toml`:

```toml
app = "project-name"
primary_region = "nrt"  # Tokyo — closest to user

[build]

[http_service]
  internal_port = 8000  # or 8501 for Streamlit
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

[env]
  # Non-secret env vars here
```

Generate production `Dockerfile` if not exists (or if only dev Dockerfile exists):

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose Production

Generate `docker-compose.prod.yml` that differs from dev:
- No volume mounts for source code
- No dev servers (use production builds)
- Proper restart policies
- Health checks
- No exposed debug ports

#### Fastlane (iOS)

Generate `fastlane/Fastfile`:

```ruby
default_platform(:ios)

platform :ios do
  desc "Run tests"
  lane :test do
    run_tests(
      scheme: "AppScheme",
      device: "iPhone 16"
    )
  end

  desc "Build and upload to TestFlight"
  lane :beta do
    build_app(scheme: "AppScheme")
    upload_to_testflight
  end
end
```

### Step 4: Generate CD Workflow

Generate `.github/workflows/deploy.yml`:

```yaml
name: Deploy
on:
  push:
    branches: [main]
  workflow_run:
    workflows: [CI]
    types: [completed]
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' || github.event_name == 'push' }}
    steps:
      - uses: actions/checkout@v4
      # Platform-specific deploy steps below
```

Platform-specific deploy steps:

#### Vercel

```yaml
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: --prod
```

#### Fly.io

```yaml
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

#### Firebase

```yaml
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npx firebase deploy --only functions,hosting
        env:
          FIREBASE_TOKEN: ${{ secrets.FIREBASE_TOKEN }}
```

### Step 5: Generate `.env.example`

Create `.env.example` listing all environment variables the project needs (without actual values):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# App Config
APP_ENV=production
APP_SECRET_KEY=generate-a-random-key
```

Only generate if `.env.example` doesn't already exist.

### Step 6: Report

```
Project: ~/my-project
Type: Python API (FastAPI) + Next.js frontend

Deploy targets:
  Backend → Fly.io (Tokyo region)
  Frontend → Vercel

Generated:
  ✅ fly.toml (backend)
  ✅ Dockerfile (production)
  ✅ vercel.json (frontend)
  ✅ .github/workflows/deploy.yml (CD)
  ✅ .env.example

Security checks:
  ✅ .env in .gitignore
  ✅ No hardcoded secrets found
  ⚠️  Update CORS_ORIGINS in settings.py for production domain

Required GitHub Secrets:
  - FLY_API_TOKEN — get from: flyctl tokens create deploy
  - VERCEL_TOKEN — get from: vercel.com/account/tokens
  - VERCEL_ORG_ID — get from: vercel.com/account
  - VERCEL_PROJECT_ID — get from: vercel project settings

Next steps:
  1. Review generated configs
  2. Set up GitHub Secrets in repo settings
  3. For Fly.io: flyctl launch (first time) or flyctl deploy
  4. For Vercel: vercel link (first time)
  5. Push to main to trigger CD
```
