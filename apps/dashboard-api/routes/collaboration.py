"""Learning and collaboration read model."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from lib.agents import list_agents

router = APIRouter()

# ── Collaboration (learnings) ────────────────────────────────────────

@router.get("/api/collaboration", tags=["Collaboration"])
def api_collaboration() -> dict[str, Any]:
    import re

    agents = list_agents()
    seen_dirs: set[str] = set()
    for agent in agents:
        if agent.working_directory:
            seen_dirs.add(agent.working_directory)

    total_pending = 0
    total_resolved = 0
    found = False

    for wd in seen_dirs:
        errors_md = Path(wd) / ".learnings" / "ERRORS.md"
        if not errors_md.exists():
            continue
        found = True
        content = errors_md.read_text()
        for line in content.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if re.match(r"^-\s*\[x\]", s, re.IGNORECASE):
                total_resolved += 1
            elif re.match(r"^-\s*\[\s\]", s):
                total_pending += 1
            elif "resolved" in s.lower() or "fixed" in s.lower():
                total_resolved += 1
            elif s.startswith("- ") or s.startswith("* "):
                total_pending += 1

    total = total_pending + total_resolved
    return {
        "found": found,
        "pending": total_pending,
        "resolved": total_resolved,
        "resolution_rate": round(total_resolved / total * 100) if total > 0 else 0,
    }
