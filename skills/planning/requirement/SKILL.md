---
name: requirement
loop: dev
pdca: plan
description: >
  Define structured requirements for a feature: 統一語言表（ubiquitous language）first,
  then user stories and acceptance criteria. The glossary pins one name per domain concept
  before any story or schema introduces a second one.
  TRIGGER when: user says "define requirement", "write user story", "what should we build",
  "統一語言", "術語表", "名詞對齊", or describes a feature idea without clear scope.
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

### Step 2: 統一語言表（先釘名詞，再寫故事）

**順序是刻意的**：user story 本身就會引進名詞。等故事寫完才對齊術語，是在事後改寫故事；
等 schema 寫完才對齊，就來不及了 —— `system-design` §2 那條「踩過的坑」
（`report_date` vs `year_month` vs `date`、`2330.TW` vs `2330`）就是這張表不存在的結果。
同一個概念三個名字，不是命名品味問題，是**當初沒有人被迫在一張表上二選一**。

產出一張表，每個跨越一個以上 user story 的領域名詞一列：

| 業務講的詞 | 系統裡的名字 | **不是什麼** | 誰能拍板 |
|---|---|---|---|
| 工單 | `work_order` | 不是 `job`（job 是排程單位，一張工單可拆多個 job） | 廠務 PM |

規則：

- **「系統裡的名字」全系統只有一個**：程式碼、DB 欄位、API 欄位、UI 文案共用。不是三個。
- **「不是什麼」那欄是這張表的價值所在**，跟 `system-design` §3 的「不負責什麼」同一個道理 ——
  負向資訊比正向的更能防止誤解。**填不出「不是什麼」，通常代表兩個概念還黏在一起**，
  先拆概念再回來填。
- **業務方講不出來的詞不要自己發明。** 標「待確認」+ 寫下誰能拍板，一併存進 Step 5 的需求文件。
  編一個名字出來，後面整條鏈都會沿用它。
- 名詞有同義詞是正常的（現場講「單」、系統叫 `work_order`）；**把同義詞也列進「業務講的詞」那格**，
  不要假裝只有一種講法。

這張表是 `system-design` §2 欄位命名的**輸入**，不是它的產出。

### Step 3: Write User Stories

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

### Step 4: Define Scope Boundary

Produce a two-column table:

| In Scope | Out of Scope |
|----------|-------------|
| ... | ... |

This prevents scope creep later.

### Step 5: Output

Save to `docs/requirements/{feature-name}.md` (ask user for feature name if unclear).

**統一語言表跟著存進同一份文件**，放在 user stories 之前。它之後會被 `system-design` §2
讀去命名欄位、被 `qa-dataflow` 讀去對帳圖上的節點名 —— 只存在於對話裡的表格等於沒有。

### Step 6: Handoff

After saving, prompt:

> **Requirement complete.** Follow the gstack UI workflow:
>
> | Step | Skill | Purpose |
> |------|-------|---------|
> | 2 | `/user-flow` | Screen transitions + branches |
> | 3 | `/gstack-design-consultation` | Design system / brand direction |
> | 4 | `/gstack-design-shotgun` | Generate design variants, pick one |
> | 5 | `/mockup` → `/gstack-design-html` | Finalize static HTML |
> | 6 | `/system-design` | SA/SD：資料模型 / 職責邊界 / 介面契約 / 功能關係圖(target) |
> | 7 | `/planning-with-files` → `/gstack-plan-eng-review` | Implementation task list + architecture review |
>
> Next: `/user-flow`
