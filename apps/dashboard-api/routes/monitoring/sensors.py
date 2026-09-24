"""System monitor: live sensors (exelban/stats parity) and persisted history."""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from lib.system_history import query as history_query
from lib.system_sensors import snapshot

router = APIRouter()

RANGES = {
    "15m": 900, "1h": 3600, "6h": 6 * 3600, "24h": 86400,
    "7d": 7 * 86400, "30d": 30 * 86400, "90d": 90 * 86400, "1y": 365 * 86400,
}


@router.get("/api/health/sensors", tags=["Health"])
def api_sensors(interval_ms: int = Query(250, ge=50, le=2000)) -> dict[str, Any]:
    """Live SMC temperatures and fans, IOReport power and per-core load, battery.

    `status: unavailable` carries `error` (not macOS, helper build failed,
    AppleSMC closed); the UI must show that instead of zero readings.
    """
    return snapshot(interval_ms)


@router.get("/api/health/metrics/history", tags=["Health"])
def api_metrics_history(
    range: str = Query("1h", description="15m / 1h / 6h / 24h / 7d / 30d / 90d / 1y"),
    until: int | None = Query(None, description="window end, epoch seconds (default now)"),
    keys: str | None = Query(None, description="comma-separated metric keys; omit for all"),
    points: int = Query(600, ge=10, le=5000),
) -> dict[str, Any]:
    """Bucketed history from the collector's store (system-metrics.db).

    `status` is ok / empty / unavailable; `collector.running` is false when no
    sample arrived in the last minute, so a flat or empty chart is explained.
    """
    if range not in RANGES:
        raise HTTPException(400, f"range must be one of {', '.join(RANGES)}")
    end = until or int(time.time())
    wanted = [k for k in (keys or "").split(",") if k] or None
    return history_query(end - RANGES[range], end, wanted, points)
