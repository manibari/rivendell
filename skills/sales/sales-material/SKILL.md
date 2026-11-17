---
name: sales-material
loop: sales
pdca: do
description: "Assemble client-specific sales presentations by matching customer intelligence, case studies, solutions, and subsidies from the local materials library, then generating PPTX via html2pptx."
tags: [sales, presentation, pptx, assembly, workflow]
version: 2
source: manual
user_invocable: true
when_to_use: "TRIGGER when: user says '幫我做客戶提案', '準備 B2B 提案', '做 X 公司的銷售簡報', '客戶提案素材', or /sales-material. DO NOT TRIGGER when: user wants an investor/pitch deck (use pitch-deck), editing an existing PPTX (use office-pptx), researching a company (use sales-customer-intel), or looking up subsidies (use gov-subsidy-scraper)."
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
    ├─ 1. Identify Client → Read sales-customer-intel report
    │     (no report? → trigger sales-customer-intel skill first)
    │
    ├─ 2. Match Cases → Grep case-studies/ by industry + tags
    │
    ├─ 3. Match Subsidies → Read subsidies/by-industry/{industry}.md
    │
    ├─ 4. Match Solutions → Read solutions/ by pain points
    │
    ├─ 4b. Storyline gate → Write `storyline.md` from the matched material;
    │                 reach `status: signed-off` with `slide-office-hours` before slides.
    │                 Give the deck to the `sales` agent before it goes to the client.
    │
    ├─ 5. Assemble → Use the brand's locked template in `mockups/slide-templates/`
    │                 when one exists; otherwise slide-blueprints.md.
    │
    ├─ 6. Convert → html2pptx (office-pptx skill); for a finished HTML deck,
    │                 slide-workflow `scripts/deck-export` (image or editable PPTX)
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
   "找不到 {client} 的 sales-customer-intel 報告，要先執行客戶調查嗎？"
   If yes → invoke sales-customer-intel skill, then resume
```

### Step 2-4: Material Matching

Read [matching.md](matching.md) for the matching algorithm.

### Step 5-6: Slide Assembly

Read [slide-blueprints.md](slide-blueprints.md) for HTML templates per slide type.

Read the office-pptx skill (`SKILL.md`, `html2pptx.md`) before you generate a PPTX; html2pptx accepts only the HTML it documents.

### Step 7: Output

Save to: `materials/presentations/{client-slug}_{YYYY-MM-DD}.pptx`

## First Meeting Deck (owner rules, 2026-11-16)

Use this shape when `storyline.md` has `stage: first-call`. The proposal table in the next section is for a later meeting, after the need is confirmed.

1. Cover: company name, one background line, the services as chips, the date. The title is the company name only. Do not tell the buyer what they need.
2. Who we are: one value line in the buyer's business words (for example 「使用 AI 技術減少浪費，加速企業實踐 ESG 目標」), our strengths in three sentences, the representative products, and a wall of customer and partner logos.
3. Track record: one timeline from the founding year to this year. Each year lists product releases, awards, investors and accelerator programs, with real event photos.
4. Case index: one table, grouped by industry, numbered 01, 02, and so on. Columns: industry, number, project, system, AI applications (CV / ML / GPT ticks), page. The order agrees with the case pages.
5. One page for each case: a highlight card, need, approach, system, AI applications, products used, status. Show the real picture when one exists.
6. Products: one page in two tiers (AI platform; application systems). Each card lists the case numbers that use it.
7. Deployment experience: one page, with one real case under it. The contact line goes on this page.

Why pages 2 and 3 (owner 2026-11-17, from a sales colleague's first-call deck, 大武山 v5): a first-call buyer does not know us yet. Build trust in the company before the cases and the products. Show who uses us and who recognized us, with names and years. Do not use adjectives. Keep this opening when the rest of the deck has another shape, for example products, then solution pages, then rollout.

Do not put these in a first deck: prices, an agenda, a next-step page, or common sense such as "white-label" or "we will not compete with you". Every project has system development and AI; do not sort projects into "system" and "AI" groups.

Proof and anonymization (the `sales` agent holds the full rules):

- Burn masks into the image files. A CSS mask does not travel into a PPTX or the assets folder. Check every screenshot for site, ship, account, program, partner and other brand names.
- A vendor buyer knows its own customers. "Industry type + work done" can name a customer that must not be named.
- Take the logo wall from the work folder's logo library (`素材/library/logos/`). A logo on the wall and an anonymous case page (「某煉油廠」) can together name the customer. Check each anonymous case against the wall.
- A status on a case page agrees with the same item on the overview page. A caveat that changes what a number means (for example "academic study, not a customer result") stays on the slide, because the buyer gets the PDF without the speaker notes.
- Write a change in plain words: 「降低 25–30%」, not 「−25–30%」.
- Case pages show real customer projects only. Show a presales demo or an open opportunity as a product capability.
- A number on a highlight card needs a measured source. Without one, state a function that the screen shows.
- Product pictures show our own product screens.
- Fill a template field on every page, or remove the field.
- Never cite an informal talk or a hint from someone inside a customer.

Before the deck leaves, give it to the `sales` agent. The owner decides on its findings.

Export the final HTML deck with slide-workflow `scripts/deck-export`: `--image` gives the exact look; the default gives native text for edits in PowerPoint. Read each compare image before delivery.

## Slide Deck Structure

A proposal deck (after the need is confirmed):

| # | Slide | Source |
|---|-------|--------|
| 1 | Cover | client name + our logo |
| 2 | Agenda | auto-generated |
| 3 | 我們是誰 | company/profile.md |
| 4 | 能力矩陣 | company/capabilities.md |
| 5 | 了解您的挑戰 | sales-customer-intel Section 六 (pain points) |
| 6 | 建議方案 | solutions/ matched template |
| 7 | 方案架構 | solutions/ detail |
| 8 | 成功案例 1 | case-studies/ matched |
| 9 | 成功案例 2 | case-studies/ matched (optional) |
| 10 | 補助機會 | subsidies/ matched |
| 11 | 時程與預算 | solutions/ typical_duration + budget |
| 12 | 團隊介紹 | company/team.md |
| 13 | 下一步 | strategy from sales-customer-intel Section 八 |
| 14 | Q&A / 聯繫方式 | company/profile.md |

## Key Dependencies

- `office-pptx` skill — html2pptx conversion (MUST read before generating)
- `slide-workflow` skill — `scripts/deck-export` for a finished HTML deck
- `sales` agent (`~/.claude/agents/sales.md`) — review before the deck leaves
- `sales-customer-intel` skill — client research reports
- `materials/` — all local material files
- `reports/customer-intel/` — intel reports
