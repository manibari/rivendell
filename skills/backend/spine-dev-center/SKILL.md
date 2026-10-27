---
name: spine-dev-center
loop: dev
pdca: plan
description: >
  Canonical recipe for the developer mode inside a product (開發中心 / 開發者模式):
  one area where the owner and the developers see what the system is (開發藍圖,
  figures), what work is open (開發進度, tickets) and what shipped (版本與交付),
  next to the system's own logs. The mode is a route prefix; the backend guards every
  route; each page reads one source with one writer service; history is append-only;
  only a human acceptance closes a ticket; every object has a deep link. Yellow-Chick
  is the standard shape (platform back office); PTI-ARES (透明度) has the most complete
  content; PTI-ARES and ChimesERP (開發中心) converge to the Yellow-Chick shape.
  TRIGGER when: building or changing a developer area in a product; "開發者模式",
  "開發中心", "管理中心／開發中心", "開發藍圖", "開發進度", "版本管理頁", "透明度頁",
  "developer mode", "dev center", "讓老闆看到開發進度", "對照架構和 logs"; deciding who
  may see the developer area or which pages it has.
  SKIP when: ticket IDs, statuses and done rules only (spine-roadmap); version
  numbers and the release gate (spine-versioning); who counts as an admin
  (spine-rbac); planning the ops checklist of a new app (app-ops-baseline);
  drawing one figure (system-design, chart-design).
tags: [backend, frontend, admin, roadmap, tickets, versions, logs, spine, reference]
version: 1.1.0
source: manual
---

# spine-dev-center

One area inside the product where the owner and the developers see three things:
what the system is, what work is open, and what shipped. The ChimesERP owner
(2026-10): 「讓開發者才能思考與確認相關架構與對比當前的 logs」, 「不然你做了一大堆我都無法掌握」.

Three real implementations, in build order:

| Product | Name in the UI | Built | Audience |
|---|---|---|---|
| Yellow-Chick | 平台後台 › 開發藍圖 / 開發進度 / 版本管理 | 2026-09 | Platform operator only |
| PTI-ARES | 透明度 › 開發藍圖 / 開發進度 / 版本管理 / 使用手冊 | 2026-09 to 10, tracker copied from YC | Every signed-in user reads; admin writes |
| ChimesERP | 開發中心 (switch 管理中心 / 開發中心) | 2026-10-20 to 27, tracker from YC, numbers and capability items from PTI-ARES | Admin only, internal deployment only |

ChimesFlow has a blueprint view only (看板, 時間軸). It is not a full implementation.

This skill owns the surface: entry, audience, pages, links and guards. Other skills
own the data rules:

- Tickets, statuses, "done = accepted delivery": `spine-roadmap` (full tier).
- Version numbers and the release gate: `spine-versioning`.
- Who is an admin, platform operator versus tenant owner: `spine-rbac`.
- The ops checklist when a new app is planned: `app-ops-baseline`.
- The figures on the blueprint page: `system-design`, `qa-dataflow`, `chart-design`.

## Rules (all three agree)

1. **The mode is the route.** A route prefix is the mode: ERP `/dev/*`, YC
   `/admin/operations?view=blueprint|development|versions`, PTI `/roadmap`,
   `/progress`, `/changelog`. Do not store a mode flag. Inside the area, the account
   menu offers the way back (ERP: 「切換到 一般模式」).
2. **Three core pages, kept apart.** 開發藍圖 shows figures (what the system is).
   開發進度 shows tickets (what work is open). 版本與交付 shows versions, then their
   deliveries. The ERP owner: 「開發藍圖是圖」「開發進度是 ticket」. Do not merge the
   figures and the ticket list into one page.
3. **The backend guards every route.** The frontend guard is a convenience only.
   Reads and writes have separate checks. On 401 or 403 the frontend clears the
   area's cached data (YC `OperatorAccess`).
4. **One source for each page, one writer for each source.** The UI and the CLI call
   the same service (YC `app/development/tracker.py`, PTI `dev_tracking/service.py`,
   ERP `devcenter/tracker/service.py`). Do not change status with raw SQL, and do not
   edit an exported `TODOS.md` by hand.
5. **History is append-only, and edits are checked.** A database trigger blocks
   update and delete on the event table. Each edit sends the version it read; a
   mismatch returns 409 `edit_conflict`. The UI keeps the user's draft and offers a
   reload (YC 「捨棄草稿並重新載入」).
6. **Only a person closes a ticket.** Merged work is `review` (待驗收). 發版不等於驗收.
   An agent may create tickets and add steps. It can never accept. ERP: acceptance
   needs an interactive session and an e-mail in `DEVCENTER_ACCEPTORS`.
7. **An unreadable source is an error on the page.** YC returns 503 for a broken
   source document; PTI shows a failed delivery sync in red. Never show an empty list
   for a read failure (「0 筆」不等於合格).
8. **Every object has a deep link, and filters live in the URL.** Ticket, delivery,
   version, blueprint item, source document. Pages link both ways: blueprint item
   to ticket, ticket to delivery, delivery to version and back. Use a whitelist of
   URL keys (YC `features/administration/search.ts`).
9. **The product shows its own version and build.** PTI: a side-nav badge with the
   version and build commit, which opens 版本管理. ERP: a version card from
   `VERSION`, the docs bundle manifest and the Alembic heads.

## The standard and the gaps

Owner, 2026-10-27: 「yellow chick 才是標準的，未來 PTI ARES 跟 CHIMES ERP 也要同步成這樣」,
「目前 PTIARES 在長肉上是最完整的」. Thus Yellow-Chick sets the shape: entry, guard,
pages, where the data lives. PTI-ARES sets the content: what goes inside each page.
A new product starts from the Yellow-Chick shape and the PTI-ARES content.

| Part | Standard (Yellow-Chick) | PTI-ARES now | ChimesERP now |
|---|---|---|---|
| Who sees it | Platform operator only; a tenant owner gets 403 | Every signed-in user reads, admin writes (by design: 「透明度，全角色」) | Admin only, and only in the internal deployment |
| Entry | Account menu link 「平台後台」, shown only to an operator; the bell links pending acceptances | Side-nav group 「透明度」 | Avatar menu 切換到 開發中心 |
| Route | `/admin/operations?view=blueprint\|development\|versions` | `/roadmap`, `/progress`, `/changelog` | `/dev/*` |
| Spec and status | Spec in Git (`docs/development/*.md`, `TODOS.md`), read through an allow-list; status in the DB | `data/roadmap.json` in Git; tickets in the DB; deliveries made from roadmap.json | Spec and status in the DB; `TODOS.md` is an export (a deliberate difference, its SD §8 #2) |
| Ticket IDs | Names (`DEV-TRACKER-STORE`) | Running numbers (`PTI-123`) | Both (`ERP-295` and a name) |
| 開發藍圖 | Five architecture views (系統分層, 模組關係, 守門機制, 功能流程, 業務領域), 子項目資料流, 驗收關卡, 規則清冊, 交付回顧 | 系統架構, 子項目資料流, 能力分組 with 合約驗收, 規則清冊, 出貨回顧 | Docs and figures pages; `/dev/roadmap` as a figure is on a branch (ERP-295) |
| Source documents | A drawer on every page | Not found | Docs pages from the bundle |
| Logs | Elsewhere in the back office | Elsewhere (admin group) | 系統紀錄對照 inside the area |

Keep these differences; they do not conflict with the standard:

- ChimesERP mounts the area only in its internal deployment, and the customer image
  has no docs bundle (CI checks it). Use this in any product that is installed at
  customers.
- ChimesERP's logs page inside the area answers 「對比當前的 logs」.

### Content to copy from PTI-ARES (the most complete today)

- **Capability items with checks and evidence.** Each item has an acceptance
  sentence and yes/no checks; a check passes only with evidence; status is derived
  (`backend/app/host/meta.py:83-129`). Tickets record work, items record capability:
  「票與細項是兩層，數字不能互相換算」 (spine-roadmap).
- **合約驗收 card** on top of 能力分組: the customer-facing gates, apart from the
  capability groups.
- **Deliveries made from the source.** A sync builds deliveries from
  `roadmap.json` at startup, from the CLI or from a button; fields that come from the
  source are locked (422 `source_field_locked`); people fill only the acceptance
  date, the basis and the deployments. A failed sync shows red.
- **Version badge** in the side nav (version and build commit), which opens 版本管理.
- **Deep links between pages**: `/roadmap?m=<item>`, `/progress?ticket=<id>`,
  `/changelog?view=deliveries&version=&delivery=<id>`.
- **使用手冊 chapter** for the area (add the 開發進度 step that PTI-ARES misses).
- **Release check**: `scripts/check_release.py` before the CI release tag; commit
  trailers `Milestone:` and `Ticket:` (`scripts/hooks/commit-msg`).

## Pages

| Page | Shows | Source | Who writes |
|---|---|---|---|
| 開發藍圖 | Tabs: 系統架構 (YC has 5 views: 系統分層, 模組關係, 守門機制, 功能流程, 業務領域), 子項目資料流, 能力分組 or 驗收關卡 (capability items with checks n/m and their tickets), 規則清冊, 交付回顧 (90 days) | Git documents, `roadmap.json`, or a docs bundle | Git commits only; no UI writer |
| 開發進度 | Counts by status; the owner's rows first (待你驗收, 等你同意合併); filters; table or board; 15 per page; a drawer with editor, history, prerequisites, follow-on tickets and deliveries | Ticket and event tables | The tracker service: admin buttons, the CLI (`--operator` required), agent API with scopes |
| 版本與交付 | A version card (name, version, build, branch, bump rules), then versions, deliveries for a version, and a delivery drawer | Delivery and release tables | Sync from the source (PTI) or the tracker (ERP). People fill only the acceptance date, the basis and the deployments |
| 系統紀錄 (optional) | Access log, job runs and security events for each module; no personal data | Log files and tables | The application |
| 文件與圖 (optional) | Allow-listed documents and figures | A bundle made at image build, with a secret and personal-data scan | The build script |

A pending-work signal helps the owner: YC's bell shows 「開發票 N 張等你驗收 →」 and
links to 開發進度. Developer tickets do not light the bell's red dot (YC decision D63).

## Build order

1. Start from the Yellow-Chick shape and the PTI-ARES content ("The standard and the
   gaps"). Write any difference, and its reason, in the SD.
2. Tracker tables, the one writer service and the CLI (spine-roadmap, full tier).
   Tests: transitions, the append-only trigger, 409 on a stale version.
3. API: read routes for the audience, write routes for admins, acceptance for a person
   in an interactive session. Mount the routers only where the area may exist.
4. Shell: the route prefix, the account-menu switch, the area's own sidebar, the way
   back. Phone width: one segmented menu (ERP, below 641 px).
5. Pages, in this order: 開發進度 (the owner can act on it), 版本與交付, 開發藍圖 (the
   figures need system-design or qa-dataflow first).
6. Deep links, URL state and the links between pages.
7. The version badge or card.
8. The pending-work signal for the owner.
9. A manual chapter for every page.
10. Tests: route guards (401, 403, and 404 in a deployment without the area), one e2e
    deep link for each object type, the phone layout.

## Gotchas

- **E2E tests that return early pass and test nothing.** ERP's tracker e2e tests
  returned early with the CI profile (ERP-289). Assert that the test body ran.
- **The docs drift from the code.** YC's README and blueprint document say four
  architecture views; the code requires five. Count from the code or from a test.
- **A URL key outside the whitelist is dropped.** A YC screenshot script sent `tab=`;
  the real key is `section`.
- **Unused endpoints stay behind.** PTI's frontend never calls `/api/changelog` or
  `/api/roadmap/doc`. Remove or wire each endpoint.
- **"Released" needs a test.** ERP's `scripts/release.py` did not call
  `record_release`, so the released step was never recorded.
- **A `TODOS.md` round trip breaks.** ERP's import broke when lines got running
  numbers (ERP-294). Keep the export one way, and export again on a conflict.
- **Client names in documents.** ERP keeps them only in a bundle that only the
  internal image carries; CI checks that the customer image has no bundle.
- **The manual misses a page.** PTI's manual describes 開發藍圖 and 版本管理, not
  開發進度.
- **Polling fights the editor.** YC refreshes the list every 15 s, but not while a
  ticket is open.

## Reference implementations

### Yellow-Chick (`~/Code/Yellow-Chick`)

| Part | Path |
|---|---|
| Route and nav | `frontend/src/routes/router.tsx:90`, `frontend/src/routes/manage/operations.tsx:23`, `frontend/src/components/AccountMenu.tsx:89` |
| Guards | `app/api/operations/development.py:40` (`require_operator`), `app/api/deps.py:265`, `frontend/src/components/OperatorAccess.tsx` |
| Data | `app/development/reader.py` (allow-list, 503), `tracker.py` (advisory lock, 409), `readiness.py`, `architecture.py`; `alembic/versions/0024_development_tracker.py` |
| UI | `frontend/src/features/development/` (`shared.tsx`, `Tracking.tsx`, `DetailPanel`, `TicketEditor`, `TicketHistory`, `DocumentView.tsx`); URL keys `frontend/src/features/administration/search.ts` |
| CLI and rules | `scripts/ops/development_tracker.py`; `docs/development/README.md`; `docs/plans/development/2026-09-26-development-tracker.md` |
| Tests | `tests/operations/test_development_{api,reader,summary,tracker}.py`; `frontend/tests/admin/development.spec.ts`, `development-tracker.spec.ts` |

### PTI-ARES (`~/Code/PTI-ARES`)

| Part | Path |
|---|---|
| Nav and guards | `frontend/src/app/(main)/layout.tsx:72-86`; `backend/app/main.py:211,245` (`_gated`); `identity/auth.py:207,223` |
| Pages | `frontend/src/app/(main)/{roadmap,progress,changelog,manual}/page.tsx`; `features/dev-tracking/` |
| Data | `data/roadmap.json`; `backend/app/host/meta.py:83-129` (derived status); `backend/app/features/platform/dev_tracking/{router,service,rules,delivery_sync,cli}.py` |
| Tests | `tests/accounts/test_dev_tracking_{rules,db}.py`, `test_dev_delivery_db.py`; `tests/repo/test_roadmap_taxonomy.py`, `test_release_check.py`; `tests/console/test_blueprint_presentation.py` |

### ChimesERP (`~/Code/ChimesERP`)

| Part | Path |
|---|---|
| Centers and guards | `backend/app/platform/centers.py`, `profile.py:162`; `backend/app/router_groups.py:204-224`; `frontend/src/lib/shell-menu.ts`; `frontend/src/components/dev-sidebar.tsx`, `dev-gate.tsx` |
| Tracker | `backend/app/devcenter/tracker/{service,api,access}.py`; `scripts/devtracker.py`; `docs/development/tracker-for-agents.md` |
| Docs, version, logs | `scripts/build_dev_docs.py`; `backend/app/devcenter/module_map.py`; CI check `.github/workflows/backend-ci.yml:66,70` |
| Design | `docs/design/2026-10-20-shell-centers-i18n-sd.md`, `2026-10-23-dev-tracker-sd.md`; mockups `docs/mockups/2026-10-21-shell-centers.html` (`d-dev`), `2026-10-23-dev-tracker.html` |
| Tests | `backend/tests/test_devcenter_*.py`, `test_centers.py`, `test_devtracker_cli.py`; `frontend/e2e/dev-center.spec.ts`, `dev-tracker.spec.ts`, `dev-tracker-phone.spec.ts` |

Status on 2026-10-27: ERP's DEV-* tickets are on main and wait for the owner's
acceptance (`review`). DEV-CENTER-PROGRESS (ERP-295, `/dev/roadmap` as a figure) is on
a branch.

## Sources

- Survey of the three repos on 2026-10-27 (main branches; ERP branches for the parts
  not yet merged).
- Registry `rivendell/docs/spine-modules.md` (#21).
