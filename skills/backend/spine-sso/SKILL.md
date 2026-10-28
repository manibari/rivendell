---
name: spine-sso
loop: dev
pdca: do
description: >
  Canonical Microsoft Entra ID (Office 365) sign-in for the product fleet: the CONVERGENT core
  (AZURE_AD_* settings, id_token checks, company-domain limit, SSO allowlist, provisioning order,
  password sign-in kept as break-glass) plus the one DIVERGENT choice, the flow: browser MSAL
  (ChimesFlow) or server-side authorization code (people-ops, recommended). Also the Entra app
  registration hand-off and the same registration for Graph calendar writes. Audit of ChimesFlow,
  people-ops (hr.chimes.ai) and ChimesERP, 2026-10-28.
  TRIGGER when: "微軟登入", "Microsoft 登入", "公司帳號登入", "Entra", "Azure AD SSO", "串 SSO",
  adding or fixing company-account sign-in in a fleet product, an AADSTS error at sign-in, or
  registering an Entra app for sign-in or Outlook calendar sync.
  SKIP when: local passwords, JWT, hashing (spine-auth); per-user tokens for a third-party API
  (oauth-token-vault); roles and permission matrices (spine-rbac).
tags: [backend, auth, sso, entra, fastapi, nextjs, spine, security]
version: 1.0.0
source: manual
---

# spine-sso

One Entra app registration per product. The browser goes to Microsoft, comes back, and the
backend turns a verified Microsoft identity into the product's own session. Everything except
the flow is the same in every product; copy the core, choose the flow.

## 1. Choose the flow (the only divergent decision)

| | A. Browser MSAL (SPA) | B. Server-side code flow (recommended) |
|---|---|---|
| Where | ChimesFlow (`frontend/src/lib/msal.ts`, `loginRedirect`) | people-ops / hr.chimes.ai (NextAuth `azure-ad` provider) |
| Entra platform | **Single-page application** | **Web** |
| Who redeems the code | the browser (PKCE, no secret) | the server (client secret + PKCE) |
| Backend receives | an `id_token` (`POST /api/auth/login/azure`) | the `code`, then exchanges it |
| Cost | `@azure/msal-browser` dependency, token handling in the browser | two server routes; the secret never reaches the browser |

The platform type must match the flow, or Microsoft refuses at the callback:
`AADSTS9002325` (a secret sent for a SPA redirect URI; the message talks about PKCE and misleads)
and `AADSTS9002326` (a browser redeem against a Web redirect URI). Pick B for new work. Keep A
where it already runs.

## 2. Convergent core (every product)

- **Settings**: `AZURE_AD_TENANT_ID`, `AZURE_AD_CLIENT_ID`, `AZURE_AD_CLIENT_SECRET`,
  `AZURE_AD_ALLOWED_DOMAIN`. ChimesFlow and ChimesERP also keep them in a DB row that an admin page
  edits (DB first, env fallback; the secret per field). A missing value means SSO is off and the
  login page shows only passwords; nothing else breaks.
- **Public config endpoint** `GET /api/auth/sso-config`: `enabled`, tenant, client, domain. Never
  the secret.
- **id_token checks**: signature against the tenant JWKS (refetch once on an unknown `kid`),
  `aud` = client ID, `iss` = `https://login.microsoftonline.com/<tenant>/v2.0`, expiry, the e-mail
  domain = the allowed domain, and in flow B the `nonce` from the start step.
- **Provisioning order** for a first sign-in: (1) the SSO allowlist row gives the role,
  (2) the first user of an empty system becomes admin, (3) else the default role. Link the new
  user to the employee row with the same company e-mail. A disabled user gets 403.
- **Audit** each failure with a reason code (`not_configured`, `invalid_token`, `domain`,
  `disabled`, `state`), never with the token or the code.
- **Break-glass**: password sign-in stays for admins (expired secret, broken registration, new
  staff without a mailbox). SSO-created users get a random password hash.

## 3. Flow B steps (Next.js front + FastAPI back, same-origin proxy)

1. **Routes are Next route handlers, not the generic `/api/*` proxy.** A proxy that forwards only
   the body and `content-type` drops `Location` and `Set-Cookie` (ChimesERP
   `app/api/[...path]/route.ts`). Put them beside the password route: `/session/microsoft/start`
   and `/session/microsoft/callback`, and list both as public in the auth middleware.
2. **Start**: the backend makes `state`, `nonce` and a PKCE verifier, signs them with `next` into a
   10-minute token (the app `SECRET_KEY`), and returns the authorize URL (`response_type=code`,
   `scope=openid profile email`, `code_challenge_method=S256`). Next stores the token in an
   HttpOnly cookie (`SameSite=Lax`, `Secure` on https, path `/session/microsoft`) and redirects.
3. **Callback**: Next sends `code`, `state` and the cookie token to the backend. The backend checks
   the token and `state` (constant-time compare), redeems the code with the secret and the
   verifier, runs the section 2 checks, provisions, and returns the session token. Next sets the
   session cookie exactly like the password route, clears the state cookie, and redirects to `next`.
4. **Redirect URI** comes from configuration (`PUBLIC_BASE_URL` + the callback path), never from the
   `Host` header. Accept `next` only as a relative path that starts with one `/`.
5. **Errors** redirect to `/login?error=<code>`; the login page maps each code to a message in the
   UI language.

Done when: a company account signs in and lands on its start page; an outside account, a disabled
account and a replayed callback are refused with the right message; password sign-in still works.

## 4. Entra registration (an Entra admin does it; give them this list)

- New registration per product, single tenant. Name it after the product.
- Platform **Web** (flow B) or **SPA** (flow A). Redirect URIs: production
  `https://<domain>/session/microsoft/callback` and local `http://localhost:<port>/session/microsoft/callback`
  (people-ops: `https://hr.chimes.ai/api/auth/callback/azure-ad`, the NextAuth path).
- Client secret: 24 months, and a calendar reminder before it expires. When it expires, every
  sign-in fails with a Microsoft-side error that nobody links to the secret.
- Delegated Graph permissions `openid`, `profile`, `email`, `User.Read` (no admin consent in a
  single tenant).
- Outlook calendar writes from the server (1:1 meetings, approved leave): application permission
  `Calendars.ReadWrite` plus admin consent (Global Administrator or Privileged Role Administrator),
  `client_credentials` grant with scope `https://graph.microsoft.com/.default`, token cached until
  one minute before expiry. Use the same registration.
- The admin sends back tenant ID and client ID. The product owner types the secret into the admin
  page or the server `.env` personally; it never passes through a chat.

## 5. Troubleshooting

| Symptom | Cause |
|---|---|
| No Microsoft button | settings incomplete, or the container was not restarted after an env change |
| `AADSTS50011` redirect URI mismatch | the registered URI differs in scheme, host, port, path or a trailing slash |
| `AADSTS9002325` / `AADSTS9002326` | platform type does not match the flow (section 1) |
| "Only company accounts" | a personal or guest account; the domain check works |
| Everyone fails at once | the client secret expired |
| Signed in but sees no own data | the employee row e-mail differs from the sign-in e-mail |

## Fleet status (2026-10-28)

| Product | Flow | State |
|---|---|---|
| ChimesFlow | A (MSAL redirect) | live |
| people-ops (hr.chimes.ai) | B (NextAuth) | live; allowlist kept by SQL only |
| ChimesERP | backend has A's `/login/azure`; the login button is a disabled placeholder | flow B planned; `sso-config` was `enabled: false` on 8110 and erp.chimes.ai |

Related: [[spine-auth]] (passwords and JWT), [[spine-rbac]] (roles), [[gcp-vm-deploy]] (token
clients behind the frontend proxy).
