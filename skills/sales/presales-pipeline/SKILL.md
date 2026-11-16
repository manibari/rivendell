---
name: presales-pipeline
loop: sales
pdca: do
description: >
  Manage a B2B presales pipeline on the file system (`客戶/<通路>/<階段>/<YYYYMM_客戶>/`
  in the registered work folder): `範本/new-client.sh` scaffolds the client folder, the
  stage folder (01-Presales, 02-Deliveries, ...) is the state, and sales-customer-intel
  reports go into the client folder.
  TRIGGER: 「新 client」「presales」「這個可以 archive / lost 了」, company-level
  prospect naming, or cd-ing into an `01-Presales` directory.
  SKIP: deep one-off company research (sales-customer-intel); CRM record edits
  (sales-crm-projection); a sales deck (sales-material / pitch-deck).
tags: [workflow, sales, presales]
version: 1.2.0
source: manual
---

# presales-pipeline

A filesystem-as-database presales tracker: one folder per client, the stage folder as
the state — no external CRM needed for the early funnel.

The rules live in the work folder's `CLAUDE.md` (sections 頂層結構 and Lifecycle Stages).
This skill does not repeat them, so the two cannot disagree (owner rule: one copy of
each rule). Find the work folder with `sk work-root get chimes-work`. An error means
this machine has no registered work folder: stop and ask the user to register it. Do
not guess the path.

## Workflow

1. **New client** — run `<work-root>/範本/new-client.sh <YYYYMM_客戶> <通路> [stage]`
   (stage: presales (default) | delivery | maintenance | pending | closed). It creates
   `客戶/<通路>/<NN-Stage>/<YYYYMM_客戶>/` with the lifecycle skeleton and a `README.md`
   from the template. It refuses a slug that already exists under any channel or stage.
2. **Enrich** — put a sales-customer-intel report into the client folder
   (`1-presales/intel/`), so the client file carries real research, not just a name.
3. **Change stage** — move the folder to the new stage folder, then regenerate the work
   index `README.md`, as the work folder's `CLAUDE.md` says. The stage folder is the
   state; the client README's `current_phase` is the finer work phase.
4. **Review** — list the stage folders to see the live funnel.

## Gotchas

- **Never delete on lost/closed**: close = move to `05-Closed`, not `rm`. Lost clients
  are the best source of "why we lose" analysis later.
- **One folder per client, slug is the key**: pick a stable `<YYYYMM_客戶>` up front;
  renaming later orphans the sales-customer-intel cross-references.
- An older version of this skill kept the state in `status:` frontmatter under
  `01_presales/`. The work folder replaced that with stage folders. Follow the work
  folder.
