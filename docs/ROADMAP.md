# Rivendell Development Roadmap（已停用）

> **這份不是現行 roadmap。** 現行的是 repo 根目錄的 [ROADMAP.md](../ROADMAP.md)
> （Wave 制,取自 PTI-ARES）。本檔停在 0.1.0 時期的 P0-P3 優先序,基線欄位在
> 2026-09-16 對帳時已與事實不符（版本落後兩個大版、agent SSOT 早已從
> `agents.conf` 換成 `agents/registry/*.md`）。兩份 roadmap 同時存在、又互相
> 矛盾,是 doc-drift-sync 要抓的典型情況。
>
> 保留原因:下方 P1-P3 有些項目可能還沒了結,但**逐項狀態未經查證**（待補）。
> 要沿用的項目請搬進根目錄 ROADMAP.md 的對應 Wave,不要在這裡繼續打勾。

This roadmap tracks human-owned development priorities. Generated reports under
`reports/*` remain owned by scheduled agents and should not be manually edited
as roadmap material.

## Current Baseline（2026-06 當時,已過期）

- Version: `0.1.0` — 現為 `0.3.0`
- Canonical skills: `skills/*/*/SKILL.md` — 仍然成立
- Dashboard: `dashboard-next` web on port `3000`, FastAPI on port `8000` — 仍然成立
- Agent SSOT: `agents/agents.conf` — **已換成 `agents/registry/*.md`**,
  `agents.conf` 降為不進 git 的生成產物（2026-07-30,`bd10c54` `94b03bf`）
- Release notes: `CHANGELOG.md` — 仍然成立

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
