---
name: ci-pipeline
loop: dev
description: >
  Detect project stack and generate GitHub Actions CI workflow with lint, test, build jobs.
  TRIGGER when: user asks to set up CI, create a pipeline, or project has no .github/workflows/ directory.
  DO NOT TRIGGER when: project already has a complete CI config and user did not ask to modify it.
tags: [meta]
version: 1
source: manual
user_invocable: false
---

# CI Pipeline Generator

Auto-detect project stack and generate GitHub Actions CI workflow + pre-commit config.

## Instructions

### Step 1: Detect Project Stack

Scan the project root (and up to 2 levels deep for monorepos) for these indicators:

| Indicator | Stack | Package Manager |
|-----------|-------|-----------------|
| `pyproject.toml` or `requirements.txt` | Python | pip / poetry / uv |
| `package.json` + `pnpm-lock.yaml` | Node.js | pnpm |
| `package.json` + `bun.lock` / `bun.lockb` | Node.js | bun |
| `package.json` + `yarn.lock` | Node.js | yarn |
| `package.json` (fallback) | Node.js | npm |
| `Package.swift` or `*.xcodeproj` | iOS/macOS | swift / xcodebuild |
| `Cargo.toml` | Rust | cargo |
| `go.mod` | Go | go |
| `Dockerfile` or `docker-compose.yml` | Docker | docker |
| `firebase.json` | Firebase | firebase-tools |

Also detect:

| Indicator | Tool |
|-----------|------|
| `[tool.ruff]` or `ruff` in deps | ruff (Python linter) |
| `[tool.black]` or `black` in deps | black (Python formatter) |
| `[tool.mypy]` or `mypy` in deps | mypy (type checker) |
| `pytest` in deps or `[tool.pytest]` | pytest |
| `eslint` in package.json deps/scripts | eslint |
| `prettier` in package.json deps/scripts | prettier |
| `vitest` in package.json deps/scripts | vitest |
| `jest` in package.json deps/scripts | jest |
| `next` in package.json deps | Next.js |
| `nuxt` in package.json deps | Nuxt |
| `turbo` in package.json deps/scripts | Turborepo |
| `streamlit` in Python deps | Streamlit |
| `fastapi` or `uvicorn` in Python deps | FastAPI |
| `.pre-commit-config.yaml` exists | pre-commit (already set up) |

### Step 2: Select Workflow Template

Based on detected stack, choose the appropriate CI pattern:

#### Python project (FastAPI / Streamlit / library)

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt  # or: pip install -e ".[dev]"
      - name: Lint
        run: ruff check .  # or: black --check .
      - name: Type check
        run: mypy .  # only if mypy detected
      - name: Test
        run: pytest
```

#### Node.js project (Next.js / Nuxt)

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ["20", "22"]
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4  # only if pnpm
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: pnpm  # or npm / yarn
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint  # eslint
      - run: pnpm test  # vitest / jest
      - run: pnpm build
```

#### pnpm monorepo (Turborepo)

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo lint
      - run: pnpm turbo test
      - run: pnpm turbo build
```

#### iOS / Xcode project

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: macos-15
    steps:
      - uses: actions/checkout@v4
      - name: Select Xcode
        run: sudo xcode-select -s /Applications/Xcode_16.2.app
      - name: Build and test
        run: |
          xcodebuild test \
            -scheme $SCHEME_NAME \
            -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' \
            -resultBundlePath TestResults \
            | xcpretty
```

#### Full stack (Python + Node.js)

Use parallel jobs: one for backend (Python lint + test), one for frontend (Node lint + test + build). Each job follows its respective single-stack template above.

#### Docker project

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker images
        run: docker compose build
      - name: Run tests
        run: docker compose run --rm app pytest  # adapt command
```

### Step 3: Generate `.github/workflows/ci.yml`

1. Create `.github/workflows/` directory if it doesn't exist
2. Write the workflow file based on detected stack
3. Adapt the template:
   - Replace placeholder commands with actual project scripts (check `package.json` scripts, `Makefile` targets, `pyproject.toml` scripts)
   - Set correct Python/Node versions based on project config
   - Add cache configuration for the detected package manager
   - If project uses environment variables, add a comment about required GitHub Secrets

### Step 4: Generate Pre-commit Config (if missing)

If `.pre-commit-config.yaml` does NOT exist, generate one based on detected tools:

#### Python project

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

#### Node.js project

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.18.0
    hooks:
      - id: eslint
        additional_dependencies:
          # list project's eslint plugins here
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
```

#### Full stack

Combine both Python and Node.js hooks.

If `.pre-commit-config.yaml` already exists, skip this step and note it in the report.

### Step 5: Report

Show a summary of what was generated:

```
Project: ~/my-project
Detected stack: Python 3.12 (FastAPI, ruff, pytest), Docker

Generated:
  ✅ .github/workflows/ci.yml
     Jobs: lint-and-test (Python 3.11, 3.12)
     Triggers: push to main, pull_request
  ✅ .pre-commit-config.yaml
     Hooks: ruff, ruff-format

Secrets needed:
  (none for this config)

Next steps:
  1. Review the generated workflow
  2. Run: git add .github/ .pre-commit-config.yaml && git commit
  3. Push to trigger CI: git push
  4. Install pre-commit hooks locally: pre-commit install
```

### Adaptation Rules

- **Never hardcode secrets** — use `${{ secrets.NAME }}` and note required secrets
- **Always pin action versions** — use `@v4` not `@latest`
- **Use `--frozen-lockfile`** (pnpm) / `--ci` (npm) / `--frozen-lockfile` (yarn) — never modify lockfile in CI
- **Cache aggressively** — use built-in cache in setup-node/setup-python actions
- **Fail fast** — don't continue on lint failure
- If the project has a `Makefile` with `lint`, `test`, `build` targets, prefer `make lint`, `make test`, `make build` in the workflow for consistency
