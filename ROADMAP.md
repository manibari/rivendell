# Rivendell Roadmap

> Living roadmap for the rivendell skills library + automation platform.
> **Reviewed every iteration** (weekly, ISO week) at `workflow-retro`. Kept in
> sync with [CHANGELOG.md](CHANGELOG.md) by the `doc-drift-sync` skill — a Done
> item here must have a CHANGELOG entry.
>
> Iteration cadence: 1 week = 1 retro = 1 doc-alignment pass. See
> `skills/meta/doc-drift-sync/SKILL.md` → "The iteration cycle".

## Now (in flight)

- **Version/roadmap/iteration system** — this ROADMAP + CHANGELOG + `doc-drift-sync`
  skill; anchor doc hygiene to the weekly retro.
- **Telegram ops-bridge** (infra under `~/.claude`, `~/.config`, `~/.local/share`):
  session-completion notifier with one-tap **Continue / Wrapup / Commit&Push**
  buttons; owned `ops-bot`; `ask-telegram` MCP tool for remote choice-questions
  with a 5W1H "都不對" escape hatch. (MCP server registration — 待補)

## Next

- **Retire `knowledge-graph` skill** — 0 triggers, flagged 3+ retros running
  (workflow-retro W22 action 1).
- **Root-cause agent exit-1 dual-state** — `harvest` / `material-health` report
  failure while producing output (W22 action 2).
- **`doe-ml-analysis` skill** — DOE/process ML EDA (heatmap→PCA→regression R²);
  harvest-rated Strong, hits the known 製造運營 domain gap.
- **`bin/sk index`** — INDEX-first tiered skill discovery to cut per-session token
  cost (FEATURE_REQUESTS 2026-05-08).

## Later

- **`presales-poc-scoping`** mother-skill — domain-agnostic PoC acceptance scoping
  (n≥3 across poc-to-product-audit / data-poc-scoping / cv-poc-acceptance-criteria;
  watch item from W22).
- **Domain skill gaps** (抽 when a real case lands): 商業洞察 (市場調研/配給/庫存/通路),
  製造運營 (視覺檢測 AOI/SPC, 排程/產能), 工安治理 (EHS), 法務 (RFP/NDA/MOU)
  (FEATURE_REQUESTS 2026-05-18).
- **DFM 知識 reference skill** — PCB CAM/DFM domain knowledge loader over the Vault
  SoT (knowledge→skill library pattern, instance #1).

## Done

- chimesflow-design + app-ops-baseline gate skills (`ff8ea85`).
- sk-setup-agents PROJECTS_DIR landmine + ssot-drift cron fix (`8007c6d`).
- dashboard Git 衛生 panel — uncommitted/unpushed across ~/code repos (`7523816`).

---

_Add items as they surface; move between sections at each weekly retro. Don't
fabricate completed work — a Done entry needs a real commit/CHANGELOG line._
