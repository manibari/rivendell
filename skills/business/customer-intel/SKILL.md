---
name: customer-intel
description: >
  B2B customer intelligence: company name → web research → actionable sales report.
  WebSearch + Playwright (findbiz.nat.gov.tw for TW). Markdown SSOT auto-synced to Nexus.
  TRIGGER: "客戶調查", "公司調查", "會前準備", "情蒐", "更新[公司名]報告".
  SKIP: stocks (investment-research); code review (code-reviewer).
tags: [workflow, sales]
version: 3
source: manual
user_invocable: true
---

# Customer Intelligence

Structured B2B customer research workflow. Input a company name, get an actionable intel report for sales meeting prep.

## Goals

1. **Know the customer** — company background, leadership, financials, market position
2. **Find entry points** — pain points, challenges, and how our capabilities map to their needs
3. **Prepare for the meeting** — talking points, topics to avoid, risk assessment

## Architecture: md as Single Source of Truth

```
┌─────────────────────────────────────────────────────┐
│  reports/customer-intel/[company]_[date].md          │  ← SSOT
│  (complete intel report, 8 sections)                 │
└────────────┬──────────────────────┬──────────────────┘
             │ auto-sync on change  │ read for answers
             ▼                      ▼
   ┌─────────────────┐    ┌──────────────────┐
   │  Nexus Intel API │    │  Agent 對話查詢   │
   │  (structured)    │    │  (read md → reply)│
   └─────────────────┘    └──────────────────┘
```

**Rules:**
1. **md is SSOT** — all changes go to md first, then sync to Nexus
2. **Nexus is a projection** — never edit Nexus directly; always derive from md
3. **Agent handles sync** — user talks to agent, agent updates md + Nexus together
4. **Conversation-first** — user adds/corrects info via chat, agent writes to correct section

## Lifecycle

```
Phase 1: Research     /customer-intel [公司名]
  → 產出 md 報告 → 解析 parsed_json → POST intel → confirm → materialize

Phase 2: Enrich       使用者對話補充（聯絡人、預算、會議紀錄...）
  → agent 更新 md 對應 section → PATCH intel parsed_json → re-materialize

Phase 3: Maintain     持續更新（新新聞、人事異動、deal 進展）
  → agent 更新 md → sync Nexus
```

---

## Reference Files

This skill is split into focused modules. Read them as needed:

| File | When to read | Content |
|------|-------------|---------|
| [`research.md`](research.md) | Phase 1 — doing research | Search queries, disambiguation, Steps 1-5, small vs large company strategy |
| [`report-template.md`](report-template.md) | Phase 1 — writing the report | md template (8 sections), reliability indicators |
| [`nexus-sync.md`](nexus-sync.md) | Phase 1 (sync) + Phase 2 (enrich) | parsed_json schema, field mapping, merge rules, materialize, API reference |

---

## Phase 1: Research Workflow

```
1. Input & Disambiguation  →  2. Official Registry   →  3. Company Overview
   (confirm identity)          (findbiz / gov data)      (WebSearch + WebFetch)

4. Deep Intel Collection   →  5. Pain Points Analysis →  6. Report Output
   (news, people, finance)     (challenges + our fit)     (markdown + file save)

7. Nexus Sync              →  8. Done
   (POST + confirm +            (report in terminal +
    materialize)                  saved to file)
```

**Before starting**: read [`research.md`](research.md) for detailed search strategies.
**When writing report**: follow [`report-template.md`](report-template.md).
**When syncing to Nexus**: follow [`nexus-sync.md`](nexus-sync.md).

---

## Phase 2: Conversational Enrichment

When user provides new info via chat → update md section → merge-sync to Nexus.

**Details**: see [`nexus-sync.md`](nexus-sync.md) — Update Procedure, Merge Rules, Re-materialize Rules.

---

## Phase 3: Continuous Maintenance

For existing reports, periodically refresh with new data:

```
使用者：「更新奇美食品的報告」
  → agent 讀取現有 md
  → 重新執行 Step 3a (新聞) + Step 3b (人事) 搜尋
  → 比對差異，僅更新有變動的 section
  → sync Nexus (follow merge rules in nexus-sync.md)
  → 在 md 底部加上更新紀錄：
    _Updated on [date]: 新增 2026 Q1 新聞 3 則_
```

---

## Report Index Maintenance

After creating or updating any report, update `reports/customer-intel/INDEX.md`:

```
1. Read INDEX.md
2. If company exists → update 最後更新 date
3. If new company → append row: | 公司 | 檔案(link) | Intel ID | 建立日期 | 最後更新 |
4. Write INDEX.md
```
