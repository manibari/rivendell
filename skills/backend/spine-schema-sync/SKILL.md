---
name: spine-schema-sync
loop: dev
pdca: do
description: >
  Canonical DB schema migration + dev↔prod sync for the FastAPI + Postgres fleet.
  Audit (2026-06-27) of chimesflow / mops / family-fiscal: chimesflow + mops BOTH
  converge on Alembic; family-fiscal hand-rolls a migrate_schema() and is the
  "too small to bother" outlier. So the canonical core is real: Alembic migrations
  + `alembic upgrade head` run on deploy = the dev↔prod sync mechanism. The one
  decision is single-alembic (monolith) vs per-service alembic (monorepo, like mops).
  TRIGGER when: setting up DB migrations / schema changes / Alembic / "同步 db
  schema" / dev↔prod schema drift / "prod 的表跟 dev 對不上" / adding a column or
  table to a FastAPI + Postgres product; wiring migrations into a deploy/redeploy.
  SKIP when: a non-Postgres / non-SQLAlchemy store; an analytics-only read replica
  with no app-managed schema; a throwaway prototype where the DB is recreated each run.
tags: [backend, database, alembic, migration, postgres, spine, deploy, reference]
version: 1.0.0
source: manual
---

# spine-schema-sync

How the fleet keeps prod's DB schema in step with the code. **Audit finding: the
core converges** — chimesflow and mops both use Alembic; family-fiscal's hand-rolled
`migrate_schema()` is the small-app outlier (and a cautionary tale). Grounded in
`~/code/ChimesFlow/backend/alembic/` + `scripts/deploy/wsl/chimesflow-redeploy.sh`,
`~/code/mops_dbs/services/*/alembic.ini`, and `~/code/Family-Fiscal/backend/db.py`.

## Canonical core — use as-is

1. **Alembic for every schema change.** `alembic.ini` with `sqlalchemy.url` from env
   (never hardcoded). Models are the source; `alembic revision --autogenerate` in dev.
2. **dev → prod sync = `alembic upgrade head` on deploy.** This IS the sync mechanism.
   The deploy/redeploy script runs it **before the app starts serving**, so code and
   schema move together. chimesflow's `chimesflow-redeploy.sh` does exactly this and
   logs `ERR: alembic upgrade failed — schema may be out of sync` on failure (the ops
   monitor surfaces that — ties to [[spine-deploy]]).
3. **Direction is fixed**: autogenerate + edit in **dev**, commit the version file,
   `upgrade head` in **prod**. Never autogenerate against prod; never hand-edit prod schema.
4. **Seed data = its own migration** (chimesflow: `release_items_seed_001.py`,
   `seed_roadmap.py`), idempotent, so a fresh prod and an upgraded prod converge.

```bash
# dev: after changing a model
alembic revision --autogenerate -m "add soft_delete columns"
# review + edit the generated version, commit it

# prod (inside the deploy/redeploy script, BEFORE starting the app):
alembic upgrade head || { echo "ERR: alembic upgrade failed — schema out of sync"; exit 1; }
```

## The one decision: single vs per-service Alembic

- **Single** `alembic/` (chimesflow): one service, one migration history. Default.
- **Per-service** `services/<svc>/alembic.ini` (mops, a multi-service monorepo): each
  service owns its schema + history. Pick this only when services own disjoint tables
  and deploy independently. Don't split a monolith's migrations.

## Gotchas — from the audit

- **Don't hand-roll `migrate_schema()`**: family-fiscal does `_col_exists()` + `ALTER TABLE
  ADD COLUMN IF NOT EXISTS` by hand in `db.py`. It works at 2-table scale but has no
  history, no downgrade, no autogenerate, and silently diverges once two machines apply
  different ad-hoc ALTERs. Use Alembic from product #1 — retrofitting it onto a live DB is
  the painful path.
- **`create_all()` is for tests, never prod**: fine in `conftest.py`; in prod it creates
  tables once and then never tracks changes, so you lose migration history and drift. Prod
  schema changes go through `alembic upgrade head` only.
- **Run `upgrade head` BEFORE the app serves, not after**: if the app boots on an old schema
  and the new code reads a not-yet-added column, you get 500s in the window. Gate startup on
  a successful upgrade (deploy script exits non-zero on failure — see the redeploy pattern).
- **`sqlalchemy.url` from env, per environment**: same migration files, different DB URL for
  dev/prod via env. Hardcoding the URL in `alembic.ini` ships dev creds or points prod at dev.
- **Review autogenerate output — it's not magic**: Alembic misses some changes (server defaults,
  CHECK constraints, type widenings like mops's `002_widen_pct_columns`, enum changes). Read the
  generated migration before committing; add the bits it missed by hand.
- **One head**: parallel branches (two devs autogenerate at once) create multiple heads →
  `upgrade head` errors. Merge with `alembic merge` and keep a single head on main.

## Sources (SoT)

- Alembic (converged): `~/code/ChimesFlow/backend/alembic/` + `alembic.ini`;
  deploy sync in `~/code/ChimesFlow/scripts/deploy/wsl/chimesflow-redeploy.sh`;
  per-service variant `~/code/mops_dbs/services/{mops_rev,mops_cf,mops_notes}/alembic.ini`
- Anti-pattern (outlier): `~/code/Family-Fiscal/backend/db.py` (`migrate_schema` / `_col_exists`)
- Registry `rivendell/docs/spine-modules.md` (#7, shared core). Pairs with [[spine-deploy]]
  (the deploy script that runs the upgrade).
