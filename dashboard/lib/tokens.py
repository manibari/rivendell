"""Token usage data from Claude Code session JSONL files.

Previously also read ~/.claude/stats-cache.json, but Claude Code stopped
maintaining that cache in early 2026 (frozen at 2026-02-16 for this user),
so the dashboard relied on a half-dead source and showed gaps. JSONL is
now the sole source; an in-process TTL cache amortizes the full-tree
parse across requests.
"""

from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from functools import lru_cache
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

PROJECTS_DIR = Path.home() / ".claude" / "projects"
_CACHE_TTL = 60.0  # seconds; full JSONL parse takes ~1-2s for 500MB

# Pricing per million tokens
PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-7":              {"input": 15.0, "output": 75.0, "cache_read": 1.5, "cache_create": 18.75},
    "claude-opus-4-7[1m]":          {"input": 15.0, "output": 75.0, "cache_read": 1.5, "cache_create": 18.75},
    "claude-opus-4-6":              {"input": 15.0, "output": 75.0, "cache_read": 1.5, "cache_create": 18.75},
    "claude-opus-4-5-20251101":     {"input": 15.0, "output": 75.0, "cache_read": 1.5, "cache_create": 18.75},
    "claude-sonnet-4-5-20250929":   {"input": 3.0,  "output": 15.0, "cache_read": 0.3, "cache_create": 3.75},
    "claude-sonnet-4-6":            {"input": 3.0,  "output": 15.0, "cache_read": 0.3, "cache_create": 3.75},
    "claude-haiku-4-5-20251001":    {"input": 0.8,  "output": 4.0,  "cache_read": 0.08, "cache_create": 1.0},
}
DEFAULT_PRICING = {"input": 15.0, "output": 75.0, "cache_read": 1.5, "cache_create": 18.75}


@dataclass
class DailyUsage:
    date: str
    sessions: int
    messages: int
    tool_calls: int
    tokens_total: int
    cost_usd: float
    cache_tokens: int = 0  # cache_read + cache_create: context re-read, not new work
    models: dict[str, int] = field(default_factory=dict)


@dataclass
class ProjectUsage:
    project: str
    sessions: int
    messages: int
    tool_calls: int
    tokens_total: int
    cost_usd: float


@dataclass
class ModelSummary:
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_create_tokens: int
    cost_usd: float


def _estimate_cost(model: str, input_t: int, output_t: int,
                   cache_read: int, cache_create: int) -> float:
    p = PRICING.get(model, DEFAULT_PRICING)
    return (
        input_t * p["input"] / 1_000_000
        + output_t * p["output"] / 1_000_000
        + cache_read * p["cache_read"] / 1_000_000
        + cache_create * p["cache_create"] / 1_000_000
    )


_CACHE: dict[str, Any] = {"ts": 0.0, "result": None}


def _cached_full_usage() -> "FilteredUsage":
    """Cached all-time JSONL parse. Refreshes every _CACHE_TTL seconds."""
    now = time.time()
    if _CACHE["result"] is None or now - _CACHE["ts"] > _CACHE_TTL:
        _CACHE["result"] = get_filtered_usage()
        _CACHE["ts"] = now
    return _CACHE["result"]


def get_all_time_usage() -> "FilteredUsage":
    """Public alias for the cached all-time usage. Use for default
    (no-date-filter) dashboard queries — avoids re-parsing 500MB+ of JSONL
    on every request. For date-filtered queries, call `get_filtered_usage`
    directly (uncached)."""
    return _cached_full_usage()


def get_daily_usage(days: int | None = 30) -> list[DailyUsage]:
    """Daily usage merged from SQLite history (older dates) + JSONL (recent).

    JSONL is authoritative for dates it covers (Claude Code rotates older
    sessions out — typically ~5 weeks back). SQLite `token_usage` stores
    per-day snapshots written by `bin/sk-token-snapshot` so totals survive
    JSONL rotation. JSONL wins on overlap.
    """
    full = _cached_full_usage()
    by_date: dict[str, DailyUsage] = {d.date: d for d in full.daily}

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d") if days else ""
    history = read_daily_history(start_date=cutoff or None)
    for h in history:
        by_date.setdefault(h.date, h)  # JSONL wins on overlap

    results = sorted(by_date.values(), key=lambda x: x.date)
    if cutoff:
        results = [d for d in results if d.date >= cutoff]
    return results


def get_model_summary() -> list[ModelSummary]:
    """Per-model totals from JSONL session files."""
    return list(_cached_full_usage().models)


def get_total_stats() -> dict[str, Any]:
    """High-level totals merged from JSONL + SQLite history."""
    full = _cached_full_usage()
    history = read_daily_history()
    jsonl_dates = {d.date for d in full.daily}
    history_only = [h for h in history if h.date not in jsonl_dates]

    history_cost = sum(h.cost_usd for h in history_only)
    history_messages = sum(h.messages for h in history_only)
    history_sessions = sum(h.sessions for h in history_only)

    all_dates = sorted({d.date for d in full.daily} | {h.date for h in history})
    first_date = all_dates[0] if all_dates else ""
    last_date = all_dates[-1] if all_dates else ""

    return {
        "total_sessions": full.total_sessions + history_sessions,
        "total_messages": full.total_messages + history_messages,
        "first_session": first_date,
        "last_computed": last_date,
        "total_cost_usd": full.total_cost_usd + history_cost,
        "total_input": sum(m.input_tokens for m in full.models),
        "total_output": sum(m.output_tokens for m in full.models),
        "total_cache_read": sum(m.cache_read_tokens for m in full.models),
    }


# ─── Daily history persistence ──────────────────────────────────────────────
# JSONL files get rotated by Claude Code (~5 weeks back). These functions
# persist completed-day snapshots to SQLite so totals survive rotation.

def _history_db_path() -> Path:
    return Path(__file__).parent.parent / "data" / "rivendell.db"


def upsert_daily_usage(usage: DailyUsage) -> None:
    """Write/overwrite a single day's snapshot to the token_usage table.

    Idempotent: re-running for the same date overwrites. Caller decides
    which days to snapshot (typically: every completed day except today).
    """
    import sqlite3
    db_path = _history_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    details = json.dumps({
        "tool_calls": usage.tool_calls,
        "models": usage.models,
    })
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS token_usage (
                date TEXT PRIMARY KEY,
                sessions INTEGER,
                api_calls INTEGER,
                tokens_total INTEGER,
                cost_usd REAL,
                details_json TEXT
            )
        """)
        conn.execute("""
            INSERT INTO token_usage(date, sessions, api_calls, tokens_total, cost_usd, details_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                sessions=excluded.sessions,
                api_calls=excluded.api_calls,
                tokens_total=excluded.tokens_total,
                cost_usd=excluded.cost_usd,
                details_json=excluded.details_json
        """, (usage.date, usage.sessions, usage.messages,
              usage.tokens_total, usage.cost_usd, details))
        conn.commit()
    finally:
        conn.close()


def upsert_project_usage(day: str, rows: list[tuple[str, int, float]]) -> None:
    """Persist one day's per-project breakdown (project, tokens, cost_usd).

    Why (2026-07-05, Peter): the JSONL session files rotate away after ~5
    weeks, and they are the ONLY source of the per-project split — the daily
    token_usage table stores totals only. Without this table the answer to
    '這些 token 是做了什麼/花在哪個專案' silently disappears for older dates.
    Idempotent per (date, project); the day's rows are replaced wholesale.
    Queryable directly: sqlite3 data/rivendell.db
    'select * from token_project_usage where date=...'
    """
    import sqlite3
    db_path = _history_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS token_project_usage (
                date TEXT NOT NULL,
                project TEXT NOT NULL,
                tokens_total INTEGER,
                cost_usd REAL,
                PRIMARY KEY (date, project)
            )
        """)
        conn.execute("DELETE FROM token_project_usage WHERE date = ?", (day,))
        conn.executemany(
            "INSERT INTO token_project_usage(date, project, tokens_total, cost_usd) VALUES (?, ?, ?, ?)",
            [(day, p, tk, c) for p, tk, c in rows],
        )
        conn.commit()
    finally:
        conn.close()


def read_project_history(start_date: str | None = None,
                         end_date: str | None = None) -> list[dict[str, Any]]:
    """Read per-project daily rows from token_project_usage (oldest first)."""
    import sqlite3
    db_path = _history_db_path()
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        q = "SELECT date, project, tokens_total, cost_usd FROM token_project_usage"
        cond, args = [], []
        if start_date:
            cond.append("date >= ?"); args.append(start_date)
        if end_date:
            cond.append("date <= ?"); args.append(end_date)
        if cond:
            q += " WHERE " + " AND ".join(cond)
        q += " ORDER BY date, cost_usd DESC"
        try:
            rows = conn.execute(q, args).fetchall()
        except sqlite3.OperationalError:
            return []
        return [{"date": r[0], "project": r[1], "tokens_total": r[2], "cost_usd": r[3]} for r in rows]
    finally:
        conn.close()


def read_daily_history(start_date: str | None = None,
                       end_date: str | None = None) -> list[DailyUsage]:
    """Read per-day snapshots from token_usage. Empty list if table absent."""
    import sqlite3
    db_path = _history_db_path()
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        sql = "SELECT date, sessions, api_calls, tokens_total, cost_usd, details_json FROM token_usage"
        clauses, params = [], []
        if start_date:
            clauses.append("date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("date <= ?")
            params.append(end_date)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY date"
        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return []  # table doesn't exist yet
        results = []
        for date, sessions, api_calls, tokens, cost, details in rows:
            d = json.loads(details) if details else {}
            results.append(DailyUsage(
                date=date, sessions=sessions or 0,
                messages=api_calls or 0,
                tool_calls=d.get("tool_calls", 0),
                tokens_total=tokens or 0, cost_usd=cost or 0.0,
                models=d.get("models", {}),
            ))
        return results
    finally:
        conn.close()


# Keep in sync with SKIP_PARENT_DIRS in bin/sk (cmd_audit's token block) —
# the dashboard and the CLI audit must name projects identically.
_SKIP_PARENT_DIRS = {"Documents", "Projects", "Desktop", "repos", "src", "code", "dev",
                     "Company", "engineering"}


@lru_cache(maxsize=1)
def _known_repos() -> tuple[str, ...]:
    """Actual top-level repo dir names under ~/code, longest-encoded-first.

    Used to resolve the dash-encoded project dir names unambiguously:
    '-...-code-mops-dbs-apps-analytics' can't be split on dashes alone
    (both '/' and '_' encode to '-'), but prefix-matching against the real
    repo names ('mops_dbs') recovers the right top-level project.
    """
    code = Path.home() / "code"
    try:
        names = [d.name for d in code.iterdir() if d.is_dir()]
    except OSError:
        return ()
    return tuple(sorted(names, key=lambda n: len(re.sub(r"[/_]", "-", n)), reverse=True))


def _dir_to_project_name(dir_name: str) -> str:
    """Convert project dir name to the TOP-LEVEL project name.

    e.g. '-Users-manibari-code-tukey-or-apps-web' → 'tukey-or'
         '-Users-manibari-code-mops-dbs-apps-analytics' → 'mops_dbs'

    Attribution is deliberately rolled up to the top-level repo (2026-07-05,
    Peter): subfolder sessions (apps/web, apps/api, backend, …) fragmented the
    per-project view and made 'where does my money go' unanswerable. The dir
    name encodes the absolute path with '-' replacing both '/' AND '_', so we
    prefix-match against the real dir names under ~/code (longest first)
    instead of splitting on dashes.

    Used as a FALLBACK only — per-line cwd is preferred (_cwd_to_project_name).
    """
    home = str(Path.home())  # e.g. /Users/manibari
    home_prefix = home.replace("/", "-")  # → -Users-manibari
    name = dir_name
    if name.startswith(home_prefix):
        name = name[len(home_prefix):]
        name = name.lstrip("-")
        parts = name.split("-")
        # Drop generic parent dirs (code, Documents, …) before matching
        idx = 0
        while idx < len(parts) and parts[idx] in _SKIP_PARENT_DIRS:
            idx += 1
        remainder = "-".join(parts[idx:])
        if not remainder:
            return name if name else dir_name
        # Resolve against real ~/code repo names (handles '-' vs '_' ambiguity)
        for repo in _known_repos():
            enc = re.sub(r"[/_]", "-", repo)
            if remainder == enc or remainder.startswith(enc + "-"):
                return repo
        # Unknown root (Vault/…, deleted repo): first segment only — no subfolders
        name = parts[idx]
    return name if name else dir_name


def _cwd_to_project_name(cwd: str) -> str:
    """Convert a real cwd path to the TOP-LEVEL project name.

    e.g. '/Users/manibari/code/tukey-or/apps/web' → 'tukey-or'
         '/Users/manibari/code/IC-YMS/backend'   → 'IC-YMS'
         '/Users/manibari/Vault/Peter/Family'    → 'Vault'

    Rolled up to the first segment after the generic parent dirs (2026-07-05,
    Peter): sub-folder sessions (apps/web, backend, …) must attribute to the
    enclosing repo, never appear as their own 'project'. The earlier design
    kept the full sub-path on purpose (finer attribution); that fragmented the
    per-project cost view, so the roll-up now wins.
    """
    if not cwd:
        return ""
    home = str(Path.home())
    if cwd.startswith(home):
        rel = cwd[len(home):].lstrip("/")
        if not rel:
            return Path(cwd).name or ""
        parts = rel.split("/")
        idx = 0
        while idx < len(parts) and parts[idx] in _SKIP_PARENT_DIRS:
            idx += 1
        if idx < len(parts):
            return parts[idx]
        return parts[-1] if parts else ""
    # Path outside home — use last segment
    return Path(cwd).name or cwd


@dataclass
class FilteredUsage:
    """All usage data filtered by date range, parsed from JSONL in one pass."""
    models: list[ModelSummary]
    projects: list[ProjectUsage]
    daily: list[DailyUsage]
    total_sessions: int
    total_messages: int
    total_cost_usd: float
    total_tokens: int


def get_filtered_usage(date_start: str | None = None,
                       date_end: str | None = None) -> FilteredUsage:
    """Parse all JSONL sessions once, filtered by date range.

    date_start/date_end are ISO date strings (YYYY-MM-DD), inclusive.
    If both are None, returns all data.
    """
    # Per-project accumulators
    projects: dict[str, dict] = defaultdict(lambda: {
        "sessions": set(), "messages": 0, "tool_calls": 0,
        "by_model": defaultdict(lambda: {
            "input": 0, "output": 0, "cache_read": 0, "cache_create": 0,
        }),
    })
    # Per-model accumulators
    models_agg: dict[str, dict] = defaultdict(lambda: {
        "input": 0, "output": 0, "cache_read": 0, "cache_create": 0,
    })
    # Per-day accumulators
    daily_agg: dict[str, dict] = defaultdict(lambda: {
        "sessions": set(), "messages": 0, "tool_calls": 0,
        "by_model": defaultdict(lambda: {
            "input": 0, "output": 0, "cache_read": 0, "cache_create": 0,
        }),
    })
    all_sessions: set[str] = set()

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        project_name = _dir_to_project_name(project_dir.name)
        for jsonl_path in project_dir.glob("*.jsonl"):
            # Cached per-file aggregate (parse once per file version); the date
            # filter applies at merge time. See _file_agg_cached for why.
            file_agg = _file_agg_cached(jsonl_path, project_name)
            _merge_file_agg(
                file_agg, date_start, date_end,
                projects, models_agg, daily_agg, all_sessions,
            )

    # Build model summary
    model_results = []
    for model, m in models_agg.items():
        cost = _estimate_cost(model, m["input"], m["output"], m["cache_read"], m["cache_create"])
        model_results.append(ModelSummary(
            model=model, input_tokens=m["input"], output_tokens=m["output"],
            cache_read_tokens=m["cache_read"], cache_create_tokens=m["cache_create"],
            cost_usd=cost,
        ))
    model_results.sort(key=lambda x: x.cost_usd, reverse=True)

    # Build project usage
    proj_results = []
    for project, d in projects.items():
        tokens = sum(m["input"] + m["output"] for m in d["by_model"].values())
        cost = sum(
            _estimate_cost(mdl, m["input"], m["output"], m["cache_read"], m["cache_create"])
            for mdl, m in d["by_model"].items()
        )
        proj_results.append(ProjectUsage(
            project=project, sessions=len(d["sessions"]),
            messages=d["messages"], tool_calls=d["tool_calls"],
            tokens_total=tokens, cost_usd=cost,
        ))
    proj_results.sort(key=lambda x: x.cost_usd, reverse=True)

    # Build daily usage
    daily_results = []
    for date_str in sorted(daily_agg):
        d = daily_agg[date_str]
        tokens = sum(m["input"] + m["output"] for m in d["by_model"].values())
        cache = sum(m["cache_read"] + m["cache_create"] for m in d["by_model"].values())
        cost = sum(
            _estimate_cost(mdl, m["input"], m["output"], m["cache_read"], m["cache_create"])
            for mdl, m in d["by_model"].items()
        )
        daily_results.append(DailyUsage(
            date=date_str, sessions=len(d["sessions"]),
            messages=d["messages"], tool_calls=d["tool_calls"],
            tokens_total=tokens, cost_usd=cost, cache_tokens=cache,
            models={mdl: m["input"] + m["output"] for mdl, m in d["by_model"].items()},
        ))

    total_cost = sum(m.cost_usd for m in model_results)
    total_tokens = sum(m.input_tokens + m.output_tokens for m in model_results)
    total_messages = sum(d["messages"] for d in projects.values())

    return FilteredUsage(
        models=model_results, projects=proj_results, daily=daily_results,
        total_sessions=len(all_sessions), total_messages=total_messages,
        total_cost_usd=total_cost, total_tokens=total_tokens,
    )


def _parse_jsonl_granular(path: Path, fallback_project: str) -> dict:
    """Parse one JSONL file into a date→project granular aggregate.

    Shape: {date: {project: {"sessions": [ids], "messages": n, "tool_calls": n,
                             "models": {model: [input, output, cache_read, cache_create]}}}}

    Every aggregate the dashboard needs (per-project, per-model, per-day, any
    date filter) derives EXACTLY from this, which is what makes it cacheable:
    parse once per file version, merge many times. Project attribution is
    per-line (entry["cwd"]); fallback_project only when no cwd seen yet.
    """
    agg: dict = {}
    last_cwd: str | None = None
    try:
        with open(path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                cwd_now = entry.get("cwd")
                if cwd_now:
                    last_cwd = cwd_now

                ts = entry.get("timestamp", "")
                if not ts:
                    continue
                date_str = ts[:10]

                msg = entry.get("message", {})
                usage = msg.get("usage")
                if not usage:
                    continue

                model = msg.get("model", "unknown")
                session_id = entry.get("sessionId", str(path))

                input_t = usage.get("input_tokens", 0)
                output_t = usage.get("output_tokens", 0)
                cache_read = usage.get("cache_read_input_tokens", 0)
                cache_create = usage.get("cache_creation_input_tokens", 0)

                tool_calls = 0
                if msg.get("role") == "assistant":
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        tool_calls = sum(
                            1 for c in content
                            if isinstance(c, dict) and c.get("type") == "tool_use"
                        )

                project = _cwd_to_project_name(last_cwd) if last_cwd else ""
                if not project:
                    project = fallback_project

                day = agg.setdefault(date_str, {})
                p = day.setdefault(project, {
                    "sessions": set(), "messages": 0, "tool_calls": 0, "models": {},
                })
                p["sessions"].add(session_id)
                p["messages"] += 1
                p["tool_calls"] += tool_calls
                m = p["models"].setdefault(model, [0, 0, 0, 0])
                m[0] += input_t
                m[1] += output_t
                m[2] += cache_read
                m[3] += cache_create
    except Exception:
        pass
    # sets → lists for JSON serialization
    for day in agg.values():
        for p in day.values():
            p["sessions"] = sorted(p["sessions"])
    return agg


def _file_agg_cached(path: Path, fallback_project: str) -> dict:
    """Per-file aggregate with a SQLite cache keyed on (mtime, size).

    Why: the JSONL corpus reached ~1GB and the api re-parsed ALL of it on every
    cold start. That parse (GIL-bound) starved every other endpoint past the
    watchdog's 5s probe → kickstart -k → cache gone → re-parse → a permanent
    kill/restart spiral (22,474 restarts observed, 2026-07-18). With this cache
    an old 148MB session parses ONCE ever; a cold start re-parses only files
    that changed since last seen (normally just the active sessions).
    """
    import sqlite3

    try:
        st = path.stat()
    except OSError:
        return {}
    db_path = _history_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jsonl_file_cache (
                path TEXT PRIMARY KEY,
                mtime REAL NOT NULL,
                size INTEGER NOT NULL,
                agg TEXT NOT NULL
            )
        """)
        row = conn.execute(
            "SELECT mtime, size, agg FROM jsonl_file_cache WHERE path = ?",
            (str(path),),
        ).fetchone()
        if row and row[0] == st.st_mtime and row[1] == st.st_size:
            try:
                return json.loads(row[2])
            except json.JSONDecodeError:
                pass  # corrupt cache row → re-parse below
        agg = _parse_jsonl_granular(path, fallback_project)
        conn.execute(
            "INSERT INTO jsonl_file_cache(path, mtime, size, agg) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(path) DO UPDATE SET mtime=excluded.mtime, size=excluded.size, agg=excluded.agg",
            (str(path), st.st_mtime, st.st_size, json.dumps(agg)),
        )
        conn.commit()
        return agg
    finally:
        conn.close()


def _merge_file_agg(
    agg: dict,
    date_start: str | None, date_end: str | None,
    projects: dict, models_agg: dict, daily_agg: dict,
    all_sessions: set,
) -> None:
    """Merge one cached per-file aggregate into the query accumulators,
    applying the date filter at merge time (the cache itself is unfiltered)."""
    for date_str, day in agg.items():
        if date_start and date_str < date_start:
            continue
        if date_end and date_str > date_end:
            continue
        dd = daily_agg[date_str]
        for project, p in day.items():
            sessions = p.get("sessions", [])
            all_sessions.update(sessions)
            pd = projects[project]
            pd["sessions"].update(sessions)
            pd["messages"] += p.get("messages", 0)
            pd["tool_calls"] += p.get("tool_calls", 0)
            dd["sessions"].update(sessions)
            dd["messages"] += p.get("messages", 0)
            dd["tool_calls"] += p.get("tool_calls", 0)
            for model, m in p.get("models", {}).items():
                for agg_slot in (pd["by_model"][model], models_agg[model], dd["by_model"][model]):
                    agg_slot["input"] += m[0]
                    agg_slot["output"] += m[1]
                    agg_slot["cache_read"] += m[2]
                    agg_slot["cache_create"] += m[3]


def get_project_usage() -> list[ProjectUsage]:
    """Get token usage aggregated by project (cached, all-time JSONL)."""
    return list(_cached_full_usage().projects)
