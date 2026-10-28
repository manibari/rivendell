---
name: system-port
loop: dev
pdca: plan
description: >
  Plan and steer the port of one working system (the source) into another system (the
  target), page by page: owner rules on top, the source refreshed and pinned, a port
  inventory (every source page with endpoints, models, target status, model map, company
  values, reusable target branches), the source running locally on demo data, port as-is,
  keep the better screen where the target already has one, small batches grouped into
  tickets, one shared rule file for every lane, golden-value parity when the language
  changes. Source: ChimesERP taking in people-ops and ChimesFlow (ERP-298 to ERP-313,
  2026-10-28); line-calendar-mobile Dart to Swift (2026-10-28).
  TRIGGER when: "搬移清單", "系統搬移", "把舊系統搬進新系統", "搬功能", "兩套系統合併成一套",
  "port a system", "merge two systems into one", "rewrite in another language with parity";
  or work is about to port pages or modules from a running system into another one.
  SKIP when: only the database engine changes (sqlite-to-postgres); porting a skill from
  another repo (skill-scout); a new system with no source (system-design); one port ticket
  that is ready to code (agent-code-dispatch).
tags: [planning, migration, port, parity, consolidation]
version: 1.0.0
---

# system-port

A port moves a working system into another system. The source already works, so its
pages, fields, steps and messages are the specification. The code is not the main risk.
The main risks are an old copy of the source, a list that is too coarse, and lanes that
each make different decisions.

Claude plans, reviews and compares. An executor writes the code (`agent-code-dispatch`).
The owner decides the open rules and accepts each ticket (`spine-roadmap`).

## 0. Get the owner rules first

Write the rules that override the source in one decision file in the target repo
(`docs/decisions/<date>-port-rules.md`). Every lane reads it. Typical rules:

- **Port as-is.** Keep the same pages, fields, steps, states, validations, calculations
  and messages. Do not redesign. Keep a field that looks odd and note it in the report.
  QA makes the flow smooth later. (Owner, 2026-10-28: 「搬移優先，透過 qa 優化及順暢就好了吧」.)
- **Compare where the target already has the page** (section 4). Keep the better one, or
  combine the good parts. (Owner, 2026-10-28: 「已完成的部分可以比較一下畫面跟操作邏輯，留比較好的」.)
- **The target's data boundaries win.** Example: personal data never goes to the cloud.
  A source page that shows personal data ports only its work-data part.
- **One module per concern.** Approvals, employees and files use the target's existing
  module and its single writer. Do not port a second engine or a second employee table.
- **Company values become settings.** Rates, names, bank codes, e-mail domains and working
  hours in the source code go to target settings with neutral defaults.

When the source and a rule disagree, the rule wins, and the lane says so in its report.

## 1. Refresh and pin the source

1. Run `git -C <source> status --short`. If the tree is not clean, ask before you pull.
2. Fetch and pull. Then `git -C <source> log --oneline HEAD..origin/<branch>` must be empty.
3. Write the source commit in the inventory header.

(2026-10-28: the local people-ops copy was at 10-02. The remote had 79 more commits:
58 pages changed, 3 new pages, schema changes. The inventory, the local source stack and
three lanes used the old copy.)

When the source moves after the inventory, give each running lane a catch-up round:

1. The lane lists the source files of its batches.
2. It reads `git -C <source> diff <old> <new> -- <those files>` and the schema diff.
3. It ports each change in those diffs, with tests. A new source page goes to the lane of its area.
4. It applies the owner rules again.
5. Its report starts with a table: source change, what changed, where it is in the target.

Add a "Source update" section to the inventory with the new commit and the changed rows.

## 2. Write the port inventory

Give the inventory to an executor; it is a reading task. Claude spot-checks rows against
the source code. One file: `docs/porting/<date>-port-inventory.md` in the target repo.

| Section | Content |
|---|---|
| Summary | Per source: page count, `has` / `partial` / `missing` / `skip` |
| Pages | One row per source page: route and file, title, user role, function, endpoints, models read and written, target status and route, difference or limit |
| Model map | Source model to target table, with the missing fields |
| Unmerged target work | Target branches ahead of main that cover a part. Reuse reviewed work; do not rewrite it |
| Company-specific values | Source `file:line`, the literal, the target setting |
| Port batches | One area, at most 6 pages: source files, target tables and migration, dependencies, size, QA against the source |
| Skip list | Thin wrappers, redirects, duplicates, each with its reason |
| Evidence limits | What static reading cannot prove |
| Source update | Added when the source moves (section 1) |

- `has` needs screen and logic parity evidence. A route name that matches is `partial` at most.
- Mark personal-data fields in the model map. The ported tables leave them out.
- Split a batch when its source server logic is more than about 2,500 lines.

Then group the batches into tickets: one area per ticket, the employee side and the admin
side together. Order the waves by daily use. Add an appendix with the changed files per
ticket; a large count shows a ticket to split. (2026-10-28: 66 batches became 13 tickets;
wave 1 was attendance, work logs, HR base and the customer area.)

## 3. Run the source locally

Run each source system on this machine to take screenshots and to check behavior.

- Use demo data only. Do not use production data or production URLs.
- Bind every server and database to 127.0.0.1. Register each port first
  (`data/ports.conf` where it exists).
- Give each source its own compose project name. Do not touch other stacks or volumes.
- Use one script with `start`, `stop` and `status` for all parts.
- Keep demo account credentials in a mode-600 file. Never print them.
- Open the app with the host name that its auth expects. (people-ops sets its session
  cookie for `localhost`; `127.0.0.1` does not sign in.)
- Write a runbook: ports, compose projects, volumes, start and stop.

## 4. Compare where the target already has the page

For each `partial` page:

1. Do the same task on the source and on the target dev site.
2. Take screenshots of both at the same width. List the step differences.
3. Make one page for the owner: the screenshots side by side, then the steps.
4. A clear winner: adopt it and say so. Not clear: mark it and ask the owner.

The lane report starts with this compare table. QA uses the same method at the end.

## 5. One shared rule file for every lane

Write `port-common.md` once. Put it at the top of each lane brief, after the
`agent-code-dispatch` brief rules. It holds:

- the owner rules (section 0) and the decision files to read;
- the stack mapping for each source, for example Next.js route handlers and Prisma to a
  FastAPI router, service functions and SQLAlchemy models;
- where pages go, and "keep the source layout, columns, filters and button order; use the
  target components and styles";
- "use the inventory rows of your batches; read the source files they name before you
  write code";
- the scope rule for ports: a new package for the area, plus the area's existing files that
  the port replaces or extends, plus the area's entry points (home card, menu item, route
  registration). List each existing file that you change, with one line why. A table keeps
  its existing writer module;
- each repo guard that fails when an entry is missing, with the files the entry goes in;
- the test command, and the report: source pages and files ported, what was not ported and
  why, settings added, guard entries added, red and green output.

(2026-10-28: the first port briefs allowed only new files. Three lanes stopped within
minutes, because the compare and the port needed existing pages. The scope rule above
came from that.)

## 6. Parity tests when the language changes

When the port changes the language (Dart to Swift, TypeScript to Python), run the source
code on fixed inputs and save its outputs as golden values. The target tests assert the
same outputs. Do IDs, hashes, money rounding and date edges first. (line-calendar-mobile,
2026-10-28: event IDs in Swift match the Dart golden values.)

## 7. Order

1. Owner rules (section 0).
2. Refresh and pin the source (section 1).
3. Inventory, then tickets (section 2, `spine-roadmap`).
4. Source stack (section 3).
5. Lanes by wave with the shared rule file (section 5, `agent-code-dispatch`).
6. Compare pages in the lanes (section 4).
7. Merge, then QA: the same task on the source and on the target.
8. Owner acceptance closes each ticket.

## Gotchas

- **An inventory row is not parity.** Static reading misses imported components and dynamic
  fetch calls. Keep the "Evidence limits" section, and let the compare and QA prove parity.
- **Half-done target branches.** Look for them before the tickets (`git log main..<branch>`).
  Reviewed work on a branch is a start, not a conflict.
- **Two sources, two stacks.** Write one stack mapping for each source in the shared file.
- **Guards that run only in the full suite** catch missing entries late. Run the full
  suite before merge, not only the lane tests.

## Sources

- ChimesERP `docs/porting/2026-10-28-port-inventory.md` (ERP-298, with the source update
  section), `docs/decisions/2026-10-21-people-port-rules.md`.
- ChimesERP ERP-300 source-stacks runbook (people-ops 3060, ChimesFlow 3100 and 8100).
- Pairs with [[system-design]] (the target design), [[spine-roadmap]] (tickets and
  acceptance), [[agent-code-dispatch]] (lanes and review gate).
