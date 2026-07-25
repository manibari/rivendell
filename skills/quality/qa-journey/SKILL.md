---
name: qa-journey
description: >
  Persona-driven journey QA — simulate a REAL user (with limited knowledge and patience)
  completing an end-to-end task through the UI, and report UX friction, not bugs.
  The simulated user may only act on what is visible on screen (no direct URL jumps),
  and every violation is logged to a friction ledger (WIRING_GAP / LOST / DEAD_END /
  CONTEXT_LOSS / UNLABELED). Orthogonal to gstack-qa: gstack-qa answers "does each
  feature work", qa-journey answers "can a human actually get through the flow".
  TRIGGER when: user says "/qa-journey", "旅程測試", "走一遍使用者流程", "模擬使用者",
  "UX 體驗測試", "persona QA", or complains that QA feels like a disconnected feature
  checklist; also after a user-flow diagram exists and needs live validation.
  DO NOT TRIGGER when: hunting functional bugs page-by-page (use gstack-qa / qa-only),
  writing test code (use qa-testing), planning test cases from a diff (use qa-planner),
  or designing the flow diagram itself (use user-flow).
when_to_use: when a web app needs end-to-end UX validation through a persona's eyes — task completion, navigation wiring, and friction measurement rather than functional bug hunting
version: 1.0.0
tags: [quality, ux, journey, persona]
languages: all
user_invocable: true
---

# QA Journey — Persona-Driven Journey Testing

Functional QA tests **nodes** (does each page work). UX dies on the **edges** (can the
user get from step A to step B without getting lost). This skill walks the app as a
specific persona with a specific task, under constraints that force human-like
navigation, and produces a **friction report** — a measurable account of where a real
user would get stuck.

**Announce at start:** "I'm using the qa-journey skill to walk this flow as [persona]."

## Why the constraints matter (read this before running)

An agent that has read the codebase navigates by omniscience: it jumps straight to
`/invoices/new` because it knows that route exists. A real user cannot do that — they
can only click what the UI shows them. Every time you are *forced* to cheat (jump a
URL, guess a hidden route), you have found a **wiring gap**: a step the product never
connected for the user. The cheat ledger IS the UX report. Do not avoid cheating by
being clever; cheat when stuck, and **record it**.

## Step 0 — HARD GATE: load persona + journey (do not skip)

1. **Persona card**: look for `docs/personas/*.md` in the target project.
   - Found → Read the card. Use ONLY its **rule layer** (規則層) to drive behavior;
     the narrative layer is background color, not instructions.
   - Not found → create one now from
     [references/persona-card-template.md](references/persona-card-template.md).
     Ask the user 3 things (who is the user, what task, how tech-savvy) and fill the
     rule layer with concrete values. Save to the target project's `docs/personas/`.
2. **Journey source**: look for `docs/flows/*.md` (user-flow Mermaid diagrams).
   - Found → the happy path of the relevant flow becomes the journey's expected route.
   - Not found → derive a one-line task journey from the persona's goal. Note in the
     report that no flow SoT existed (that itself is a finding).
3. **Entry point + completion check**: from the persona card. If the card lacks a
   verifiable completion check, stop and fix the card first — "walked around a bit"
   is not a journey.

## Step 1 — Compile the persona into run rules

Translate card fields into the session's operating rules. The card is data; this table
is the compiler:

| Card field (rule layer) | Becomes |
|---|---|
| 目標 (task language) | The ONE task to complete; completion check = pass/fail |
| 知識邊界: 不知道 | Forbidden actions (typically: direct URL nav, internal feature names in search) |
| 耐心閾值 | Numeric triggers for LOST / DEAD_END events |
| 在乎什麼 | Severity weighting when scoring friction events |

Baseline constraints (apply regardless of persona, unless the card overrides):

- **Entry point only**: navigate directly to the entry URL once. After that, every
  navigation must originate from a visible, clickable element on the current screen.
- **No source peeking**: do not consult the codebase, sitemap, or route files during
  the walk. What the screen shows is all you know.
- **Carry state**: you have a memory of what you did ("I just created invoice #123").
  If a later step can't find earlier output, that's a CONTEXT_LOSS event, not a retry.

## Step 2 — Walk the journey, keep the ledger

Use the browser harness (`/gstack-browse` if available, otherwise Playwright/headless
Chrome directly). At each step: screenshot, decide as the persona would, act, record.

Ledger event types:

| Event | Definition | When to record |
|---|---|---|
| `LOST` | Couldn't find the entry to the next step within patience threshold | After N failed scans of the screen (N from persona card, default 2) |
| `DEAD_END` | Gave up on a path; no visible way forward or back | After patience exhausted (default 3 attempts); then allowed ONE cheat to continue |
| `WIRING_GAP` | Forced to jump a URL / use out-of-persona knowledge to proceed | Every single cheat, no exceptions — this is the核心 metric |
| `CONTEXT_LOSS` | Output of a previous step not reachable/visible in the current step | e.g. created a record, next screen can't find it |
| `UNLABELED` | Acted on an element only because of prior knowledge — its label alone would not have told a new user what it does | Judgment call; screenshot required |

Each ledger entry: step number, screen (screenshot path), what the persona was trying
to do, what happened, event type. Functional bugs found along the way (500s, broken
buttons) go in a separate list — they are gstack-qa territory, report them but do not
let them dominate the friction narrative.

## Step 3 — Friction report

Write to `reports/qa-journey-<flow>-<persona>-YYYY-MM-DD.md` in the target project
(or print inline for interactive runs). ALWAYS use this structure:

```markdown
# Journey Report: <task> as <persona>
- Completion: DONE / ABANDONED at step N (completion check: pass/fail)
- Steps taken: N (expected from flow SoT: M)
- Friction score: X events — WIRING_GAP n / LOST n / DEAD_END n / CONTEXT_LOSS n / UNLABELED n

## Wiring gaps (接線 backlog — highest value section)
每個 WIRING_GAP 一條：從哪個畫面、想去哪、為什麼過不去、建議接線（入口/導引/預設值）

## Journey log
逐步：screenshot + persona 內心話（我在找什麼、我點了什麼、為什麼）

## Functional bugs (hand off to gstack-qa / fix flow)
```

The wiring-gap section is the deliverable: it maps 1:1 to "缺的不多，是沒串" work items
— each gap is a candidate lever (see Product Evolution Strategy: lever-first).

## Step 4 — Regression across releases

Journey definitions (persona card + flow) live in the target repo and are stable
across releases. Re-running the same journey after changes gives comparable friction
scores. When re-running, diff against the previous report: gaps closed, gaps opened,
step count delta. A UX regression = friction score went up on an unchanged journey.

## Boundaries

- This skill does not fix anything — report only (like qa-only). Fixes route to the
  normal implement → gstack-review pipeline, using the wiring-gap backlog as input.
- Persona cards are product assets owned by the target project (`docs/personas/`),
  not by this skill. This skill only ships the template.
- Future consumers of the same persona card (user-flow role branching, agentic-worker
  prompts via agent-persona) read other projections of the card — do not overwrite
  sections you don't own.
