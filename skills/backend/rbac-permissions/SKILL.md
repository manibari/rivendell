---
name: rbac-permissions
loop: dev
pdca: do
description: >
  Design and implement Role-Based Access Control (RBAC) for full-stack apps.
  Covers role hierarchy, Python/FastAPI decorator-based backend protection,
  React AuthContext + AuthGuard frontend, and API middleware.
  TRIGGER when: user says "權限管理", "RBAC", "role-based access", "每個人只能看自己的",
  "多人帳號", "admin/member 分權", "auth guard", "protect routes", "permission middleware",
  "內外帳", "誰能看什麼", "user roles".
  DO NOT TRIGGER when: user only needs authentication (login/logout) without role differentiation
  — use a simpler JWT auth pattern instead.
tags: [backend, frontend]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# RBAC Permissions

Full-stack role-based access control: backend decorators + frontend guards.

## Step 1: Define Role Hierarchy

Ask the user to confirm their roles, or default to this three-tier model:

```python
# backend/app/core/roles.py
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"    # Full access: all CRUD + user management
    LEAD = "lead"      # Content management + view-only for sensitive data
    MEMBER = "member"  # Read-only for own data

# Permission matrix
ROLE_PERMISSIONS = {
    Role.ADMIN:  {"users:manage", "data:read", "data:write", "data:delete", "settings:manage"},
    Role.LEAD:   {"data:read", "data:write", "team:manage"},
    Role.MEMBER: {"data:read"},
}

def has_permission(role: Role, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
```

Adjust roles and permissions based on the actual product. Common customizations:
- Add `VIEWER` below `MEMBER` for read-only guests
- Add resource-level ownership (`data:write:own` vs `data:write:all`)
- B2C: use `owner` / `collaborator` instead of admin/lead/member

---

## Step 2: Backend — FastAPI

### Permission decorator

```python
# backend/app/core/permissions.py
from functools import wraps
from fastapi import HTTPException, status
from .roles import Role, has_permission

def require_role(*allowed_roles: Role):
    """Decorator: restrict endpoint to specific roles."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=None, **kwargs):
            if current_user is None or current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role: {[r.value for r in allowed_roles]}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_permission(permission: str):
    """Decorator: restrict endpoint by permission string."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=None, **kwargs):
            if not has_permission(current_user.role, permission):
                raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

### FastAPI dependency injection

```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from .core.roles import Role

security = HTTPBearer()

async def get_current_user(token=Depends(security)) -> User:
    """Decode JWT, return User with .role populated."""
    # ... your JWT decode logic ...
    return user

async def require_admin(user=Depends(get_current_user)) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(403, "Admin only")
    return user

async def require_lead_or_above(user=Depends(get_current_user)) -> User:
    if user.role not in (Role.ADMIN, Role.LEAD):
        raise HTTPException(403, "Lead or above required")
    return user
```

### Usage in routes

```python
# backend/app/api/routes/users.py
from fastapi import APIRouter, Depends
from ..deps import require_admin, require_lead_or_above, get_current_user

router = APIRouter()

@router.get("/users")          # Admin only
async def list_users(admin=Depends(require_admin)):
    ...

@router.get("/reports")        # Lead and above
async def get_reports(user=Depends(require_lead_or_above)):
    ...

@router.get("/profile")        # Any authenticated user
async def get_profile(user=Depends(get_current_user)):
    # Resource-level: only own data
    return user.profile
```

---

## Step 3: Frontend — React/Next.js

### AuthContext

```tsx
// contexts/AuthContext.tsx
"use client";
import { createContext, useContext, useState, useEffect } from "react";

type Role = "admin" | "lead" | "member";

interface AuthState {
  user: { id: string; name: string; role: Role } | null;
  isLoading: boolean;
}

const AuthContext = createContext<AuthState>({ user: null, isLoading: true });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, isLoading: true });

  useEffect(() => {
    // Fetch current user from /api/me
    fetch("/api/me")
      .then(r => r.ok ? r.json() : null)
      .then(user => setState({ user, isLoading: false }))
      .catch(() => setState({ user: null, isLoading: false }));
  }, []);

  return <AuthContext.Provider value={state}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
```

### AuthGuard component (route-level protection)

```tsx
// components/AuthGuard.tsx
"use client";
import { useAuth } from "@/contexts/AuthContext";
import { redirect } from "next/navigation";

type Role = "admin" | "lead" | "member";

const ROLE_RANK: Record<Role, number> = { admin: 3, lead: 2, member: 1 };

export function AuthGuard({
  children,
  minRole = "member",
  fallback = null,
}: {
  children: React.ReactNode;
  minRole?: Role;
  fallback?: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div>Loading...</div>;
  if (!user) { redirect("/login"); return null; }

  const hasAccess = ROLE_RANK[user.role] >= ROLE_RANK[minRole];
  if (!hasAccess) return fallback ?? <p className="text-red-500">權限不足</p>;

  return <>{children}</>;
}
```

### Usage in pages

```tsx
// app/admin/page.tsx
import { AuthGuard } from "@/components/AuthGuard";

export default function AdminPage() {
  return (
    <AuthGuard minRole="admin">
      <AdminDashboard />
    </AuthGuard>
  );
}
```

### useAuth hook for conditional rendering

```tsx
// Anywhere in a component
const { user } = useAuth();

return (
  <div>
    <p>歡迎，{user?.name}</p>
    {user?.role === "admin" && <AdminPanel />}
    {(user?.role === "admin" || user?.role === "lead") && <ReportsLink />}
  </div>
);
```

---

## Step 4: DB Schema

```sql
-- Add role column to users table
ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'member'
  CHECK (role IN ('admin', 'lead', 'member'));

-- Index for fast role queries
CREATE INDEX idx_users_role ON users(role);
```

---

## Step 5: Testing Patterns

```python
# tests/test_permissions.py
import pytest

@pytest.mark.parametrize("role,endpoint,expected_status", [
    ("admin",  "/api/users",    200),
    ("lead",   "/api/users",    403),
    ("member", "/api/users",    403),
    ("admin",  "/api/reports",  200),
    ("lead",   "/api/reports",  200),
    ("member", "/api/reports",  403),
    ("member", "/api/profile",  200),
])
async def test_role_access(role, endpoint, expected_status, client, make_token):
    token = make_token(role=role)
    resp = await client.get(endpoint, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == expected_status
```

---

## Common Issues

| Issue | Fix |
|-------|-----|
| AuthGuard flickers on load | Show spinner while `isLoading` is true |
| Role changes not reflected immediately | Invalidate session/refresh token after role update |
| Resource ownership (user sees only own data) | Add `WHERE owner_id = current_user.id` in queries, not just role check |
| Frontend guard bypassed | Always validate on backend — frontend guard is UX only |
