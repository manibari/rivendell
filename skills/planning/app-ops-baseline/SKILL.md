---
name: app-ops-baseline
description: >
  Planning-stage gate that injects a standard "ops baseline" feature checklist into
  every new product / web app: 開發 roadmap, 系統日誌, 版本管理 (changelog), 意見回饋
  (feedback), API 金鑰, 一般設定. Anchors each item to ChimesFlow's existing
  implementation as the copy-from reference (SoT). Ensures these are PLANNED, not an
  afterthought — it does not build them itself.
  TRIGGER: scoping/planning a new web or product app with a UI and users; "做一個新
  app", "新系統", "new app", "new product"; or at requirement / init-project /
  planning stage of a user-facing application.
  SKIP: backend-only services, CLI tools, scrapers, single-page report generators,
  libraries — anything without a multi-user admin/settings surface.
tags: [workflow, scaffold, gate]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Bash, Grep, Glob, Skill"
---

# App Ops Baseline (planning gate)

Every new product app ships the same six operational surfaces. This skill makes sure
they enter the plan up front and points at ChimesFlow's working implementation as the
reference to copy from — so they aren't bolted on late or reinvented.

Same pattern as `chimesflow-design`: the SoT is ChimesFlow's real code; this skill is
the gate/loader, not the builder. See `~/.claude/CLAUDE.md` → "Cross-Repo Strategy".

## Hard Rules

1. **Scope gate first (Step 0).** Apply ONLY to user-facing product/web apps. For a
   CLI / scraper / backend service / library → say "non-product app, ops baseline
   skipped" and stop. Never scaffold a feedback/api-keys page into a scraper.
2. **Plan, don't build.** Output is a checklist folded into the requirement / plan,
   each item linked to its ChimesFlow reference. Generation is delegated to the normal
   flow (`requirement` → `mockup` → implement), not done here.
3. **Reference is the SoT — read it before copying.** Don't reimplement from memory;
   open the ChimesFlow file and mirror its shape (model + migration + router + page).
4. **Baseline is a floor, not a ceiling.** The six are the minimum. A project may add
   more (health check, RBAC, notifications) — note additions explicitly; never silently
   drop one of the six without stating why it doesn't apply.

---

## Step 0 — Scope check

Confirm the target is a product/web app with a UI and users. If not → skip and stop.

## Step 1 — Emit the baseline checklist

Fold this into the requirement / plan. Each item → mirror the ChimesFlow reference
(`CF=${CHIMESFLOW_DIR:-$HOME/code/ChimesFlow}`):

| # | Baseline feature | ChimesFlow reference (read before copying) |
|---|------------------|--------------------------------------------|
| 1 | **開發 roadmap** | FE `frontend/src/app/(main)/admin/roadmap/` · BE `backend/app/routers/roadmap.py` |
| 2 | **系統日誌** (system + audit) | FE `admin/logs/`, `admin/audit-log/` · BE `routers/audit.py`, `models/audit_log.py`, `services/audit_service.py` |
| 3 | **版本管理** (changelog) | FE `settings/changelog/` · source: repo `CHANGELOG.md` / changelog migration |
| 4 | **意見回饋** (feedback) | FE `feedback/`, `components/feedback/` · BE `routers/feedback.py`, `models/feedback.py`, `schemas/feedback.py` |
| 5 | **API 金鑰** | FE `settings/api-keys/` · BE `routers/api_keys.py`, `models/api_key.py`, `schemas/api_key.py` |
| 6 | **一般設定** | FE `settings/` (shell that hosts changelog + api-keys + general prefs) |

For each: state **include / defer / N-A + reason**. Default = include. A deferred item
must carry a one-line why and a follow-up note, not vanish.

## Step 2 — Hand off

Pass the agreed checklist into the standard build flow via the `Skill` tool
(`requirement` for stories/acceptance, then `mockup`, then implement). If the project
also adopts ChimesFlow's design, pair with `chimesflow-design` at UI time.

---

## Notes

- The six are full-stack in ChimesFlow (FE page + DB table + migration + router), but
  thin — pages are 1–3 files because logic lives in shared components/APIs. Copying one
  is bounded work, not a project.
- This is prompt-routed, not a hook (a hook would over-fire on every file touch).
  `~/.claude/CLAUDE.md` new-app / requirement flow should call it at planning time.
