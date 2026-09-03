---
name: sales-client-kickoff-docs
loop: sales
pdca: do
description: >
  At new-client kickoff (NDA signed, before the first working session), read the
  client's homework files and scaffold the four-piece project starter:
  scope.md + deadline.md + MEMORY.md + README.md. Goes beyond init-project (which
  only makes CLAUDE.md/AGENTS.md) to cover the business-project artifacts.
  TRIGGER: 「新客戶 kickoff」「NDA 簽完準備討論」「讀 homework 建專案檔」
  「建立客戶專案初始檔」.
  SKIP: dev-only project init (CLAUDE.md/AGENTS.md → init-project); a deck/proposal
  (sales-material / pitch-deck); deep company research (sales-customer-intel).
tags: [workflow, client, kickoff, scaffolding]
version: 1.1.0
source: manual
---

# sales-client-kickoff-docs

Turn a new client's raw homework into a consistent four-piece project skeleton so
every engagement starts from the same shape.

## Workflow

1. **Read the homework** — whatever the client handed over (brief, spec, slides,
   emails). Extract: goal, scope boundaries, deadlines, key contacts, open
   questions.
2. **Scaffold the four-piece set** under the client's project dir:
   - `scope.md` — what's in / explicitly out, deliverables, acceptance.
   - `deadline.md` — milestones + dates; flag anything the homework left vague.
   - `MEMORY.md` — durable context (who / why / constraints) for future sessions.
   - `README.md` — one-screen orientation + links to the other three.
3. **Mark gaps, don't invent** — where the homework is silent (budget, exact
   dates, success metric), write `待補` and list it as an open question rather
   than fabricating a plausible-sounding answer.

## Gotchas

- **Thin homework ≠ permission to fabricate**: clients often hand over vague
  material. Scope/deadline you can't source from the homework go in as `待補` +
  an open-question list — a confident-but-wrong scope.md is worse than a blank.
- **Don't duplicate init-project**: this is the *business* layer (scope/deadline/
  memory), not dev config (CLAUDE.md/AGENTS.md). Run both if the engagement also
  has a codebase.
- **MEMORY.md is the handoff**: it's what a future session (or teammate) reads to
  get up to speed — write durable context, not a task list.
