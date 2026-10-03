"""Subscription quota vs token usage per account (/tokens 帳號與額度)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from lib.tokens_quota import get_quota

router = APIRouter()


@router.get("/api/tokens/quota", tags=["Tokens"])
def api_tokens_quota() -> dict[str, Any]:
    """Accounts used, their latest quota reading (used / remaining %, reset time),
    and per reset window the tokens spent against the quota it moved.

    Reads only the stored result; a background thread recomputes it every minute.
    """
    return get_quota()
