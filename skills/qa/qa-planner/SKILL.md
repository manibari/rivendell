---
name: QA Planner
description: >
  Analyze code changes to generate a structured QA plan with impact analysis, test cases, and risk assessment.
  TRIGGER when: feature implementation is complete, before PR review, user says /qa-planner or "plan QA",
  or dev-process-gate detects missing QA stage.
  DO NOT TRIGGER when: writing test code (use qa-testing), running existing tests (use post-change-qa),
  debugging failures (use systematic-debugging), or user explicitly skips QA.
when_to_use: when a feature or fix is complete and needs a structured QA plan before testing
version: 1.0.0
tags: [quality, testing, planning]
languages: all
user_invocable: true
---

# QA Planner

Analyze code changes and generate a structured QA plan. This skill bridges the gap between "code done" and "tests written" — it tells you **what** to test before you write a single test.

## When to Use

```
writing-plans → executing-plans → [code complete] → QA PLANNER → qa-auto → post-change-qa
                                                     ^^^^^^^^^^^
                                                     you are here
```

## Phase 1: Change Analysis

### 1.1 Gather the Diff

Determine the scope of changes:

```bash
# If on a feature branch
git diff main...HEAD --stat
git diff main...HEAD --name-only

# If recent commits on main
git diff HEAD~N --stat   # N = number of commits in this feature

# If working directory has uncommitted changes
git diff --stat
git diff --name-only
```

### 1.2 Classify Changed Files

Categorize each changed file:

| Category | Pattern | Impact Level |
|----------|---------|-------------|
| **API endpoint** | `routes/`, `api/`, `views.py` | High — affects external contracts |
| **Business logic** | `services/`, `utils/`, `lib/` | High — core behavior |
| **Data model** | `models/`, `schema/`, `types/` | Critical — affects data integrity |
| **UI component** | `components/`, `pages/`, `views/` | Medium — visual regression risk |
| **Config** | `*.config.*`, `.env*`, `settings` | Medium — environment-dependent |
| **Test** | `tests/`, `__tests__/`, `*.test.*` | Low — tests themselves |
| **Docs** | `*.md`, `docs/` | None — skip |

### 1.3 Identify Impact Radius

For each changed function/class/component:

1. **Direct callers** — who calls this function? (`grep -rn "function_name"`)
2. **Downstream consumers** — what depends on the output?
3. **Shared state** — does it modify global state, DB, or cache?
4. **API surface** — does it change request/response shapes?

Output format:

```markdown
### Impact Radius

| Changed | Type | Direct Callers | Downstream Risk |
|---------|------|---------------|-----------------|
| `createUser()` | service | `POST /api/users`, `signupFlow()` | user dashboard, email service |
| `UserCard.tsx` | component | `UserList`, `ProfilePage` | visual only |
```

## Phase 2: Risk Assessment

### 2.1 Risk Matrix

Rate each change area:

| Risk Factor | Weight | Questions |
|-------------|--------|-----------|
| **Data mutation** | Critical | Does it write to DB? Can it corrupt existing data? |
| **Auth/security** | Critical | Does it touch authentication, authorization, or sensitive data? |
| **External API** | High | Does it call third-party services? New API contracts? |
| **State management** | High | Does it change how state flows? Race conditions? |
| **User-facing** | Medium | Will users see the change? Visual regression? |
| **Performance** | Medium | Does it change query patterns, loops, or data volume? |
| **Edge cases** | Medium | New input types? Null handling? Boundary values? |
| **Config/env** | Low | Environment-specific behavior? |

### 2.2 Regression Risk Zones

Identify areas NOT changed but at risk:

```markdown
### Regression Risk

- [ ] **User login flow** — `createUser()` changed, verify login still works
- [ ] **Email notifications** — user model changed, verify email templates still render
- [ ] **Mobile responsive** — new CSS added, verify mobile layout
```

## Phase 3: Test Case Generation

### 3.1 Test Case Template

For each changed function/feature, generate test cases:

```markdown
### TC-001: [Feature/Function Name]

**Scope**: unit / integration / e2e
**Priority**: P0 (must test) / P1 (should test) / P2 (nice to test)
**Changed file**: `path/to/file.py:42`

#### Happy Path
- [ ] Input: valid data → Expected: success response / correct state
- [ ] Input: typical use case → Expected: expected behavior

#### Edge Cases
- [ ] Input: empty/null → Expected: graceful error
- [ ] Input: boundary values (0, max, negative) → Expected: handled
- [ ] Input: unicode/special chars → Expected: no crash

#### Error Cases
- [ ] Input: invalid data → Expected: validation error with message
- [ ] Dependency failure (DB down, API timeout) → Expected: error handling
- [ ] Auth: unauthorized user → Expected: 401/403

#### Regression
- [ ] Existing functionality X still works after change
- [ ] Related feature Y not broken
```

### 3.2 Priority Assignment

| Priority | Criteria | Action |
|----------|----------|--------|
| **P0** | Data mutation, auth, money, core flow | Must test before merge |
| **P1** | User-facing, API contracts, state changes | Should test before merge |
| **P2** | Edge cases, performance, cosmetic | Can test after merge |

### 3.3 Test Type Recommendation

Based on the change type, recommend test approaches:

| Change Type | Recommended Tests |
|-------------|------------------|
| Pure function added/modified | Unit test with parametrize |
| API endpoint added/modified | Integration test (HTTP client) |
| DB model changed | Migration test + integration test |
| UI component changed | Snapshot test + visual verify |
| Auth flow changed | Integration test + E2E |
| Config/env changed | Environment-specific integration test |

## Phase 4: Output QA Plan

### 4.1 Document Format

Save to `docs/qa/qa-plan-YYYY-MM-DD-<feature>.md`:

```markdown
# QA Plan: [Feature Name]

**Date**: YYYY-MM-DD
**Branch**: feature/xxx
**Changed files**: N files, +X/-Y lines

## Summary
[1-2 sentence overview of what changed and why it matters for QA]

## Impact Analysis
[From Phase 1]

## Risk Assessment
[From Phase 2]

## Test Cases
[From Phase 3]

## Test Execution Order
1. P0 unit tests (fastest feedback)
2. P0 integration tests
3. P1 tests
4. Visual verification (if UI changed)
5. P2 tests (if time permits)

## Coverage Gaps
[List any areas that CANNOT be automatically tested and need manual verification]
```

### 4.2 Summary Report

After generating the plan, present a concise summary:

```
## QA Plan Summary

| Metric | Value |
|--------|-------|
| Changed files | 12 |
| Impact radius | 8 downstream consumers |
| Risk level | High (DB migration + API change) |
| P0 test cases | 6 |
| P1 test cases | 11 |
| P2 test cases | 4 |
| Estimated effort | ~30 min (unit) + ~15 min (integration) |

Proceed with `/qa-auto` to generate and execute tests?
```

## Integration with Other Skills

| Skill | Handoff |
|-------|---------|
| **executing-plans** | After plan execution completes → qa-planner runs |
| **qa-auto** | qa-planner output feeds into qa-auto for test generation |
| **qa-testing** | qa-planner recommends frameworks; qa-testing provides templates |
| **post-change-qa** | After qa-auto completes → post-change-qa runs visual verify |
| **review-pr** | qa-planner output can be attached to PR for reviewer context |
| **dev-process-gate** | dev-process-gate triggers qa-planner when QA stage is missing |

## Skip Conditions

- User says "skip QA", "不用測", "先不跑"
- Only docs/config changed (no code changes)
- Change is a WIP (user says "還沒好", "still working")
- Tests already exist and cover the changes (verified by coverage check)
