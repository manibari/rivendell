---
name: agent-persona
description: >
  Generate structured role prompts for headless Claude Code agents (tester, maintainer,
  reviewer, developer, researcher). Auto-injects project structure, tool permissions,
  and output format. Manages persona templates with version control.
  TRIGGER when: user says "建立 agent", "新增 tester", "agent prompt", "agent 角色",
  "create agent persona", "設定 maintainer", or is setting up a new headless agent role.
  DO NOT TRIGGER when: user wants to schedule an agent (use headless-agent/launchd-agent),
  or wants to run an existing agent.
tags: [meta]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Agent Persona

Structured role prompt generation for headless Claude Code agents.

## Built-in Roles

### tester
- **Mission**: Validate project health — tests, build, lint, structure
- **Tools**: Read, Bash, Glob, Grep (no Edit/Write)
- **Output**: Structured test report with pass/fail/warn counts
- **Cadence**: Daily or on every push

### maintainer
- **Mission**: Fix broken tests, update dependencies, resolve CI failures
- **Tools**: Read, Write, Edit, Bash, Glob, Grep
- **Output**: Commits with fixes, summary of what was changed
- **Cadence**: Daily or triggered by tester failures

### developer
- **Mission**: Implement features from issue descriptions or task lists
- **Tools**: All tools including Agent, WebFetch, WebSearch
- **Output**: Branch with implementation, PR description
- **Cadence**: On-demand

### researcher
- **Mission**: Gather information, analyze data, produce reports
- **Tools**: Read, Bash, Glob, Grep, WebFetch, WebSearch
- **Output**: Markdown report with findings
- **Cadence**: Scheduled or on-demand

### reviewer
- **Mission**: Review diffs for bugs, security issues, style violations
- **Tools**: Read, Bash, Glob, Grep (no Edit/Write)
- **Output**: Review comments with severity ratings
- **Cadence**: Per-PR

## Persona Generation Flow

### Step 1: Choose Role

Select from built-in roles or define a custom one:
- Role name and mission statement
- Allowed tools (principle of least privilege)
- Output format and destination

### Step 2: Inject Project Context

Auto-read and inject:
```
- Project name and description (from CLAUDE.md or package.json)
- Directory structure (top 2 levels)
- Tech stack (detect from package.json, pyproject.toml, etc.)
- Existing test framework and commands
- CI/CD configuration
```

### Step 3: Generate Prompt

Template structure:
```
You are a {role} agent for the {project_name} project.

## Mission
{mission_statement}

## Project Context
{auto_injected_context}

## Constraints
- Only use these tools: {allowed_tools}
- Only modify files matching: {allowed_paths}
- Never modify: {forbidden_paths}
- Maximum budget: ${budget} USD

## Output Format
{output_template}

## Task
{specific_task_or_standing_orders}
```

### Step 4: Configure Execution

Generate the corresponding entries for:
- `agents.conf` (launchd scheduling)
- `.claude/agents.json` (agent metadata)
- Wrapper script in `bin/` (execution entry point)

## Composition

Agents can be composed:
```
# tester finds issues → maintainer fixes them
tester (daily 06:00) → on failure → maintainer (auto-trigger)
```

## Version Control

Persona prompts are stored as markdown files:
```
.claude/personas/
  tester.md
  maintainer.md
  custom-researcher.md
```

When the project structure changes significantly, re-run persona generation
to update the injected context.
