---
name: init-project
loop: dev
description: >
  Initialize Claude Code project config files (AGENTS.md, .claude/CLAUDE.md).
  TRIGGER when: starting a new project, onboarding Claude to an existing project,
  user says /init-project, or no CLAUDE.md / AGENTS.md detected in project root.
  DO NOT TRIGGER when: project already has both config files.
tags: [meta]
version: 1
user_invocable: false
---

# init-project

Set up the multi-level Claude Code config for a new or existing project.

## Instructions

### Step 1: Detect project context

Scan the current project root for:
- `package.json` → framework, dependencies, scripts
- `pyproject.toml` / `requirements.txt` → Python project
- `Cargo.toml` → Rust project
- `go.mod` → Go project
- `tsconfig.json` → TypeScript
- Existing `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/settings.json`
- `.git/` → git repo status
- Existing test files → test runner and patterns

Summarize what you found before proceeding.

### Step 2: Create AGENTS.md (cross-tool, team-shared)

If `AGENTS.md` does not exist, create it at the project root. This file is read by all AI tools (Claude Code, Cursor, Copilot, etc.) and should go into git.

Template — fill in based on detected context, leave TODOs for unknowns:

```markdown
# AGENTS.md

## Project Overview

<!-- One paragraph: what this project does, who it's for -->

## Tech Stack

<!-- List detected frameworks, languages, key dependencies -->

## Build & Run

<!-- Key commands: install, dev, build, test, lint -->

## Project Structure

<!-- Top-level directory layout with brief descriptions -->

## Coding Style

<!-- Language-specific conventions detected from config/existing code -->

## Testing

<!-- Test runner, patterns, how to run -->

## Git Commit

<!-- Commit message format, branch naming -->
- Use conventional commits: `type(scope): description`
- Types: feat, fix, refactor, docs, test, chore

## Definition of Done

- Tests pass
- Linter clean
- Builds successfully
- PR reviewed
```

### Step 3: Create .claude/CLAUDE.md (Claude-specific)

If `.claude/CLAUDE.md` does not exist, create it. This file is for Claude Code-specific behavior that other AI tools don't understand.

```markdown
# Claude Code Project Settings

@AGENTS.md

## Workflow

- Read existing code before modifying
- Verify changes compile/pass before claiming done
- Prefer editing existing files over creating new ones

## Context Management

- Use subagents for independent parallel tasks
- Use plan mode for tasks requiring 10+ steps
```

### Step 4: Add .claude.local.md to .gitignore

If `.gitignore` exists but doesn't include `.claude.local.md`, append it:

```
# Claude Code local overrides
.claude.local.md
```

### Step 5: Report

Show what was created/skipped:

```
Created:
  - AGENTS.md (cross-tool team config)
  - .claude/CLAUDE.md (Claude-specific settings, imports AGENTS.md)
  - .gitignore updated (added .claude.local.md)

Skipped:
  - [file] already exists

Next steps:
  - Review and customize AGENTS.md with your project specifics
  - Add .claude.local.md for personal local overrides (not in git)
  - Restart Claude Code to pick up new config
```
