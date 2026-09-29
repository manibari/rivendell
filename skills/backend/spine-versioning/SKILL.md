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
  SKIP when: a published library with its own semantic-release tooling; a throwaway
  prototype with no releases; a repo where version is fully auto-derived from tags already.
tags: [backend, versioning, changelog, release, ci, git-hooks, spine, reference]
version: 1.1.0
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

## Reference with a working gate: Yellow-Chick (read before copying)

`YC=~/Code/Yellow-Chick`. Policy text: `docs/development/README.md` 「上線版本規則」.

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
- SemVer-ish `MAJOR.MINOR.PATCH`, bumped **per release batch**, not per commit.
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
- **Bump per batch, not per commit**: tie the bump to a release/ship, not every commit, or
  the changelog becomes noise.
- **dev-changelog ≠ user-changelog**: terse repo log vs curated in-app "更新歷程". Mixing
  them gives users dev jargon or gives you a marketing doc instead of a diff.

## Sources (SoT)

- `~/code/ChimesFlow/CHANGELOG.md` + `frontend version.ts` (APP_VERSION, UI footer);
  user-facing roadmap-in-DB (`routers/roadmap.py`, `scripts/seed_roadmap.py`)
- `~/code/Family-Fiscal/backend/db.py` (`release_items` table = user-facing 更新歷程)
- `~/Code/Yellow-Chick/scripts/checks/check_release.py`, `app/development/versioning.py`,
  `docs/development/README.md` (bump + hotfix policy), `docs/development/deliveries.md`
- Recurrence + fix rationale: `~/.claude/learnings/LEARNINGS.md` (2026-06-22 sed no-op;
  2026-06-28 memory-not-gate). Registry `rivendell/docs/spine-modules.md` (#5). Pairs with
  [[spine-roadmap]] (#4, the user-facing surface) — version is the data, roadmap is the view.
