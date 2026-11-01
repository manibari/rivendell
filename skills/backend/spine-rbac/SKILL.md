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
  migration path (chimesflow walked it itself). Also the frontend permission check
  (read what the backend allows; never a second rule list) and the role x route test
  table, merged from rbac-permissions (2026-11-02).
  TRIGGER when: adding roles / permissions / 權限 / 權限管理 / access control /
  require_admin / require_permission / "給人用要分權限" to a FastAPI product;
  deciding how granular authz should be; a product's roles outgrowing admin/member;
  where the admin backend lives ("管理後台要不要獨立", "後台要不要拆成另一個 app",
  platform admin vs tenant owner); "使用者管理", "加帳號", "B2C 後台"; "RBAC",
  "role-based access", "user roles", "每個人只能看自己的", "多人帳號", "admin/member 分權",
  "內外帳", "誰能看什麼", "auth guard", "protect routes", "permission middleware". A system that
  more than one person uses needs sign-in, roles and a user page from day 1; a B2C
  product puts every admin function in a back office apart from the user area.
  SKIP when: single-user / no multi-role product (no RBAC needed); authentication
  only with no authorization (that's spine-auth); row-level data scoping mechanics
  specifically (a sub-concern noted here but deeper in each product's utils/rbac).
tags: [backend, rbac, authz, permissions, fastapi, spine, security, reference]
version: 1.3.0
source: manual
user_invocable: true
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
- Cost: ~20 lines. A `role` column with a CHECK constraint on the allowed values; no
  permission tables. You still need the user page (below) when a second person signs in.

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
- Row scope goes in the query (`WHERE owner_id = :user_id`), not only in a role check.

## Decision rubric

Start **Tier 1**. Migrate to **Tier 2** when ANY of: roles > 3 · a non-dev needs to edit
permissions · per-entity read/write granularity · auditors ask "who can do what" and you
can't answer from a table. Single-tenant tiny tools usually never leave Tier 1.

## Migration Tier 1 → Tier 2 (chimesflow walked it)

chimesflow's own code comment: *"Replaces `require_role(...)` once endpoints are migrated."*
The proven path: **keep `require_role` working** while you add `require_permission`; migrate
endpoints one at a time (swap the `Depends`); seed the matrix so `admin` keeps full access
from day one; delete `require_role` only after the last endpoint moves. Never big-bang.

## Frontend: show only what the backend allows

The backend guard is the security. The frontend guard only keeps users away from
buttons and pages that will fail.

- **Ask the backend; do not copy the rules.** One endpoint returns what the current
  user may do. ChimesERP: `GET /api/permissions/me` returns `{entity: "none" | "read" |
  "write"}` (`backend/app/routers/permissions.py`), and the frontend reads it with
  `permissionsMe()` (`frontend/src/lib/flow-api.ts`). Do not keep a role list or a
  role rank in the frontend. It drifts from the backend.
- **One provider, one hook.** After sign-in, load the user and the permissions once.
  Give the components a `can(entity, level)` helper.
- **A route guard for each page group**, with three results:
  - loading: show a spinner, not the page (no flash of content or of 權限不足);
  - no session (401): go to sign-in, then come back to the same URL;
  - no permission (403): show 權限不足 with a way back, and clear the cached data of
    that area (Yellow-Chick `OperatorAccess`).
- **Hide the actions that the user cannot do** (menu items, buttons) with `can(...)`.
  A direct URL still meets the route guard, and the backend still returns 403.
- **After a role change, load the permissions again**, or end the session. An old
  permission list shows actions that now fail.

```tsx
// Shape only. The backend sends the permissions and enforces them.
type Level = "none" | "read" | "write";
const Auth = createContext<{ user: User | null; perms: Record<string, Level>; isLoading: boolean }>(
  { user: null, perms: {}, isLoading: true });

export function useCan() {
  const { perms } = useContext(Auth);
  return (entity: string, level: "read" | "write" = "read") =>
    perms[entity] === "write" || (level === "read" && perms[entity] === "read");
}

export function RequirePermission({ entity, level = "read", children }: Props) {
  const { user, isLoading } = useContext(Auth);
  const can = useCan();
  if (isLoading) return <Spinner />;
  if (!user) return <RedirectToSignIn />;            // keeps the current URL
  if (!can(entity, level)) return <NoPermission />;  // 權限不足
  return <>{children}</>;
}
```

## Tests: one role x route table

One parametrized test holds the whole rule. Add a row for each guarded route and
each role, and a row with no session.

```python
@pytest.mark.parametrize("role,method,path,expected", [
    (None,     "GET",  "/api/partners",   401),  # no session
    ("member", "GET",  "/api/partners",   200),
    ("member", "POST", "/api/partners",   403),  # read, not write
    ("admin",  "POST", "/api/partners",   201),
    ("member", "GET",  "/api/auth/users", 403),  # the user page is for admins
    ("admin",  "GET",  "/api/auth/users", 200),
])
async def test_role_access(role, method, path, expected, client, login_as, sample_body):
    headers = await login_as(role) if role else {}
    resp = await client.request(method, path, headers=headers, json=sample_body(method, path))
    assert resp.status_code == expected
```

Row scope needs its own test. User A asks for a record of user B and gets 404, not
403, so the answer does not show that the record exists. (TWstock flow U2:
「改別人的資料一律回『找不到』」.)

## Day 1: sign-in, roles and the user page

When more than one person will use the system, open these tickets on day 1. Do not
wait until the owner finds the gap.

- Sign-in (`spine-auth`, `spine-sso`), roles (the tier above), and a guard on every
  route with personal data.
- **The user page.** The permission system is not done until an admin manages people
  in the product, with no script:
  - a list with search: name, e-mail, role, status, last sign-in;
  - add a person with a role and a temporary password, shown once with a copy
    button; the person must change it at the first sign-in;
  - change the role (and the department, if rows are scoped by department);
  - disable and enable; do not delete, because audit rows point to the person;
  - reset to a new temporary password, with an audit row.

Two products found the gap late:

- TWstock (2026-10-20): no sign-in at all. Anyone could read `/api/my/*`. The owner
  asked 「是不是沒有做權限管理系統？」.
- ChimesERP (2026-10-30, ERP-348): the user endpoints existed, but no screen used
  them. A colleague's admin account took an owner-run script and three failed rounds.

## Admin surface: same app, separate identity (audit 2026-10-20)

Where does the admin backend live? Four products, checked in code:

| Product | Admin surface | Guard |
|---|---|---|
| Yellow-Chick (multi-tenant) | Route `/admin/operations` in the same React app; API prefix `/api/operations*` | `require_operator`: a separate `operator` row, granted on purpose |
| ChimesERP | `/settings/{audit,access-review,jobs,sod}` in the same app | `require_role` / `require_permission` |
| ChimesFlow | `(main)/admin/*` route group | `require_role("admin")` |
| PTI-ARES | `(main)/{logs,members,settings}` | `require_admin` |

- **Converged (n=4): same app, same deploy.** No product runs a separate admin app.
  Do not build one by default.
- **Multi-tenant only (n=1, Yellow-Chick): the platform operator is not a tenant role.**
  A tenant owner is the top role inside one tenant. The operator works across tenants.
  Keep the operator in its own table, with its own API prefix and dependency. A tenant
  owner without the grant gets 403. Each entry into a tenant writes an audit row
  (`operator.impersonated`), so the owner can see who came in.
- **A separate admin deploy needs a reason.** Examples: the admin must not be reachable
  from the public internet, or admins need a different login (SSO, MFA). Write the
  reason in an ADR.
- **B2C (anyone can sign up): the admin is apart from the user area.** The owner
  (TWstock, 2026-10-20): 「b2c 的產品，管理員的後台應該是獨立的」.
  - The user area has no admin menu. Move every admin function (API keys, data
    quality, recalculation, users) to the back office.
  - The back office is its own route (`/admin`) with its own layout, API prefix and
    dependency, as Yellow-Chick's `/admin/operations`.
  - Grant the operator role from the host (a CLI), never from a page.
  - The back office shows account data (e-mail, sign-up date, last sign-in), not the
    users' private data.
  - Optional: an access proxy in front of `/admin` (Cloudflare Access) that admits
    only the owner. Sign-in for users stays in the product.
- **Internal or B2B tool: an admin center inside the same app**, guarded by role
  (ChimesERP 管理中心).

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
- Admin surface: YC `frontend/src/routes/router.tsx` (`operationsRoute`), `app/api/deps.py:265`
  `require_operator`, `scripts/ops/platform_admin.py`, `app/api/operations/ops.py`,
  `docs/plans/admin/2026-09-25-operations-admin-boundary.md`,
  `docs/design/admin/2026-09-26-platform-admin-entry-sd.md`; ChimesERP
  `backend/app/routers/admin_logs.py`; ChimesFlow `backend/app/middleware/auth.py`;
  PTI-ARES `backend/app/features/platform/identity/README.md`
- User page: ChimesERP ERP-348 (`GET /api/auth/users`, `PUT /api/auth/users/{id}`,
  `POST /api/auth/register` with `must_change_password`). B2C back office: TWstock
  auth flows U1 to U5 (session 2026-10-20)
- Pairs with [[spine-auth]] (decision 3 there defers here). Registry: `rivendell/docs/spine-modules.md` (#2).
