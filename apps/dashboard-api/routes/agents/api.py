"""Agent lifecycle, schedule, files, and run APIs."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from lib.agents import list_agents, load_agent, unload_agent, start_agent, install_agent, update_schedule
from lib.db import get_today_agent_cost, get_last_success_time, read_agent_runs, StoreUnreadable
from lib.projects import load_projects
from routes.agents.presenter import _agent_to_dict

router = APIRouter()

# ── Agents ────────────────────────────────────────────────────────────

@router.get("/api/agents", tags=["Agents"])
def api_agents() -> dict[str, Any]:
    agents = list_agents()
    last_success = get_last_success_time()
    today_cost = get_today_agent_cost()

    # Group agent names by project
    by_project: dict[str, list[str]] = {}
    for a in agents:
        by_project.setdefault(a.project, []).append(a.name)

    return {
        "metrics": {
            "total": len(agents),
            "running": sum(1 for a in agents if a.loaded),
            "last_success": last_success[:16] if last_success else None,
            "today_cost": today_cost,
        },
        "agents": [_agent_to_dict(a) for a in agents],
        "by_project": by_project,
    }


class AgentAction(BaseModel):
    label: str


@router.post("/api/agents/load", tags=["Agents"])
def api_agent_load(body: AgentAction) -> dict[str, Any]:
    ok = load_agent(body.label)
    if not ok:
        raise HTTPException(400, f"Failed to load {body.label}")
    return {"ok": True}


@router.post("/api/agents/unload", tags=["Agents"])
def api_agent_unload(body: AgentAction) -> dict[str, Any]:
    ok = unload_agent(body.label)
    if not ok:
        raise HTTPException(400, f"Failed to unload {body.label}")
    return {"ok": True}


@router.post("/api/agents/start", tags=["Agents"])
def api_agent_start(body: AgentAction) -> dict[str, Any]:
    ok = start_agent(body.label)
    if not ok:
        raise HTTPException(400, f"Failed to start {body.label}")
    return {"ok": True}


class InstallAction(BaseModel):
    plist_path: str


@router.post("/api/agents/install", tags=["Agents"])
def api_agent_install(body: InstallAction) -> dict[str, Any]:
    ok, logs = install_agent(Path(body.plist_path))
    if not ok:
        raise HTTPException(400, {"logs": logs})
    return {"ok": True, "logs": logs}


class ScheduleUpdate(BaseModel):
    label: str
    entries: list[dict[str, int]]


@router.post("/api/agents/schedule", tags=["Agents"])
def api_agent_schedule(body: ScheduleUpdate) -> dict[str, Any]:
    agents = list_agents()
    agent = next((a for a in agents if a.label == body.label), None)
    if not agent:
        raise HTTPException(404, "Agent not found")
    ok, msg = update_schedule(agent, body.entries)
    if not ok:
        raise HTTPException(400, msg)
    return {"ok": True, "message": msg}


@router.get("/api/agents/{agent_label}/live", tags=["Agents"])
def api_agent_live(agent_label: str, offset: int = 0) -> dict[str, Any]:
    """Live execution status: is agent running + tail of stdout log."""
    import re as _re
    import subprocess

    agents = list_agents()
    agent = next((a for a in agents if a.label == agent_label), None)
    if not agent:
        raise HTTPException(404, "Agent not found")

    # Check if running via launchctl
    running = False
    pid = None
    try:
        result = subprocess.run(
            ["launchctl", "list", agent_label],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            if '"PID"' in line:
                m = _re.search(r"(\d+)", line)
                if m:
                    pid = int(m.group(1))
                    running = True
    except Exception:
        pass

    # Find and tail stdout log
    wd = agent.working_directory
    if not wd and agent.project and agent.project != "unknown":
        projects = load_projects()
        p = projects.get(agent.project)
        if p:
            wd = p.repo

    log_lines: list[str] = []
    log_size = 0
    if wd:
        # Search multiple candidate log paths
        wd_path = Path(wd)
        candidates = [
            wd_path / "reports" / f"{agent.name}-stdout.log",
        ]
        # Also check plist StandardOutPath (handles agents with non-standard log dirs)
        if agent.plist_path:
            try:
                import plistlib
                with open(agent.plist_path, "rb") as pf:
                    pdata = plistlib.load(pf)
                sop = pdata.get("StandardOutPath")
                if sop:
                    candidates.insert(0, Path(sop))
            except Exception:
                pass

        stdout_log = None
        for c in candidates:
            if c.is_file():
                stdout_log = c
                break

        if stdout_log:
            content = stdout_log.read_text(errors="replace")
            # Strip ANSI
            content = _re.sub(r'\033\[[0-9;]*m', '', content)
            all_lines = content.splitlines()
            log_size = len(all_lines)
            # Return lines after offset
            if offset < log_size:
                log_lines = all_lines[offset:]

    return {
        "running": running,
        "pid": pid,
        "log_lines": log_lines,
        "log_size": log_size,
        "offset": offset,
    }


@router.get("/api/agents/{agent_label}/runs", tags=["Agents"])
def api_agent_runs(agent_label: str, limit: int = 10) -> list[dict[str, Any]]:
    parts = agent_label.split(".")
    agent_name = parts[-1] if len(parts) > 4 else parts[-1]

    # An unreadable store is a 503, never an empty list. Returning [] for both
    # is what let the agent_runs file split sit unnoticed for six weeks: the
    # page rendered "no runs" and nothing anywhere raised.
    try:
        rows = read_agent_runs(agent_name, limit)
    except StoreUnreadable as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "store_unreadable", "detail": str(exc)},
        ) from exc

    return [
        {
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "exit_code": row["exit_code"],
            "tokens_used": row["tokens_used"],
            "cost_usd": row["cost_usd"],
            "commit_sha": row["commit_sha"],
            "files_changed": row["files_changed"],
            "qa_passed": row["qa_passed"],
            "branch_name": row["branch_name"],
            "pr_url": row["pr_url"],
        }
        for row in rows
    ]


# ── Agent Files ──────────────────────────────────────────────────────

@router.get("/api/agents/{agent_label}/files", tags=["Agents"])
def api_agent_files(agent_label: str) -> list[dict[str, Any]]:
    """List log/report files for an agent."""
    agents = list_agents()
    agent = next((a for a in agents if a.label == agent_label), None)
    if not agent:
        return []

    wd = agent.working_directory
    if not wd and agent.project and agent.project != "unknown":
        projects = load_projects()
        p = projects.get(agent.project)
        if p:
            wd = p.repo
    if not wd:
        return []

    # Determine log directory: prefer plist StandardOutPath dir, fallback to reports/
    reports_dir = Path(wd) / "reports"
    log_dirs = [reports_dir]
    if agent.plist_path:
        try:
            import plistlib
            with open(agent.plist_path, "rb") as pf:
                pdata = plistlib.load(pf)
            sop = pdata.get("StandardOutPath")
            if sop:
                plist_log_dir = Path(sop).parent
                if plist_log_dir != reports_dir and plist_log_dir.is_dir():
                    log_dirs.insert(0, plist_log_dir)
        except Exception:
            pass

    # Match files by agent name prefix or known output patterns
    name = agent.name
    files = []
    seen_names: set[str] = set()
    for log_dir in log_dirs:
        if not log_dir.is_dir():
            continue
        for f in sorted(log_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not f.is_file():
                continue
            fname = f.name
            if fname in seen_names:
                continue
            # Match: agent-name*.log, agent-name*.md, agent-name*.jsonl,
            #        stdout/stderr logs, scraper-* logs, daily/weekly reports
            if (fname.startswith(name)
                or fname.startswith(f"{name}-stdout")
                or fname.startswith(f"{name}-stderr")
                or fname.startswith("scraper-")
                or (name.endswith("-daily") and fname.startswith("daily-"))
                or (name.endswith("-weekly") and fname.startswith("weekly-"))):
                seen_names.add(fname)
                stat = f.stat()
                files.append({
                    "name": fname,
                    "path": str(f),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "type": f.suffix.lstrip("."),
                })
    return files[:30]


def _plain_log_timeline(agent, wd: str, started_at: str | None) -> list[dict[str, Any]]:
    """Fallback: convert plain log files to timeline events for non-Claude agents."""
    import re as _re
    from datetime import datetime

    # Find the log file — check plist StandardOutPath dir for dated logs
    log_dir = Path(wd) / "reports"
    if agent.plist_path:
        try:
            import plistlib
            with open(agent.plist_path, "rb") as pf:
                pdata = plistlib.load(pf)
            sop = pdata.get("StandardOutPath")
            if sop:
                log_dir = Path(sop).parent
        except Exception:
            pass

    if not log_dir.is_dir():
        return []

    # Find dated log file matching started_at
    run_date = ""
    if started_at:
        try:
            run_date = datetime.fromisoformat(started_at).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Search for: scraper-YYYY-MM-DD.log, agent-name-YYYY-MM-DD.log, etc.
    log_file = None
    name = agent.name
    for pattern in [f"scraper-{run_date}.log", f"{name}-{run_date}.log", f"{name}.log"]:
        candidate = log_dir / pattern
        if candidate.is_file():
            log_file = candidate
            break

    if not log_file:
        # Try any log file modified around started_at
        if started_at:
            try:
                target_ts = datetime.fromisoformat(started_at).timestamp()
                logs = [f for f in log_dir.glob("*.log")
                        if f.is_file() and abs(f.stat().st_mtime - target_ts) < 300]
                if logs:
                    log_file = max(logs, key=lambda f: f.stat().st_mtime)
            except ValueError:
                pass

    if not log_file:
        return []

    # Parse log lines into events
    events = []
    content = log_file.read_text(errors="replace")
    for line in content.splitlines():
        line = _re.sub(r'\033\[[0-9;]*m', '', line).strip()
        if not line:
            continue

        # Extract timestamp from Python logging format: "2026-03-24 12:41:04,748 INFO ..."
        ts = ""
        text = line
        ts_match = _re.match(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}),?\d*\s+(\w+)\s+(.*)', line)
        if ts_match:
            ts = ts_match.group(1).replace(" ", "T")
            level = ts_match.group(2)
            text = ts_match.group(3)

            # Color-code by level
            if level == "ERROR":
                events.append({"ts": ts, "type": "log_error", "text": text})
            elif level == "WARNING":
                events.append({"ts": ts, "type": "log_warn", "text": text})
            else:
                events.append({"ts": ts, "type": "log", "text": text})
        elif line.startswith("==="):
            events.append({"ts": "", "type": "log_header", "text": line.strip("= ")})
        else:
            events.append({"ts": ts, "type": "log", "text": text})

    return events


@router.get("/api/agents/{agent_label}/timeline", tags=["Agents"])
def api_agent_timeline(
    agent_label: str,
    run_index: int = 0,
    started_at: str | None = None,
) -> list[dict[str, Any]]:
    """Parse structured JSONL into a timeline of events.

    If started_at is provided (e.g. '2026-03-15T12:54:12'), match the
    structured log file whose filename timestamp is closest to that time.
    Otherwise fall back to run_index (0 = most recent).
    """
    agents = list_agents()
    agent = next((a for a in agents if a.label == agent_label), None)
    if not agent:
        return []

    wd = agent.working_directory
    if not wd and agent.project and agent.project != "unknown":
        projects = load_projects()
        p = projects.get(agent.project)
        if p:
            wd = p.repo
    if not wd:
        return []

    reports_dir = Path(wd) / "reports"
    if not reports_dir.is_dir():
        return []

    # Find structured JSONL files, sorted newest first
    name = agent.name
    # Also match base name (research-agent for research-agent-weekly)
    base = name.replace("-weekly", "").replace("-daily", "")
    jsonl_files = sorted(
        [f for f in reports_dir.glob("*.structured.jsonl")
         if f.name.startswith(name) or f.name.startswith(base)],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not jsonl_files:
        # Fallback: convert plain log to timeline events for non-Claude agents
        return _plain_log_timeline(agent, wd, started_at)

    # Match by started_at timestamp if provided
    target = None
    if started_at:
        # Extract date+time from started_at: "2026-03-15T12:54:12" → "20260315-1254"
        import re
        clean = re.sub(r"[T:\-]", "", started_at)[:12]  # "20260315125412"
        match_prefix = clean[:8] + "-" + clean[8:]  # "20260315-125412"
        for f in jsonl_files:
            # Filename like: research-agent-20260315-125412.structured.jsonl
            if match_prefix[:13] in f.name:  # match "20260315-1254"
                target = f
                break
        # Fallback: closest by mtime
        if not target:
            from datetime import datetime
            try:
                target_ts = datetime.fromisoformat(started_at).timestamp()
                target = min(jsonl_files, key=lambda f: abs(f.stat().st_mtime - target_ts))
            except ValueError:
                pass

    if not target:
        if run_index >= len(jsonl_files):
            return []
        target = jsonl_files[run_index]
    events = []
    import json as _json
    for line in target.read_text(errors="replace").splitlines():
        try:
            obj = _json.loads(line)
        except (ValueError, _json.JSONDecodeError):
            continue
        etype = obj.get("type", "")
        ts_val = obj.get("ts", "")
        if etype == "tool":
            # Parse input JSON for display
            input_str = obj.get("input", "")
            try:
                input_parsed = _json.loads(input_str) if isinstance(input_str, str) else input_str
            except (ValueError, _json.JSONDecodeError):
                input_parsed = input_str
            events.append({
                "ts": ts_val,
                "type": "tool",
                "name": obj.get("name", ""),
                "input": input_parsed,
            })
        elif etype == "text":
            events.append({
                "ts": ts_val,
                "type": "text",
                "text": obj.get("text", "")[:500],
                "len": obj.get("len", 0),
            })
        elif etype == "thinking":
            events.append({
                "ts": ts_val,
                "type": "thinking",
                "preview": obj.get("preview", ""),
                "len": obj.get("len", 0),
            })
        elif etype == "result":
            events.append({
                "ts": ts_val,
                "type": "result",
                "model": obj.get("model", ""),
                "input_tokens": obj.get("input_tokens", 0),
                "output_tokens": obj.get("output_tokens", 0),
                "cost_usd": obj.get("cost_usd", 0),
            })
        elif etype in ("auto_commit", "auto_push", "qa_gate_failed", "path_filter_rejected"):
            events.append({
                "ts": ts_val,
                "type": etype,
                "detail": obj.get("detail", ""),
            })

    return events


@router.get("/api/agents/{agent_label}/artifacts", tags=["Agents"])
def api_agent_artifacts(agent_label: str, started_at: str = "") -> list[dict[str, Any]]:
    """Find report/output files associated with a specific run.

    Matches by:
    1. Filename containing the run date (e.g. daily-2026-03-15.md)
    2. File modification time within the run window (started_at → finished_at)
    """
    if not started_at:
        return []

    agents = list_agents()
    agent = next((a for a in agents if a.label == agent_label), None)
    if not agent:
        return []

    wd = agent.working_directory
    if not wd and agent.project and agent.project != "unknown":
        projects = load_projects()
        p = projects.get(agent.project)
        if p:
            wd = p.repo
    if not wd:
        return []

    reports_dir = Path(wd) / "reports"
    if not reports_dir.is_dir():
        return []

    from datetime import datetime

    try:
        run_dt = datetime.fromisoformat(started_at)
    except ValueError:
        return []

    run_date = run_dt.strftime("%Y-%m-%d")
    run_ts = run_dt.timestamp()
    # Search window: from run start to +2 hours (generous for long runs)
    window_end = run_ts + 7200

    results = []
    seen = set()
    for f in sorted(reports_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file():
            continue
        fname = f.name
        suffix = f.suffix.lower()
        # Only report files (.md, .html, .json) — skip logs/jsonl
        if suffix not in (".md", ".html", ".json"):
            continue
        # Skip structured log jsonl and stdout/stderr logs
        if "structured" in fname or "stdout" in fname or "stderr" in fname:
            continue

        mtime = f.stat().st_mtime
        # Match by date in filename or by modification time within window
        if run_date in fname or (run_ts - 60 <= mtime <= window_end):
            if fname not in seen:
                seen.add(fname)
                results.append({
                    "name": fname,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "modified": mtime,
                    "type": suffix.lstrip("."),
                })

    return results[:10]


@router.get("/api/agents/{agent_label}/file", tags=["Agents"])
def api_agent_file(agent_label: str, path: str = "") -> dict[str, Any]:
    """Read content of a specific agent file."""
    agents = list_agents()
    agent = next((a for a in agents if a.label == agent_label), None)
    if not agent:
        raise HTTPException(404, "Agent not found")

    wd = agent.working_directory
    if not wd and agent.project and agent.project != "unknown":
        projects = load_projects()
        p = projects.get(agent.project)
        if p:
            wd = p.repo
    if not wd:
        raise HTTPException(404, "Agent working directory unknown")

    file_path = Path(path)
    wd_path = Path(wd)

    # Security: allow reading from the agent's working directory tree
    try:
        file_path.resolve().relative_to(wd_path.resolve())
    except ValueError:
        raise HTTPException(403, "Access denied")

    if not file_path.is_file():
        raise HTTPException(404, "File not found")

    content = file_path.read_text(errors="replace")
    # Strip ANSI escape codes for display
    import re
    content = re.sub(r'\033\[[0-9;]*m', '', content)

    return {
        "name": file_path.name,
        "content": content,
        "size": len(content),
    }
