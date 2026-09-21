"""Manage project definitions from ~/.claude/projects.json."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECTS_JSON = Path.home() / ".claude" / "projects.json"


@dataclass
class MissionBrief:
    goal: str = ""
    commercial_value: str = ""
    potential_clients: list[str] = field(default_factory=list)
    expected_revenue: str = ""
    blockers: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    resources_needed: str = ""
    situation_analysis: str = ""
    deadline: str = ""


@dataclass
class GitStatus:
    branch: str = ""
    last_commit_msg: str = ""
    last_commit_ago: str = ""
    ahead: int = 0
    behind: int = 0
    recent_files: list[str] = field(default_factory=list)
    is_git: bool = False
    error: str = ""


@dataclass
class ProjectInfo:
    name: str
    repo: str
    description: str
    agents: list[str] = field(default_factory=list)
    mission: MissionBrief = field(default_factory=MissionBrief)
    # runtime computed
    agent_count_loaded: int = 0
    total_cost_usd: float = 0.0
    git: GitStatus = field(default_factory=GitStatus)


def _mission_from_dict(d: dict) -> MissionBrief:
    return MissionBrief(
        goal=d.get("goal", ""),
        commercial_value=d.get("commercial_value", ""),
        potential_clients=d.get("potential_clients", []),
        expected_revenue=d.get("expected_revenue", ""),
        blockers=d.get("blockers", []),
        next_steps=d.get("next_steps", []),
        resources_needed=d.get("resources_needed", ""),
        situation_analysis=d.get("situation_analysis", ""),
        deadline=d.get("deadline", ""),
    )


def _mission_to_dict(m: MissionBrief) -> dict:
    """Only serialize non-empty fields to keep JSON clean."""
    d: dict = {}
    if m.goal:
        d["goal"] = m.goal
    if m.commercial_value:
        d["commercial_value"] = m.commercial_value
    if m.potential_clients:
        d["potential_clients"] = m.potential_clients
    if m.expected_revenue:
        d["expected_revenue"] = m.expected_revenue
    if m.blockers:
        d["blockers"] = m.blockers
    if m.next_steps:
        d["next_steps"] = m.next_steps
    if m.resources_needed:
        d["resources_needed"] = m.resources_needed
    if m.situation_analysis:
        d["situation_analysis"] = m.situation_analysis
    if m.deadline:
        d["deadline"] = m.deadline
    return d


def load_projects() -> dict[str, ProjectInfo]:
    """Read ~/.claude/projects.json and return {name: ProjectInfo}.

    Returns empty dict if file doesn't exist or is invalid.
    """
    if not PROJECTS_JSON.exists():
        return {}

    try:
        data = json.loads(PROJECTS_JSON.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}

    projects: dict[str, ProjectInfo] = {}
    for name, entry in data.items():
        if not isinstance(entry, dict):
            continue
        mission_raw = entry.get("mission", {})
        projects[name] = ProjectInfo(
            name=name,
            repo=entry.get("repo", ""),
            description=entry.get("description", ""),
            agents=entry.get("agents", []),
            mission=_mission_from_dict(mission_raw if isinstance(mission_raw, dict) else {}),
        )
    return projects


def _serialize(projects: dict[str, ProjectInfo]) -> dict[str, Any]:
    """Convert ProjectInfo dict back to JSON-serializable form."""
    result: dict[str, Any] = {}
    for name, p in projects.items():
        entry: dict[str, Any] = {
            "repo": p.repo,
            "description": p.description,
            "agents": p.agents,
        }
        mission_dict = _mission_to_dict(p.mission)
        if mission_dict:
            entry["mission"] = mission_dict
        result[name] = entry
    return result


def save_projects(projects: dict[str, ProjectInfo]) -> None:
    """Atomic write projects to ~/.claude/projects.json."""
    PROJECTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(_serialize(projects), indent=2, ensure_ascii=False)

    fd, tmp_path = tempfile.mkstemp(
        dir=PROJECTS_JSON.parent,
        suffix=".tmp",
    )
    try:
        os.write(fd, data.encode())
        os.close(fd)
        fd = -1  # mark as closed
        os.replace(tmp_path, PROJECTS_JSON)
    except Exception:
        if fd >= 0:
            os.close(fd)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def get_project(name: str) -> ProjectInfo | None:
    """Get a single project by name."""
    return load_projects().get(name)


def create_project(
    name: str,
    repo: str,
    description: str = "",
    agents: list[str] | None = None,
) -> ProjectInfo:
    """Create a new project and persist it."""
    projects = load_projects()
    if name in projects:
        raise ValueError(f"Project '{name}' already exists")
    project = ProjectInfo(
        name=name,
        repo=repo,
        description=description,
        agents=agents or [],
    )
    projects[name] = project
    save_projects(projects)
    return project


def update_project(name: str, **kwargs: Any) -> ProjectInfo:
    """Update an existing project's fields and persist."""
    projects = load_projects()
    if name not in projects:
        raise KeyError(f"Project '{name}' not found")
    p = projects[name]
    readonly = {"name", "agent_count_loaded", "total_cost_usd", "git"}
    for key, val in kwargs.items():
        if key == "mission" and isinstance(val, dict):
            # Merge mission fields (don't replace the whole object)
            for mkey, mval in val.items():
                if hasattr(p.mission, mkey):
                    setattr(p.mission, mkey, mval)
        elif hasattr(p, key) and key not in readonly:
            setattr(p, key, val)
    save_projects(projects)
    return p


def delete_project(name: str) -> None:
    """Delete a project from projects.json (does not touch plist files)."""
    projects = load_projects()
    if name not in projects:
        raise KeyError(f"Project '{name}' not found")
    del projects[name]
    save_projects(projects)


def enrich_projects(
    projects: dict[str, ProjectInfo],
    agents_list: list[Any],
) -> dict[str, ProjectInfo]:
    """Cross-reference loaded agents to fill runtime fields."""
    for p in projects.values():
        p.agent_count_loaded = 0
        p.total_cost_usd = 0.0

    for agent in agents_list:
        for p in projects.values():
            if agent.name in p.agents:
                if agent.loaded:
                    p.agent_count_loaded += 1
                break

    return projects


def _run_git(repo: str, args: list[str], timeout: int = 3) -> str | None:
    """Run a git command in repo dir. Returns stdout stripped, or None on failure."""
    try:
        result = subprocess.run(
            ["git", "-C", repo] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def enrich_git(projects: dict[str, ProjectInfo]) -> None:
    """Read git status for each project with a valid repo path. Mutates in place."""
    for p in projects.values():
        if not p.repo or not Path(p.repo).is_dir():
            p.git = GitStatus(error="no-repo")
            continue

        # Check it's actually a git repo
        branch = _run_git(p.repo, ["branch", "--show-current"])
        if branch is None:
            p.git = GitStatus(error="no-git")
            continue

        git = GitStatus(is_git=True, branch=branch)

        # Last commit message + time ago
        log = _run_git(p.repo, ["log", "-1", "--format=%s|%ar"])
        if log and "|" in log:
            parts = log.split("|", 1)
            git.last_commit_msg = parts[0].strip()
            git.last_commit_ago = parts[1].strip()

        # Ahead / behind origin
        rev = _run_git(p.repo, ["rev-list", "--left-right", "--count", "origin/HEAD...HEAD"])
        if rev:
            parts = rev.split()
            if len(parts) == 2:
                try:
                    git.behind = int(parts[0])
                    git.ahead = int(parts[1])
                except ValueError:
                    pass

        # Recently changed files
        diff = _run_git(p.repo, ["diff", "--name-only", "HEAD~3", "HEAD"])
        if diff:
            git.recent_files = [f for f in diff.splitlines() if f][:5]

        p.git = git


def get_git_log(repo: str, n: int = 10) -> list[dict]:
    """Return last n commits for a repo as list of dicts."""
    if not repo or not Path(repo).is_dir():
        return []
    log = _run_git(repo, ["log", f"-{n}", "--format=%h|%s|%an|%ar"])
    if not log:
        return []
    commits = []
    for line in log.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "message": parts[1],
                "author": parts[2],
                "ago": parts[3],
            })
    return commits


def get_project_for_agent(agent_name: str) -> str | None:
    """Reverse lookup: return the project name an agent belongs to, or None."""
    projects = load_projects()
    for name, p in projects.items():
        if agent_name in p.agents:
            return name
    return None
