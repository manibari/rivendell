---
name: db-migration
loop: dev
pdca: do
description: >
  Set up database migration tools and generate migration files for schema changes.
  TRIGGER when: user modifies DB schema, adds a new model, asks about migrations,
  or project has a database but no migration tool configured.
  DO NOT TRIGGER when: project has no database, or migrations are already set up and user did not ask about them.
tags: [backend]
version: 1
source: manual
user_invocable: false
---

# Database Migration Setup

Detect database stack, set up migration tooling, and guide safe schema changes.

## Instructions

### Step 1: Detect Database Stack

Scan the project for database indicators:

| Indicator | ORM / Driver | Recommended Migration Tool |
|-----------|-------------|---------------------------|
| `sqlalchemy` in Python deps | SQLAlchemy | Alembic |
| `prisma` in Node.js deps | Prisma | Prisma Migrate (`npx prisma migrate dev`) |
| `drizzle-orm` in Node.js deps | Drizzle | Drizzle Kit (`npx drizzle-kit generate`) |
| `psycopg2` or `asyncpg` in Python deps (no ORM) | Raw SQL | Recommend adding SQLAlchemy + Alembic |
| `django` in Python deps | Django ORM | Django Migrations (`python manage.py makemigrations`) |
| `sqlite3` usage, `*.db` files | SQLite | Alembic (if SQLAlchemy) or manual |
| `mongoose` in Node.js deps | MongoDB / Mongoose | No formal migration needed (schema-less), but recommend migration scripts for data transforms |
| `firebase-admin` with Firestore | Firestore | No formal migration (schema-less), but recommend Firestore Security Rules versioning |

If no database is detected, inform the user and exit:
> No database detected in this project. This skill is for projects with databases.

### Step 2: Set Up Migration Tool

#### Alembic (Python / SQLAlchemy)

If Alembic is not installed:

1. Add `alembic` to project dependencies
2. Run `alembic init alembic` to scaffold
3. Configure `alembic/env.py`:
   - Import the project's SQLAlchemy `Base` metadata
   - Set `target_metadata = Base.metadata`
   - Configure `sqlalchemy.url` from environment variable

Key `env.py` configuration:

```python
from app.models import Base  # adjust import path

target_metadata = Base.metadata

def run_migrations_online():
    url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    connectable = create_engine(url)
    # ... standard alembic online migration
```

4. Add to `alembic.ini`:
   ```ini
   sqlalchemy.url = postgresql://localhost/dbname
   ```
   And add a comment: `# Override with DATABASE_URL env var in production`

#### Prisma Migrate (Node.js / Prisma)

If Prisma is detected but no migrations exist:

1. Ensure `prisma/schema.prisma` has a valid datasource and generator
2. Guide: `npx prisma migrate dev --name init`
3. This creates `prisma/migrations/` directory

#### Drizzle Kit (Node.js / Drizzle)

If Drizzle is detected:

1. Ensure `drizzle.config.ts` exists
2. Guide: `npx drizzle-kit generate` to create migration SQL
3. Guide: `npx drizzle-kit migrate` to apply

#### Raw SQL project (no ORM)

Recommend adding SQLAlchemy + Alembic:

> This project uses raw SQL (`psycopg2`). I recommend adding SQLAlchemy for schema management and Alembic for migrations. This gives you:
> - Version-controlled schema changes
> - Rollback capability
> - CI migration checks
>
> Want me to set this up?

### Step 3: Generate Migration

When the user modifies a model or schema:

1. **Generate migration file**:
   - Alembic: `alembic revision --autogenerate -m "description of change"`
   - Prisma: `npx prisma migrate dev --name description_of_change`
   - Drizzle: `npx drizzle-kit generate`

2. **Review the generated SQL**:
   - For Alembic: Read the generated file in `alembic/versions/`
   - Check for destructive operations (DROP TABLE, DROP COLUMN)
   - Flag data loss risks

3. **Test locally**:
   ```bash
   # Apply
   alembic upgrade head
   # Rollback
   alembic downgrade -1
   # Re-apply (confirms rollback works)
   alembic upgrade head
   ```

### Step 4: Add Migration Check to CI

If `.github/workflows/ci.yml` exists, suggest adding a migration check job:

```yaml
  migration-check:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - name: Run migrations
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
        run: alembic upgrade head
      - name: Check for pending migrations
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
        run: |
          alembic check || (echo "Pending migrations detected!" && exit 1)
```

### Step 5: Migration Best Practices

Always advise the user on these practices:

1. **Never edit an applied migration** — create a new one instead
2. **Always review autogenerated migrations** — they may miss rename operations (shows as drop + create)
3. **Test rollback** — ensure `downgrade()` works before pushing
4. **One migration per PR** — easier to review and rollback
5. **Add data migrations separately** — don't mix schema and data changes
6. **Back up before production migrations** — `pg_dump` before `alembic upgrade head`

### Step 6: Report

```
Project: ~/my-project
Database: PostgreSQL (psycopg2 + SQLAlchemy)

Migration setup:
  ✅ Alembic initialized (alembic/)
  ✅ env.py configured with project metadata
  ✅ Initial migration generated

Files created/modified:
  + alembic.ini
  + alembic/env.py
  + alembic/versions/001_initial.py

Next steps:
  1. Review the migration: alembic/versions/001_initial.py
  2. Apply locally: alembic upgrade head
  3. Test rollback: alembic downgrade -1
  4. Add migration check to CI (see suggestion above)
```
