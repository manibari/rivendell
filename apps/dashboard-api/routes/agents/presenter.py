"""Agent activity and presentation for API read models."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from lib.agents import get_recent_commit
from lib.projects import load_projects

# ── Helpers ───────────────────────────────────────────────────────────

_TOOL_LABELS: dict[str, str] = {
    "WebFetch": "抓取網頁",
    "WebSearch": "搜尋網路",
    "Read": "讀取檔案",
    "Write": "寫入檔案",
    "Edit": "編輯檔案",
    "Bash": "執行指令",
    "Glob": "搜尋檔案",
    "Grep": "搜尋內容",
    "Agent": "子任務",
}


def _get_agent_activity(agent) -> dict[str, Any] | None:
    """Read the tail of an agent's stream-json stdout to determine current activity.

    Returns {"tool": "WebFetch", "label": "抓取網頁", "detail": "..."} or None.
    """
    import json as _json

    if agent.pid is None:
        return None

    wd = agent.working_directory
    if not wd:
        return None

    # Try multiple log file patterns (agents log to different locations)
    candidates = []
    wd_path = Path(wd)
    from datetime import date as _date
    today = _date.today().isoformat()

    # Pattern 0: ~/Library/Logs/sk-agent/{label}-stdout.log (launchd logs, TCC-safe)
    launchd_log_dir = Path.home() / "Library" / "Logs" / "sk-agent"
    if hasattr(agent, "label") and agent.label:
        candidates.append(launchd_log_dir / f"{agent.label}-stdout.log")
    # Pattern 1: reports/{name}-stdout.log (legacy)
    candidates.append(wd_path / "reports" / f"{agent.name}-stdout.log")
    # Pattern 2: materials/*/scraper-stdout.log (for scraper agents)
    for sub in ("tenders", "subsidies"):
        candidates.append(wd_path / "materials" / sub / "scraper-stdout.log")
    # Pattern 3: materials/*/scraper-{DATE}.jsonl
    for sub in ("tenders", "subsidies"):
        candidates.append(wd_path / "materials" / sub / f"scraper-{today}.jsonl")
    # Pattern 4: reports/{name}-{DATE}.jsonl (general pattern)
    candidates.append(wd_path / "reports" / f"{agent.name}-{today}.jsonl")

    # Find the most recently modified candidate that exists
    log_path = None
    best_mtime = 0
    for c in candidates:
        if c.is_file():
            mt = c.stat().st_mtime
            if mt > best_mtime:
                best_mtime = mt
                log_path = c

    if not log_path:
        return None

    # Only consider logs modified in the last 10 minutes (agent is "active")
    import time
    if time.time() - best_mtime > 600:
        return None

    # Read tail of file (last 8KB to find recent events)
    try:
        size = log_path.stat().st_size
        with open(log_path, "r", errors="replace") as f:
            if size > 8192:
                f.seek(size - 8192)
                f.readline()  # skip partial line
            content = f.read()
    except Exception:
        return None

    # Parse stream-json lines in reverse to find the most recent tool_use or text
    lines = content.strip().splitlines()
    for line in reversed(lines):
        try:
            obj = _json.loads(line)
        except (ValueError, _json.JSONDecodeError):
            continue

        msg = obj.get("message", obj)
        content_blocks = None

        # Handle Claude CLI stream-json format
        if isinstance(msg, dict) and "content" in msg:
            content_blocks = msg["content"]
        elif isinstance(msg, dict) and "role" in msg:
            content_blocks = msg.get("content", [])

        if not isinstance(content_blocks, list):
            continue

        for block in reversed(content_blocks):
            if not isinstance(block, dict):
                continue

            if block.get("type") == "tool_use":
                tool_name = block.get("name", "")
                label = _TOOL_LABELS.get(tool_name, tool_name)
                # Extract a short detail from input
                inp = block.get("input", {})
                detail = ""
                if isinstance(inp, dict):
                    # Common patterns
                    if "command" in inp:
                        detail = str(inp["command"])[:60]
                    elif "file_path" in inp:
                        detail = Path(str(inp["file_path"])).name
                    elif "pattern" in inp:
                        detail = str(inp["pattern"])[:40]
                    elif "url" in inp or "prompt" in inp:
                        detail = str(inp.get("url") or inp.get("prompt", ""))[:60]
                return {"tool": tool_name, "label": label, "detail": detail}

            if block.get("type") == "text":
                text = block.get("text", "")
                if text.strip():
                    return {"tool": "text", "label": "回覆中", "detail": text[:60]}

            if block.get("type") == "thinking":
                return {"tool": "thinking", "label": "思考中", "detail": ""}

    return None


def _agent_to_dict(agent) -> dict[str, Any]:
    """Serialize AgentInfo to JSON-safe dict."""
    commit = None
    if agent.working_directory:
        commit = get_recent_commit(agent.working_directory, agent.name)

    cfg = agent.agents_json_config
    description = cfg.description if cfg else ""
    git_safety = None
    if cfg and (cfg.allowed_paths or cfg.forbidden_paths or cfg.max_files_changed):
        git_safety = {
            "allowed_paths": cfg.allowed_paths,
            "forbidden_paths": cfg.forbidden_paths,
            "max_files_changed": cfg.max_files_changed,
        }

    def _resolve_working_dir(a) -> str:
        """Fallback: resolve working dir from projects.json repo path."""
        if a.project and a.project != "unknown":
            projects = load_projects()
            p = projects.get(a.project)
            if p:
                return p.repo
        return ""

    # Only compute activity for running agents (has PID)
    activity = _get_agent_activity(agent) if agent.pid else None

    return {
        "label": agent.label,
        "name": agent.name,
        "description": description,
        "project": agent.project,
        "plist_path": str(agent.plist_path),
        "working_directory": agent.working_directory or _resolve_working_dir(agent),
        "schedule": agent.schedule,
        "schedule_display": agent.schedule_display,
        "schedule_list": agent.schedule_list,
        "loaded": agent.loaded,
        "installed": agent.installed,
        "pid": agent.pid,
        "exit_code": agent.exit_code,
        "role_badge": agent.role_badge,
        "merge_strategy_display": agent.merge_strategy_display,
        "qa_display": agent.qa_display,
        "recent_commit": {"sha": commit[0], "message": commit[1]} if commit else None,
        "git_safety": git_safety,
        "current_activity": activity,
    }
