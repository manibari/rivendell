---
name: presales-pipeline
description: >
  Manage a B2B presales pipeline on the file system (`01_presales/<client-slug>/`):
  a `new-client.sh` scaffolds the standard folder (client-readme.md +
  company-overview.md + status frontmatter), with active / won / lost / archive
  state transitions, integrating customer-intel reports.
  TRIGGER: 「新 client」「presales」「這個可以 archive / lost 了」, company-level
  prospect naming, or cd-ing into an `01_presales` directory.
  SKIP: deep one-off company research (customer-intel); CRM record edits
  (crm-projection); a sales deck (sales-material / pitch-deck).
tags: [workflow, sales, presales]
version: 1.1.0
source: manual
---

# presales-pipeline

A filesystem-as-database presales tracker: one folder per prospect, status in
frontmatter, transitions by script — no external CRM needed for the early funnel.

## Workflow

1. **New prospect** — `new-client.sh <client-slug>` creates
   `01_presales/<client-slug>/` with `client-readme.md` + `company-overview.md` and
   `status: active` frontmatter.
2. **Enrich** — pull a customer-intel report into the folder so the prospect file
   carries real research, not just a name.
3. **Transition** — move status through `active → won | lost | archive`. Keep the
   folder; status lives in frontmatter (the SoT), not in the directory location.
4. **Review** — list/filter by status frontmatter to see the live funnel.

## Gotchas

- **Status frontmatter is the SoT**: don't encode state by moving folders between
  `won/`/`lost/` dirs — a frontmatter field survives moves, greps cleanly, and
  won't desync from a half-finished `mv`.
- **Never delete on lost/archive**: archive = status change, not `rm`. Lost
  prospects are the best source of "why we lose" analysis later.
- **One folder per prospect, slug is the key**: pick a stable `<client-slug>` up
  front; renaming later orphans the customer-intel cross-references.
