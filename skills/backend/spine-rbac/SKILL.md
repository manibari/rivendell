---
name: spine-rbac
loop: dev
pdca: plan
description: >
  Canonical RBAC tiering for the FastAPI product fleet. UNLIKE spine-auth, RBAC
  has almost NO convergent code core — a real audit of family-fiscal vs chimesflow
  (2026-06-27) found them at opposite tiers (hardcoded 2-role vs data-driven
  Role×Entity×Level matrix). So this is a TIER-DECISION skill: it gives the two
  archetypes, when to pick each, the one thing that DOES converge (enforce via a
  FastAPI Depends factory, never an in-body check), and the proven Tier1→Tier2
  migration path (chimesflow walked it itself).
  TRIGGER when: adding roles / permissions / 權限 / 權限管理 / access control /
  require_admin / require_permission / "給人用要分權限" to a FastAPI product;
  deciding how granular authz should be; a product's roles outgrowing admin/member.
  SKIP when: single-user / no multi-role product (no RBAC needed); authentication
  only with no authorization (that's spine-auth); row-level data scoping mechanics
  specifically (a sub-concern noted here but deeper in each product's utils/rbac).
tags: [backend, rbac, authz, permissions, fastapi, spine, security, reference]
version: 1.0.0
source: manual
---

# spine-rbac

How much RBAC machinery a product needs. **Key audit finding: RBAC does NOT have a
shared code core** — family-fiscal and chimesflow sit at opposite tiers, and copying
either one whole is the n=1 trap. This skill picks the tier and the migration path.
Grounded in `~/code/Family-Fiscal/backend/auth.py` (Tier 1) and
`~/code/ChimesFlow/backend/app/middleware/auth.py` (Tier 2, which itself migrated up).

## The ONE thing that converges: enforce via a `Depends` factory

Whatever tier you pick, the enforcement primitive is the same shape — a factory that
returns a FastAPI dependency, applied with `Depends(...)`:

```python
def require_role(*roles: str):
    async def checker(... = Depends(bearer_scheme), db = Depends(get_db)) -> User:
        user = await get_current_user(...)
        if user.role not in roles:
            raise HTTPException(403, "insufficient role")
        return user
    return checker

# usage — the gate is in the SIGNATURE, not the body:
@router.post("/partners")
async def create(..., user: User = Depends(require_role("admin"))): ...
```

**Why this and not an in-body check**: family-fiscal calls `require_admin(user)` *inside*
the handler. That works but is forget-prone — one handler that omits the call is a
silently open endpoint. A `Depends(...)` gate is visible in the signature and impossible
to forget for that route. **Always enforce via Depends.**

## The two tiers — pick one (don't default to Tier 2)

### Tier 1 — hardcoded roles (family-fiscal)
- 2-3 role strings on the user; `require_role("admin")` / `require_admin(user)`; a single
  superuser via `require_owner` (admin + `username == OWNER_USERNAME`).
- **When**: ≤3 roles, only devs change who-can-do-what, no per-entity granularity.
- Cost: ~20 lines. No tables, no admin UI.

### Tier 2 — data-driven Role×Entity×Level matrix (chimesflow)
- `role_permissions` table (role × entity × level ∈ {read, write}); a `SEED_MATRIX`
  (admin = write on every entity, via seed not hardcoded); `require_permission(entity,
  action="write")` dependency; an admin API (`GET/PATCH /api/permissions`) to flip cells;
  multi-role users (`roles: list[str]`).
- **When**: roles outgrow ~3, OR non-devs must manage permissions in a UI, OR you need
  per-entity granularity (read partner but not write contract).
- Cost: table + seed + matrix dep + admin API + UI. Heavy — earn it.

### Second axis — column vs row (don't conflate)
- **Column** = which entity/action (allow/deny) → the matrix above.
- **Row scope** = which *records* (DEPT / OWN / ALL) → chimesflow keeps this SEPARATE in
  `app/utils/rbac.py`, the matrix dep only does allow/deny. If you need "managers see
  their dept's rows only", that's a different mechanism — don't cram it into the matrix.

## Decision rubric

Start **Tier 1**. Migrate to **Tier 2** when ANY of: roles > 3 · a non-dev needs to edit
permissions · per-entity read/write granularity · auditors ask "who can do what" and you
can't answer from a table. Single-tenant tiny tools usually never leave Tier 1.

## Migration Tier 1 → Tier 2 (chimesflow walked it)

chimesflow's own code comment: *"Replaces `require_role(...)` once endpoints are migrated."*
The proven path: **keep `require_role` working** while you add `require_permission`; migrate
endpoints one at a time (swap the `Depends`); seed the matrix so `admin` keeps full access
from day one; delete `require_role` only after the last endpoint moves. Never big-bang.

## Gotchas — from the audit

- **Don't start at Tier 2**: the matrix + admin API + seed is real weight. For 2 roles it's
  over-engineering. backend-async-jobs taught the same lesson — pick the tier, don't max it.
- **Enforce via `Depends`, never an in-body call**: family-fiscal's `require_admin(user)`
  inside handlers is one forgotten line from an open endpoint. The Depends gate is in the
  signature.
- **admin-bypass via the seed/data, not scattered `if role == "admin"`**: chimesflow gives
  admin `write` on every entity in `SEED_MATRIX`. Scattering hardcoded admin checks is how
  authz drifts.
- **column-perm ≠ row-scope**: allow/deny (which entity) and which-rows (DEPT/OWN/ALL) are
  two axes. One matrix can't express both; keep row scope in its own module.
- **multi-role vs single-role: decide early**: chimesflow has `roles: list[str]`; family-fiscal
  a single `role`. Retrofitting single→multi touches every check. If unsure, single is simpler.
- **owner-by-username is a single-superuser hack**: family-fiscal gates the app-owner on
  `username == OWNER_USERNAME` (env). Fine for one superuser, but username-as-identity breaks
  if the email rotates — prefer an `is_owner` flag/role once you have >1 privileged user.

## Sources (SoT)

- Tier 1: `~/code/Family-Fiscal/backend/auth.py` (`require_admin` / `require_owner` / `is_owner`)
- Tier 2: `~/code/ChimesFlow/backend/app/middleware/auth.py` (`require_role` / `require_permission`),
  `app/models/role_permission.py`, `app/utils/role_permission_seed.py`, `app/routers/permissions.py`,
  row scope in `app/utils/rbac.py`
- Pairs with [[spine-auth]] (decision 3 there defers here). Registry: `rivendell/docs/spine-modules.md` (#2).
