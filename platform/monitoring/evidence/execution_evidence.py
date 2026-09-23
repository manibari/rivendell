"""Execution evidence: one store and one query for "has this job actually run?".

Two writers exist and stay as they are:

- sk-exec-lib appends scheduled runs to rivendell.db `agent_runs`.
- task-tag.sh appends interactive session tags to
  ~/.claude/session-logs/<repo>/tasks.jsonl.

`sync()` copies both into `execution_event`, keyed by (source, source_id), so
it can be re-run any number of times without double counting. `job_summary()`
reads only `execution_event` and reports a status next to the numbers:

    ok           the store was read and holds at least one event
    empty        the store was read and holds nothing
    unavailable  a source or the store could not be read; counts are partial

"unavailable" must never be shown as zero runs. That collapse is the defect the
2026-09-22 dataflow audit found in the role view.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_DIR = Path(__file__).resolve().parents[3]
DB_DIR = Path(os.environ.get(
    "RIVENDELL_DB_DIR", str(REPO_DIR / "apps" / "dashboard-legacy" / "data")
))
SESSION_LOGS = Path(os.environ.get(
    "RIVENDELL_SESSION_LOGS", str(Path.home() / ".claude" / "session-logs")
))
SOURCES = ("agent_runs", "session")

SCHEMA = """
CREATE TABLE IF NOT EXISTS execution_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    project TEXT,
    agent_name TEXT,
    role TEXT,
    job TEXT,
    stage TEXT,
    occurred_at TEXT,
    exit_code INTEGER,
    note TEXT,
    imported_at TEXT NOT NULL,
    UNIQUE (source, source_id)
);
CREATE INDEX IF NOT EXISTS execution_event_job ON execution_event(job);
CREATE TABLE IF NOT EXISTS execution_import_cursor (
    source TEXT PRIMARY KEY,
    position TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _stage(value: Any) -> str:
    return str(value or "").strip().lower()


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=5)
    try:
        conn.executescript(SCHEMA)
    except sqlite3.Error:
        conn.close()
        raise
    return conn


def _import_agent_runs(conn: sqlite3.Connection) -> dict[str, Any]:
    """Copy agent_runs rows past the cursor. agent_runs.id is the source_id."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(agent_runs)")}
    if not cols:
        return {"status": "empty", "imported": 0}
    row = conn.execute(
        "SELECT position FROM execution_import_cursor WHERE source = 'agent_runs'"
    ).fetchone()
    last = int(row[0]) if row else 0
    task = [c if c in cols else f"NULL AS {c}" for c in ("role", "job", "stage")]
    rows = conn.execute(
        f"SELECT id, project, agent_name, {', '.join(task)}, started_at, exit_code "
        "FROM agent_runs WHERE id > ? ORDER BY id",
        (last,),
    ).fetchall()
    now = _now()
    imported = 0
    for rid, project, agent, role, job, stage, started, exit_code in rows:
        if job and not role:
            role = str(job).rstrip("abcdefghijklmnopqrstuvwxyz")
        cur = conn.execute(
            "INSERT OR IGNORE INTO execution_event (source, source_id, project, agent_name, "
            "role, job, stage, occurred_at, exit_code, imported_at) "
            "VALUES ('agent_runs', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(rid), project, agent, role or None, job or None, _stage(stage) or None,
             started, exit_code, now),
        )
        imported += cur.rowcount
        last = rid
    conn.execute(
        "INSERT INTO execution_import_cursor (source, position, updated_at) VALUES ('agent_runs', ?, ?) "
        "ON CONFLICT(source) DO UPDATE SET position = excluded.position, updated_at = excluded.updated_at",
        (str(last), now),
    )
    return {"status": "ok", "imported": imported}


def _import_session_tags(conn: sqlite3.Connection, logs_dir: Path) -> dict[str, Any]:
    """Import every tasks.jsonl line. The line hash is the source_id, so the
    files can be re-read in full; append-only files need no byte cursor."""
    if not logs_dir.is_dir():
        return {"status": "empty", "imported": 0}
    now = _now()
    imported = 0
    bad_lines: list[str] = []
    unreadable: list[str] = []
    for path in sorted(logs_dir.glob("*/tasks.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            unreadable.append(f"{path}: {exc}")
            continue
        slug = path.parent.name
        for number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if not isinstance(rec, dict):
                    raise ValueError("not an object")
            except ValueError:
                bad_lines.append(f"{path}:{number}")
                continue
            source_id = hashlib.sha256(f"{slug}\n{line}".encode()).hexdigest()[:32]
            job = str(rec.get("job") or "") or None
            role = str(rec.get("role") or "") or (job.rstrip("abcdefghijklmnopqrstuvwxyz") if job else None)
            cur = conn.execute(
                "INSERT OR IGNORE INTO execution_event (source, source_id, project, role, job, "
                "stage, occurred_at, note, imported_at) VALUES ('session', ?, ?, ?, ?, ?, ?, ?, ?)",
                (source_id, rec.get("project") or slug, role, job, _stage(rec.get("stage")) or None,
                 rec.get("ts"), rec.get("note"), now),
            )
            imported += cur.rowcount
    result: dict[str, Any] = {"status": "ok", "imported": imported}
    if bad_lines:
        result["bad_lines"] = bad_lines
    if unreadable:
        result["status"] = "unavailable"
        result["error"] = "; ".join(unreadable)
    return result


def sync(db_dir: Path | None = None, logs_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Import both sources. Returns per-source {status, imported, error?}."""
    db_path = (db_dir or DB_DIR) / "rivendell.db"
    out: dict[str, dict[str, Any]] = {}
    try:
        conn = _connect(db_path)
    except (sqlite3.Error, OSError) as exc:
        err = {"status": "unavailable", "imported": 0, "error": f"{db_path}: {exc}"}
        return {name: dict(err) for name in SOURCES}
    try:
        for name, step in (("agent_runs", lambda: _import_agent_runs(conn)),
                           ("session", lambda: _import_session_tags(conn, logs_dir or SESSION_LOGS))):
            try:
                out[name] = step()
                conn.commit()
            except (sqlite3.Error, OSError) as exc:
                conn.rollback()
                out[name] = {"status": "unavailable", "imported": 0, "error": str(exc)}
    finally:
        conn.close()
    return out


def job_summary(db_dir: Path | None = None, logs_dir: Path | None = None, *, refresh: bool = True) -> dict[str, Any]:
    """{status, sources, jobs: {job: {runs, by_stage, last_run, sources}}}."""
    sources = sync(db_dir, logs_dir) if refresh else {}
    db_path = (db_dir or DB_DIR) / "rivendell.db"
    jobs: dict[str, dict[str, Any]] = {}
    counts = {name: 0 for name in SOURCES}
    try:
        conn = _connect(db_path)
        try:
            for name, count in conn.execute("SELECT source, COUNT(*) FROM execution_event GROUP BY source"):
                counts[name] = count
            rows = conn.execute(
                "SELECT job, stage, occurred_at, source FROM execution_event "
                "WHERE job IS NOT NULL AND job != ''"
            ).fetchall()
        finally:
            conn.close()
    except (sqlite3.Error, OSError) as exc:
        return {"status": "unavailable", "error": f"{db_path}: {exc}",
                "sources": sources, "jobs": {}}
    for job, stage, ts, source in rows:
        rec = jobs.setdefault(job, {"runs": 0, "by_stage": {}, "last_run": "", "sources": {}})
        rec["runs"] += 1
        if stage:
            rec["by_stage"][stage] = rec["by_stage"].get(stage, 0) + 1
        day = (ts or "")[:10]
        if day > rec["last_run"]:
            rec["last_run"] = day
        rec["sources"][source] = rec["sources"].get(source, 0) + 1
    for name in SOURCES:
        sources.setdefault(name, {"status": "ok"})["events"] = counts[name]
    if any(s.get("status") == "unavailable" for s in sources.values()):
        status = "unavailable"
    else:
        status = "ok" if sum(counts.values()) else "empty"
    return {"status": status, "sources": sources, "jobs": jobs}


def reconcile(legacy_db: Path, db_dir: Path | None = None) -> dict[str, Any]:
    """Compare a legacy agent_runs store with execution_event before retiring it:
    row counts, job/stage distribution, newest time, and legacy rows missing
    from the current store (matched on agent_name + started_at)."""
    def side(conn: sqlite3.Connection, table: str, where: str = "") -> dict[str, Any]:
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        time_col = "started_at" if "started_at" in cols else "occurred_at"
        count, newest = conn.execute(f"SELECT COUNT(*), MAX({time_col}) FROM {table} {where}").fetchone()
        dist = {}
        if {"job", "stage"} <= cols:
            for job, stage, n in conn.execute(
                f"SELECT job, stage, COUNT(*) FROM {table} {where} {'AND' if where else 'WHERE'} "
                "job IS NOT NULL AND job != '' GROUP BY job, stage"
            ):
                dist[f"{job}/{_stage(stage)}"] = n
        return {"rows": count, "newest": newest, "job_stage": dist}

    legacy = sqlite3.connect(f"file:{legacy_db}?mode=ro", uri=True)
    current = _connect((db_dir or DB_DIR) / "rivendell.db")
    try:
        have = set(current.execute(
            "SELECT agent_name, occurred_at FROM execution_event WHERE source = 'agent_runs'"
        ).fetchall())
        missing = [list(r) for r in legacy.execute("SELECT agent_name, started_at FROM agent_runs")
                   if tuple(r) not in have]
        return {"legacy": side(legacy, "agent_runs"),
                "current": side(current, "execution_event", "WHERE source = 'agent_runs'"),
                "missing_from_current": missing}
    finally:
        legacy.close()
        current.close()


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "summary"
    if cmd == "sync":
        result: Any = sync()
    elif cmd == "summary":
        summary = job_summary()
        result = {k: summary[k] for k in ("status", "sources")} | {"jobs": len(summary["jobs"])}
    elif cmd == "reconcile" and len(argv) == 2:
        result = reconcile(Path(argv[1]))
    else:
        print("usage: execution_evidence.py sync | summary | reconcile <legacy.db>", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if isinstance(result, dict) and result.get("status") == "unavailable" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
