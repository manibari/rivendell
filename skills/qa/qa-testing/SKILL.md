---
name: qa-testing
description: >
  Cross-framework test strategy and writing guidance for pytest, Vitest, and Swift Testing.
  TRIGGER when: user writes tests, asks about testing strategy, mocking patterns,
  test structure, or says "write tests" / "add test coverage".
  DO NOT TRIGGER when: debugging (use systematic-debugging), reviewing existing code
  (use code-reviewer), or security testing (use security-review).
tags: [quality, testing]
version: 1
source: manual
user_invocable: true
---

# QA Testing

Cross-framework test authoring guidance for pytest, Vitest, and Swift Testing.

## 1. Test Philosophy

- Tests exist so you can **refactor with confidence**, not to chase coverage numbers
- A test that never fails is worthless; a test that fails for the wrong reason is worse
- Write the **minimum test that catches the bug** — then stop
- Prefer testing behavior (inputs → outputs) over testing implementation details

## 2. Decision Tree — Which Test to Write

```
Is it a pure function or single method?
  → YES → Unit test
  → NO  → Does it cross a boundary (DB, API, file system)?
            → YES → Integration test
            → NO  → Does it involve user interaction across screens?
                      → YES → E2E test
                      → NO  → Unit test with mocked dependencies
```

## 3. Test Pyramid

| Layer | Ratio | Scope | Speed |
|-------|-------|-------|-------|
| **Unit** | ~70% | Single function/class, all deps mocked | < 10ms |
| **Integration** | ~20% | Module boundaries, real deps where cheap | < 1s |
| **E2E** | ~10% | Full user flow, real UI/API | seconds |

Rules:
- If a unit test needs more than 3 mocks, consider integration instead
- E2E tests should cover critical happy paths only — don't duplicate unit coverage

## 4. AAA Pattern (All Frameworks)

Every test follows **Arrange → Act → Assert**:

```
Arrange: Set up inputs, mocks, fixtures
Act:     Call the function / trigger the action (ONE call)
Assert:  Verify the output or side effect
```

Keep each section visually separated. One Act per test — if you need two, split into two tests.

## 5. Framework Templates

### Auto-detection

Before generating test code, detect the project's framework:
- `pyproject.toml` or `pytest.ini` or `conftest.py` → **pytest**
- `vitest.config.*` or `package.json` with `vitest` → **Vitest**
- `Package.swift` or `*.xcodeproj` with `Testing` import → **Swift Testing**
- `*.xcodeproj` with UI test target → **XCUITest**

Only output templates for the detected framework(s). If multiple apply (e.g. monorepo), ask which to target.

### pytest (Python)

```python
import pytest
from unittest.mock import MagicMock, patch

# Fixture for reusable setup
@pytest.fixture
def mock_db():
    db = MagicMock()
    db.query.return_value = [{"id": 1, "name": "test"}]
    return db

# Basic test
def test_get_user_returns_user_when_exists(mock_db):
    # Arrange
    service = UserService(db=mock_db)
    # Act
    result = service.get_user(user_id=1)
    # Assert
    assert result.name == "test"
    mock_db.query.assert_called_once()

# Parametrize for multiple cases
@pytest.mark.parametrize("input_val,expected", [
    ("hello", "HELLO"),
    ("", ""),
    ("123", "123"),
])
def test_to_upper(input_val, expected):
    assert to_upper(input_val) == expected

# Patching external dependencies
@patch("myapp.services.requests.get")
def test_fetch_data_handles_timeout(mock_get):
    mock_get.side_effect = TimeoutError()
    with pytest.raises(ServiceUnavailableError):
        fetch_data("https://api.example.com")
```

### Vitest (TypeScript)

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock entire module
vi.mock('./api', () => ({
  fetchUser: vi.fn(),
}))

import { fetchUser } from './api'
import { getUserName } from './user-service'

describe('getUserName', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns name when user exists', async () => {
    // Arrange
    vi.mocked(fetchUser).mockResolvedValue({ id: 1, name: 'Alice' })
    // Act
    const name = await getUserName(1)
    // Assert
    expect(name).toBe('Alice')
    expect(fetchUser).toHaveBeenCalledWith(1)
  })

  it('throws when user not found', async () => {
    vi.mocked(fetchUser).mockRejectedValue(new Error('Not found'))
    await expect(getUserName(999)).rejects.toThrow('Not found')
  })
})
```

### Swift Testing

```swift
import Testing
@testable import MyApp

@Suite("UserService Tests")
struct UserServiceTests {
    let sut: UserService
    let mockRepo: MockUserRepository

    init() {
        mockRepo = MockUserRepository()
        sut = UserService(repository: mockRepo)
    }

    @Test("returns user when ID exists")
    func getUserReturnsUser() async throws {
        // Arrange
        mockRepo.stubbedUser = User(id: 1, name: "Alice")
        // Act
        let user = try await sut.getUser(id: 1)
        // Assert
        #expect(user.name == "Alice")
        #expect(mockRepo.getCallCount == 1)
    }

    @Test("throws notFound when ID missing")
    func getUserThrows() async {
        mockRepo.stubbedUser = nil
        await #expect(throws: UserError.notFound) {
            try await sut.getUser(id: 999)
        }
    }

    @Test("validates email format", arguments: [
        ("alice@example.com", true),
        ("not-an-email", false),
        ("", false),
    ])
    func validateEmail(email: String, isValid: Bool) {
        #expect(EmailValidator.isValid(email) == isValid)
    }
}
```

### XCUITest

```swift
import XCTest

final class LoginUITests: XCTestCase {
    let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = false
        app.launchArguments = ["--ui-testing"]
        app.launch()
    }

    func test_login_withValidCredentials_showsHome() {
        // Arrange — use accessibility identifiers, not labels
        let emailField = app.textFields["login_email_field"]
        let passwordField = app.secureTextFields["login_password_field"]
        let loginButton = app.buttons["login_submit_button"]

        // Act
        emailField.tap()
        emailField.typeText("alice@example.com")
        passwordField.tap()
        passwordField.typeText("password123")
        loginButton.tap()

        // Assert
        XCTAssertTrue(app.staticTexts["home_welcome_label"].waitForExistence(timeout: 5))
    }
}
```

## 6. Mock & Stub Patterns

### Python — MagicMock + @patch

```python
# Prefer dependency injection over @patch where possible
# Use @patch only for module-level imports you can't inject

mock = MagicMock()
mock.method.return_value = "value"        # Stub return
mock.method.side_effect = Exception("!")  # Stub exception
mock.method.assert_called_once_with(42)   # Verify call
```

### TypeScript — vi.mock + vi.fn

```typescript
// Module mock — hoisted automatically
vi.mock('./module', () => ({ fn: vi.fn() }))

// Inline mock
const callback = vi.fn().mockReturnValue(42)
const asyncFn = vi.fn().mockResolvedValue({ ok: true })

// Spy on existing
const spy = vi.spyOn(obj, 'method')
```

### Swift — Protocol-based mocks

```swift
// 1. Define protocol
protocol UserRepository {
    func getUser(id: Int) async throws -> User
}

// 2. Production implementation
struct APIUserRepository: UserRepository { ... }

// 3. Test mock
final class MockUserRepository: UserRepository {
    var stubbedUser: User?
    var getCallCount = 0

    func getUser(id: Int) async throws -> User {
        getCallCount += 1
        guard let user = stubbedUser else { throw UserError.notFound }
        return user
    }
}
```

Always prefer protocol-based DI in Swift. Avoid swizzling or reflection-based mocking.

## 7. Test Naming

Use a consistent format across all frameworks:

```
test_<action>_<condition>_<expected>
```

| Framework | Example |
|-----------|---------|
| pytest | `test_get_user_when_id_exists_returns_user` |
| Vitest | `it('returns user when id exists')` inside `describe('getUser')` |
| Swift Testing | `@Test("returns user when ID exists") func getUser...` |
| XCUITest | `func test_login_withValidCredentials_showsHome()` |

Rules:
- Describe behavior, not implementation
- Include the condition that differentiates this test from siblings
- Never use `test1`, `test2`, or generic names

## 8. Integration with Other Skills

| After using... | QA Testing suggests... |
|----------------|----------------------|
| **systematic-debugging** | Write a regression test that reproduces the fixed bug |
| **code-reviewer** | Add missing test coverage identified in review |
| **security-review** | (Out of scope — security tests are handled by security-review) |

When fixing a bug with systematic-debugging, always suggest:
> "Bug fixed. Want me to write a regression test to prevent this from recurring?"

## 9. Quick Reference Cheatsheet

| Task | pytest | Vitest | Swift Testing |
|------|--------|--------|---------------|
| Test function | `def test_x():` | `it('x', () => {})` | `@Test func x()` |
| Assertion | `assert x == y` | `expect(x).toBe(y)` | `#expect(x == y)` |
| Exception | `pytest.raises(E)` | `expect().rejects.toThrow()` | `#expect(throws: E)` |
| Setup | `@pytest.fixture` | `beforeEach(() => {})` | `init()` |
| Parametrize | `@pytest.mark.parametrize` | `it.each([...])` | `@Test(arguments:)` |
| Mock | `MagicMock()` | `vi.fn()` | Protocol + manual mock |
| Module mock | `@patch('mod.fn')` | `vi.mock('./mod')` | Inject via protocol |
| Skip | `@pytest.mark.skip` | `it.skip(...)` | `@Test(.disabled())` |
| Run subset | `pytest -k "name"` | `vitest run file` | `swift test --filter` |
