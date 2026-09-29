---
name: spine-roadmap
loop: dev
pdca: plan
description: >
  Canonical 開票 + roadmap mechanism for the product fleet: every piece of work
  (feature, task, hotfix) gets a FIXED ticket ID before code, the ticket's spec lives
  in Git while its status lives in one tracked place, a ticket only reaches "done"
  through an accepted + released delivery, and ROADMAP.md is a view derived from the
  tickets, not a second list. Two tiers: light (TODOS.md fixed IDs + deliveries
  ledger, any repo) and full (DB tracker + admin portal + operator CLI, products with
  a platform-admin surface). Reference = Yellow-Chick (full), ChimesFlow roadmap-in-DB
  (user-facing view).
  TRIGGER when: "開票", "開 ticket", "開工作票", "工作票", "hotfix 要不要開票",
  "改 roadmap", "roadmap 怎麼維護", "票的狀態", setting up ticket / backlog / work-package
  tracking for a product; or when work is about to start with no ticket ID to cite.
  SKIP when: version bump / release gate itself (spine-versioning); aligning
  CHANGELOG / ROADMAP / progress text after the fact (doc-drift-sync); a one-off
  script or throwaway prototype; the team already runs Jira / Linear as the SoT.
tags: [backend, roadmap, tickets, work-packages, release, spine, reference]
version: 1.0.0
source: manual
---

# spine-roadmap

Ticket + roadmap, **ID-first**. The pattern that worked on Yellow-Chick (0.5 → 0.12,
122 tickets by 2026-09-29): nothing ships without a fixed ticket ID, the ticket is the
join key between spec, delivery, version and deployment, and the roadmap is read off
the tickets instead of being hand-maintained beside them. Pairs with
[[spine-versioning]] (version is the data, roadmap is the view) and
[[doc-drift-sync]] (keeps the text files agreeing).

## The four rules (both tiers)

1. **Fixed ID before code.** `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)+$`, e.g. `CRM-RELATIONSHIPS`,
   `HOTFIX-OAUTH-QUOTA`. The ID never changes when the title does. Commits, plans, QA
   docs and deliveries all cite the ID.
2. **Hotfix is a ticket too.** `HOTFIX-*` with problem, acceptance criteria and QA;
   it ships as a PATCH release with a tag. A commit + CHANGELOG line alone is not a
   hotfix record.
3. **Spec in Git, status in one place.** Title / detail / dependencies are reviewed
   text (TODOS.md). Status / assignee / target_version live in exactly one tracker
   (light tier: the same TODOS line; full tier: the DB). Never both writable.
4. **Done = accepted delivery, not merged code.** A ticket moves to `done` only by
   pointing at a delivery that lists the ticket in `work_ids` and has a version,
   `verified_on`, evidence sources and a deployment record. "已合入 main" is
   `review` (待驗收). **發版不等於驗收** — say so in the roadmap header.

## Tier choice

| Tier | When | What you build |
|------|------|----------------|
| **Light** | Any repo that ships versions; no admin portal | `TODOS.md` fixed-ID lines + `docs/development/deliveries.md` ledger + ROADMAP header counts |
| **Full** | Product with a platform-admin surface, multiple agents/people editing status | Light tier + DB tracker (tickets + immutable history) + admin pages + operator CLI |

Default to light. Move to full only when two writers start overwriting each other's
status, or the owner wants to read progress in the app.

## Light tier

**TODOS.md line** (one per ticket, status in the bold header):

```markdown
- [ ] **CRM-RELATIONSHIPS：客戶／夥伴／公海與組織人物（待驗收，已合入 main）** — 老闆原話 + 範圍 + [需求](docs/requirements/...)
- [x] **[HOTFIX-OAUTH-QUOTA：OAuth 對話被月用量攔截](docs/plans/...)** — 2026-09-26 已驗收，以 **0.5.2** 本機發布。
```

Keep the owner's own words in the ticket (「老闆：……」) — that is the requirement
evidence a MINOR release later cites.

**deliveries.md** — JSON frontmatter (no YAML dependency) before a `---` line:

```json
{ "id": "crm-relationships-0929", "title": "...", "version": "0.12.0",
  "delivered_on": "2026-09-29", "verified_on": "2026-09-29",
  "work_ids": ["CRM-RELATIONSHIPS"], "sources": ["<requirement id>", "<qa id>"],
  "deployments": [{"environment": "local-development", "deployed_on": "2026-09-29", "evidence": "<qa id>"}],
  "release": {"previous_version": "0.11.0", "kind": "minor", "requirement_source": "<requirement id>"} }
```

Not yet shipped → `"version": null, "release": null, "deployments": []` (UI shows 待發布).
Never back-fill a deployment you cannot evidence.

**ROADMAP.md header** — derived, re-counted each release, never guessed:

```markdown
更新：YYYY-MM-DD。本機產品 **0.12.0**（MM-DD 發布）：<一句話本版內容>。**發版不等於驗收**，0.12.0 的 N 張票驗收中。
共 **122 票：完成 58、待驗收 16、進行中 4、待辦 6、等待需求 34、受阻 1、延後 3**。工作包大小不同，不能換算完成率。
```

Below it: a "已交付的階段" table (版本 → 已交付 → 驗收依據 link) and per-product-line
tables (已完成工作包 / 尚待工作包). ROADMAP owns scope and order; TODOS owns spec;
the tracker owns current status; CHANGELOG owns what shipped.

## Full tier (Yellow-Chick reference — read before copying)

`YC=~/Code/Yellow-Chick`

| Piece | Reference | Point to copy |
|-------|-----------|---------------|
| Statuses + transitions | `app/development/tracker_views.py` `TRANSITIONS` | `pending / waiting / in_progress / blocked / review / done / deferred`; `done` only from `review`; `done → in_progress` reopens and clears the accepted delivery |
| Command contracts | `app/development/tracker_contracts.py` | `CreateTicket` (id, title, detail, dependencies, kind task/feature/hotfix, target_version); `ChangeTicket` requires `expected_version` + `source_revision` |
| Owner service | `app/development/tracker.py` | dependency gate (can't start/finish before deps are done); `done` requires a matching released delivery; every change writes immutable history |
| Operator CLI | `scripts/development_tracker.py` | `list / import / create / change / history / export-todos`; requires `--operator` (no silent identity); `--body` JSON file; `import` only adds missing tickets, never overwrites status |
| Portal + docs | `docs/development/README.md`, `frontend/src/features/development/` | 開發藍圖 / 開發進度 / 版本管理 three pages share the same ledger; 15 per page, filters in URL |

The part to keep even if you simplify everything else: **optimistic concurrency**.
An agent editing a ticket must send the `row_version` it read and the source
revision; mismatch → 409 `edit_conflict`, reload, retry. This is what lets parallel
lanes/sessions touch the tracker without silently clobbering each other.

## ChimesFlow (user-facing roadmap view)

`~/code/ChimesFlow/backend/app/routers/roadmap.py` + `models/release_item.py`: a
curated, role-filtered "what's coming / what shipped" list for end users. That is a
different audience from the dev tracker above — build it as a view, don't make it the
ticket SoT.

## Gotchas

- **Two writable status lists drift.** If TODOS.md and the DB both hold status, one
  goes stale within a day. Full tier: TODOS keeps spec only, `export-todos` writes a
  labelled snapshot (「快照；目前進度以後台為準」).
- **Counts in ROADMAP are derived.** Re-count from the tracker at each release;
  a hand-typed "58 完成" is wrong by the next session.
- **"0 tickets found" is not "nothing to do"** — if the tracker can't be read, report
  unreadable, don't render an empty roadmap (YC reader raises instead of showing 0).
- **Ticket IDs are not version numbers.** Don't name tickets `V0-12-X`; the version
  a ticket lands in is the delivery's field, set at release time.
- **Deferred ≠ dropped.** Owner said "later" → `deferred` with the date/decision in
  the note; the ticket stays visible.

## Sources (SoT)

- `~/Code/Yellow-Chick/ROADMAP.md`, `TODOS.md`, `docs/development/{README,deliveries}.md`
- `~/Code/Yellow-Chick/app/development/`, `scripts/development_tracker.py`
- `~/code/ChimesFlow/backend/app/routers/roadmap.py` (user-facing view)
- Registry `rivendell/docs/spine-modules.md` (#4).
