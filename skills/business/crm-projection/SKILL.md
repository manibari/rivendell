---
name: crm-projection
description: "Project nx_client + nx_deal data to local markdown files at materials/clients/. Cross-references customer-intel reports. Runs daily as headless agent."
tags: [automation, crm, sales-enablement, local, projection]
version: 1
source: manual
user_invocable: true
when_to_use: "TRIGGER when: user says /crm-projection, '更新客戶索引', 'sync clients', or invoked by headless agent on schedule. DO NOT TRIGGER when: user is creating/editing a specific client (use Nexus UI or API)."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# CRM Projection

Projects `nx_client` and `nx_deal` data from the database to local markdown files at `materials/clients/`. This creates a local, offline-readable snapshot of CRM state for sales material assembly.

## Architecture

```
nx_client + nx_deal (DB read-only)
    ↓
Python query via services/nexus/clients.py
    ↓
materials/clients/INDEX.md (local markdown)
    ↓
Cross-reference reports/customer-intel/INDEX.md
```

**DB is read-only source. Markdown is the local projection.**

## Workflow

Read [projection.md](projection.md) for the complete workflow.

### Quick Reference

1. **Query** — Call `get_all_clients()` from `services/nexus/clients.py`
2. **Enrich** — For each client, get active deals via deal data
3. **Cross-ref** — Read `reports/customer-intel/INDEX.md` to find which clients have intel reports
4. **Write** — Generate `materials/clients/INDEX.md` with full client overview
5. **Summary** — Output stats

## Output Format

`materials/clients/INDEX.md` contains:

- Client table: name, industry, status, deal count, budget total, intel report link
- Summary stats: active clients, total pipeline, clients with intel
- Last updated timestamp

## Key Files

- `services/nexus/clients.py` — `get_all_clients()`, `get_client()`
- `services/nexus/deals.py` — Deal data with MEDDIC
- `reports/customer-intel/INDEX.md` — Intel report index
- `materials/clients/INDEX.md` — Output (auto-generated)

## Headless Execution

LaunchAgent: `com.sk.agent.sales.crm-projection`
Schedule: Daily 07:00
Runner: `scripts/crm-projection.sh`
