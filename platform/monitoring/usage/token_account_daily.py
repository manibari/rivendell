"""Per-day token usage split by source, account and model, persisted to SQLite.

Why (2026-10-05, Peter): "how much did account X use this week" was answerable
only from the raw JSONL / rollout files, and Claude Code deletes those after its
cleanup period. token_usage keeps daily totals but no account, so once the
files rotate the per-account answer is gone. This table keeps it.

Attribution is the same as the /tokens timeline: Claude rows go to the login
sighted at their timestamp (token_account_log), Codex rows to the sighted login
or else the rollout's creator. A row nobody can attribute is stored with an
empty account (未判讀), never guessed.

A day is only rewritten when the new total is at least the stored one: a day
whose files have partly rotated away re-parses smaller, and that must not
overwrite the complete figure taken earlier.
"""

from __future__ import annotations

import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta

from lib import tokens_accounts as accounts
from lib import tokens_timeline as timeline
from lib.tokens import _estimate_cost, _history_db_path

_FIELDS = ("input", "output", "cache_read", "cache_create")


def _connect() -> sqlite3.Connection:
    path = _history_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS token_account_daily (
            date TEXT NOT NULL,
            source TEXT NOT NULL,
            account_id TEXT NOT NULL,
            label TEXT NOT NULL,
            model TEXT NOT NULL,
            input INTEGER NOT NULL,
            output INTEGER NOT NULL,
            cache_read INTEGER NOT NULL,
            cache_create INTEGER NOT NULL,
            requests INTEGER NOT NULL,
            cost_usd REAL NOT NULL,
            PRIMARY KEY (date, source, account_id, model)
        )
    """)
    return conn


def collect(since: float, until: float) -> dict[str, dict[tuple[str, str, str], dict]]:
    """date -> (source, account_id, model) -> totals, for records in [since, until)."""
    with timeline._LOCK:
        merged = timeline._collect(since)
    claude_spans = accounts.intervals("claude", since)
    codex_spans = accounts.intervals("codex", since)
    days: dict[str, dict] = defaultdict(lambda: defaultdict(
        lambda: dict.fromkeys((*_FIELDS, "requests"), 0)))
    for source, creator, rec in merged.values():
        at, model = rec[0], rec[5]
        if at < since or at >= until or not any(rec[1:5]):
            continue
        if source == "codex":
            account = accounts.codex_account_at(codex_spans, at, creator)
        else:
            account = accounts.account_at(claude_spans, at)
        day = datetime.fromtimestamp(at).strftime("%Y-%m-%d")
        cell = days[day][(source, account or "", model)]
        for name, value in zip(_FIELDS, rec[1:5]):
            cell[name] += value
        cell["requests"] += 1
    return days


def _day_total(rows) -> int:
    return sum(r["input"] + r["output"] + r["cache_read"] + r["cache_create"] for r in rows)


def store(days: dict[str, dict]) -> int:
    """Write each day unless the stored total for it is larger. Returns days written."""
    names = accounts.labels()
    written = 0
    with _connect() as conn:
        for day, cells in sorted(days.items()):
            stored = conn.execute(
                "SELECT COALESCE(SUM(input + output + cache_read + cache_create), 0) "
                "FROM token_account_daily WHERE date = ?", (day,)).fetchone()[0]
            if _day_total(cells.values()) < stored:
                continue
            conn.execute("DELETE FROM token_account_daily WHERE date = ?", (day,))
            conn.executemany(
                "INSERT INTO token_account_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(day, source, account, names.get((source, account), "") if account else "",
                  model, c["input"], c["output"], c["cache_read"], c["cache_create"],
                  c["requests"],
                  _estimate_cost(model, c["input"], c["output"], c["cache_read"], c["cache_create"]))
                 for (source, account, model), c in cells.items()])
            written += 1
    return written


def snapshot(days_back: int = 7, now: float | None = None) -> int:
    """Persist the last `days_back` finished days (today is skipped: incomplete)."""
    now = time.time() if now is None else now
    today = datetime.fromtimestamp(now).replace(hour=0, minute=0, second=0, microsecond=0)
    since = (today - timedelta(days=days_back)).timestamp()
    return store(collect(since, today.timestamp()))


def read(start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """Stored rows, oldest first."""
    q, cond, args = "SELECT * FROM token_account_daily", [], []
    if start_date:
        cond.append("date >= ?"); args.append(start_date)
    if end_date:
        cond.append("date <= ?"); args.append(end_date)
    if cond:
        q += " WHERE " + " AND ".join(cond)
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(q + " ORDER BY date, source, account_id, model", args)]
