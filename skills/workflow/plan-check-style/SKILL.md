---
name: plan-check-style
loop: dev
description: >
  Scan available style skills and load matching design conventions when entering plan mode for UI tasks.
  TRIGGER when: Claude enters plan mode AND the task involves frontend UI,
  styling, component creation, or layout work.
  DO NOT TRIGGER when: backend-only tasks, CLI tools, scripts, or non-UI work.
tags: [meta]
version: 1
user_invocable: false
---

# plan-check-style

## Instructions

When you enter plan mode for a task that involves frontend UI or styling, you MUST do the following BEFORE writing your plan:

### Step 1: Scan available style skills

Read all SKILL.md files under `~/.claude/skills/` and identify skills that have a `tags` field containing `style` or `frontend`.

List them in a summary like:

```
Found style skills:
- react-tailwind: React + Tailwind CSS conventions
- vue-scss: Vue 3 + SCSS conventions
```

### Step 2: Detect project context

Check the current project for clues:
- `package.json` → look for framework dependencies (react, vue, svelte, angular, etc.)
- `tailwind.config.*`, `postcss.config.*` → CSS tooling
- `tsconfig.json` → TypeScript usage
- Existing component files → naming patterns, file structure

### Step 3: Ask the user to confirm

Use AskUserQuestion to present the detected context and matching style skills. Example:

```
Detected: React + Tailwind (from package.json)
Matching style skill: react-tailwind
```

Options:
- Use detected style skill (recommended)
- [List other available style skills]
- No style skill — use defaults

### Step 4: Apply the chosen skill

Once the user confirms, load and follow the chosen style skill's instructions for the remainder of the plan and implementation.

If no style skills are installed, skip this process silently and proceed with defaults.
