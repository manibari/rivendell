# Material Matching Algorithm

How to find the best-fit case studies, solutions, and subsidies for a given client.

## Input

From the customer-intel report, extract:
- `industry` — client's industry
- `pain_points` — from Section 六
- `tags` — any technology or domain keywords

## Case Study Matching

### Step 1: Glob and Parse

```
1. Glob materials/case-studies/*.md (exclude INDEX.md)
2. For each file, parse YAML frontmatter:
   - industry, solution_type, tags, outcome, scale
```

### Step 2: Score

Score each case study by relevance:

| Match | Points |
|-------|--------|
| Same industry | +3 |
| Overlapping solution_type with client pain points | +2 per overlap |
| Overlapping tags | +1 per overlap |
| Same scale as client | +1 |

### Step 3: Select

- Pick top 1-2 cases by score
- If no cases score > 0, skip case study slides and warn user
- Prefer cases with quantified outcomes (outcome field not empty)

## Solution Matching

### Step 1: Glob and Parse

```
1. Glob materials/solutions/**/*.md (exclude INDEX.md)
2. For each file, parse YAML frontmatter:
   - name, category, target_industry, tags, typical_duration, typical_budget
```

### Step 2: Match by Pain Points

Map client pain points to solution keywords:

| Pain Point Keywords | Solution Match |
|--------------------|----------------|
| 數據, 報表, 決策, BI | data-driven-platform |
| 設備, 停機, 維護, 故障 | predictive-maintenance |
| 轉型, 數位化, 不知從何 | digital-transformation |
| 品質, 異常, 檢測 | ai-quality-inspection |
| 供應鏈, 庫存, 物流 | supply-chain-optimization |

### Step 3: Select

- Pick the best-fit solution (1 primary, optionally 1 secondary)
- If target_industry includes client's industry → bonus
- Prefer solutions that have related case studies

## Subsidy Matching

### Step 1: Read Industry File

```
1. Map client industry to slug:
   製造業 → manufacturing
   科技業 → technology
   服務業 → services
   零售業 → retail
2. Read materials/subsidies/by-industry/{slug}.md
3. If file doesn't exist, read materials/subsidies/INDEX.md as fallback
```

### Step 2: Filter

From matched subsidies:
- Only include `status: active`
- Only include those where deadline is in the future
- Prefer subsidies whose scope aligns with the proposed solution

### Step 3: Select

- Pick top 1-3 relevant subsidies
- If budget covers proposed solution → highlight as "可降低導入成本"
- Include deadline info for urgency

## Output Structure

The matching step produces:

```python
matched = {
    "cases": [
        {"file": "chimei-foods_2025.md", "score": 5, "reason": "same industry + solution overlap"},
    ],
    "solutions": [
        {"file": "ai-data/predictive-maintenance.md", "reason": "matches 設備維護 pain point"},
    ],
    "subsidies": [
        {"name": "SBIR", "deadline": "2026-06-30", "reason": "全產業, covers AI development"},
    ],
}
```

This feeds into the assembler for slide generation.
