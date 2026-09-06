---
name: Context Recovery
loop: platform
pdca: do
description: Automatically recover working context after session compaction or when continuation is implied but context is missing. Uses filesystem artifacts, git state, and project metadata.
when_to_use: when session starts with truncated context, user references prior work without details, compaction indicators appear, or user says "continue" / "where were we"
version: 1.0.0
tags: [workflow, session-management, context]
languages: all
---

# Context Recovery

Automatically recover working context after session compaction or when continuation is implied but context is missing. Since Claude Code runs in a terminal (no chat history API), recovery relies entirely on filesystem artifacts and git state.

**Core principle:** Terminal sessions leave traces in the filesystem. Git, file timestamps, project config, and memory files are your recovery sources.

## Triggers

### Automatic Triggers
- Session begins with a `<summary>` tag (compaction detected)
- User message contains compaction indicators: "Summary unavailable", "context limits", "truncated", "compacted"

### Manual Triggers
- User says "continue", "did this happen?", "where were we?", "what was I working on?"
- User references "the project", "the PR", "the branch", "the issue" without specifying which
- User implies prior work exists but context is unclear
- User asks "do you remember...?" or "we were working on..."

**Do not wait for user to ask** -- if compaction is detected, proactively recover and present context.

---

## Execution Protocol

### Step 1: Identify the Working Directory

Determine the current project from:
- The shell's working directory
- Presence of `.git/`, `package.json`, `pyproject.toml`, `Cargo.toml`, etc.

```bash
pwd
ls -la .git/ 2>/dev/null && echo "Git repo detected"
```

### Step 2: Recover Git State

Git is the richest source of context in a terminal workflow.

```bash
# Current branch and status
git branch --show-current
git status --short

# Recent commits (what was being worked on)
git log --oneline --no-decorate -15

# Uncommitted changes (work in progress)
git diff --stat
git diff --cached --stat

# Stashed work (interrupted tasks)
git stash list

# Recent branch activity (switched contexts?)
git reflog --no-decorate -20
```

**Parse for:**
- Current branch name (often describes the task)
- Uncommitted changes (active work in progress)
- Recent commit messages (what was completed)
- Stashed entries (interrupted work)
- Reflog patterns (branch switches suggest context changes)

### Step 3: Find Recently Modified Files

Since terminal scrollback is not accessible, file modification times reveal what was being touched.

```bash
# Files modified in the last 2 hours (adjust as needed)
find . -name '.git' -prune -o -name 'node_modules' -prune -o -name '.venv' -prune -o -type f -mmin -120 -print | head -30

# Check for TODO/FIXME markers in recently modified files
find . -name '.git' -prune -o -name 'node_modules' -prune -o -name '.venv' -prune -o -type f -mmin -120 -print 2>/dev/null | head -20 | xargs grep -n 'TODO\|FIXME\|HACK\|XXX\|WIP' 2>/dev/null
```

### Step 4: Read Project Context Files

Project-level instructions often describe current goals and state.

```bash
# Project instructions (may describe current task)
cat CLAUDE.md 2>/dev/null
cat .claude/CLAUDE.md 2>/dev/null
cat AGENTS.md 2>/dev/null

# Check for AGENTS.md in subdirectories (scoped instructions)
find . -maxdepth 3 -name 'AGENTS.md' 2>/dev/null
```

### Step 5: Check Claude Code Session and Memory Data

```bash
# Auto-generated memory files for this project
PROJECT_DIR=$(pwd)
PROJECT_HASH_DIRS=$(ls -d ~/.claude/projects/*/ 2>/dev/null)
for dir in $PROJECT_HASH_DIRS; do
  if [ -d "$dir/memory" ]; then
    echo "=== Memory: $dir ==="
    ls -lt "$dir/memory/" 2>/dev/null | head -5
    for f in $(ls -t "$dir/memory/"* 2>/dev/null | head -3); do
      echo "--- $f ---"
      cat "$f"
    done
  fi
done

# Project-specific CLAUDE.md managed by Claude Code
for dir in $PROJECT_HASH_DIRS; do
  if [ -f "$dir/CLAUDE.md" ]; then
    echo "=== Project CLAUDE.md: $dir ==="
    cat "$dir/CLAUDE.md"
  fi
done
```

### Step 6: Check Self-Improving Agent Learnings (if active)

```bash
# .learnings/ directory from self-improving-agent skill
if [ -d ".learnings" ]; then
  echo "=== Learnings directory found ==="
  ls -lt .learnings/ | head -10
  # Read recent learnings
  for f in $(ls -t .learnings/*.md 2>/dev/null | head -3); do
    echo "--- $f ---"
    cat "$f"
  done
fi
```

### Step 7: Synthesize Context

Compile a structured summary from all gathered evidence:

```markdown
## Recovered Context

**Project:** <project-name>
**Directory:** <working-directory>
**Branch:** <current-branch>
**Sources Used:** <which steps yielded data>

### Active Task
- **Branch:** <branch-name> (often describes the task)
- **PR:** #<number> if identifiable from branch name or commits
- **Status:** <uncommitted changes / clean / stashed work>

### Recent Work Timeline
1. <commit or action from git log>
2. <commit or action>
3. <commit or action>

### Work in Progress
- <uncommitted file changes from git status>
- <stashed entries if any>

### Pending Items
- <TODO/FIXME markers found in recently modified files>
- <incomplete actions inferred from context>

### Key References
| Type | Value |
|------|-------|
| Branch | <name> |
| Files | <recently modified paths> |
| Stash | <stash entries if any> |

### Last Identifiable Action
> "<most recent commit message or change description>"

### Confidence Level
- Git state: <high/medium/low>
- File timestamps: <high/medium/low>
- Memory/session data: <found/partial/none>
- Project docs: <found/none>
```

### Step 8: Respond with Context

Present the recovered context, then prompt:

> "Context recovered. Based on [sources], your last action was [X]. The current state is [Y]. Shall I [continue/pick up where we left off/clarify what's needed]?"

---

## Constraints

- **MANDATORY:** Execute this protocol before responding "I don't have context" or asking clarifying questions when context appears missing
- Terminal scrollback is not accessible -- rely on filesystem artifacts only
- Git history: last 15 commits and reflog of 20 entries (token budget)
- Recently modified files: cap at 30 files, last 2 hours
- Memory files: last 3 per project
- If recovery yields nothing useful, state what was attempted and what sources were empty
- Do NOT fabricate context -- report only what evidence supports

---

## Auto-Trigger Detection

At session start, scan for compaction indicators:

```
if message contains "<summary>":
    trigger_context_recovery()
elif message contains any of ["Summary unavailable", "context limits", "truncated", "compacted"]:
    trigger_context_recovery()
elif message matches continuation_patterns:
    # "continue", "where were we", "what was I working on", etc.
    trigger_context_recovery()
```

**Do not wait for user to ask** -- if compaction is detected, proactively recover and present context.

---

## Example

**Scenario:** Session starts after compaction

```
User message: "<summary>Summary unavailable due to context limits...</summary>"
User message: "continue where we left off"
```

**Agent executes:**
1. Detects compaction via `<summary>` tag
2. Runs `git branch --show-current` -> `feat/add-export-csv`
3. Runs `git status` -> 3 modified files in `src/export/`
4. Runs `git log --oneline -5` -> last commit: "add CSV header generation"
5. Finds TODO in `src/export/writer.rs`: "TODO: handle unicode in field values"
6. Reads `~/.claude/projects/*/memory/` -> finds note about CSV export feature
7. Responds:

> "Context recovered from git state and memory files. You were working on a CSV export feature (`feat/add-export-csv` branch). Last commit added CSV header generation. There are 3 uncommitted files in `src/export/` and a TODO about handling unicode in field values.
>
> **Current state:**
> - Branch: `feat/add-export-csv`
> - Uncommitted: `src/export/writer.rs`, `src/export/format.rs`, `src/export/mod.rs`
> - Pending: Unicode handling in CSV fields
>
> Shall I continue with the unicode handling, or would you like to focus on something else?"
