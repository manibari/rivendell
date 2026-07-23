---
name: sales-material
description: "Assemble client-specific sales presentations by matching customer intelligence, case studies, solutions, and subsidies from the local materials library, then generating PPTX via html2pptx."
tags: [sales, presentation, pptx, assembly, workflow]
version: 1
source: manual
user_invocable: true
when_to_use: "TRIGGER when: user says '幫我做客戶提案', '準備 B2B 提案', '做 X 公司的銷售簡報', '客戶提案素材', or /sales-material. DO NOT TRIGGER when: user wants an investor/pitch deck (use pitch-deck), editing an existing PPTX (use office-pptx), researching a company (use customer-intel), or looking up subsidies (use subsidy-scraper)."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - WebSearch
  - Agent
---

# Sales Material Assembler

Orchestrates the full pipeline from client name to finished PPTX presentation by pulling from the local materials library.

## Architecture

```
User: "幫我做奇美食品的提案簡報"
    │
    ├─ 1. Identify Client → Read customer-intel report
    │     (no report? → trigger customer-intel skill first)
    │
    ├─ 2. Match Cases → Grep case-studies/ by industry + tags
    │
    ├─ 3. Match Subsidies → Read subsidies/by-industry/{industry}.md
    │
    ├─ 4. Match Solutions → Read solutions/ by pain points
    │
    ├─ 5. Assemble → Build HTML slides — MUST use locked template from
    │                 mockups/slide-templates/ if one exists for this brand
    │                 (e.g. chimes-ai.html, cht-corporate.html). Otherwise
    │                 fall back to slide-blueprints.md.
    │
    ├─ 6. Convert → html2pptx (office-pptx skill)
    │
    └─ 7. Output → materials/presentations/{client}_{date}.pptx
```

## Workflow

### Step 1: Client Intelligence

Read [assembler.md](assembler.md) for the full assembly workflow.

```
1. Search reports/customer-intel/ for the client
   - Glob: reports/customer-intel/{client_name}*.md
2. If found → read the report, extract:
   - Company overview (Section 一)
   - Pain points (Section 六)
   - Key people (Section 三)
   - Strategy recommendations (Section 八)
3. If NOT found → ask user:
   "找不到 {client} 的 customer-intel 報告，要先執行客戶調查嗎？"
   If yes → invoke customer-intel skill, then resume
```

### Step 2-4: Material Matching

Read [matching.md](matching.md) for the matching algorithm.

### Step 5-6: Slide Assembly

Read [slide-blueprints.md](slide-blueprints.md) for HTML templates per slide type.

**CRITICAL**: Before generating any PPTX, read the office-pptx skill completely:
- `~/.claude/skills/office-pptx/SKILL.md`
- `~/.claude/skills/office-pptx/html2pptx.md`

### Step 7: Output

Save to: `materials/presentations/{client-slug}_{YYYY-MM-DD}.pptx`

## Slide Deck Structure

A typical client proposal deck:

| # | Slide | Source |
|---|-------|--------|
| 1 | Cover | client name + our logo |
| 2 | Agenda | auto-generated |
| 3 | 我們是誰 | company/profile.md |
| 4 | 能力矩陣 | company/capabilities.md |
| 5 | 了解您的挑戰 | customer-intel Section 六 (pain points) |
| 6 | 建議方案 | solutions/ matched template |
| 7 | 方案架構 | solutions/ detail |
| 8 | 成功案例 1 | case-studies/ matched |
| 9 | 成功案例 2 | case-studies/ matched (optional) |
| 10 | 補助機會 | subsidies/ matched |
| 11 | 時程與預算 | solutions/ typical_duration + budget |
| 12 | 團隊介紹 | company/team.md |
| 13 | 下一步 | strategy from customer-intel Section 八 |
| 14 | Q&A / 聯繫方式 | company/profile.md |

## Key Dependencies

- `office-pptx` skill — html2pptx conversion (MUST read before generating)
- `customer-intel` skill — client research reports
- `materials/` — all local material files
- `reports/customer-intel/` — intel reports
