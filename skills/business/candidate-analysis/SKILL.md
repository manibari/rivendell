---
name: candidate-analysis
description: Interview candidate management — extract structured data from PDF resumes, analyze GitHub repos for code quality, and generate candidate profile markdown with YAML frontmatter.
tags: [workflow, hiring, recruitment]
version: 1
source: harvest-2026-03-25
user_invocable: true
---

# candidate-analysis

TRIGGER when: user says "分析履歷", "建立候選人", "evaluate candidate", "看一下這個 GitHub" (hiring context), or `/candidate-analysis`.
DO NOT TRIGGER when: researching companies (use customer-intel), general PDF reading (use office-pdf), or stock research (use investment-research).

## Workflow

### Step 1: Initialize Project Structure

If no candidate directory exists:
```
candidates/
├── profiles/          # One .md per candidate
├── resumes/           # Original PDF/DOC files
└── README.md          # Index of all candidates
```

### Step 2: Parse Resume

Input: PDF resume (user provides path or file)

1. Read PDF with the Read tool (supports PDF natively)
2. Extract structured fields:
   - Name, contact, location
   - Education (school, degree, years)
   - Work experience (company, role, duration, highlights)
   - Technical skills (languages, frameworks, tools)
   - Certifications, publications

### Step 3: Analyze GitHub (optional)

If user provides a GitHub profile URL:

1. Use `gh api users/{username}/repos --sort=updated -L 10` to list recent repos
2. For top 2-3 repos:
   - Clone or browse via `gh api repos/{owner}/{repo}/contents`
   - Assess: code organization, testing, documentation, commit patterns
   - Note: primary languages, framework choices, code style
3. Rate on a 1-5 scale:
   - Code quality, architecture sense, testing discipline, documentation

### Step 4: Generate Profile

Output: `candidates/profiles/{name}.md`

```markdown
---
name: Full Name
status: screening  # screening | phone | interview | offer | rejected
position: Target Role
source: Where found
date_added: YYYY-MM-DD
resume: ../resumes/filename.pdf
github: https://github.com/username
overall_rating: 0-5
---

# Full Name

## Summary
One paragraph assessment.

## Education
| School | Degree | Year |
|--------|--------|------|

## Experience
| Company | Role | Duration | Highlights |
|---------|------|----------|------------|

## Technical Skills
- **Languages**: ...
- **Frameworks**: ...
- **Tools**: ...

## GitHub Analysis
| Repo | Stars | Language | Assessment |
|------|-------|----------|------------|

Code quality: X/5 | Testing: X/5 | Documentation: X/5

## Interview Notes
(To be filled during interview)

## Verdict
(To be filled after evaluation)
```

### Step 5: Update Index

Append to `candidates/README.md`:

```markdown
| Name | Position | Status | Rating | Date |
|------|----------|--------|--------|------|
```

## Comparison with Existing Skills

- **customer-intel**: targets companies, produces sales intelligence
- **office-pdf**: raw PDF operations, no resume-specific extraction
- **knowledge-graph**: entity tracking in JSONL, not candidate profiles
