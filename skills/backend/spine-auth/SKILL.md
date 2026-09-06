---
name: spine-auth
loop: dev
pdca: do
description: >
  Canonical FastAPI auth for the product fleet — the CONVERGENT crypto core
  (jose JWT + bcrypt + HS256, hash/verify/decode, a get_current_user Bearer
  dependency) PLUS the DIVERGENT policy decisions (single vs refresh token,
  tenant claim, simple vs data-driven RBAC, flat vs modular layout) you must
  choose per product. Grounded in a real convergence audit of chimesflow +
  family-fiscal (2026-06-27): the crypto core matches almost line-for-line; the
  token policy and RBAC do NOT — so copying one product whole bakes in its
  policy. First module of the fleet infra spine (see rivendell docs/spine-modules.md).
  TRIGGER when: adding auth / login / 帳密 / 帳號密碼 / JWT / token / 登入 /
  password hashing / get_current_user to a FastAPI + Postgres product; standing
  up a new fleet product that needs users (pti-ares, ic-yms, tukey-*, mops admin).
  SKIP when: frontend-only auth UI with no backend; a non-user internal pipeline
  with no login (mops-style scraper service); OAuth/SSO-only with no local
  passwords (a different module); a non-FastAPI backend.
tags: [backend, auth, jwt, fastapi, spine, security, reference]
version: 1.0.0
source: manual
---

# spine-auth

Canonical auth for the FastAPI + Postgres product fleet. Grounded in a real
side-by-side audit of `~/code/ChimesFlow/backend/app/services/auth_service.py`
(+ `middleware/auth.py`, `routers/auth.py`) and `~/code/Family-Fiscal/backend/auth.py`.
The point of this skill: **the crypto core is genuinely shared; the policy on top
is NOT.** Use the core verbatim; decide the policy per product.

## Canonical core — CONVERGENT, use as-is

Both products independently landed on the same choices (this is the real shared shape):

- **jose** (`python-jose`) for JWT — not pyjwt. **bcrypt** directly — not passlib.
  **HS256**. `SECRET_KEY` from env/settings.
- `hash_password` / `verify_password`: `bcrypt.hashpw(pw.encode(), bcrypt.gensalt())`
  / `bcrypt.checkpw(...)`, decode to str for storage.
- `decode_token`: `try: jwt.decode(token, SECRET, algorithms=[ALG]) except JWTError: return None`.
- `get_current_user` dependency: `HTTPBearer(auto_error=False)` → pull token →
  decode → `int(payload["sub"])` → DB lookup by id → return a `CurrentUser`. On any
  failure raise `401` **with `headers={"WWW-Authenticate": "Bearer"}`**.

```python
# the shared 30 lines (fill the CurrentUser shape + db lookup per product)
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

_bearer = HTTPBearer(auto_error=False)

def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> CurrentUser:
    raw = creds.credentials if creds else None
    if not raw:
        raise HTTPException(401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(raw)
    if payload is None:
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    user = db.get_user_by_id(int(payload["sub"]))   # sub is ALWAYS str(user_id)
    if user is None:
        raise HTTPException(401, "User not found", headers={"WWW-Authenticate": "Bearer"})
    return CurrentUser(...)   # shape is per-product (see decisions)
```

**SECRET_KEY guard — copy this, never ship a fallback default.** Put it right after
`settings = Settings()`. HS256 is symmetric, so a source-visible default key = anyone
can forge a token for any user. Fail loud in prod instead of silently signing:

```python
# In Settings: no source-visible fallback — empty default, real key comes from .env
SECRET_KEY: str = ""          # (or lowercase secret_key)
ENV: str = "development"      # development | production

settings = Settings()

# ENV-gated so dev/tests stay green; prod refuses to boot on a missing/placeholder key.
if settings.ENV == "production" and (
    not settings.SECRET_KEY
    or settings.SECRET_KEY == "dev-secret-key-change-in-production"
):
    raise RuntimeError(
        "SECRET_KEY must be set to a real secret when ENV=production. Generate one "
        'with: python3 -c "import secrets; print(secrets.token_hex(32))"'
    )
```

`product-skeleton` uses the stricter `len(SECRET_KEY) < 32` form; prefer it for
greenfield, but a live product already running a <32-char key must rotate the key
first (rotating invalidates every existing JWT → users re-login), so ship the
placeholder-check form above and rotate on the next planned deploy.

## Decisions to make — DIVERGENT, ask before writing

These genuinely differ across the fleet; pick per product, don't inherit blindly:

1. **Token strategy**: single long-lived token (family-fiscal: 30-day, simplest) vs
   **access + refresh** (chimesflow: minute-level access + refresh, revocable). Refresh
   only if you need revocation / short access windows.
2. **Tenant claim**: `family_id` / `org_id` / none (single-tenant). Goes in the payload
   and the `CurrentUser`. Pick the tenant key now — retrofitting it is painful.
3. **RBAC depth**: hardcoded roles + owner-by-username (family-fiscal: `require_admin`,
   `require_owner`, 2 roles, fast) vs **data-driven permissions table** (chimesflow:
   `permissions` router, extensible). Start hardcoded; graduate to data-driven when
   roles outgrow 2-3. (This is the `spine-rbac` module's territory.)
4. **Layout**: flat `auth.py` (small product) vs `services/middleware/routers` split
   (chimesflow, large). Don't split a 3-endpoint product.
5. **Token transport**: Bearer header only, vs + `?token=` query-param fallback
   (family-fiscal added it for authed file downloads). Add the fallback only if you
   have browser file-download links.

## Gotchas — from the audit, each is a real trap

- **Don't端整碗一家的 policy**: the crypto core converges, but token-policy + RBAC
  DIVERGE (chimesflow refresh + data-driven RBAC vs family-fiscal single-token +
  hardcoded roles). Copying one product whole freezes its policy into the new one.
  Answer the 5 decisions first — that's the whole reason this skill exists.
- **`SECRET_KEY` fallback default is a landmine**: family-fiscal shipped
  `os.getenv("SECRET_KEY", "fallback-insecure-key-change-me")` — forget to set it in
  prod and you silently run on a public default with no error. The spine version must
  **fail loud** when `SECRET_KEY` is missing/short in prod, never default-and-continue
  (see the SECRET_KEY guard above). A 2026-07-20 fleet audit found the SAME landmine in
  chimesflow + Norns-ERP (`SECRET_KEY: str = "dev-secret-key-change-in-production"`) and
  lorien (`secret_key: str = "change-this-in-production"`), all publicly tunneled — every
  product built before this gotcha was written inherited it. pti-ares + product-skeleton
  (built after) already guard correctly. When you spin a new product, grep the fleet for
  this pattern before assuming it's isolated.
- **`sub` must be `str(user_id)`, never username**: family-fiscal originally put
  username in `sub`, then had to reject old tokens (`int(sub)` fails → force re-login).
  Use `str(user_id)` from day one.
- **bcrypt silently truncates at 72 bytes**: long passphrases past 72 bytes are cut;
  pre-hash with sha256 or cap length, or two different long passwords collide.
- **`HTTPBearer(auto_error=False)` on purpose**: `auto_error=True` raises its own 403
  with no `WWW-Authenticate` header and no custom detail. Use `auto_error=False` and
  raise your own 401 so clients get the header + a useful message.
- **jose, not pyjwt — fleet-wide**: both products use python-jose. Don't mix pyjwt in a
  new product (different API, different claim-validation defaults).

## Sources (SoT)

- `~/code/ChimesFlow/backend/app/services/auth_service.py` (+ `middleware/auth.py`, `routers/auth.py`)
- `~/code/Family-Fiscal/backend/auth.py`
- Convergence audit + spine context: `rivendell/docs/spine-modules.md` (#1) + the
  office-hours design doc (2026-06-27). Related: `spine-rbac` (decision 3 lives there).
