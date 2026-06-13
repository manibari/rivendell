# Changelog

All notable changes to the rivendell platform are recorded here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

**Versioning = ISO week** (one iteration per week, closed at `workflow-retro`).
The `[Unreleased]` section collects changes mid-week; it is promoted to a dated
`## [YYYY-Www]` heading when the iteration closes. Kept aligned with
[ROADMAP.md](ROADMAP.md) by the `doc-drift-sync` skill.

## [Unreleased]

### Added
- `doc-drift-sync` skill (`skills/meta/`) — detects/fixes drift across
  CHANGELOG / ROADMAP / CLAUDE.md / progress and defines the weekly iteration cycle.
- `ROADMAP.md` + `CHANGELOG.md` — version/roadmap discipline for rivendell itself,
  reviewed each iteration at `workflow-retro`.

## [2026-W24] — 2026-06-13

### Added
- chimesflow-design + app-ops-baseline gate skills (`ff8ea85`).

### Fixed
- sk-setup-agents PROJECTS_DIR landmine + ssot-drift cron 11-arg (`8007c6d`).
- `bin/sk` cmd_check_ssot derives project from PROJECT_REL_PATH not label (`389eacb`).

### Added (earlier in W24)
- dashboard Git 衛生 panel — uncommitted/unpushed across ~/code repos (`7523816`).
- learnings: iCloud-detach + agent gotchas, 3 entries (`2181b66`).

---

_Earlier history predates this changelog (待補 if reconstructed from git log)._
