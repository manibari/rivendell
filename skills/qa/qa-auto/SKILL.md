---
name: QA Auto
description: >
  Auto-generate test code from QA plan or code diff, execute tests, and report coverage gaps.
  TRIGGER when: user says /qa-auto, "auto generate tests", "自動產生測試", QA plan exists and needs execution,
  or qa-planner just completed.
  DO NOT TRIGGER when: manually writing tests (use qa-testing), only running existing tests (use post-change-qa),
  planning what to test (use qa-planner), or debugging test failures (use systematic-debugging).
when_to_use: when test code needs to be auto-generated from a QA plan or code changes, then executed
version: 1.0.0
tags: [quality, testing, automation]
languages: all
user_invocable: true
---

# QA Auto

Auto-generate test code from QA plans or code diffs, execute tests, and report results with coverage analysis.

## Position in Workflow

```
qa-planner → QA AUTO → post-change-qa
(what to test)  (generate + run)  (visual verify)
              ^^^^^^^^^^^
              you are here
```

## Phase 1: Input Detection

### 1.1 Determine Input Source

Check in priority order:

1. **QA Plan exists** — read `docs/qa/qa-plan-*.md` for structured test cases
2. **Explicit diff** — user provides specific files or a PR
3. **Working directory diff** — `git diff --name-only` for uncommitted changes
4. **Recent commits** — `git log --oneline -5` for the latest feature

### 1.2 Detect Test Framework

Auto-detect the project's test framework (same as qa-testing):

| Indicator | Framework | Test Dir |
|-----------|-----------|----------|
| `conftest.py` or `pytest` in deps | pytest | `tests/` |
| `vitest` in package.json | Vitest | `__tests__/` or `*.test.ts` |
| `jest` in package.json | Jest | `__tests__/` or `*.test.js` |
| `Package.swift` with Testing | Swift Testing | `Tests/` |
| `*.xcodeproj` with test target | XCUITest | `*UITests/` |

### 1.3 Detect Existing Test Patterns

Before generating tests, read existing tests to match project conventions:

```bash
# Find existing test files
find . -name "*.test.*" -o -name "test_*.py" -o -name "*Tests.swift" | head -10
```

Extract patterns:
- **Import style** — absolute vs relative imports
- **Mock strategy** — DI, `@patch`, `vi.mock`, protocol-based
- **Fixture patterns** — shared fixtures, factory functions
- **Naming convention** — `test_x_when_y_returns_z` vs `it('should...')`
- **File organization** — mirror src structure vs flat

## Phase 2: Test Generation

### 2.1 Generation Strategy

For each function/component that needs tests:

1. **Read the source code** — understand inputs, outputs, side effects
2. **Identify test boundaries** — what to mock, what to keep real
3. **Generate test cases** — from QA plan (if exists) or from code analysis
4. **Match project style** — use detected conventions from Phase 1.3

### 2.2 Per-Function Test Generation

For each changed function, generate:

```
1. Happy path test (valid input → expected output)
2. Edge case tests (empty, null, boundary values)
3. Error handling tests (invalid input, dependency failures)
4. Regression test (if fixing a bug — reproduce the bug first)
```

### 2.3 Framework-Specific Templates

#### pytest

```python
import pytest
from unittest.mock import MagicMock, patch
# Import from project (match existing style)

class TestFeatureName:
    """Tests for [changed function/class]."""

    @pytest.fixture
    def setup(self):
        """Shared setup matching project conventions."""
        # Arrange common dependencies
        pass

    def test_happy_path(self, setup):
        # Arrange
        # Act
        result = function_under_test(valid_input)
        # Assert
        assert result == expected_output

    @pytest.mark.parametrize("input_val,expected", [
        # Edge cases from QA plan
        ("", None),            # empty input
        (None, None),          # null input
        ("boundary", "edge"),  # boundary value
    ])
    def test_edge_cases(self, input_val, expected):
        result = function_under_test(input_val)
        assert result == expected

    def test_error_handling(self):
        with pytest.raises(ExpectedError, match="message"):
            function_under_test(invalid_input)
```

#### Vitest

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
// Import from project (match existing style)

describe('FeatureName', () => {
  // Shared setup matching project conventions
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('handles valid input correctly', async () => {
    // Arrange
    // Act
    const result = await functionUnderTest(validInput)
    // Assert
    expect(result).toEqual(expectedOutput)
  })

  it.each([
    ['empty', '', null],
    ['null', null, null],
    ['boundary', 'edge', 'result'],
  ])('handles %s input', async (_desc, input, expected) => {
    const result = await functionUnderTest(input)
    expect(result).toEqual(expected)
  })

  it('throws on invalid input', async () => {
    await expect(functionUnderTest(invalidInput))
      .rejects.toThrow('expected message')
  })
})
```

#### Swift Testing

```swift
import Testing
@testable import AppName

@Suite("FeatureName")
struct FeatureNameTests {
    // Shared setup
    let sut: FeatureUnderTest

    init() {
        sut = FeatureUnderTest()
    }

    @Test("handles valid input correctly")
    func happyPath() async throws {
        let result = try await sut.function(validInput)
        #expect(result == expectedOutput)
    }

    @Test("handles edge cases", arguments: [
        ("empty", "", nil),
        ("boundary", "edge", "result"),
    ])
    func edgeCases(desc: String, input: String, expected: String?) {
        let result = sut.function(input)
        #expect(result == expected)
    }

    @Test("throws on invalid input")
    func errorHandling() async {
        await #expect(throws: FeatureError.invalid) {
            try await sut.function(invalidInput)
        }
    }
}
```

### 2.4 Integration Test Generation

For API endpoints or cross-boundary changes:

```python
# pytest example for FastAPI
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_resource_returns_201():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/resource", json={
            "name": "test",
            "value": 42,
        })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test"

async def test_create_resource_validates_input():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/resource", json={})
    assert response.status_code == 422
```

### 2.5 File Placement

Place generated tests to match project conventions:

| Convention | Pattern |
|-----------|---------|
| **Mirror structure** | `src/services/user.py` → `tests/services/test_user.py` |
| **Co-located** | `src/services/user.ts` → `src/services/user.test.ts` |
| **Flat** | All tests in `tests/` or `__tests__/` |

Detect which convention the project uses from existing test files.

## Phase 3: Execute Tests

### 3.1 Run Generated Tests

```bash
# Python
python -m pytest tests/test_new_feature.py -v --tb=short

# TypeScript
npx vitest run src/feature.test.ts

# Swift
swift test --filter FeatureNameTests
```

### 3.2 Handle Failures

When generated tests fail:

1. **Test logic error** (our test is wrong) → fix the test
2. **Missing mock/fixture** → add the missing setup
3. **Actual bug found** → report to user, do NOT auto-fix production code
4. **Flaky test** (passes sometimes) → add retry or fix timing

Decision flow:

```
Test fails
  → Is the assertion wrong? → Fix test, re-run
  → Is a mock missing? → Add mock, re-run
  → Does the code have a bug? → Report: "Found potential bug in X"
  → Maximum 2 fix attempts per test, then report as-is
```

### 3.3 Coverage Analysis

After tests pass, check coverage if the project has it configured:

```bash
# Python
python -m pytest --cov=src --cov-report=term-missing tests/test_new_feature.py

# TypeScript
npx vitest run --coverage src/feature.test.ts
```

## Phase 4: Report

### 4.1 Results Summary

```markdown
## QA Auto Results

### Generated Tests
| File | Tests | Pass | Fail | Coverage |
|------|-------|------|------|----------|
| `tests/test_user_service.py` | 8 | 8 | 0 | 92% |
| `tests/test_api_users.py` | 5 | 4 | 1 | 85% |
| **Total** | **13** | **12** | **1** | **89%** |

### Failures
- `test_api_users.py::test_create_user_duplicate_email`
  - Expected: 409 Conflict
  - Got: 500 Internal Server Error
  - **Likely bug**: duplicate email handling not implemented

### Coverage Gaps
- `services/user.py:78-85` — error recovery path not covered
- `services/user.py:102` — admin-only branch not tested

### Next Steps
- [ ] Fix duplicate email handling (bug found)
- [ ] Add test for admin-only branch (coverage gap)
- [ ] Run `/post-change-qa` for visual verification
```

### 4.2 Handoff

After reporting:
- If all pass → suggest running `post-change-qa` for visual verify
- If failures found → ask user whether to investigate (use systematic-debugging)
- If coverage gaps → ask user whether to add more tests

## Rules

1. **Never modify production code** — only generate test files
2. **Match existing conventions** — read existing tests before generating
3. **Maximum 2 fix attempts** per failing test — then report as-is
4. **Report bugs, don't fix them** — if a test reveals a real bug, tell the user
5. **Don't over-test** — follow the test pyramid (70% unit, 20% integration, 10% E2E)
6. **Skip trivial code** — don't test getters/setters, constants, or type definitions
7. **Ask before writing E2E tests** — they're slow and expensive, confirm with user first

## Integration with Other Skills

| Skill | Relationship |
|-------|-------------|
| **qa-planner** | Reads QA plan as input; if no plan exists, does lightweight analysis |
| **qa-testing** | Uses qa-testing's framework templates and mock patterns |
| **post-change-qa** | Hands off to post-change-qa for server restart + visual verify |
| **systematic-debugging** | If generated tests reveal bugs, suggest systematic-debugging |
| **code-reviewer** | Generated tests can be reviewed with code-reviewer |

## Skip Conditions

- User says "skip tests", "不用測", "先不寫"
- No test framework detected and user doesn't want to set one up
- Change is trivial (only comments, whitespace, or docs)
- Tests already exist with adequate coverage for the changed code
