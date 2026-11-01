---
name: spine-versioning
loop: dev
pdca: act
description: >
  Canonical version + changelog for the product fleet — and crucially the
  ENFORCEMENT that stops "forgot to bump". Audit (2026-06-27/28) of chimesflow,
  family-fiscal, 孕: all three HAVE a version + changelog, but NONE has a gate, so
  bumps get forgotten in flow (chimesflow's version stuck 4 releases via a silent
  sed no-op; 孕 shipped a whole batch then back-filled v0.11.0). So unlike a normal
  module, the canonical core here is the GATE (a pre-push / CI check: code changed
  but version/CHANGELOG didn't → block), not the changelog data model. The decision
  is dev-facing CHANGELOG.md vs user-facing in-app "更新歷程" (most products want both).
  TRIGGER when: adding version / changelog / release notes / 更新歷程 / 版本號 /
  bump / "顯示版本" to a product; setting up release hygiene; OR right after someone
  says "I'll remember to bump next time" (that's the signal to install the gate).
  Yellow-Chick (2026-09) is the first product WITH the gate: owner-defined bump
  rules, hotfix-needs-ticket, and scripts/checks/check_release.py in CI.
  Owner rule 2026-10-31: one version for each merged ticket (feature = MINOR, any
  other ticket = PATCH), made in the merge flow right after the merge, recorded
  with its ticket, and checked by a local pre-push gate (ChimesERP ERP-357, ERP-358).
  SKIP when: a published library with its own semantic-release tooling; a throwaway
  prototype with no releases; a repo where version is fully auto-derived from tags already.
tags: [backend, versioning, changelog, release, ci, git-hooks, spine, reference]
version: 2.0.0
source: manual
---

# spine-versioning

Version + changelog, **enforcement-first**. The audit finding that defines this module:
every product HAS a version and a changelog, and every product FORGETS to bump it,
because bumping is a manual end-of-flow step and **memory is the wrong mechanism for a
mechanical gate**. chimesflow's version stuck for 4 releases (silent `sed` no-op,
2026-06-22); 孕 shipped W4-W40 / food analysis / photo logging then back-filled v0.11.0
(2026-06-28). Neither had a gate. **So the core of this module is the gate.** Grounded in
`~/code/ChimesFlow/CHANGELOG.md` + `version.ts`, `~/code/Family-Fiscal/backend/db.py`
(`release_items`).

## The rule: one version for each merged ticket (owner, 2026-10-31)

This rule replaces "one version for each release batch" in every product.

| Part | When |
|------|------|
| MINOR | The merged ticket is a feature: a new or changed function for users |
| PATCH | Any other merged ticket: bug fix, documents, tests, operations |
| MAJOR | Only the owner decides. Record the owner's words |

- The release is a step of the merge flow, directly after the merge commit of the
  ticket. Commits on the ticket branch do not change the version.
- Two tickets merged together get two versions, in merge order.
- The version and the ticket point to each other. The release record lists the
  ticket. The ticket and the blueprint module show the version (`spine-dev-center`).

Why: with "one version for each batch", nobody decided when a batch ended, so the
version did not move. ChimesERP stayed at 0.1.0 with 162 unreleased deliveries. The
owner then set 0.1.1 to 0.96.0 after the fact, one version for each of 137 deliveries
(2026-10-31). TWstock released 0.1.0 on 2026-10-28, then merged six PRs (#29 to #34)
with no new version.

## The merge flow for one ticket

Do these steps after the owner approves the merge, in this order, in the same
session. If you skip a step, the developer pages disagree with each other.

1. Merge the ticket branch into main.
2. Set the ticket to `review` (待驗收). Merged is not done (`spine-roadmap` rule 4).
3. Make the release: the next version from the ticket kind, a CHANGELOG section that
   cites the ticket ID, the version file, and the tag `v<version>`.
4. Record the release with its ticket in the tracker, or in `deliveries.md` in the
   light tier. The 版本與交付 page reads this record.
5. If the ticket adds a module or changes one, change the blueprint file in the same
   release (`spine-dev-center`).
6. Make generated developer data again on main, in the release commit. Do not commit
   generated data on ticket branches. Two branches that change it conflict (TWstock
   #28 and #29, 2026-10-28).
7. Push. The local gate (below) refuses code without a new version.

ChimesERP: `scripts/release.py --next feature|fix --entry "<text>"` does step 3. It
computes the version and writes the CHANGELOG line. Step 4 is a separate command,
`scripts/devtracker.py release`. `release.py` does not record the release (checked
2026-11-02), so do not skip step 4.

## The gap every product has = the enforcement gate (install this)

A pre-push hook (or CI job) that refuses a push where code changed but the version /
changelog didn't. This is the canonical contribution — none of the products have it,
and that absence is the whole bug:

```bash
#!/usr/bin/env bash
# .git/hooks/pre-push  (or wire via husky / a CI step on PRs)
# Block a push that changes code but not the version/CHANGELOG.
set -uo pipefail
range="@{push}..HEAD"; git rev-parse "@{push}" >/dev/null 2>&1 || range="origin/main..HEAD"
changed=$(git diff --name-only "$range" 2>/dev/null)
code=$(printf '%s\n' "$changed" | grep -vE '^(docs/|reports/|.*\.md$)' | head -1)
ver=$(printf  '%s\n' "$changed" | grep -iE 'CHANGELOG|version\.(ts|py|json)|^package\.json$' | head -1)
if [ -n "$code" ] && [ -z "$ver" ]; then
  echo "⚠️  code changed but no version/CHANGELOG bump in this push."
  echo "   bump the version + add a CHANGELOG entry, or: SKIP_VERSION_GATE=1 git push"
  [ "${SKIP_VERSION_GATE:-}" = "1" ] || exit 1
fi
```

CI variant: the same diff check as a required PR step (fails the check instead of the
push) — better for teams; the hook is better for solo (catches it before it leaves the
machine). Do both if you want belt + suspenders.

**Install the hook, not only the CI step.** A CI check does nothing when CI does not
run. ChimesERP's `check_version.py` ran only in GitHub CI, and that CI was not running
(ERP-358). With one version for each merged ticket, compare with the newest tag, not
with the remote branch:

- `scripts/check_version.py --since-tag`: code changed since the newest `v*` tag and
  `VERSION` did not → fail.
- `scripts/hooks/pre-push` runs it for a push to `main`.
- `scripts/install-hooks.sh` sets `core.hooksPath` to `scripts/hooks`. Run it once in
  each clone and each worktree that pushes to main.

## Reference with a working gate: Yellow-Chick (read before copying)

`YC=~/Code/Yellow-Chick`. Policy text: `docs/development/README.md` 「上線版本規則」.

Yellow-Chick's bump rules came before the 2026-10-31 rule. Its gate and its validator
still apply. Its batch rule ("one batch takes only the highest level", "commits do not
bump") is replaced by one version for each merged ticket.

**Bump rules** (owner-defined 2026-09-26, MINOR revised 09-28):

| Part | When | Extra evidence required |
|------|------|-------------------------|
| PATCH | every ordinary update that goes live | — |
| MINOR | a new module / feature goes live | `release.requirement_source` = a requirement doc or recorded owner decision |
| MAJOR | owner decides | `release.decided_by` + basis |

- One batch takes only the highest level; MINOR resets PATCH, MAJOR resets both.
- **Commits, doc edits, dev-complete and local tests do NOT bump.** Restarting the same
  build is not a release. Release = QA passed → service reloaded → version + page
  verified → local tag. "Every independently-acceptable segment ships a version."
- **Hotfix needs a ticket** (`HOTFIX-*`, see [[spine-roadmap]]) and a PATCH release with
  a tag; a delivery record links the ticket via `work_ids`. Commit + CHANGELOG alone is
  rejected. First case: `HOTFIX-OAUTH-QUOTA` → `0.5.2`.
- Deployment evidence names its environment (`local-development` ≠ production).

**The gate** — `scripts/checks/check_release.py`, run in CI with `--base <previous commit>`
(`.github/workflows/ci.yml`), and with `--tag` after a local release:

1. Product paths changed (`app/`, `frontend/src/`, `employees/`, `library/`, `alembic/`)
   → runtime version must increase AND `CHANGELOG.md` must be in the diff.
2. Runtime version (`app/__init__.py __version__`, the only source; frontend has no
   constant) == newest CHANGELOG heading == generated `frontend/openapi.json` version.
3. `docs/development/deliveries.md` has a delivery for this version with a `release`
   decision and `deployments` evidence.
4. `--tag`: the version tag exists and points at HEAD.

**Release-decision validator** — `app/development/versioning.py`: the new version must
equal `previous_version` + `kind` exactly (no skipped numbers); MINOR needs a known
requirement source; MAJOR needs `decided_by`; a version with no deployment is refused.
Historical versions before the policy date are kept as-is, not rewritten.

Unlike the generic pre-push hook above, this gate checks **coherence across four
places** and **release evidence**, not just "did a CHANGELOG line appear". Prefer it
for products with a runtime version + generated API schema.

## What converges (use as-is)

- **One version string, one source of truth** (`version.ts` `APP_VERSION`, or a
  `__version__` / `VERSION`), surfaced in the **UI footer** so a stale bump is visible.
- SemVer-ish `MAJOR.MINOR.PATCH`, bumped **once for each merged ticket**, not for
  each commit and not for each batch.
- A changelog with newest-first dated entries.

## Decision: dev-facing vs user-facing changelog (most want both)

- **Dev-facing `CHANGELOG.md`** (chimesflow): terse, every release, in the repo. For you.
- **User-facing 更新歷程 / roadmap** (family-fiscal `release_items` table; chimesflow
  roadmap-in-DB): friendly "what's new", in the app, curated. For users.
- These are **different audiences and different detail** — don't make one serve both. A
  product with users usually needs both; an internal tool needs only the dev one.

## Gotchas — from the audit

- **"I'll remember to bump next time" is a failed strategy** — it failed twice (chimesflow
  + 孕). Seeing yourself promise to remember a mechanical step = the signal to install the
  gate above, not to try harder. (Generalises: same root as "I can't remember what modules
  exist" — systematise, don't memorise.)
- **Never `sed` the version bump**: `sed -i '' "s/'1.2.3'/'1.2.4'/"` no-matches **silently**
  (exit 0, no change) and the version freezes while the changelog marches on (chimesflow,
  4 releases). Use the Edit tool (errors on no-match) or an auto-bump script, and `grep` the
  new value to verify.
- **One source of truth for the version, not N**: chimesflow had the number in `version.ts`
  AND in roadmap migrations → they drifted. Pick one canonical place; derive the rest.
- **Bump per merged ticket, not per batch and not per commit.** A batch has no clear end,
  so its version never comes (ChimesERP 0.1.0 with 162 unreleased deliveries; TWstock
  0.1.0 after six merged PRs). A commit is too small; the changelog becomes noise.
- **A release that is not recorded is not on the page.** ChimesERP's tracker had
  `record_release` but no route, so 版本與交付 showed 0 releases while main was at
  0.96.0 (ERP-357). After the first release, open the page and find the version and
  its ticket.
- **A stuck version: give each delivery its version after the fact.** Go through the
  deliveries in merge order, one version each, from the ticket kind. Keep the older
  tags. Record the releases with a script that has a dry run (ChimesERP
  `scripts/backfill_releases.py`, 0.1.1 to 0.96.0).
- **dev-changelog ≠ user-changelog**: terse repo log vs curated in-app "更新歷程". Mixing
  them gives users dev jargon or gives you a marketing doc instead of a diff.

## Sources (SoT)

- `~/code/ChimesFlow/CHANGELOG.md` + `frontend version.ts` (APP_VERSION, UI footer);
  user-facing roadmap-in-DB (`routers/roadmap.py`, `scripts/seed_roadmap.py`)
- `~/code/Family-Fiscal/backend/db.py` (`release_items` table = user-facing 更新歷程)
- `~/Code/Yellow-Chick/scripts/checks/check_release.py`, `app/development/versioning.py`,
  `docs/development/README.md` (bump + hotfix policy), `docs/development/deliveries.md`
- `~/Code/ChimesERP/docs/development/README.md` ("Versions and releases", the
  2026-10-31 rule), `scripts/release.py`, `scripts/check_version.py`,
  `scripts/hooks/pre-push`, `scripts/install-hooks.sh`, `scripts/backfill_releases.py`
  (ERP-357, ERP-358)
- `~/Code/TWstock_invest`: `VERSION`, `CHANGELOG.md`, `docs/development/deliveries.md`
  (0.1.0 on 2026-10-28, no release after #29 to #34)
- Recurrence + fix rationale: `~/.claude/learnings/LEARNINGS.md` (2026-06-22 sed no-op;
  2026-06-28 memory-not-gate). Registry `rivendell/docs/spine-modules.md` (#5). Pairs with
  [[spine-roadmap]] (#4, the user-facing surface) — version is the data, roadmap is the view.
