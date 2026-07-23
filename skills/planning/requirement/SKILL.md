---
name: requirement
description: >
  Define structured requirements, user stories, and acceptance criteria for a feature.
  TRIGGER when: user says "define requirement", "write user story", "what should we build",
  or describes a feature idea without clear scope.
  DO NOT TRIGGER when: requirements already exist and user is asking to implement.
tags: [workflow]
version: 1
source: manual
user_invocable: true
---

# Requirement Definition

Produce a structured requirement document before any design or implementation begins.

**Announce at start:** "I'm using the Requirement skill to define the scope."

## Instructions

### Step 0: Demand Validation (via gstack-office-hours)

Before writing user stories, validate the "why".

**If the feature is new and hasn't been through office hours yet**, invoke `/gstack-office-hours` first.
It will expose: demand reality, status quo, desperate specificity, and narrowest wedge.

Skip Step 0 if:
- The user explicitly says "skip office hours" or "直接做"
- A design doc from `/gstack-office-hours` already exists in `docs/`

### Step 1: Clarify the Goal

Ask the user (skip questions they already answered):

1. **Who** is the target user?
2. **What** problem does this solve?
3. **Why** now — what's the trigger or business context?

### Step 2: Write User Stories

For each distinct user action, produce:

```markdown
### US-{N}: {title}

**As a** {role}
**I want to** {action}
**So that** {benefit}

**Acceptance Criteria:**
- [ ] Given {context}, when {action}, then {result}
- [ ] Given {context}, when {edge case}, then {fallback}
```

Rules:
- One story per user action — don't bundle
- Acceptance criteria must be testable (no "should be nice")
- Include at least one error/edge case per story

### Step 3: Define Scope Boundary

Produce a two-column table:

| In Scope | Out of Scope |
|----------|-------------|
| ... | ... |

This prevents scope creep later.

### Step 4: Output

Save to `docs/requirements/{feature-name}.md` (ask user for feature name if unclear).

### Step 5: Handoff

After saving, prompt:

> **Requirement complete.** Follow the gstack UI workflow:
>
> | Step | Skill | Purpose |
> |------|-------|---------|
> | 2 | `/user-flow` | Screen transitions + branches |
> | 3 | `/gstack-design-consultation` | Design system / brand direction |
> | 4 | `/gstack-design-shotgun` | Generate design variants, pick one |
> | 5 | `/mockup` → `/gstack-design-html` | Finalize static HTML |
> | 6 | `/planning-with-files` → `/gstack-plan-eng-review` | Implementation task list + architecture review |
>
> Next: `/user-flow`
