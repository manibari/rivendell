---
name: github-repo-audit
loop: dev
pdca: check
description: >
  Audit a GitHub repository for structure quality, documentation coverage, CI/CD health,
  dependency freshness, and code hygiene. Produces a scored report with actionable fixes.
  TRIGGER when: user says "audit repo", "檢查 repo", "repo 健康度", "code audit",
  "review this repository", or wants a quality assessment of a codebase.
  DO NOT TRIGGER when: user wants a security-focused audit (use gstack-cso),
  or wants to review a specific PR diff (use gstack-review).
tags: [quality]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Bash, Glob, Grep, WebFetch, WebSearch"
---

# GitHub Repo Audit

Systematic repository quality assessment with scored report.

## Audit Dimensions

### 1. Structure (0-10)
- [ ] Has README.md with project description, setup instructions, usage
- [ ] Has LICENSE file
- [ ] Has .gitignore appropriate for the stack
- [ ] Logical directory structure (src/, tests/, docs/, etc.)
- [ ] No large binary files committed
- [ ] No secrets or credentials in history

### 2. Documentation (0-10)
- [ ] README covers: what, why, how to install, how to use, how to contribute
- [ ] API documentation exists (if applicable)
- [ ] Architecture decision records or ARCHITECTURE.md
- [ ] CHANGELOG.md with recent entries
- [ ] Code comments on non-obvious logic (not over-commented)

### 3. CI/CD (0-10)
- [ ] CI pipeline exists (.github/workflows/, .gitlab-ci.yml, etc.)
- [ ] Tests run on every PR
- [ ] Linting/formatting enforced
- [ ] Build step succeeds
- [ ] Deploy pipeline defined (if applicable)

### 4. Dependencies (0-10)
- [ ] Lock file committed (package-lock.json, poetry.lock, etc.)
- [ ] No known critical vulnerabilities (npm audit, pip-audit)
- [ ] Dependencies reasonably up-to-date (no major version gaps > 2)
- [ ] No unused dependencies

### 5. Code Hygiene (0-10)
- [ ] Consistent formatting (prettier, black, gofmt, etc.)
- [ ] No dead code or commented-out blocks
- [ ] Test coverage exists (even if not 100%)
- [ ] Error handling present at system boundaries
- [ ] No TODO/FIXME/HACK older than 6 months without tracking issue

## Audit Process

1. **Clone or read** the repository
2. **Detect stack** from manifests (package.json, pyproject.toml, go.mod, Cargo.toml)
3. **Run checks** for each dimension
4. **Score** each dimension 0-10 with evidence
5. **Produce report** with composite score and top-3 actionable improvements

## Report Format

```markdown
# Repo Audit: {repo_name}

**Composite Score: {score}/50** ({grade})

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Structure | 8/10 | Missing LICENSE |
| Documentation | 6/10 | README lacks setup instructions |
| CI/CD | 9/10 | Full pipeline with deploy |
| Dependencies | 7/10 | 3 outdated major versions |
| Code Hygiene | 8/10 | Good coverage, minor dead code |

## Top 3 Actions
1. Add LICENSE file (MIT recommended for this project type)
2. Add "Getting Started" section to README
3. Update react from v17 to v18

## Detailed Findings
[Per-dimension breakdown with evidence]
```

## Grading Scale

| Score | Grade | Meaning |
|-------|-------|---------|
| 45-50 | A | Production-ready, well-maintained |
| 35-44 | B | Good shape, minor improvements needed |
| 25-34 | C | Functional but needs attention |
| 15-24 | D | Significant issues, not ready for collaboration |
| 0-14 | F | Needs major restructuring |
