---
name: jd-writer
description: >
  Generate structured Job Descriptions (JD / 職缺描述) from organizational context.
  Produces work responsibilities, required skills, nice-to-haves, career path,
  and optionally salary range. Understands org hierarchy to write accurate JDs.
  TRIGGER when: user says "寫 JD", "補 JD", "職缺描述", "job description",
  "write a JD for", "招募文", "徵才", or wants to create/refine a job posting.
  DO NOT TRIGGER when: user wants to analyze a candidate resume (use candidate-analysis).
tags: [workflow]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep, WebSearch"
---

# JD Writer

Structured job description generation from organizational context.

## Discovery Questions

Before writing, gather:

1. **職務名稱** — exact title and level (Junior/Mid/Senior/Lead/Principal)
2. **組織位置** — reports to whom? manages whom? team size?
3. **核心職責** — what does this person do day-to-day? (top 3-5 responsibilities)
4. **必備技能** — hard requirements (years of experience, specific tech, certifications)
5. **加分條件** — nice-to-haves that differentiate strong candidates
6. **成功指標** — how do you measure success in this role at 3/6/12 months?
7. **職涯路徑** — where does this role lead? (lateral moves, promotions)
8. **薪資範圍** — optional, but improves candidate quality
9. **工作型態** — remote / hybrid / onsite? location?

## Output Structure

```markdown
# [Job Title] — [Company Name]

## About Us
[2-3 sentences about the company, mission, and team]

## The Role
[1 paragraph describing what this person will do and why it matters]

## Responsibilities
- [Responsibility 1 — action verb + measurable outcome]
- [Responsibility 2]
- ...

## Required Qualifications
- [Hard requirement with specific threshold]
- ...

## Nice-to-Have
- [Differentiating skill]
- ...

## What We Offer
- [Career path: this role → next role]
- [Compensation range if provided]
- [Benefits, work style, culture notes]

## How to Apply
[Application instructions]
```

## Writing Guidelines

- **Action verbs first**: "Design and implement..." not "Responsible for designing..."
- **Specific thresholds**: "3+ years of Python" not "experience with Python"
- **Avoid jargon soup**: Don't list 15 technologies; group by category
- **Show career path**: Candidates want to know where this leads
- **Org context matters**: A "Senior SWE" at a 10-person startup ≠ a "Senior SWE" at a 10,000-person enterprise. Adjust expectations accordingly.
- **Gender-neutral language**: Use "they/them" or rewrite to avoid pronouns
- **Honest about challenges**: Mention the hard parts — it filters better

## Cross-Reference

- Pair with `candidate-analysis` for the full hiring pipeline
- If the JD needs to go into a presentation, use `office-docx` or `gdoc-report-builder`
