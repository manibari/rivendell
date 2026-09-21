"""Project catalog API."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from lib.agents import list_agents
from lib.projects import (
    load_projects, get_project, create_project, update_project,
    delete_project, enrich_projects, enrich_git, get_git_log,
)
from routes.agents.presenter import _agent_to_dict

router = APIRouter()

# ── Projects ──────────────────────────────────────────────────────────

def _project_to_dict(p, agents_list: list | None = None) -> dict[str, Any]:
    """Serialize ProjectInfo to JSON-safe dict."""
    d: dict[str, Any] = {
        "name": p.name,
        "repo": p.repo,
        "description": p.description,
        "agents": p.agents,
        "agent_count_loaded": p.agent_count_loaded,
        "total_cost_usd": p.total_cost_usd,
        "mission": {
            "goal": p.mission.goal,
            "commercial_value": p.mission.commercial_value,
            "potential_clients": p.mission.potential_clients,
            "expected_revenue": p.mission.expected_revenue,
            "blockers": p.mission.blockers,
            "next_steps": p.mission.next_steps,
            "resources_needed": p.mission.resources_needed,
            "situation_analysis": p.mission.situation_analysis,
            "deadline": p.mission.deadline,
        },
        "git": {
            "branch": p.git.branch,
            "last_commit_msg": p.git.last_commit_msg,
            "last_commit_ago": p.git.last_commit_ago,
            "ahead": p.git.ahead,
            "behind": p.git.behind,
            "recent_files": p.git.recent_files,
            "is_git": p.git.is_git,
            "error": p.git.error,
        },
    }
    if agents_list is not None:
        d["agent_details"] = [
            _agent_to_dict(a)
            for a in agents_list
            if a.name in p.agents
        ]
    return d


@router.get("/api/projects", tags=["Projects"])
def api_projects() -> dict[str, Any]:
    agents = list_agents()
    projects = load_projects()
    enrich_projects(projects, agents)
    enrich_git(projects)
    return {
        "projects": [_project_to_dict(p) for p in projects.values()],
    }


@router.get("/api/projects/{name}", tags=["Projects"])
def api_project_detail(name: str) -> dict[str, Any]:
    p = get_project(name)
    if not p:
        raise HTTPException(404, f"Project '{name}' not found")
    agents = list_agents()
    enrich_projects({name: p}, agents)
    enrich_git({name: p})
    return _project_to_dict(p, agents_list=agents)


@router.get("/api/projects/{name}/git-log", tags=["Projects"])
def api_project_git_log(name: str) -> dict[str, Any]:
    p = get_project(name)
    if not p:
        raise HTTPException(404, f"Project '{name}' not found")
    commits = get_git_log(p.repo, n=10)
    return {"commits": commits}


class ProjectCreate(BaseModel):
    name: str
    repo: str
    description: str = ""
    agents: list[str] = []


@router.post("/api/projects", tags=["Projects"])
def api_project_create(body: ProjectCreate) -> dict[str, Any]:
    try:
        p = create_project(body.name, body.repo, body.description, body.agents)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return {"ok": True, "project": _project_to_dict(p)}


class MissionBriefIn(BaseModel):
    goal: str | None = None
    commercial_value: str | None = None
    potential_clients: list[str] | None = None
    expected_revenue: str | None = None
    blockers: list[str] | None = None
    next_steps: list[str] | None = None
    resources_needed: str | None = None
    situation_analysis: str | None = None
    deadline: str | None = None


class ProjectUpdate(BaseModel):
    repo: str | None = None
    description: str | None = None
    agents: list[str] | None = None
    mission: MissionBriefIn | None = None


@router.put("/api/projects/{name}", tags=["Projects"])
def api_project_update(name: str, body: ProjectUpdate) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    for k, v in body.model_dump().items():
        if v is None:
            continue
        if k == "mission":
            # Pass only non-None mission fields
            kwargs["mission"] = {mk: mv for mk, mv in v.items() if mv is not None}
        else:
            kwargs[k] = v
    try:
        p = update_project(name, **kwargs)
    except KeyError as e:
        raise HTTPException(404, str(e))
    enrich_git({name: p})
    return {"ok": True, "project": _project_to_dict(p)}


@router.delete("/api/projects/{name}", tags=["Projects"])
def api_project_delete(name: str) -> dict[str, Any]:
    try:
        delete_project(name)
    except KeyError as e:
        raise HTTPException(404, str(e))
    return {"ok": True}
