# Requirement: Port Map Page

**Feature:** `port-map`
**Date:** 2026-03-31
**Location:** `dashboard-next` → new page at `/ports`

---

## Context

The rivendell project runs multiple Docker services. Each service maps one or more host ports. The developer frequently opens the wrong port because there is no central reference. The source of truth is `docker-compose.yml`, but cross-referencing it manually is error-prone.

---

## User Stories

### US-1: View all port mappings at a glance

**As a** developer running multiple Docker services
**I want to** see a table of all host ports and their corresponding services
**So that** I can quickly find the correct port without reading `docker-compose.yml`

**Acceptance Criteria:**
- [ ] Given the page loads, when docker-compose.yml is parsed, then all host ports are listed with service name and container name
- [ ] Given a service exposes multiple ports (e.g. news-stock: 8001, 3001, 8501), when displayed, then each port appears as a separate row
- [ ] Given the page has no docker-compose.yml access, when it loads, then an error state is shown (not a blank page)

---

### US-2: Know at a glance if a port is live, missing, or unmanaged

**As a** developer
**I want to** see whether each port is live, declared-only, wild, or unknown
**So that** I don't try to open a service that isn't running

**Acceptance Criteria:**
- [ ] Given a compose-declared service is listening, when the page loads, then its rows show a green "live" badge
- [ ] Given a compose-declared service is not listening, when the page loads, then its rows show "declared-only" / drift
- [ ] Given a local TCP listener is not declared in `docker-compose.yml`, when the page loads, then it appears as "wild"
- [ ] Given the listener scan fails, when the page loads, then compose rows show "unknown" rather than crashing

---

### US-3: Open a service directly from the table

**As a** developer
**I want to** click a port row to open it in a new browser tab
**So that** I don't need to type `localhost:PORT` manually

**Acceptance Criteria:**
- [ ] Given a port has a web UI (not a DB/Redis port), when I click its row or a link icon, then `http://localhost:{PORT}` opens in a new tab
- [ ] Given a port is for a non-HTTP service (5432 postgres, 6379 redis), when displayed, then no clickable link is shown (or link is visually disabled)

---

### US-4: Refresh status without reloading the page

**As a** developer who just started/stopped a service
**I want to** refresh the status column without reloading the whole page
**So that** I can verify the service came up

**Acceptance Criteria:**
- [ ] Given the page is open, when I click "Refresh", then status badges update to reflect current state
- [ ] Given a declared-only service is now listening, when I refresh, then its badge changes from "declared-only" to "live"

---

## Scope Boundary

| In Scope | Out of Scope |
|---|---|
| Parse `docker-compose.yml` for host port mappings | Editing port config from the UI |
| Show service name, container name, port, status, link | Showing container logs |
| Live/drift/wild status via listener scan | Docker stats (CPU/memory) |
| Clickable `localhost:PORT` links for web services | Support for remote hosts / SSH tunnels |
| Manual refresh button | Auto-refresh on a timer |
| Page at `/ports` in dashboard-next | Standalone app |

---

## Data Source

- **Port map**: parsed from `docker-compose.yml` at build time or via API endpoint
- **Status**: runtime check — compare `docker-compose.yml` host port declarations with local TCP listeners
- **Non-HTTP ports** (no link): 5432 (postgres), 6379 (redis)

## Known Port Map (as of 2026-06-13)

| Host Port | Service | Container | Type |
|---|---|---|---|
| 8000 | dashboard-api | rivendell-api | API (web) |
| 3000 | dashboard-web | rivendell-web | Frontend (web) |
| 8001 | news-stock | sk-news-stock | API (web) |
| 3001 | news-stock | sk-news-stock | Frontend (web) |
| 8501 | news-stock | sk-news-stock | Streamlit (web) |
| 8002 | sales | sk-sales | API (web) |
| 3002 | sales | sk-sales | Frontend (web) |
| 3004 | marketing-web | sk-marketing-web | Frontend (web) |

## Status Semantics

| Status | Meaning |
|---|---|
| `live` | Port is declared in compose and has a local TCP listener |
| `drift` / `declared-only` | Port is declared in compose but no local listener is present |
| `wild` | Port has a local listener but is not declared in compose |
| `unknown` | Runtime listener scan failed |
