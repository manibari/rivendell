# Rivendell Development Roadmap

This roadmap tracks human-owned development priorities. Generated reports under
`reports/*` remain owned by scheduled agents and should not be manually edited
as roadmap material.

## Current Baseline

- Version: `0.1.0`
- Canonical skills: `skills/*/*/SKILL.md`
- Dashboard: `dashboard-next` web on port `3000`, FastAPI on port `8000`
- Agent SSOT: `agents/agents.conf`
- Release notes: `CHANGELOG.md`

## P0: Restore Operational Confidence

1. [done 2026-06-13] Load and verify launchd agents from `agents/agents.conf`.
2. [done 2026-06-13] Make `./bin/sk check agents` clean on the maintainer machine.
3. [done 2026-06-13] Fix CI pull-request filtering so dashboard, API, and skill
   validation jobs do not silently skip relevant PRs.
4. Add a small regression suite for `dashboard-next/api/server.py` data parsers:
   ports, agents, skill catalog, and harvest summaries.
   - [done 2026-06-13] Port parser and live/drift/wild semantics.

## P1: Make Health Reports Trustworthy

1. Fix `./bin/sk audit` catalog generation so descriptions do not shift between
   skills and local gstack links do not appear as Rivendell-owned skills.
2. Add metadata checks for `tags`, `version`, `last_reviewed`, and `imported_at`
   to CI or scheduled tester output.
3. Add a README catalog drift check that fails when `SKILL.md` frontmatter and
   `README.md` disagree.
4. Keep report janitor behavior documented and avoid manual edits to generated
   reports.

## P2: Improve Dashboard Reliability

1. Keep the port map based on both `docker-compose.yml` declarations and live
   local listeners.
2. Add API contract tests for `/api/ports`, `/api/health/agents`,
   `/api/health/ssot`, and `/api/skills`.
3. Add a lightweight frontend test harness for pages that transform API data.
4. Keep `next build --webpack` as the stable production build path until the
   Turbopack cache issue is no longer reproducible.

## P3: Repository Hygiene

1. Remove tracked `__pycache__`/`.pyc` artifacts.
2. Decide whether archived `reports/*-error.log` files are historical records or
   should be converted to generated artifacts outside git.
3. Move stale root planning files into dated `docs/plans/` files or delete them
   after extracting durable decisions.
4. Decide whether the root `package.json` is a supported toolchain. If yes, add
   a lockfile; if no, remove or document it.

## Release Checklist

Before bumping `VERSION`:

1. Update `CHANGELOG.md`.
2. Run `./bin/sk check --verbose`.
3. Run `./bin/sk check ssot`.
4. Run `./bin/sk check agents` when launchd state is relevant.
5. Run dashboard/API validation commands for files touched in the release.
6. Do not include manual edits to generated `reports/*`.
