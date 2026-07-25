---
name: oauth-token-vault
description: OAuth Token Vault - Implement OAuth 2.0 flow with Fernet-encrypted token storage in FastAPI + PostgreSQL projects. TRIGGER when integrating third-party OAuth providers, storing access/refresh tokens securely, or building "Connect [Service]" UI. DO NOT TRIGGER when using API keys or non-OAuth authentication.
tags: [backend, oauth, security, tokens, fastapi]
version: 1.0.0
---

# OAuth Token Vault

Implement OAuth 2.0 flow with Fernet-encrypted token storage in FastAPI + PostgreSQL projects. Covers any provider (Microsoft Graph, Google, Slack, GitHub).

**TRIGGER when**: integrating third-party OAuth providers, storing access/refresh tokens securely, or building "Connect [Service]" UI in settings pages.

## Database Schema

```sql
-- Encrypted OAuth tokens
CREATE TABLE IF NOT EXISTS nx_oauth_token (
    id              SERIAL PRIMARY KEY,
    provider        TEXT NOT NULL UNIQUE,   -- 'microsoft_graph', 'google', 'slack'
    access_token    TEXT NOT NULL,          -- Fernet encrypted
    refresh_token   TEXT,                   -- Fernet encrypted
    token_type      TEXT DEFAULT 'Bearer',
    expires_at      TIMESTAMPTZ,
    scopes          TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

## Step 1: Encryption Module

Create `services/nexus/crypto.py`:

```python
"""Fernet symmetric encryption for sensitive values (OAuth tokens, API keys)."""
import os
from cryptography.fernet import Fernet

def _get_fernet() -> Fernet:
    key = os.environ.get("NEXUS_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("NEXUS_ENCRYPTION_KEY env var not set")
    return Fernet(key.encode() if isinstance(key, str) else key)

def encrypt_value(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()

def decrypt_value(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
```

Generate a key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

Add to `.env`:
```
NEXUS_ENCRYPTION_KEY=<generated-key>
```

**⚠️ Back up this key.** If lost, all stored tokens become unrecoverable.

## Step 2: OAuth Service

Create `services/nexus/oauth.py` (example for Microsoft Graph):

```python
import os, httpx
from datetime import datetime, timezone, timedelta
from services.nexus.crypto import encrypt_value, decrypt_value

MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

SCOPES = "Mail.Read Mail.Send Calendars.ReadWrite Contacts.ReadWrite offline_access"

def get_auth_url(redirect_uri: str) -> str:
    tenant = os.environ.get("MICROSOFT_TENANT_ID", "common")
    params = {
        "client_id": os.environ["MICROSOFT_CLIENT_ID"],
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "response_mode": "query",
    }
    return MICROSOFT_AUTH_URL.format(tenant=tenant) + "?" + "&".join(f"{k}={v}" for k,v in params.items())

async def exchange_code(code: str, redirect_uri: str) -> dict:
    tenant = os.environ.get("MICROSOFT_TENANT_ID", "common")
    async with httpx.AsyncClient() as client:
        resp = await client.post(MICROSOFT_TOKEN_URL.format(tenant=tenant), data={
            "client_id": os.environ["MICROSOFT_CLIENT_ID"],
            "client_secret": os.environ["MICROSOFT_CLIENT_SECRET"],
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        resp.raise_for_status()
        return resp.json()

def store_token(provider: str, token_data: dict, cur) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
    cur.execute("""
        INSERT INTO nx_oauth_token (provider, access_token, refresh_token, expires_at, scopes)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (provider) DO UPDATE SET
            access_token = EXCLUDED.access_token,
            refresh_token = COALESCE(EXCLUDED.refresh_token, nx_oauth_token.refresh_token),
            expires_at = EXCLUDED.expires_at,
            scopes = EXCLUDED.scopes,
            updated_at = NOW()
    """, (
        provider,
        encrypt_value(token_data["access_token"]),
        encrypt_value(token_data["refresh_token"]) if token_data.get("refresh_token") else None,
        expires_at,
        token_data.get("scope", ""),
    ))

def get_valid_token(provider: str, cur) -> str:
    """Return a valid access token, refreshing if needed."""
    cur.execute("SELECT * FROM nx_oauth_token WHERE provider = %s", (provider,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"No token stored for {provider}")

    # Check expiry (refresh 5 min early)
    if row["expires_at"] and row["expires_at"] < datetime.now(timezone.utc) + timedelta(minutes=5):
        if row["refresh_token"]:
            token_data = _refresh_token(provider, decrypt_value(row["refresh_token"]))
            store_token(provider, token_data, cur)
            return token_data["access_token"]

    return decrypt_value(row["access_token"])
```

## Step 3: OAuth Router (FastAPI)

```python
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api/nx/oauth")

@router.get("/{provider}/url")
def auth_url(provider: str, request: Request):
    redirect_uri = f"{request.base_url}api/nx/oauth/{provider}/callback"
    return {"url": get_auth_url(redirect_uri)}

@router.get("/{provider}/callback")
async def auth_callback(provider: str, code: str, request: Request):
    redirect_uri = f"{request.base_url}api/nx/oauth/{provider}/callback"
    token_data = await exchange_code(code, redirect_uri)
    with get_conn() as conn:
        with conn.cursor() as cur:
            store_token(provider, token_data, cur)
    # Close popup and notify opener
    return HTMLResponse("""
        <script>
          window.opener?.postMessage('oauth_complete', '*');
          window.close();
        </script>
        <p>已連接，視窗即將關閉...</p>
    """)

@router.get("/{provider}/status")
def auth_status(provider: str):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT provider, expires_at, scopes, updated_at FROM nx_oauth_token WHERE provider = %s", (provider,))
            row = cur.fetchone()
    if not row:
        return {"connected": False}
    expired = row["expires_at"] and row["expires_at"] < datetime.now(timezone.utc)
    return {"connected": True, "expired": expired, "scopes": row["scopes"], "updated_at": str(row["updated_at"])}
```

## Step 4: Frontend OAuth Flow

```typescript
// Settings tab — connect button
async function connectOAuth(provider: string) {
  const { url } = await fetch(`/api/nx/oauth/${provider}/url`).then(r => r.json());
  const popup = window.open(url, 'oauth', 'width=600,height=700');

  await new Promise<void>((resolve) => {
    window.addEventListener('message', (e) => {
      if (e.data === 'oauth_complete') {
        popup?.close();
        resolve();
      }
    }, { once: true });
  });

  // Refresh status
  await refreshStatus();
}
```

## Common Pitfalls

| Issue | Solution |
|-------|---------|
| Azure AD phone verification blocked | Use Microsoft Authenticator app instead of SMS |
| Token refresh fails silently | Always log refresh errors; fall back to re-auth |
| `NEXUS_ENCRYPTION_KEY` not set | Raise loudly at startup, not at first use |
| Popup blocked by browser | Use button click (user gesture) to trigger `window.open()` |
| Multiple providers | Use `provider` text field as UNIQUE key — one row per provider |

## Environment Variables

```env
# Required
NEXUS_ENCRYPTION_KEY=<fernet-key>

# Microsoft Graph
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=http://localhost:8002/api/nx/oauth/microsoft_graph/callback

# Google
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8002/api/nx/oauth/google/callback
```

## Dependencies

```
cryptography>=42.0
httpx>=0.27
```
