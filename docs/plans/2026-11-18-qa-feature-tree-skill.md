# Skill design: `qa/qa-feature-tree`

- **Date**: 2026-11-18
- **Status**: design. Waiting for owner approval of §10.
- **Source**: owner, 2026-11-18: 「系統架構與資料夾的關係」「每個功能跟按鈕都有意義，QA 應該要把所有流程變成一個樹狀的結構，並完全測試吧」「現在好像都是針對 unit test」

---

## 1. Problem

Each QA skill starts from a different input. No skill starts from "all controls of the system".

| Skill | Starts from | Produces | Gap |
|---|---|---|---|
| `qa-planner` | git diff | test cases per changed function | A control that did not change is never listed |
| `qa-auto` | QA plan or diff | unit and integration tests per function | Tests functions, not controls on a screen |
| `qa-testing` | one function | test code patterns | Mocks by default |
| `gstack-qa` | a running app | bugs, page by page | No list of what it did not touch |
| `qa-journey` | one persona, one task | friction report | One path per run, by design |
| `qa-dataflow` | a written claim | data path gap table | Checks stores, not controls |
| `user-flow` | one feature | Mermaid flow of screens | One feature, no tests |
| `system-design` §3.1 | a design | target folder tree | Used once at design time. Nothing checks the code later |

Result: the owner cannot get this answer: "The tree has 200 leaves. Tests cover 170. These 30 are not covered."

## 2. Decision

- Add one skill: `skills/qa/qa-feature-tree/`. `loop: dev`. `pdca: check`.
- Each system keeps one tree file: `docs/qa/feature-tree.json`. This file is the single source for three checks (§4).
- **Definition of complete** (「完全測試」): every leaf has at least one end-to-end test that passed in the latest run, and checks 1 and 2 have no red rows.
- All combinations of cases are out of scope. A finite leaf count is necessary to measure progress.
- Do not extend `qa-planner` or `qa-auto`. They start from a diff. This skill starts from the whole system.

## 3. The tree

```
system
└─ module        one owner of code (folder globs)
   └─ screen     one route, plus the states that show hidden controls
      └─ control one button / link / input: what it does, success, failure
         └─ case one leaf: happy, empty, invalid input, no permission, ...
```

### 3.1 Fields

| Level | Required fields | Optional fields |
|---|---|---|
| system | `schema`, `system`, `config` | - |
| module | `id`, `name_zh`, `paths` (globs) | `status: planned`, `blueprint_id` |
| screen | `id`, `route` (not for a layout screen) | `layout: true`, `sample` (values for dynamic routes), `states` |
| control | `id`, `role`, `name`, `does`, `evidence`, `success`, `failure`, `cases` | `state`, `repeat: true` |
| case | `id`, `kind`, `expect` | `status: na` + `na_reason`, `boundary: recorder` |

- **Leaf ID** = `<module>.<screen>.<control>.<case>`. Kebab case. Do not reuse an ID after you remove a leaf.
- A test names its leaf with the tag `@leaf:<id>`.
- `name` is the accessible name. It can be a regular expression for a repeated control (one card per agent).
- `does: "unknown"` is a red row. It means that no person can say why the control exists. The owner decides: give it a meaning, or remove the control.
- `evidence` is `file:line` of the handler. The handler is the start of the path: control, then API, then store.

### 3.2 Case kinds

`references/case-kinds.md` defines seven kinds:

| Kind | Question |
|---|---|
| `happy` | Does the normal action give the correct result on screen and in the store? |
| `empty` | What does the screen show when there is no data? |
| `invalid-input` | Does the app reject bad input with a clear message? |
| `no-permission` | Does the app stop a user without the right role? |
| `dependency-down` | What does the screen show when the API or a service fails? |
| `repeat` | Is a double click or a second submit safe? |
| `side-effect` | Does the action call the correct outside system (launchd, docker, mail) with the correct values? |

For each control, write each kind as a case, or as `status: na` with a reason. A kind that is not written is a red row. This rule stops silent gaps.

### 3.3 Example (illustrative names)

```json
{
  "schema": 1,
  "system": "rivendell-dashboard",
  "config": {
    "source_roots": ["apps/dashboard-web/src", "apps/dashboard-api/routes"],
    "route_files": ["apps/dashboard-web/src/app/**/page.tsx"],
    "e2e_dirs": ["apps/dashboard-web/e2e"],
    "e2e_report": "apps/dashboard-web/e2e/.results/report.json",
    "base_url": "http://127.0.0.1:<test-port>"
  },
  "modules": [{
    "id": "tokens", "name_zh": "Token 用量",
    "paths": ["apps/dashboard-web/src/app/tokens/**", "apps/dashboard-api/routes/monitoring/token_*.py"],
    "screens": [{
      "id": "main", "route": "/tokens",
      "states": [{"id": "waste", "steps": [{"click": {"role": "tab", "name": "浪費報告"}}]}],
      "controls": [{
        "id": "waste-tab", "role": "tab", "name": "浪費報告",
        "does": "Show the newest token waste report",
        "evidence": "apps/dashboard-web/src/app/tokens/page.tsx:120",
        "success": "Report text shows; the date matches the newest file",
        "failure": "A message says that no report exists",
        "cases": [
          {"id": "happy", "kind": "happy", "expect": "Newest report shows"},
          {"id": "empty", "kind": "empty", "expect": "Message: no report yet"},
          {"id": "api-down", "kind": "dependency-down", "expect": "Error message, page stays usable"},
          {"id": "no-perm", "kind": "no-permission", "status": "na", "na_reason": "No login. One local user."}
        ]
      }]
    }]
  }]
}
```

### 3.4 Layout, states, and steps

- A screen with `"layout": true` holds the controls that show on every screen (the sidebar, the top bar). It has no `route`. The scan does not open it alone. Check 2 matches its controls on every scanned screen.
- A control with no `state` belongs to the state `default`. The state `default` is the page right after it loads, with no steps.
- A step is one object with one key:

| Step | Value | Action |
|---|---|---|
| `click` | `{"role", "name"}` | Click the element `getByRole(role, {name, exact: true})` |
| `fill` | `{"role", "name", "value"}` | Type `value` into the element |
| `press` | `{"key"}` | Press one key, for example `Escape` |
| `goto` | `"/path"` | Open a path under `config.base_url` |
| `wait_for` | `{"role", "name"}` | Wait until the element is visible |

- `sample` gives one value for each dynamic segment: route `/agents/[label]`, sample `{"label": "com.sk.agent.demo"}`.
- `route_style` in `config` is `next-app` in this version: `app/<segments>/page.tsx` gives `/<segments>`. Route groups `(name)` are removed. `[x]`, `[...x]`, and `[[...x]]` stay in the route text.

### 3.5 Scan file contract (`scan.json`)

`screen_scan.mjs` writes this file. `tree_check.py screens` reads it.

```json
{
  "schema": 1,
  "base_url": "http://127.0.0.1:3190",
  "scanned_at": "2026-11-19T10:00:00+08:00",
  "screens": [
    {"module": "tokens", "screen": "main", "state": "default",
     "url": "http://127.0.0.1:3190/tokens", "reached": true, "error": null,
     "controls": [{"role": "button", "name": "重新整理"}, {"role": "link", "name": ""}]}
  ]
}
```

- One entry for each non-layout screen and state, including `default`.
- `reached: false` and a text in `error` when the page or a step fails. Then `controls` is empty.
- `controls` lists each node with a role from §4 check 2. A repeated control shows one time for each copy. A control with no name has `"name": ""`.

Check 2 compare rules, for one entry (module, screen, state):

1. Matchers: the controls of this screen with this state, the controls of this screen with state `default`, and the controls of each layout screen.
2. A scanned control with an empty name is `UNLABELED`.
3. A scanned control that no matcher matches is `ORPHAN`. A match needs the same role, and the same name. A tree name in the form `/.../` is a regular expression that must match the full name.
4. A tree control of this screen with this state that matches no scanned control is `MISSING`.
5. A layout control is `MISSING` only when it matches no control in any reached `default` entry.
6. If `reached` is false, or the entry does not exist, each tree control of that screen and state is `NOT_REACHED`.

### 3.6 Format

- JSON, because Python and Node read it with no extra package. PyYAML is not installed on this machine.
- All writes go through `tree_check.py fmt`. It writes one canonical order and layout. Then a change of one leaf gives a diff of a few lines (global rule: no full re-serialization noise).
- People read the tree as `docs/qa/feature-tree.md`. The script makes this file from the JSON. Do not edit the Markdown file.

## 4. Three checks

### Check 1: tree vs folders (`tree_check.py folders`)

| Result | Meaning | Severity |
|---|---|---|
| A source file matches no module glob | Code with no owner | red |
| A source file matches two module globs | The boundary is not clean | red |
| A module glob matches no file | Module in the tree, no code (except `status: planned`) | red |
| One folder holds files of two or more modules | Structure drift from `system-design` §3.1 | yellow (input for a restructure, does not block) |

### Check 2: tree vs screens (`screen_scan.mjs`, then `tree_check.py screens`)

- For each screen and each state, open the page in Playwright, do the steps, and read the accessibility tree (`locator.ariaSnapshot()`).
- Roles: button, link, textbox, searchbox, combobox, checkbox, radio, switch, tab, menuitem, slider.

| Result | Code | Severity |
|---|---|---|
| On the screen, not in the tree | `ORPHAN`: no person says what it does | red |
| In the tree, not on the screen | `MISSING`: the entry is broken or removed | red |
| Control with no accessible name | `UNLABELED` (same code as `qa-journey`) | red |
| Route file with no screen in the tree | `UNMAPPED_ROUTE` | red |
| The scan did not reach the state of a control | `NOT_REACHED` | yellow, never counts as passed |

### Check 3: tree vs tests (`tree_check.py tests`)

- Find `@leaf:<id>` tags in the files under `config.e2e_dirs`. Read the latest Playwright JSON report.
- Each leaf gets one status: `passed`, `failed`, `no-test`, or `na`.
- A tag with an ID that is not in the tree is red `STALE`.
- Only tests in `config.e2e_dirs` count. A unit test does not cover a leaf.

### Rules for a leaf test

1. Drive the real UI in a browser. Go through the real API to the real store. Assert the result on the screen and in the store.
2. Do not mock app code. Do not mock API responses.
3. Two exceptions. The case must declare each one, so the report shows it:
   - `dependency-down`: abort the request at the network layer (`page.route(...).abort()`).
   - `side-effect` with `boundary: recorder`: a recorder replaces the outside system (for example, a fake `launchctl` first on `PATH`). The recorder writes each call to a log. The test asserts the logged call. The real outside system never runs.
4. Test data: a fixture store for each run. Reset it before each test file. Never use the production store or the production ports.

### Report

`docs/qa/feature-tree-report-YYYY-MM-DD.md`. First line:

> 葉子 N 片：通過 P、失敗 F、沒有測試 U、未執行 R、不適用 X。紅燈 K 項，黃燈 Y 項。

The owner reads this line, so it is in Traditional Chinese (2026-11-19: this section first said English, and the executor followed it).

Then the three check tables, then the uncovered leaves grouped by module. A failed leaf is a bug report. Do not change the test to make it pass.

## 5. Workflow of the skill

- **Step 0: find the tree.** If `docs/qa/feature-tree.json` does not exist, do the bootstrap.
- **Bootstrap, existing system:**
  1. `tree_check.py init` lists source folders and route files. It writes draft modules and screens.
  2. `screen_scan.mjs` lists the controls on each screen. It writes draft controls.
  3. Claude reads each handler and writes `does`, `success`, `failure`, `evidence`. If the meaning is not clear, write `unknown`. Do not guess.
  4. Claude adds cases for each case kind.
  5. The owner reviews three lists: `unknown` controls, module names in Chinese, `na` reasons.
- **Bootstrap, new system:** `system-design` §3 writes modules with `status: planned`. `mockup` gives screens and controls.
- **Step 1:** run the three checks. Write the report.
- **Step 2:** for uncovered leaves, write one dispatch brief for each module (`agent-code-dispatch`). The executor writes the tests.
- **Step 3, after a change:** `qa-planner` maps changed files to modules (by globs), then to leaves, and runs the tests of those leaves.

## 6. Changes to existing skills

| Skill | Change |
|---|---|
| `system-design` §3.1 | If `docs/qa/feature-tree.json` exists, the module column comes from the tree. Add each new module to the tree with `status: planned`. |
| `qa-planner` §1.3 | If a tree exists, the impact radius is the modules whose globs match the diff, and their leaves. |
| `spine-dev-center` rule 10 | Blueprint module ID = tree module ID. The check comes later, not in this version. |
| `qa-journey`, `qa-dataflow`, `gstack-qa` | No change to the method. Add one boundary line to each. |
| `data/routing-tests.json` | Add rows for the new trigger phrases. |

Trigger phrases (check for collisions before use): 「功能樹」「每個按鈕都要測」「把流程變成樹」「測試涵蓋每個功能」「不要只有 unit test」, "feature tree", "control coverage".

Boundaries:

- `qa-feature-tree`: is each control of the system tested, and how many are not?
- `gstack-qa`: does this page have bugs now?
- `qa-journey`: can a person finish this task?
- `qa-dataflow`: does the data go where the design says?

## 7. Skill files

```
skills/qa/qa-feature-tree/
├── SKILL.md                      Claude
├── references/tree-schema.md     Claude
├── references/case-kinds.md      Claude
├── scripts/tree_check.py         executor (stdlib only)
├── scripts/screen_scan.mjs       executor (Playwright)
└── scripts/tests/                executor
```

## 8. Pilot: rivendell dashboard

Size (counted 2026-11-18):

- 22 route files (`page.tsx`).
- About 105 controls in the source: 59 `<button>`, 28 `<Link>`, 13 `<input>`, 5 `<select>`.
- 49 API endpoints. 11 of them write.
- No front-end tests. 9 pytest files in `dashboard-api/tests`.
- Estimate: about 200 leaves (about 2 cases for each control after `na`).

Isolation (found 2026-11-18):

| Item | Where | Plan |
|---|---|---|
| Many reads of `Path.home()` (`~/.claude/projects`, `~/.claude/skills`, `~/Library/Logs/sk-agent`) | `routes/skills.py`, `routes/agents/presenter.py`, others | Set `HOME` to a fixture directory for the test API process |
| `REPORTS_DIR`, `WORKFLOW_MAP_FILE`, `RIVENDELL_LIB_DIR` | `routes/harvest.py`, `routes/workflows.py`, `server.py` | Point each one to a fixture |
| `/api/agents/{load,unload,start,install,schedule}` call `launchctl` | `routes/agents/api.py` | Recorder: fake `launchctl` first on `PATH` |
| `docker ps`, `docker inspect` | `routes/deployment.py` | Recorder: fake `docker` |
| `/api/health/disk-tree/refresh` starts a background process | `routes/monitoring/disk.py` | Recorder |
| Project create / update / delete, harvest decide, workflow update write files | `routes/projects.py`, `routes/harvest.py`, `routes/workflows.py` | Fixture copies, reset for each test file |
| Ports | `data/ports.conf` | Register new test ports. Do not use the launchd dashboard ports |

Before the harness ticket, run `qa-dataflow/scripts/seam-scan.sh` on `dashboard-api`. Each store and each side effect in its output gets a fixture or a recorder.

The pilot is done when:

- The three checks run on the dashboard and the report shows the numbers.
- Each leaf has a test or an `na` reason.
- Each failed leaf is in the report as a bug. The fix is a separate ticket.

## 9. Tickets

| # | Work | Executor | Depends on |
|---|---|---|---|
| T1 | `tree_check.py`: validate, `fmt`, `init`, `folders`, `tests`, `render`, report. Stdlib only. Unit tests with fixture repos | codex | §3 schema |
| T2 | `screen_scan.mjs`: scan screens and states, write `scan.json`. `tree_check.py screens` compares. Test on a local fixture HTML page | codex | §3 schema |
| T3 | `SKILL.md`, both references, the §6 changes, routing rows, `bin/sk readme` | Claude | T1, T2 interfaces |
| T4 | Dashboard e2e harness: fixture `HOME` and data, recorders, test ports, Playwright config, one smoke test | codex | none |
| T5 | Dashboard tree draft. Owner review of `unknown` controls | Claude + owner | T1, T2 |
| T6 | Leaf tests, one ticket for each module (about 15), in parallel lanes | codex | T4, T5 |

T1, T2, and T4 can run in parallel. The schema in §3 is the shared contract.

## 10. Risks and open items

- **Owner decision, 2026-11-19: approved** (「記錄器可以」). The recorder in §4 rule 3 is an exception to "no fake data". Without it, a test click starts or stops real launchd jobs on this machine.
- Hidden controls (modal, drawer, tab) show only after steps. Check 2 is only as complete as the `states` list. `NOT_REACHED` makes this visible.
- Repeated controls in a list: one tree entry, `repeat: true`, `name` as a pattern.
- Dynamic routes (`/agents/[label]`) need `sample` values that exist in the fixture data.
- Upkeep: each UI change must update the tree. Check 2 makes drift red, but a person must fix it. This version adds no hook. Decide after the pilot.
- After the pilot works, apply it to PTI-ARES or ChimesERP. Those repos have login, so `no-permission` cases become real.
