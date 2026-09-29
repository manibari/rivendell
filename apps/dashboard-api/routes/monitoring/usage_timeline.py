"""Minute / hour token usage timeline (live chart on /tokens)."""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Query
from lib.tokens_timeline import BUCKETS, get_timeline

router = APIRouter()


@router.get("/api/tokens/timeline", tags=["Tokens"])
def api_tokens_timeline(
    bucket: Literal["minute", "hour"] = "minute",
    span: int | None = Query(None, ge=1, description="Number of buckets; capped per bucket size"),
    group: Literal["account", "model"] = "account",
) -> dict[str, Any]:
    """Recent token usage per minute or hour, one series per account or per model.

    Reads only the rows inside the window and continues from the last byte
    offset on the next call, so it is safe to poll every few seconds.
    """
    data = get_timeline(bucket, span, group)
    data["max_span"] = BUCKETS[bucket][2]
    return data
