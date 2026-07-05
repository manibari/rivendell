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


_SKIP_PARENT_DIRS = {"Documents", "Projects", "Desktop", "repos", "src", "code", "dev"}


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
            _parse_jsonl_unified(
                jsonl_path, project_name, date_start, date_end,
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
        cost = sum(
            _estimate_cost(mdl, m["input"], m["output"], m["cache_read"], m["cache_create"])
            for mdl, m in d["by_model"].items()
        )
        daily_results.append(DailyUsage(
            date=date_str, sessions=len(d["sessions"]),
            messages=d["messages"], tool_calls=d["tool_calls"],
            tokens_total=tokens, cost_usd=cost,
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


def _parse_jsonl_unified(
    path: Path, fallback_project: str,
    date_start: str | None, date_end: str | None,
    projects: dict, models_agg: dict, daily_agg: dict,
    all_sessions: set,
) -> None:
    """Parse one JSONL file, accumulating into all three aggregation dicts.

    Project attribution is per-line (uses entry["cwd"]), not per-file.
    Sessions launched in a parent dir and `cd`-ed elsewhere get split
    across the actual sub-projects worked on. fallback_project is used
    only when a line has no cwd and we haven't seen one yet in this
    session.
    """
    last_cwd: str | None = None
    try:
        with open(path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Track cwd as it changes within the session (used for
                # current and subsequent lines until the next change)
                cwd_now = entry.get("cwd")
                if cwd_now:
                    last_cwd = cwd_now

                # Date filtering via entry timestamp
                ts = entry.get("timestamp", "")
                if not ts:
                    continue
                date_str = ts[:10]  # "2026-02-15T14:54:11.096Z" → "2026-02-15"
                if date_start and date_str < date_start:
                    continue
                if date_end and date_str > date_end:
                    continue

                msg = entry.get("message", {})
                usage = msg.get("usage")
                if not usage:
                    continue

                model = msg.get("model", "unknown")
                session_id = entry.get("sessionId", str(path))
                all_sessions.add(session_id)

                input_t = usage.get("input_tokens", 0)
                output_t = usage.get("output_tokens", 0)
                cache_read = usage.get("cache_read_input_tokens", 0)
                cache_create = usage.get("cache_creation_input_tokens", 0)

                # Count tool calls
                tool_calls = 0
                if msg.get("role") == "assistant":
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        tool_calls = sum(
                            1 for c in content
                            if isinstance(c, dict) and c.get("type") == "tool_use"
                        )

                # Per-line cwd → project; fall back to filename-derived
                # project when no cwd has appeared yet in this session.
                project = _cwd_to_project_name(last_cwd) if last_cwd else ""
                if not project:
                    project = fallback_project

                # Accumulate per-project
                pd = projects[project]
                pd["sessions"].add(session_id)
                pd["messages"] += 1
                pd["tool_calls"] += tool_calls
                pd["by_model"][model]["input"] += input_t
                pd["by_model"][model]["output"] += output_t
                pd["by_model"][model]["cache_read"] += cache_read
                pd["by_model"][model]["cache_create"] += cache_create

                # Accumulate per-model
                models_agg[model]["input"] += input_t
                models_agg[model]["output"] += output_t
                models_agg[model]["cache_read"] += cache_read
                models_agg[model]["cache_create"] += cache_create

                # Accumulate per-day
                dd = daily_agg[date_str]
                dd["sessions"].add(session_id)
                dd["messages"] += 1
                dd["tool_calls"] += tool_calls
                dd["by_model"][model]["input"] += input_t
                dd["by_model"][model]["output"] += output_t
                dd["by_model"][model]["cache_read"] += cache_read
                dd["by_model"][model]["cache_create"] += cache_create
    except Exception:
        pass


def get_project_usage() -> list[ProjectUsage]:
    """Get token usage aggregated by project (cached, all-time JSONL)."""
    return list(_cached_full_usage().projects)
