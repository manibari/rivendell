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
