"""Official subscription quota vs token usage, per account and reset window.

The quota is the server's number and the one that actually runs out; token
counts are local and exact. This module lines them up:

  - accounts used, with first / last sighting, plan, latest reading, reset time
    and remaining quota
  - per reset window: quota % at the first and last reading, the tokens spent
    between them (four disjoint categories), and tokens per 1% of quota

Quota readings:
  - Codex: every rollout token_count event carries rate_limits.primary
    (used_percent, window_minutes, resets_at). The account is the login seen at
    that moment (tokens_accounts.codex_account_at), not the session's creator:
    after a login switch a running session is charged to the new account.
  - Claude: only the statusLine sees rate_limits; skills/platform/token-quota-log
    appends every change to CLAUDE_QUOTA_LOG. No history before it was installed.

Cost bounds. Codex rollouts are parsed whole once and cached by (mtime, size)
(~2s for the full history). Claude logs are far larger (GBs a week), so they are
read only from the start of the earliest still-open window, incrementally, in a
background thread; a window's result is stored in SQLite so a finished window is
never recomputed. Requests only read the cache and never parse.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from lib import tokens_accounts as accounts
from lib.tokens import PROJECTS_DIR, _history_db_path
from lib.tokens_codex import CODEX_SESSION_DIRS, _usage_delta
from lib.tokens_quota_advice import advise
from lib.tokens_timeline import _epoch, _seek_offset

CLAUDE_QUOTA_LOG = Path.home() / ".claude" / "usage-quota" / "claude-rate-limits.jsonl"
CLAUDE_WINDOWS = {"five_hour": 300, "seven_day": 10080}
WEEK_MIN = 10080
CLAUDE_LOOKBACK_S = 8 * 86400   # never parse Claude logs further back than this
REFRESH_S = 60
IDLE_HIDE_S = 30 * 86400   # an account unused this long is not listed
_FIELDS = ("input", "output", "cache_read", "cache_create")


@dataclass
class Reading:
    source: str
    account: str
    window_min: int
    resets_at: int     # rounded to the hour: the window key (server jitters it by seconds)
    at: float
    used: float
    plan: str = ""
    reset_exact: float = 0.0   # the server's own value, for display


@dataclass
class _ClaudeTail:
    inode: int = 0
    offset: int = 0
    covered_from: float = 0.0
    rows: dict[str, tuple] = field(default_factory=dict)   # key -> (at, in, out, cr, cc)


_codex_cache: dict[str, tuple[float, int, list, list]] = {}
_claude_tails: dict[str, _ClaudeTail] = {}
_state: dict[str, Any] = {"computed_at": None, "error": None}
_lock = threading.Lock()
_started = False


# ── storage ─────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    path = _history_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS token_quota_window (
            source TEXT NOT NULL,
            account_id TEXT NOT NULL,
            window_min INTEGER NOT NULL,
            resets_at INTEGER NOT NULL,
            plan TEXT NOT NULL DEFAULT '',
            first_at REAL NOT NULL,
            last_at REAL NOT NULL,
            used_from REAL NOT NULL,
            used_to REAL NOT NULL,
            readings INTEGER NOT NULL,
            input INTEGER NOT NULL,
            output INTEGER NOT NULL,
            cache_read INTEGER NOT NULL,
            cache_create INTEGER NOT NULL,
            reset_exact REAL,
            PRIMARY KEY (source, account_id, window_min, resets_at)
        )
    """)
    # Added after the table first shipped (2026-10-04); older DBs lack it.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(token_quota_window)")}
    if "reset_exact" not in columns:
        conn.execute("ALTER TABLE token_quota_window ADD COLUMN reset_exact REAL")
    return conn


# ── Codex ───────────────────────────────────────────────────────────────

def _parse_codex(path: Path) -> tuple[list[Reading], list[tuple]]:
    """Readings and per-event token deltas (at, account, in, out, cr, cc) of one rollout."""
    readings: list[Reading] = []
    usage: list[tuple] = []
    account, prev = "", {}
    with open(path, "rb") as f:
        for raw in f:
            if b'"session_meta"' in raw and not account:
                try:
                    account = (json.loads(raw).get("payload") or {}).get("creator_account_id") or ""
                except json.JSONDecodeError:
                    pass
                continue
            if b'"token_count"' not in raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            payload = entry.get("payload") or {}
            at = _epoch(entry.get("timestamp", ""))
            if payload.get("type") != "token_count" or at is None:
                continue
            total = (payload.get("info") or {}).get("total_token_usage")
            if total:
                d = _usage_delta(prev, total)
                prev = total
                cached, write = d["cached_input_tokens"], d["cache_write_input_tokens"]
                fresh = max(0, d["input_tokens"] - cached - write)
                if fresh or d["output_tokens"] or cached or write:
                    usage.append((at, account, fresh, d["output_tokens"], cached, write))
            limits = payload.get("rate_limits") or {}
            primary = limits.get("primary") or {}
            if primary.get("used_percent") is not None and primary.get("resets_at"):
                readings.append(Reading(
                    "codex", account, int(primary.get("window_minutes") or 0),
                    _hour(primary["resets_at"]), at, float(primary["used_percent"]),
                    limits.get("plan_type") or "", float(primary["resets_at"])))
    return readings, usage


def _codex_all() -> tuple[list[Reading], list[tuple]]:
    readings: list[Reading] = []
    usage: list[tuple] = []
    seen = set()
    for root in CODEX_SESSION_DIRS:
        if not root.is_dir():
            continue
        for path in root.rglob("*.jsonl"):
            key = str(path)
            try:
                st = path.stat()
            except OSError:
                continue
            seen.add(key)
            hit = _codex_cache.get(key)
            if not hit or hit[0] != st.st_mtime or hit[1] != st.st_size:
                try:
                    r, u = _parse_codex(path)
                except OSError:
                    continue
                hit = _codex_cache[key] = (st.st_mtime, st.st_size, r, u)
            readings += hit[2]
            usage += hit[3]
    for key in [k for k in _codex_cache if k not in seen]:
        del _codex_cache[key]
    # The cache keeps the creator id; attribution is applied per call so a new
    # login sighting re-labels old rows without reparsing.
    if not readings and not usage:
        return readings, usage
    since = min([r.at for r in readings] + [u[0] for u in usage])
    spans = accounts.intervals("codex", since)
    readings = [replace(r, account=accounts.codex_account_at(spans, r.at, r.account))
                for r in readings]
    usage = [(u[0], accounts.codex_account_at(spans, u[0], u[1]), *u[2:]) for u in usage]
    return readings, usage


# ── Claude ──────────────────────────────────────────────────────────────

def _claude_readings() -> list[Reading]:
    out: list[Reading] = []
    try:
        lines = CLAUDE_QUOTA_LOG.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        for name, window_min in CLAUDE_WINDOWS.items():
            limit = (row.get("limits") or {}).get(name) or {}
            if limit.get("used_percentage") is None or not limit.get("resets_at"):
                continue
            out.append(Reading("claude", row.get("account_id") or "", window_min,
                               _hour(limit["resets_at"]), float(row["ts"]),
                               float(limit["used_percentage"]), row.get("plan") or "",
                               reset_exact=float(limit["resets_at"])))
    return out


def _claude_usage(since: float) -> list[tuple]:
    """(at, account, in, out, cr, cc) for every Claude request since `since`."""
    rows: dict[str, tuple] = {}
    if PROJECTS_DIR.is_dir():
        for path in PROJECTS_DIR.rglob("*.jsonl"):
            try:
                st = path.stat()
            except OSError:
                continue
            if st.st_mtime < since:
                continue
            tail = _advance_claude(path, st, since)
            for key, rec in tail.rows.items():
                if rec[0] >= since:
                    rows.setdefault(key, rec)
    spans = accounts.intervals("claude", since)
    return [(r[0], accounts.account_at(spans, r[0]) or "", *r[1:]) for r in rows.values()]


def _advance_claude(path: Path, st, since: float) -> _ClaudeTail:
    key = str(path)
    tail = _claude_tails.get(key)
    if (tail is None or tail.inode != st.st_ino or st.st_size < tail.offset
            or since < tail.covered_from):
        tail = _claude_tails[key] = _ClaudeTail(inode=st.st_ino, covered_from=since)
        with open(path, "rb") as f:
            tail.offset = _seek_offset(f, st.st_size, since)
    with open(path, "rb") as f:
        f.seek(tail.offset)
        for raw in f:
            if not raw.endswith(b"\n"):
                break  # a row still being written; read it next time
            tail.offset += len(raw)
            if b'"usage"' not in raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            msg = entry.get("message") or {}
            usage = msg.get("usage") if isinstance(msg, dict) else None
            at = _epoch(entry.get("timestamp", ""))
            if not usage or at is None:
                continue
            # Same dedup rule as tokens_timeline: one request, last row wins.
            rid = entry.get("requestId") or msg.get("id") or f"{key}:{tail.offset}"
            tail.rows[rid] = (at, usage.get("input_tokens", 0) or 0,
                              usage.get("output_tokens", 0) or 0,
                              usage.get("cache_read_input_tokens", 0) or 0,
                              usage.get("cache_creation_input_tokens", 0) or 0)
    if tail.rows and min(r[0] for r in tail.rows.values()) < since:
        tail.rows = {k: r for k, r in tail.rows.items() if r[0] >= since}
    return tail


# ── windows ─────────────────────────────────────────────────────────────

def _hour(epoch: float) -> int:
    return int(round(float(epoch) / 3600) * 3600)


def _windows(readings: list[Reading], usage: list[tuple]) -> list[dict]:
    """One row per (source, account, window length, reset): quota moved vs tokens spent."""
    groups: dict[tuple, list[Reading]] = {}
    for r in readings:
        groups.setdefault((r.source, r.account, r.window_min, r.resets_at), []).append(r)
    by_account: dict[str, list[tuple]] = {}
    for u in usage:
        by_account.setdefault(u[1], []).append(u)
    out = []
    for (source, account, window_min, resets_at), rs in groups.items():
        rs.sort(key=lambda r: r.at)
        first, last = rs[0], rs[-1]
        sums = dict.fromkeys(_FIELDS, 0)
        for u in by_account.get(account, ()):
            if first.at < u[0] <= last.at:
                for name, value in zip(_FIELDS, u[2:6]):
                    sums[name] += value
        out.append({
            "source": source, "account_id": account, "window_min": window_min,
            "resets_at": resets_at, "reset_exact": last.reset_exact or resets_at,
            "plan": last.plan, "first_at": first.at,
            "last_at": last.at, "used_from": first.used, "used_to": last.used,
            "readings": len(rs), **sums,
        })
    return out


def _store(rows: list[dict], replace_source: str | None = None) -> None:
    """Upsert window rows. `replace_source` drops that source's rows first: Codex
    is recomputed from its full history each time, so a row whose attribution
    changed must not linger under the old account."""
    cols = ("source", "account_id", "window_min", "resets_at", "reset_exact", "plan",
            "first_at", "last_at",
            "used_from", "used_to", "readings", *_FIELDS)
    with _connect() as conn:
        if replace_source:
            conn.execute("DELETE FROM token_quota_window WHERE source = ?", (replace_source,))
        if not rows:
            return
        conn.executemany(
            f"INSERT OR REPLACE INTO token_quota_window({', '.join(cols)}) "
            f"VALUES ({', '.join('?' * len(cols))})",
            [tuple(r[c] for c in cols) for r in rows])


def refresh(now: float | None = None) -> None:
    """Recompute open windows from the logs and store them. Runs in the background."""
    now = time.time() if now is None else now
    codex_readings, codex_usage = _codex_all()
    # A closed Claude window keeps the result stored while it was open: its logs
    # are no longer read, so recomputing it now would store zero tokens.
    claude_readings = [r for r in _claude_readings() if r.resets_at > now]
    claude_usage = []
    if claude_readings:
        since = min(r.at for r in claude_readings)
        claude_usage = _claude_usage(max(since, now - CLAUDE_LOOKBACK_S))
    _store(_windows(codex_readings, codex_usage), replace_source="codex")
    _store(_windows(claude_readings, claude_usage))


# ── read side ───────────────────────────────────────────────────────────

def _stored_windows() -> list[dict]:
    try:
        with _connect() as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute(
                "SELECT * FROM token_quota_window ORDER BY resets_at DESC")]
    except sqlite3.Error:
        return []


def _sightings() -> dict[tuple[str, str], list[float]]:
    try:
        with accounts._connect() as conn:
            rows = conn.execute(
                "SELECT source, account_id, MIN(observed_from), MAX(observed_to) "
                "FROM token_account_log GROUP BY source, account_id").fetchall()
    except sqlite3.Error:
        return {}
    return {(s, a): [lo, hi] for s, a, lo, hi in rows}


def get_quota(now: float | None = None) -> dict[str, Any]:
    """Accounts with their latest quota reading, plus every reset window."""
    now = time.time() if now is None else now
    windows = _stored_windows()
    names = accounts.labels()
    seen = _sightings()
    acct: dict[tuple[str, str], dict] = {}
    for w in windows:
        key = (w["source"], w["account_id"])
        a = acct.setdefault(key, {"source": key[0], "account_id": key[1] or None,
                                  "label": names.get(key) if key[1] else None,
                                  "plan": "", "first_seen": w["first_at"],
                                  "last_seen": w["last_at"], "quota": {}})
        a["first_seen"] = min(a["first_seen"], w["first_at"])
        a["last_seen"] = max(a["last_seen"], w["last_at"])
        latest = a["quota"].get(str(w["window_min"]))
        if latest is None or w["last_at"] > latest["read_at"]:
            exact = w.get("reset_exact") or w["resets_at"]
            reset = exact <= now
            a["quota"][str(w["window_min"])] = {
                "used_percent": 0.0 if reset else w["used_to"],
                "remaining_percent": 100.0 if reset else max(0.0, 100 - w["used_to"]),
                "resets_at": exact, "read_at": w["last_at"],
                "reset_since_read": reset,
                # where this window's readings start, for the burn rate
                "window_first_at": w["first_at"], "window_used_from": w["used_from"],
            }
            if w["plan"]:
                a["plan"] = w["plan"]
    for key, (lo, hi) in seen.items():
        a = acct.setdefault(key, {"source": key[0], "account_id": key[1],
                                  "label": names.get(key), "plan": "",
                                  "first_seen": lo, "last_seen": hi, "quota": {}})
        a["first_seen"] = min(a["first_seen"], lo)
        a["last_seen"] = max(a["last_seen"], hi)
    for w in windows:
        tokens = sum(w[f] for f in _FIELDS)
        moved = w["used_to"] - w["used_from"]
        w["tokens"] = tokens
        w["label"] = names.get((w["source"], w["account_id"])) if w["account_id"] else None
        w["tokens_per_percent"] = round(tokens / moved) if moved > 0 else None
    # Accounts idle for over a month are left off the panel and the advice;
    # their data stays, so using one again brings it straight back.
    shown = [a for a in acct.values() if a["last_seen"] >= now - IDLE_HIDE_S]
    advise(shown, now)
    return {
        "generated_at": int(now),
        "computed_at": _state["computed_at"],
        "error": _state["error"],
        "claude_log_present": CLAUDE_QUOTA_LOG.exists(),
        "hidden_idle_accounts": len(acct) - len(shown),
        "accounts": sorted(shown, key=lambda a: -a["last_seen"]),
        "windows": windows,
    }


def start_refresher() -> None:
    """Recompute in a daemon thread every REFRESH_S for the life of the API."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    def loop() -> None:
        while True:
            try:
                refresh()
                _state["computed_at"], _state["error"] = int(time.time()), None
            except Exception as exc:  # a half-written log must not kill the thread
                _state["error"] = f"{type(exc).__name__}: {exc}"
            time.sleep(REFRESH_S)

    threading.Thread(target=loop, name="token-quota-refresher", daemon=True).start()
