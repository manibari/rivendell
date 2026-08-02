---
name: setup-permissions
description: >
  Allowlist the build/test/run tools a project actually uses, so routine
  commands stop prompting. Writes narrow, tool-scoped patterns — never a
  blanket grant.
  TRIGGER when: user says /setup-permissions, or asks to reduce permission
  prompts for a project that has package.json, pyproject.toml, Makefile,
  Cargo.toml, go.mod, or other tooling indicators.
  DO NOT TRIGGER when: the user wants to stop being asked entirely — that is
  the permission-mode toggle (Shift+Tab), not an allowlist. Say so instead.
tags: [meta]
version: 2
user_invocable: true
---

# setup-permissions

Allowlist the tools a project actually uses, based on what is detected in the
project root.

## What this skill does NOT do

It does **not** make Claude stop asking. No allowlist can:

- Compound commands (`cd x && npm install | tail`) still prompt if any segment
  is unmatched.
- Patterns are matched literally, so a one-off with different spacing is a
  different rule.

The only blanket bypass is the permission mode itself — **Shift+Tab** to cycle
to bypass mode, or `claude --dangerously-skip-permissions`. That is the user's
switch to throw, deliberately. If that is what they are asking for, tell them
plainly instead of writing a wider allowlist and implying it is equivalent.

## Instructions

When invoked, follow these steps:

### Step 1: Ensure global baseline exists

Read `~/.claude/settings.json`. If it doesn't have a `permissions` key, write this baseline (preserving other keys like `enabledPlugins`, `alwaysThinkingEnabled`).

The baseline is deliberately small. Claude Code already auto-allows most
read-only commands (`cat`, `ls`, `head`, `grep`, `find`, `git status`,
`git log`, `gh pr view`, …) with no rule at all, so listing them buys nothing.
What the baseline adds is only the handful of read-only tools that are *not*
auto-allowed.

**Never put these in the global baseline** — each is arbitrary code execution
or unbounded mutation, and a global grant applies to every project at once:

`bash *` · `sh *` · `source *` · `python *` · `node *` · `curl *` · `wget *`
· `rm *` · `chmod *` · `kill *` · `pkill *` · `osascript *` · `brew *`
· `git *` · `gh *` · `./bin/*` · `./scripts/*` · any leading-wildcard pattern
(`* --version`, `* -h`) — a leading `*` matches **every binary on the system**.

Project-local tooling (`npm`, `cargo`, `./bin/*`) belongs in Step 3, scoped to
the one project that actually uses it.

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep",
      "WebSearch",
      "WebFetch(domain:github.com)",
      "WebFetch(domain:npmjs.com)",
      "WebFetch(domain:pypi.org)",
      "WebFetch(domain:docs.anthropic.com)",
      "WebFetch(domain:stackoverflow.com)",
      "WebFetch(domain:developer.mozilla.org)",
      "WebFetch(domain:localhost)",
      "Bash(jq *)",
      "Bash(tree *)",
      "Bash(rg *)",
      "Bash(git log *)",
      "Bash(git diff *)",
      "Bash(git show *)",
      "Bash(git status *)",
      "Bash(gh pr view *)",
      "Bash(gh pr list *)",
      "Bash(gh run list *)",
      "Bash(gh run view *)"
    ],
    "deny": []
  }
}
```

If baseline already exists, skip this step.

> **On `deny`:** v1 of this skill shipped a four-entry deny list
> (`rm -rf /`, `sudo rm -rf *`, `dd if=*`, `> /dev/sda*`). It was theatre — it
> blocked destroying the OS while the allow list permitted `rm *`, so
> `rm -rf ~/Company` sailed through. A deny list only means something when the
> allow list is narrow. With the baseline above, nothing needs denying; leave
> it empty rather than implying a safety net that isn't there.

### Step 2: Detect project tooling

Scan the current project root for these indicators:

#### Package managers & runtimes

| File | Detected Tools | Permissions to Add |
|------|---------------|-------------------|
| `package.json` | Node.js, npm | `Bash(npm *)`, `Bash(npx *)`, `Bash(node *)` |
| `package.json` with `bun.lock` / `bun.lockb` | bun | `Bash(bun *)`, `Bash(bunx *)` |
| `package.json` with `yarn.lock` | yarn | `Bash(yarn *)` |
| `package.json` with `pnpm-lock.yaml` | pnpm | `Bash(pnpm *)`, `Bash(pnpx *)` |
| `pyproject.toml` or `requirements.txt` | Python | `Bash(python *)`, `Bash(python3 *)`, `Bash(pip *)`, `Bash(pip3 *)` |
| `pyproject.toml` with `[tool.poetry]` | poetry | `Bash(poetry *)` |
| `uv.lock` or `[tool.uv]` in pyproject | uv | `Bash(uv *)` |
| `Cargo.toml` | Rust | `Bash(cargo *)`, `Bash(rustc *)` |
| `go.mod` | Go | `Bash(go *)` |
| `Gemfile` | Ruby | `Bash(bundle *)`, `Bash(ruby *)`, `Bash(rake *)` |

#### Apple / Xcode

| File | Detected Tools | Permissions to Add |
|------|---------------|-------------------|
| `Package.swift` or `*.xcodeproj` or `project.yml` | Swift/Xcode | `Bash(swift *)`, `Bash(swiftc *)`, `Bash(xcodebuild *)`, `Bash(xcode-select *)`, `Bash(xcrun *)` |
| `project.yml` | XcodeGen | `Bash(xcodegen *)` |
| `Podfile` | CocoaPods | `Bash(pod *)` |
| iOS/macOS project (any Xcode indicator) | Simulator & macOS tools | `Bash(xcrun simctl *)`, `Bash(osascript *)`, `Bash(screencapture *)`, `Bash(plutil *)`, `Bash(defaults *)` |

#### Build & infrastructure

| File | Detected Tools | Permissions to Add |
|------|---------------|-------------------|
| `Makefile` | make | `Bash(make *)` |
| `CMakeLists.txt` | cmake | `Bash(cmake *)`, `Bash(make *)` |
| `firebase.json` or `.firebaserc` | Firebase CLI | `Bash(firebase *)` |
| `Dockerfile` or `docker-compose.yml` | Docker | `Bash(docker *)`, `Bash(docker-compose *)` |
| `k8s/` or `*.yaml` with kind: Deployment | k8s | `Bash(kubectl *)` |
| `.terraform/` or `*.tf` | Terraform | `Bash(terraform *)` |

#### Python tools (scan `pyproject.toml` and `requirements.txt`)

| Indicator | Detected Tools | Permissions to Add |
|-----------|---------------|-------------------|
| `streamlit` in deps | Streamlit | `Bash(streamlit *)` |
| `uvicorn` in deps | uvicorn | `Bash(uvicorn *)` |
| `fastapi` in deps | FastAPI dev server | `Bash(uvicorn *)`, `Bash(fastapi *)` |
| `pytest` in deps or `[tool.pytest]` | pytest | `Bash(pytest *)`, `Bash(python -m pytest *)` |
| `[tool.ruff]` or `ruff` in deps | ruff | `Bash(ruff *)` |
| `[tool.black]` or `black` in deps | black | `Bash(black *)` |
| `[tool.mypy]` or `mypy` in deps | mypy | `Bash(mypy *)` |
| `.pre-commit-config.yaml` | pre-commit | `Bash(pre-commit *)` |
| `playwright` in deps | Playwright | `Bash(playwright *)`, `Bash(python -m playwright *)` |

#### JS/TS tools (scan `package.json` scripts & deps)

| Indicator | Detected Tools | Permissions to Add |
|-----------|---------------|-------------------|
| `vitest` in scripts/deps | Vitest | `Bash(vitest *)`, `Bash(npx vitest *)` |
| `jest` in scripts/deps | Jest | `Bash(jest *)`, `Bash(npx jest *)` |
| `eslint` in scripts/deps | ESLint | `Bash(eslint *)`, `Bash(npx eslint *)` |
| `prettier` in scripts/deps | Prettier | `Bash(prettier *)`, `Bash(npx prettier *)` |
| `next` in scripts/deps | Next.js | `Bash(next *)`, `Bash(npx next *)` |
| `nuxt` or `nuxi` in scripts/deps | Nuxt | `Bash(nuxt *)`, `Bash(npx nuxi *)`, `Bash(npx nuxt *)` |
| `turbo` in scripts/deps | Turborepo | `Bash(turbo *)`, `Bash(npx turbo *)` |
| `wrangler` in scripts/deps | Cloudflare Workers | `Bash(wrangler *)`, `Bash(npx wrangler *)` |
| `tsx` in deps | tsx | `Bash(npx tsx *)` |
| `playwright` in deps | Playwright | `Bash(playwright *)`, `Bash(npx playwright *)` |

#### Database tools

| Indicator | Detected Tools | Permissions to Add |
|-----------|---------------|-------------------|
| `*.db` files or `sqlite` in deps | SQLite | `Bash(sqlite3 *)` |
| `prisma` in deps | Prisma | `Bash(npx prisma *)` |
| `drizzle` in deps | Drizzle | `Bash(npx drizzle-kit *)` |

#### Project-local scripts

Also check for project-specific CLI tools:
- `./bin/*`, `./scripts/*` -> add `Bash(./bin/*)`, `Bash(./scripts/*)`
- `Makefile` targets -> add `Bash(make <target>)` for common targets
- Extract all unique command prefixes from `package.json` scripts values

### Step 3: Write project-local permissions

Write the patterns you actually detected in Step 2 to
`.claude/settings.local.json` — one entry per detected tool, nothing wider:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm *)",
      "Bash(npx *)",
      "Bash(vitest *)",
      "Bash(docker *)",
      "Bash(./bin/*)",
      "WebFetch(domain:localhost)"
    ],
    "deny": []
  }
}
```

Rules:
- **Never write `Bash(*)`.** It allows every command in that project, which is
  the permission-mode toggle wearing a costume — and unlike the toggle, it is
  invisible and persists across sessions. If the user wants that, point them
  at Shift+Tab so the choice is theirs and visible.
- Write only patterns backed by something you actually found in the project
  root. No `Bash(cargo *)` in a repo with no `Cargo.toml`.
- Only add `WebFetch(domain:...)` entries for project-specific domains not in
  the global baseline.
- If `.claude/settings.local.json` already has entries, MERGE (don't
  overwrite) — keep existing WebFetch domains and any hand-written rules.
- **Do clean up accumulated one-off entries.** Claude Code appends a verbatim
  rule every time the user clicks "don't ask again", so these files fill up
  with dead weight like
  `Bash(curl -s -o /dev/null -w "api /docs     :%{http_code}\n" ... )` —
  matched literally, spacing included, so it will never fire again. Drop any
  entry that encodes a full one-time invocation; keep the tool-scoped ones.
- Report anything you removed (see Step 4) rather than deleting silently.

### Step 4: Report

Show a summary:

```
Project: ~/my-project
Detected: Node.js (bun), TypeScript, Vitest, Docker

Global baseline: (exists | written)

Project permissions (.claude/settings.local.json):
  Added:
    + Bash(bun *)
    + Bash(bunx *)
    + Bash(vitest *)
    + Bash(docker *)
    + Bash(docker-compose *)
    + Bash(./bin/dev *)
  Kept (existing):
    = Bash(custom-tool *)
  Cleaned up:
    - Bash(git -C /full/path/to/project commit -m "...")  (one-off, never matches again)

Still prompts: compound commands, and anything not listed above.
To stop being asked at all, use Shift+Tab (bypass mode) — this file cannot do that.

Restart Claude Code for changes to take effect.
```

The "Added" lines must be the exact strings written to the file. v1 of this
skill printed a per-tool breakdown while actually writing `Bash(*)`; the report
is not a summary of intent, it is a record of what is now on disk.
