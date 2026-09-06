---
name: dev-process-gate
loop: dev
pdca: plan
description: >
  Enforce development workflow: requirement → user-flow → wireframe → mockup → development → QA testing.
  TRIGGER when: user asks to build a feature, create a page, or implement UI functionality
  without providing requirements or design artifacts first, OR when development is complete
  and no tests have been written yet.
  DO NOT TRIGGER when: requirements/flows already exist and tests are written, or task is
  a bug fix, refactor, CLI tool, or backend-only change with no UI.
tags: [meta]
version: 1
source: manual
user_invocable: false
---

# Development Process Gate

Ensure the team follows the design-first workflow before writing code.

## Workflow Stages

```
0. Demand          1. Requirement  →  2. User Flow  →  3. Design           →  4. Mockup           →  5. Development                              →  6. QA           →  7. CI/CD
   /gstack-            /requirement      /user-flow     /gstack-design-        /mockup →               /planning-with-files →                       /gstack-qa          /ci-pipeline
   office-hours                                         consultation +         /gstack-design-html     /gstack-plan-eng-review
                                                        /gstack-design-
                                                        shotgun
```

## Instructions

When the user requests a new feature or page, check what artifacts exist before proceeding.

### Step 1: Detect Existing Artifacts

Look for these in the current project:

| Stage | Look for | Location |
|-------|---------|----------|
| Demand validation | Office-hours design doc | `docs/design-*.md` |
| Requirement | User stories, acceptance criteria | `docs/requirements/` |
| User Flow | Mermaid flowcharts, screen inventory | `docs/flows/` |
| Design | Design consultation + shotgun outputs | `docs/design/` |
| Mockup | Finalized static HTML | `docs/mockups/` |
| QA Testing | Test files matching the feature | `tests/`, `__tests__/`, `*Tests/` |

Also check if the user mentioned or linked any of these in their message.

### Step 2: Report Status & Guide

Report what's missing and suggest the next step:

**If no office-hours design doc and feature is new:**
> Before writing requirements, let's validate the "why".
> I'll run `/gstack-office-hours` to check demand reality and narrowest wedge.

**If no requirement:**
> Before building, let's define what we're building.
> I'll use `/requirement` to create user stories and scope.

**If requirement exists but no flow:**
> Requirements look good. Let's map the user journey next.
> I'll use `/user-flow` to create a flowchart.

**If flow exists but no design direction:**
> Flow is defined. Let's align on design system and brand before sketching.
> I'll use `/gstack-design-consultation` to set direction, then `/gstack-design-shotgun` to generate variants.

**If design direction exists but no finalized mockup:**
> Design direction is set. Let's lock the static layout.
> I'll use `/mockup` → `/gstack-design-html` to produce finalized HTML.

**If all design stages complete but no implementation plan:**
> All design artifacts are ready. Let's plan the implementation.
> I'll use `/planning-with-files` → `/gstack-plan-eng-review` (and `/gstack-plan-design-review` for UI tasks).

**If development is complete but no tests:**
> Implementation looks done. Before we call it finished, let's verify it works.
> I'll use `/gstack-qa` for headless browser flow tests and `/gstack-design-review` for visual consistency.

Specifically check:
1. **Acceptance criteria coverage** — each criterion in the requirement should have at least one test
2. **UI behavior tests** — key user interactions from the user-flow should be tested (use webapp-testing for web, XCUITest for iOS)
3. **Unit tests** — core logic added during development should have unit tests

**If all stages complete including tests but no CI:**
> Tests look good. I notice this project has no CI config (`.github/workflows/`).
> Consider running `/ci-pipeline` to generate a GitHub Actions workflow.

This is a suggestion, not a hard gate — skip if the user is not interested.

**If all stages complete including tests:**
> Feature is complete with tests. Ready for code review.
> Run **code-reviewer** for a final check if desired.

### Step 3: Respect Overrides

If the user explicitly says to skip a stage (e.g., "just code it", "skip wireframe"), comply but note:

> Skipping wireframe stage as requested. You can always revisit with `/user-flow`.

Do NOT block the user — this is guidance, not a hard gate.

### When NOT to Gate

Skip this check entirely for:
- Bug fixes and patches
- Refactoring or code cleanup
- CLI tools, scripts, configs
- Backend-only changes with no UI
- Tasks where the user provides complete specs in their message
