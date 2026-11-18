---
name: qa-feature-tree
loop: dev
pdca: check
description: >
  One feature tree per system (module > screen > control > case) as the single list of what
  the system can do, and three checks against it: tree vs folders (each source file has one
  module owner), tree vs screens (a headless scan finds each button that no one explains and
  each button the tree expects but the screen lost), tree vs tests (each leaf has an end-to-end
  test that passed). The report gives one number the owner can read: leaves, passed, failed,
  no test. Complete = each leaf has a passing browser test through the real API to a fixture
  store; a unit test does not count.
  TRIGGER when: "功能樹", "每個按鈕都要測", "把流程變成樹", "測試涵蓋每個功能",
  "不要只有 unit test", "feature tree", "control coverage", the owner asks how much of a
  system is tested, or a system needs a list of every control before its QA plan.
  DO NOT TRIGGER when: test cases for one diff (qa-planner); unit tests for functions
  (qa-auto / qa-testing); bug hunting on a live page (gstack-qa); one persona walks one task
  (qa-journey); checking where the data goes (qa-dataflow); drawing one feature's screen
  flow (user-flow).
when_to_use: when a system needs a full list of its controls and a measured test coverage of each one, not of its functions
version: 1.0.0
tags: [quality, testing, e2e, coverage]
languages: all
user_invocable: true
---

# QA Feature Tree

Each other QA skill starts from a diff, a page, a path, or a claim. This one starts from the
whole system. It answers one question: **is each control of the system tested, and which ones
are not?**

| Skill | Answers |
|---|---|
| `qa-feature-tree` | Is each control tested? How many are not? |
| `gstack-qa` | Does this page have bugs now? |
| `qa-journey` | Can a person finish this task? |
| `qa-dataflow` | Does the data go where the design says? |
| `qa-planner` | What must I test for this diff? |

Design and history: `docs/plans/2026-11-18-qa-feature-tree-skill.md`.

## The tree

`docs/qa/feature-tree.json` in the product repo. One file per system.

```
system
└─ module        one owner of code (folder globs)
   └─ screen     one route, plus the states that show hidden controls
      └─ control one button / link / input: what it does, success, failure
         └─ case one leaf: happy, empty, invalid input, no permission, ...
```

- Fields, layout screens, states, steps, and the scan contract: [references/tree-schema.md](references/tree-schema.md).
- The seven case kinds, and when `na` is honest: [references/case-kinds.md](references/case-kinds.md).
- Leaf ID = `<module>.<screen>.<control>.<case>`. A test names its leaf with the tag `@leaf:<id>`.
- Write the file only through `tree_check.py fmt`. People read `docs/qa/feature-tree.md`, which `render` makes.

Set `T=~/.claude/skills/qa-feature-tree/scripts` and `REPO=$(git rev-parse --show-toplevel)`.
Run `tree_check.py` from the repo root. Run `screen_scan.mjs` from the app directory: it
loads Playwright from there.

## Step 0: find or make the tree

If `docs/qa/feature-tree.json` exists, go to Step 1.

Existing system (bootstrap):

1. Write a tree file with only `schema`, `system`, `config` (template in tree-schema.md).
2. `python3 $T/tree_check.py init docs/qa/feature-tree.json` adds draft modules and screens from the route files. It prints the source files that no module owns. Give each one an owner.
3. Start the app on test ports (never the production ports). In the app directory, run
   `node $T/screen_scan.mjs --tree $REPO/docs/qa/feature-tree.json --out /tmp/scan.json`.
4. `python3 $T/tree_check.py adopt docs/qa/feature-tree.json --scan /tmp/scan.json` adds each
   control found as a draft with `does: "unknown"`.
5. Read the handler of each control (the control, then the API, then the store). Write `does`,
   `success`, `failure`, `evidence` (`file:line`). If you cannot tell why the control exists,
   keep `unknown`. Do not guess.
6. Add a case for each of the seven kinds, or `na` with a reason.
7. Show the owner three lists: the `unknown` controls, the Chinese module names, the `na`
   reasons. The owner decides each `unknown`: give it a meaning, or remove the control.

New system: `system-design` §3 writes the modules with `status: planned`. `mockup` gives the
screens and the controls.

## Step 1: run the three checks

```bash
python3 $T/tree_check.py report docs/qa/feature-tree.json \
  --scan /tmp/scan.json --e2e-report <config.e2e_report> \
  --out docs/qa/feature-tree-report-$(date +%F).md
```

The first line of the report is the answer for the owner:

> 葉子 N 片：通過 P、失敗 F、沒有測試 U、未執行 R、不適用 X。紅燈 K 項，黃燈 Y 項。

| Check | Red | Yellow |
|---|---|---|
| Tree | `KIND_MISSING`, `UNKNOWN_PURPOSE`, `NO_EVIDENCE` | - |
| Folders | a file with no module or two modules; a module with no file | `MIXED_FOLDER` |
| Routes | `UNMAPPED_ROUTE`, `MISSING_ROUTE` | - |
| Screens | `ORPHAN`, `MISSING`, `UNLABELED` | `NOT_REACHED` |
| Tests | `no-test`, `failed`, `STALE` | `not-run` |

`MIXED_FOLDER` is input for a restructure (`system-design` §3.1). It does not block.

## Step 2: write the leaf tests

The executor writes the tests (`agent-code-dispatch`), one brief for each module. Put these
rules in each brief:

1. Drive the real UI in a browser. Go through the real API to the real store. Assert the
   result on the screen and in the store.
2. Do not mock app code or API responses.
3. Two exceptions, each declared on the case so the report shows it:
   `dependency-down` aborts the request at the network layer (`page.route(...).abort()`);
   `side-effect` with `boundary: recorder` sends the outside call (launchd, docker, mail) to a
   recorder that logs it. The test asserts the logged call.
4. Fixture store for each run, reset before each test file. Never the production store or the
   production ports.
5. A failed leaf is a bug report. Do not change the test to make it pass. The fix is a
   separate ticket.

The executor sandbox cannot start a browser. Claude runs the Playwright suite after review.

## Step 3: after a change

`qa-planner` maps the changed files to modules (by their globs), then to their leaves, and
runs the tests of those leaves. Run the full report before a release.

## What "complete" means

Each leaf has at least one end-to-end test that passed in the latest run, and the tree,
folder, route, and screen checks have no red rows. All combinations of cases are out of
scope: a finite leaf count is what makes progress measurable.

## Self-deception to avoid

- **`na` to make the number look good.** `na` needs a reason that a person can check, for
  example "no login: one local user". "Not important" is not a reason.
- **A unit test as a leaf test.** Only tests in `config.e2e_dirs` count.
- **`unknown` filled in by guess.** A guessed purpose hides the one finding the owner needs.
- **A recorder that is not declared.** Each recorder case has `boundary: recorder`. A hidden
  stub is a mock.
- **`NOT_REACHED` counted as fine.** It means the scan never saw those controls. Add the state
  steps, or the check is not complete.
- **The production app as the test target.** The harness must refuse the production ports.

## Files

- `scripts/tree_check.py` and `scripts/feature_tree/`: validate, fmt, init, adopt, folders,
  routes, screens, tests, render, report. Standard library only.
- `scripts/screen_scan.mjs` and `scripts/aria_parse.mjs`: the headless scan. It loads
  Playwright from the app directory.
- `scripts/tests/`: unit tests (`python3 -m unittest discover -s scripts/tests -p 'test_*.py'`,
  `node --test scripts/tests/aria_parse.test.mjs`) and one browser test that Claude runs.
- Pilot: the rivendell dashboard, `apps/dashboard-web/e2e/` (ports 3005 and 8005).
