# Rivendell Roadmap, Versioning, and Ports Implementation Plan

> **For Claude:** Use `skills/workflow/executing-plans/SKILL.md` to implement this plan task-by-task.

**Goal:** Establish a maintainable development roadmap, explicit version/change tracking, and a more accurate port map.

**Architecture:** Treat roadmap and release notes as human-authored docs. Keep generated `reports/*` out of the change path. For ports, use `docker-compose.yml` as declared intent and local TCP listeners as runtime reality.

**Tech Stack:** Markdown, Bash, FastAPI/Python, Next.js/TypeScript.

---

### Task 1: Add Version And Changelog

**Files:**
- Create: `VERSION`
- Create: `CHANGELOG.md`

**Steps:**
1. Add `VERSION` with `0.1.0`.
2. Add a changelog entry dated `2026-06-13`.
3. Mention roadmap creation and port map behavior.
4. Verify with `test "$(cat VERSION)" = "0.1.0"`.

### Task 2: Add Development Roadmap

**Files:**
- Create: `docs/ROADMAP.md`
- Modify: `README.md`

**Steps:**
1. Document P0-P3 priorities.
2. Add a release checklist.
3. Link roadmap, changelog, and version file from README.
4. Verify links point to existing files.

### Task 3: Fix Port Map Runtime Semantics

**Files:**
- Modify: `dashboard-next/api/server.py`
- Modify: `dashboard-next/src/lib/api.ts`
- Modify: `dashboard-next/src/app/ports/page.tsx`
- Modify: `docs/requirements/port-map.md`
- Modify: `docs/flows/port-map-flow.md`

**Steps:**
1. Parse compose port declarations, including short and long syntax.
2. Collect local listening TCP ports via `lsof`.
3. Mark declared+listening ports as `live`.
4. Mark declared+not-listening ports as `drift`.
5. Add listener-only ports as `wild`.
6. Keep `unknown` only for runtime check failures.
7. Update UI labels and TypeScript types.
8. Run Python compile and Next lint/build checks.

### Task 4: Verify

**Commands:**
- `python3 -m py_compile dashboard-next/api/server.py`
- `cd dashboard-next && npm run lint`
- `cd dashboard-next && npm run build`
- `./bin/sk check --verbose`

**Expected:** Code checks pass. Existing metadata warnings may remain until the
metadata cleanup task is handled.
