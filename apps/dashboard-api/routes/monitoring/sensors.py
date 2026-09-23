"""Temperature, fan and power readings (exelban/stats parity, phase 1)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from lib.system_sensors import snapshot

router = APIRouter()


@router.get("/api/health/sensors", tags=["Health"])
def api_sensors(interval_ms: int = Query(250, ge=50, le=2000)) -> dict[str, Any]:
    """Live SMC temperatures and fans plus IOReport power, read without root.

    `status: unavailable` carries `error` (not macOS, helper build failed,
    AppleSMC closed); the UI must show that instead of zero readings.
    """
    return snapshot(interval_ms)
