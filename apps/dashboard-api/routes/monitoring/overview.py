"""Aggregate platform health read model."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from lib.db import get_probes

router = APIRouter()

# ── Health ─────────────────────────────────────────────────────────────

@router.get("/api/health", tags=["Health"])
def api_health() -> dict[str, Any]:
    """System health metrics.

    Surfaces:
    - SSOT drift between the agent registry (`agents/registry/*.md`, the
      identity SoT since registry v2 — agents.conf is a generated cache) and
      `~/.claude/projects.json` (project metadata SSOT).
    - Disk capacity of the data volume backing `$HOME` (WARN ≥90%, CRIT ≥95%).
    """
    repo_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    sk_bin = repo_dir / "bin" / "sk"

    def _sk_check_json(check: str, empty_default: dict[str, Any]) -> dict[str, Any]:
        """Run `sk check <check> --json`; return parsed JSON or an error dict.

        exit 0 = ok, non-zero = problem detected; both emit valid JSON on stdout.
        """
        try:
            result = subprocess.run(
                [str(sk_bin), "check", check, "--json"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(repo_dir),
            )
            if result.stdout.strip():
                return json.loads(result.stdout)
            return {**empty_default, "error": result.stderr.strip() or "empty stdout"}
        except subprocess.TimeoutExpired:
            return {**empty_default, "error": f"sk check {check} timed out (>10s)"}
        except json.JSONDecodeError as e:
            return {**empty_default, "error": f"JSON decode failed: {e}"}
        except FileNotFoundError:
            return {**empty_default, "error": f"sk binary not found at {sk_bin}"}

    ssot_drift = _sk_check_json(
        "ssot",
        {"total_drift": -1, "agents_conf_only": [], "projects_json_only": []},
    )
    disk = _sk_check_json(
        "disk",
        {"percent": -1, "status": "error"},
    )
    agent_drift = _sk_check_json(
        "agents",
        {"total_drift": -1, "defined": 0, "loaded": 0, "not_loaded": [], "loaded_not_in_conf": []},
    )

    # Liveness is read from the store, not computed here: the probes are run by
    # `sk check liveness` (scheduled), so a probe that has never run is absent
    # from this list rather than silently reported as passing.
    try:
        liveness = get_probes()
    except Exception as exc:  # noqa: BLE001 - health must not 500 on a sub-check
        liveness = [{"probe": "_store", "ok": 0, "detail": str(exc), "checked_at": None}]

    return {
        "ssot_drift": ssot_drift,
        "disk": disk,
        "agent_drift": agent_drift,
        "liveness": liveness,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
