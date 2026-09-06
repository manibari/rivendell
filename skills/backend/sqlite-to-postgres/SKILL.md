---
name: SQLite to PostgreSQL Migration
loop: dev
pdca: do
description: >
  Migrate an existing project from SQLite to PostgreSQL (or Supabase) — syntax diffs,
  schema conversion, data migration, connection layer, verification.
  TRIGGER: SQLite → PostgreSQL/Supabase migration, replace sqlite3 with psycopg2/asyncpg.
  SKIP: new PostgreSQL project (no SQLite); same-engine migrations (db-migration).
version: 1.0.0
tags: [backend, database, migration, sqlite, postgresql, supabase]
languages: [python, sql]
---

# SQLite → PostgreSQL Migration

A step-by-step guide for migrating from SQLite to PostgreSQL. The key challenge isn't just changing the connection — it's finding and fixing all the SQLite-specific syntax scattered through the codebase.

## Migration Checklist

```
[ ] 1. Audit — Find all SQLite-specific code
[ ] 2. Schema — Convert DDL to PostgreSQL syntax
[ ] 3. Queries — Fix SQLite-specific SQL
[ ] 4. Connection — Replace sqlite3 with psycopg2/asyncpg
[ ] 5. Data — Migrate existing data
[ ] 6. Verify — Test all endpoints/functions
```

## Step 1: Audit SQLite Usage

Search the entire codebase for SQLite-specific patterns:

```bash
# Find SQLite imports and connections
grep -rn "import sqlite3\|sqlite3.connect\|\.db\b" --include="*.py"

# Find SQLite-specific SQL syntax
grep -rn "julianday\|strftime\|datetime('now')\|INSERT OR IGNORE\|INSERT OR REPLACE" --include="*.py"
grep -rn "PRAGMA\|executescript\|INTEGER PRIMARY KEY\b" --include="*.py"
grep -rn "autoincrement\|AUTOINCREMENT" --include="*.py" -i

# Find database file references
grep -rn "\.db\"\|\.sqlite\"\|\.sqlite3\"" --include="*.py"
```

## Step 2: Schema Conversion

### Type Mapping

| SQLite | PostgreSQL | Notes |
|--------|-----------|-------|
| `INTEGER PRIMARY KEY` | `SERIAL PRIMARY KEY` | Auto-increment |
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` | Same behavior |
| `TEXT` | `TEXT` or `VARCHAR(n)` | Compatible |
| `REAL` | `DOUBLE PRECISION` | Or `NUMERIC` for exact |
| `BLOB` | `BYTEA` | |
| `TEXT` (storing JSON) | `JSONB` | Use JSONB for queryable JSON |
| `BOOLEAN` (as 0/1) | `BOOLEAN` | PostgreSQL has native boolean |

### DDL Patterns

```sql
-- SQLite
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    data TEXT,  -- storing JSON
    created_at TEXT DEFAULT (datetime('now'))
);

-- PostgreSQL
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Index Differences

```sql
-- SQLite: IF NOT EXISTS is optional
CREATE INDEX idx_users_name ON users(name);

-- PostgreSQL: same syntax, but supports more types
CREATE INDEX idx_users_name ON users(name);
CREATE INDEX idx_users_data ON users USING GIN(data);  -- JSONB index
```

## Step 3: Query Conversion

### Date/Time Functions

| SQLite | PostgreSQL |
|--------|-----------|
| `datetime('now')` | `NOW()` |
| `datetime('now', '-7 days')` | `NOW() - INTERVAL '7 days'` |
| `strftime('%Y-%m-%d', date_col)` | `TO_CHAR(date_col, 'YYYY-MM-DD')` |
| `julianday('now') - julianday(col)` | `EXTRACT(EPOCH FROM NOW() - col) / 86400` |
| `date('now')` | `CURRENT_DATE` |

### Upsert / Conflict Handling

```sql
-- SQLite
INSERT OR IGNORE INTO table (col) VALUES (?);
INSERT OR REPLACE INTO table (col) VALUES (?);

-- PostgreSQL
INSERT INTO table (col) VALUES ($1) ON CONFLICT DO NOTHING;
INSERT INTO table (col) VALUES ($1)
    ON CONFLICT (col) DO UPDATE SET col = EXCLUDED.col;
```

### Parameterized Queries

```python
# SQLite uses ? placeholders
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# psycopg2 uses %s placeholders
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# asyncpg uses $1, $2 placeholders
await conn.fetch("SELECT * FROM users WHERE id = $1", user_id)
```

### Boolean Handling

```sql
-- SQLite (no native boolean)
SELECT * FROM users WHERE active = 1;
INSERT INTO users (active) VALUES (0);

-- PostgreSQL
SELECT * FROM users WHERE active = TRUE;
INSERT INTO users (active) VALUES (FALSE);
```

### String Functions

| SQLite | PostgreSQL |
|--------|-----------|
| `\|\|` (concat) | `\|\|` (same) |
| `LIKE` (case-insensitive by default) | `ILIKE` (case-insensitive) |
| `LENGTH()` | `LENGTH()` (same) |
| `SUBSTR()` | `SUBSTRING()` |
| `GROUP_CONCAT(col, ',')` | `STRING_AGG(col, ',')` |

### PRAGMA → PostgreSQL Equivalents

```sql
-- SQLite
PRAGMA table_info(users);
PRAGMA foreign_keys = ON;

-- PostgreSQL
SELECT column_name, data_type FROM information_schema.columns
    WHERE table_name = 'users';
-- Foreign keys are always enforced in PostgreSQL
```

## Step 4: Connection Layer

### Python with psycopg2

```python
# Before (SQLite)
import sqlite3
conn = sqlite3.connect("data.db")
conn.row_factory = sqlite3.Row

# After (PostgreSQL)
import psycopg2
import psycopg2.extras
conn = psycopg2.connect(os.environ["DATABASE_URL"])
# For dict-like rows:
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
```

Key differences:
- PostgreSQL requires explicit `conn.commit()` (SQLite autocommits in some modes)
- PostgreSQL connections should use connection pooling for web apps
- Use `with conn:` for automatic transaction management

### Connection Pooling

```python
from psycopg2 import pool

db_pool = pool.ThreadedConnectionPool(
    minconn=2, maxconn=10,
    dsn=os.environ["DATABASE_URL"]
)

def get_conn():
    return db_pool.getconn()

def put_conn(conn):
    db_pool.putconn(conn)
```

### Supabase-Specific

```python
# Direct connection (for migrations/admin)
import psycopg2
conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])

# Via Supabase client (for app code with RLS)
from supabase import create_client
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)
```

## Step 5: Data Migration Script

```python
"""Migrate data from SQLite to PostgreSQL."""
import sqlite3
import psycopg2
import json

sqlite_conn = sqlite3.connect("data.db")
sqlite_conn.row_factory = sqlite3.Row
pg_conn = psycopg2.connect(os.environ["DATABASE_URL"])

# For each table:
rows = sqlite_conn.execute("SELECT * FROM users").fetchall()
for row in rows:
    pg_conn.execute(
        "INSERT INTO users (id, name, data, created_at) VALUES (%s, %s, %s, %s)",
        (row["id"], row["name"],
         json.dumps(json.loads(row["data"])) if row["data"] else None,  # TEXT → JSONB
         row["created_at"])
    )

pg_conn.commit()

# Reset sequence after importing with explicit IDs
pg_conn.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")
pg_conn.commit()
```

Important: After inserting with explicit IDs, reset the `SERIAL` sequence or the next auto-generated ID will conflict.

## Step 6: Verification

After migration, verify every database interaction:

```python
# Quick smoke test
python3 -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM users')
print(f'Users: {cur.fetchone()[0]}')
conn.close()
"
```

Checklist:
- [ ] All tables exist with correct schema
- [ ] Row counts match between SQLite and PostgreSQL
- [ ] All API endpoints return correct data
- [ ] Date/time values are correct (timezone handling)
- [ ] JSON fields are queryable
- [ ] Auto-increment sequences are correctly set
- [ ] Foreign key constraints work
- [ ] Application can handle connection pooling under load

## Common Pitfalls

1. **Forgetting to reset sequences** — After bulk insert with explicit IDs, `SERIAL` columns still start at 1. Always run `setval()`.

2. **Timezone handling** — SQLite stores text, PostgreSQL has `TIMESTAMPTZ`. Decide on UTC or local time and be consistent.

3. **Transaction behavior** — SQLite auto-commits by default in many libraries. PostgreSQL requires explicit commits. Wrap operations in `with conn:` blocks.

4. **Case sensitivity** — PostgreSQL identifiers are case-sensitive when quoted. Avoid double-quoting table/column names unless necessary.

5. **LIKE vs ILIKE** — SQLite's `LIKE` is case-insensitive for ASCII. PostgreSQL's `LIKE` is case-sensitive; use `ILIKE` for case-insensitive matching.
