"""Workflow map API backed by the platform workflow definition."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter()

# ── Workflow Map ──────────────────────────────────────────────────────────────

REPO_DIR = Path(__file__).resolve().parent.parent.parent.parent
_WORKFLOW_JSON = Path(os.environ.get("WORKFLOW_MAP_FILE", str(REPO_DIR / "platform" / "workflows" / "workflow-map.json")))


def _load_workflow() -> dict[str, Any]:
    """Load workflow-map.json; return empty shell if missing."""
    import json as _json

    if _WORKFLOW_JSON.exists():
        return _json.loads(_WORKFLOW_JSON.read_text(encoding="utf-8"))
    return {"skillMeta": {}, "tracks": [], "maintenance": [], "domainFlows": [], "situational": [], "orphaned": []}


def _save_workflow(data: dict[str, Any]) -> None:
    import json as _json

    _WORKFLOW_JSON.parent.mkdir(parents=True, exist_ok=True)
    _WORKFLOW_JSON.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/api/workflow", tags=["Workflow"])
def api_workflow() -> dict[str, Any]:
    """Return workflow config merged with live skill install status."""
    wf = _load_workflow()
    skills_dir = Path.home() / ".claude" / "skills"
    installed = {p.name for p in skills_dir.iterdir() if p.is_dir()} if skills_dir.exists() else set()

    # Annotate skillMeta with installed status
    for name, meta in wf.get("skillMeta", {}).items():
        meta["installed"] = name in installed

    # Find orphaned: installed but not referenced in any flow/trigger
    referenced: set[str] = set()
    for track in wf.get("tracks", []):
        for step in track.get("steps", []):
            referenced.update(step.get("mandatory", []))
            referenced.update(step.get("optional", []))
    for m in wf.get("maintenance", []):
        referenced.update(m.get("skills", []))
    for flow in wf.get("domainFlows", []):
        for step in flow.get("steps", []):
            referenced.update(step.get("skills", []))
    for sit in wf.get("situational", []):
        referenced.update(sit.get("skills", []))
    for orph in wf.get("orphaned", []):
        referenced.add(orph.get("skill", ""))

    auto_orphaned = sorted(installed - referenced - {"gstack"})
    wf["autoOrphaned"] = auto_orphaned
    wf["stats"] = {
        "totalSkills": len(installed),
        "mapped": len(referenced & installed),
        "unmapped": len(auto_orphaned),
        "domainFlows": len(wf.get("domainFlows", [])),
        "situational": len(wf.get("situational", [])),
    }
    return wf


@router.put("/api/workflow", tags=["Workflow"])
def api_workflow_update(body: dict[str, Any]) -> dict[str, str]:
    """Overwrite workflow-map.json with the provided data."""
    _save_workflow(body)
    return {"status": "ok"}
