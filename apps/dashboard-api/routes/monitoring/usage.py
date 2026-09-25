"""Token usage API read model."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from lib.tokens import get_filtered_usage, get_all_time_usage, get_daily_usage

router = APIRouter()


def _models_payload(f) -> list[dict[str, Any]]:
    return [
        {
            "model": m.model,
            "source": m.source,          # "claude" | "codex"
            "billing": m.billing,        # "api" | "subscription"
            "input_tokens": m.input_tokens,
            "output_tokens": m.output_tokens,
            "cost_usd": m.cost_usd,
        }
        for m in f.models
    ]


# ── Tokens ────────────────────────────────────────────────────────────

@router.get("/api/tokens", tags=["Tokens"])
def api_tokens() -> dict[str, Any]:
    """All-time token usage (cached). For date-filtered queries use /api/tokens/filtered.

    Returns the same shape as /api/tokens/filtered (with no date), but hits the
    in-process TTL cache — avoids re-parsing ~500MB of JSONL on every request.
    """
    f = get_all_time_usage()
    return {
        "total_sessions": f.total_sessions,
        "total_messages": f.total_messages,
        "total_cost_usd": f.total_cost_usd,
        "total_tokens": f.total_tokens,
        "total_cache_tokens": sum(
            m.cache_read_tokens + m.cache_create_tokens for m in f.models
        ),
        # daily merges SQLite history (older than the ~30-day JSONL window) with
        # live JSONL so the chart shows full history, not just what Claude Code
        # hasn't rotated out yet. f.daily alone is JSONL-only (~30 days).
        "daily": [
            {
                "date": d.date,
                "sessions": d.sessions,
                "messages": d.messages,
                "tokens_total": d.tokens_total,
                "cache_tokens": d.cache_tokens,
                "cost_usd": d.cost_usd,
            }
            for d in get_daily_usage(days=None)
        ],
        "models": _models_payload(f),
        # Combined totals above; this is the Claude / Codex split of them.
        "sources": f.sources,
        "projects": [
            {
                "project": p.project,
                "sessions": p.sessions,
                "messages": p.messages,
                "tokens_total": p.tokens_total,
                "cost_usd": p.cost_usd,
            }
            for p in f.projects
        ],
    }


@router.get("/api/tokens/filtered", tags=["Tokens"])
def api_tokens_filtered(
    date_start: str | None = None,
    date_end: str | None = None,
) -> dict[str, Any]:
    f = get_filtered_usage(date_start, date_end)
    # Merge SQLite history into the daily series, then clip to the requested
    # range — so a historical date filter still shows data outside the ~30-day
    # JSONL window. (projects/models for pre-JSONL dates stay JSONL-limited; the
    # snapshot table only stores per-day totals, not per-project breakdown.)
    _daily = [
        d for d in get_daily_usage(days=None)
        if (not date_start or d.date >= date_start)
        and (not date_end or d.date <= date_end)
    ]
    return {
        "total_sessions": f.total_sessions,
        "total_messages": f.total_messages,
        "total_cost_usd": f.total_cost_usd,
        "total_tokens": f.total_tokens,
        "total_cache_tokens": sum(
            m.cache_read_tokens + m.cache_create_tokens for m in f.models
        ),
        "daily": [
            {
                "date": d.date,
                "sessions": d.sessions,
                "messages": d.messages,
                "tokens_total": d.tokens_total,
                "cache_tokens": d.cache_tokens,
                "cost_usd": d.cost_usd,
            }
            for d in _daily
        ],
        "models": _models_payload(f),
        # Combined totals above; this is the Claude / Codex split of them.
        "sources": f.sources,
        "projects": [
            {
                "project": p.project,
                "sessions": p.sessions,
                "messages": p.messages,
                "tokens_total": p.tokens_total,
                "cost_usd": p.cost_usd,
            }
            for p in f.projects
        ],
    }
