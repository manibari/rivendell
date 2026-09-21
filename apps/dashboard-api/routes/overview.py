"""Dashboard overview read model."""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from lib.agents import list_agents
from lib.hooks import list_hooks
from lib.projects import load_projects, enrich_projects
from lib.skills import list_skills
from lib.tokens import get_total_stats
from routes.agents.presenter import _agent_to_dict

router = APIRouter()

# ── Overview ──────────────────────────────────────────────────────────

_OVERVIEW_CACHE: dict[str, Any] = {"t": 0.0, "data": None}


@router.get("/api/overview", tags=["Overview"])
def api_overview() -> dict[str, Any]:
    # 60s TTL cache: get_total_stats() re-parses every session JSONL (~3-4s) and
    # the overview aggregates five sources — the landing page sat on a bare
    # 載入中 for up to 8s (QA 2026-07-05 ISSUE-001). A minute of staleness is
    # invisible on a personal dashboard; a repeat visit now returns instantly.
    now = time.time()
    if _OVERVIEW_CACHE["data"] is not None and now - _OVERVIEW_CACHE["t"] < 60:
        return _OVERVIEW_CACHE["data"]

    agents = list_agents()
    hooks = list_hooks()
    skills = list_skills()
    totals = get_total_stats()
    projects = load_projects()
    enrich_projects(projects, agents)

    payload: dict[str, Any] = {
        "metrics": {
            "total_skills": len(skills),
            "running_agents": sum(1 for a in agents if a.loaded),
            "enabled_hooks": len(hooks),
            "total_cost_usd": totals["total_cost_usd"],
            "total_projects": len(projects),
        },
        "agents": [_agent_to_dict(a) for a in agents],
        "hooks": [
            {
                "event": h.event,
                "matcher": h.matcher or "",
                "command": h.command,
            }
            for h in hooks
        ],
        "projects_summary": [
            {
                "name": p.name,
                "description": p.description,
                "agent_count": len(p.agents),
                "agent_count_loaded": p.agent_count_loaded,
            }
            for p in projects.values()
        ],
    }
    _OVERVIEW_CACHE["data"] = payload
    _OVERVIEW_CACHE["t"] = now
    return payload
