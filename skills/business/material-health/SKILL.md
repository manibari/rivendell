---
name: material-health
description: "Health check for the sales materials library — detects missing frontmatter, expired subsidies, stale company info, and orphaned files."
tags: [automation, health-check, sales-enablement, maintenance]
version: 1
source: manual
user_invocable: true
when_to_use: "TRIGGER when: user says /material-health, '素材檢查', 'check materials', or invoked by headless agent on schedule. DO NOT TRIGGER when: user is editing specific materials or building a presentation."
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Material Health Check

Weekly health check for the `materials/` library. Detects issues and generates a report.

## Checks

### 1. Case Studies — Frontmatter Completeness

```
Glob: materials/case-studies/*.md (exclude INDEX.md)
For each file, verify frontmatter has ALL required fields:
  - client (non-empty)
  - industry (non-empty)
  - solution_type (non-empty array)
  - year (number)
  - outcome (non-empty)
```

Report missing or empty fields.

### 2. Subsidies — Expired Programs

```
Glob: materials/subsidies/programs/*.md (not archived/)
For each file, read frontmatter:
  - If deadline < today → flag as "應歸檔"
  - If status != "active" but not in archived/ → flag as "狀態不一致"
```

### 3. Company Info — Staleness

```
For each file in materials/company/:
  - Check file modification date (via ls -la or stat)
  - If older than 90 days → flag as "超過 90 天未更新"
  - Check for TODO placeholders → flag as "尚未填入"
```

### 4. INDEX Consistency

```
Verify:
  - case-studies/INDEX.md lists all .md files in directory
  - solutions/INDEX.md lists all .md files in subdirectories
  - subsidies/INDEX.md matches programs/*.md count
```

### 5. Orphaned Files

```
Check for files not referenced in any INDEX:
  - Case studies not in INDEX.md
  - Solutions not in INDEX.md
```

## Output Format

Generate a report at `materials/HEALTH_REPORT.md`:

```markdown
# Materials Health Report

> Generated: {datetime}

## Summary

| Check | Status | Issues |
|-------|--------|--------|
| Case study frontmatter | {pass/warn} | {N} issues |
| Expired subsidies | {pass/warn} | {N} to archive |
| Company info staleness | {pass/warn} | {N} stale files |
| INDEX consistency | {pass/warn} | {N} mismatches |
| Orphaned files | {pass/warn} | {N} orphans |

## Details

### Case Studies
{list of issues}

### Subsidies
{list of expired}

### Company Info
{list of stale/todo}

### INDEX Mismatches
{list of mismatches}
```

## Headless Execution

LaunchAgent: `com.sk.agent.sales.material-health`
Schedule: Sunday 09:00
Runner: `scripts/material-health.sh`
