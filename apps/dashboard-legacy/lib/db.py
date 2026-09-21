"""SQLite database layer for rivendell."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "rivendell.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS token_usage (
            date TEXT PRIMARY KEY,
            sessions INTEGER,
            api_calls INTEGER,
            tokens_total INTEGER,
            cost_usd REAL,
            details_json TEXT
        );

        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            project TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            exit_code INTEGER,
            log_path TEXT,
            report_path TEXT,
            tokens_used INTEGER,
            cost_usd REAL,
            commit_sha TEXT,
            files_changed INTEGER,
            qa_passed INTEGER,
            branch_name TEXT,
            pr_url TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        -- Liveness probes. Structural checks (symlinks, frontmatter) stayed
        -- green through a month-old build, an unreadable agent_runs table and
        -- a swallowed registry error, because none of them assert that a thing
        -- still DELIVERS. Each probe here traces to a failure that actually
        -- happened. A missing row means "never probed", which is not the same
        -- as ok=0 — don't collapse them.
        CREATE TABLE IF NOT EXISTS liveness_probe (
            probe TEXT PRIMARY KEY,
            checked_at TEXT NOT NULL,
            ok INTEGER NOT NULL,
            detail TEXT
        );
    """)
    conn.commit()

    # Migrate: add new columns to existing agent_runs table
    _migrate_agent_runs(conn)

    conn.close()


def _migrate_agent_runs(conn: sqlite3.Connection) -> None:
    """Add new columns to agent_runs if they don't exist yet."""
    cursor = conn.execute("PRAGMA table_info(agent_runs)")
    existing = {row[1] for row in cursor.fetchall()}
    new_columns = {
        "commit_sha": "TEXT",
        "files_changed": "INTEGER",
        "qa_passed": "INTEGER",
        "branch_name": "TEXT",
        "pr_url": "TEXT",
        # Task object: 角色 → 工作 → PDCA (docs/skills-by-role.md ids)
        "role": "TEXT",
        "job": "TEXT",
        "stage": "TEXT",
    }
    for col, col_type in new_columns.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE agent_runs ADD COLUMN {col} {col_type}")
    conn.commit()


class StoreUnreadable(RuntimeError):
    """The store could not be read. Distinct from "the query found nothing".

    Conflating the two is what let the agent_runs split hide for six weeks:
    /runs returned [] whether the table was empty or the file was the wrong
    one, so the dashboard reported zero and never erred.
    """


def read_agent_runs(agent_name: str, limit: int = 10) -> list[sqlite3.Row]:
    """Rows for one agent, newest first. Raises StoreUnreadable if the store
    itself cannot be queried — callers must not turn that into an empty list."""
    try:
        conn = get_conn()
    except (sqlite3.Error, OSError) as exc:
        # OSError matters: get_conn() mkdir's the parent first, so a full disk
        # or a bad path surfaces as OSError and would otherwise escape as a 500.
        raise StoreUnreadable(f"cannot open {DB_PATH}: {exc}") from exc
    try:
        return conn.execute(
            """
            SELECT started_at, finished_at, exit_code, tokens_used, cost_usd,
                   commit_sha, files_changed, qa_passed, branch_name, pr_url
            FROM agent_runs
            WHERE agent_name = ?
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (agent_name, limit),
        ).fetchall()
    except (sqlite3.Error, OSError) as exc:
        raise StoreUnreadable(f"agent_runs unreadable in {DB_PATH}: {exc}") from exc
    finally:
        conn.close()


def record_probe(probe: str, ok: bool, detail: str | None = None) -> None:
    """Upsert one liveness probe result."""
    from datetime import datetime
    conn = get_conn()
    conn.execute(
        "INSERT INTO liveness_probe(probe, checked_at, ok, detail) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(probe) DO UPDATE SET "
        "checked_at=excluded.checked_at, ok=excluded.ok, detail=excluded.detail",
        (probe, datetime.now().isoformat(timespec="seconds"), 1 if ok else 0, detail),
    )
    conn.commit()
    conn.close()


PROBE_STALE_HOURS = 36


def get_probes() -> list[dict]:
    """Every recorded probe, each tagged with its age.

    A probe result is only worth as much as it is recent. Nothing refreshes
    these except a `sk check liveness` run, so a passing row left behind by a
    run days ago would report green forever — the same silent-staleness bug
    this table exists to catch, just one level up. Anything older than
    PROBE_STALE_HOURS is marked stale and must not be read as passing.
    An absent probe is simply not listed: "never probed" is not "ok".
    """
    from datetime import datetime

    conn = get_conn()
    rows = conn.execute(
        "SELECT probe, checked_at, ok, detail FROM liveness_probe ORDER BY probe"
    ).fetchall()
    conn.close()

    out = []
    for r in rows:
        d = dict(r)
        try:
            age_h = (datetime.now() - datetime.fromisoformat(d["checked_at"])).total_seconds() / 3600
            d["age_hours"] = round(age_h, 1)
            d["stale"] = age_h > PROBE_STALE_HOURS
        except (ValueError, TypeError):
            d["age_hours"] = None
            d["stale"] = True
        if d["stale"]:
            d["ok"] = 0
            d["detail"] = f"STALE ({d['age_hours']}h old, limit {PROBE_STALE_HOURS}h): {d['detail']}"
        out.append(d)
    return out


def get_today_agent_cost() -> float:
    """Sum cost_usd from agent_runs for today."""
    from datetime import date
    conn = get_conn()
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT COALESCE(SUM(cost_usd), 0) FROM agent_runs WHERE started_at LIKE ?",
        (f"{today}%",),
    ).fetchone()
    conn.close()
    return float(row[0]) if row else 0.0


def get_last_success_time(agent_name: str | None = None) -> str | None:
    """Get the most recent finished_at where exit_code=0."""
    conn = get_conn()
    if agent_name:
        row = conn.execute(
            "SELECT finished_at FROM agent_runs WHERE exit_code=0 AND agent_name=? "
            "ORDER BY finished_at DESC LIMIT 1",
            (agent_name,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT finished_at FROM agent_runs WHERE exit_code=0 "
            "ORDER BY finished_at DESC LIMIT 1",
        ).fetchone()
    conn.close()
    return row[0] if row else None
