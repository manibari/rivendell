"""Disk snapshot API."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter()

@router.get("/api/health/disk-tree", tags=["Health"])
def api_disk_tree() -> dict[str, Any]:
    """Cached WizTree-style disk-usage snapshot.

    Generated daily by `bin/sk-disk-snapshot` (via sk-disk-monitor-cron) — this
    endpoint only reads the cached JSON, never scans on the request path
    (`du` over $HOME is far too slow for a request).
    """
    repo_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    snap = repo_dir / "dashboard" / "data" / "disk-tree.json"
    if not snap.exists():
        return {
            "available": False,
            "tree": None,
            "hint": "尚未產生快照 — 點「重新整理」或等每日 03:30 cron。",
        }
    try:
        data = json.loads(snap.read_text())
        data["available"] = True
        return data
    except (json.JSONDecodeError, OSError) as e:
        return {"available": False, "tree": None, "error": str(e)}


@router.post("/api/health/disk-tree/refresh", tags=["Health"])
def api_disk_tree_refresh() -> dict[str, str]:
    """Kick off a fresh snapshot in the background (du is slow — fire & forget).

    The client polls GET /api/health/disk-tree and watches `generated_at` to
    detect when the new snapshot lands.
    """
    repo_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    script = repo_dir / "bin" / "sk-disk-snapshot"
    try:
        subprocess.Popen(  # noqa: S603 — trusted local script
            [str(script)],
            cwd=str(repo_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"status": "refreshing"}
    except OSError as e:
        return {"status": "error", "error": str(e)}
