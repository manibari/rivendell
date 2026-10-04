"""Which account to use next, from each account's latest quota reading.

Unused quota is lost at reset, so among accounts of one source (Claude Code or
Codex) the one that resets soonest goes first, ties broken by more remaining.
An account is skipped only while it is blocked: its weekly quota is used up, or
(Claude) its 5-hour session is.

Per account it also answers "how long will it last": the burn rate over the
current window's readings, the time it runs out at that rate (only when that is
before the reset), and the daily pace that would last exactly until the reset.
The readings are this machine's view; other machines' use shows up only at the
next reading, so the numbers move in steps.
"""

from __future__ import annotations

from typing import Any

WEEK, SESSION = "10080", "300"
WINDOW_S = {WEEK: 7 * 86400, SESSION: 5 * 3600}
MIN_SPAN_S = 3600   # a rate over less than an hour of readings is noise


def _blocking(q: dict | None) -> bool:
    return bool(q) and not q["reset_since_read"] and q["remaining_percent"] <= 0


def _rate_per_hour(q: dict) -> float | None:
    span = q["read_at"] - q["window_first_at"]
    moved = q["used_percent"] - q["window_used_from"]
    if q["reset_since_read"] or span < MIN_SPAN_S or moved <= 0:
        return None
    return moved / (span / 3600)


def account_advice(a: dict, now: float) -> dict[str, Any]:
    week, session = a["quota"].get(WEEK), a["quota"].get(SESSION)
    if not week or not a.get("account_id"):
        return {"status": "unknown", "rank": None}
    blocked_by = "week" if _blocking(week) else "session" if _blocking(session) else None
    blocked_until = None
    if blocked_by:
        blocked_until = (week if blocked_by == "week" else session)["resets_at"]
    # A window that already reset restarts on first use, so its next reset is a
    # full window away; it is the least urgent to spend.
    effective_reset = now + WINDOW_S[WEEK] if week["reset_since_read"] else week["resets_at"]
    left = week["remaining_percent"]
    rate = _rate_per_hour(week)
    exhaust_at = None
    if rate and left > 0:
        exhaust_at = week["read_at"] + left / rate * 3600
        if exhaust_at >= effective_reset:
            exhaust_at = None   # lasts until the reset at this pace
    days_left = max(0.0, effective_reset - now) / 86400
    return {
        "status": "blocked" if blocked_by else "usable",
        "blocked_by": blocked_by,
        "blocked_until": blocked_until,
        "effective_reset": effective_reset,
        "rate_per_hour": round(rate, 2) if rate else None,
        "exhaust_at": exhaust_at,
        "pace_per_day": round(left / days_left, 1) if days_left > 0 and left > 0 else None,
        "rank": None,
    }


def advise(accounts: list[dict], now: float) -> None:
    """Attach `advice` to each account and rank the usable ones per source."""
    for a in accounts:
        a["advice"] = account_advice(a, now)
    for source in {a["source"] for a in accounts}:
        usable = [a for a in accounts
                  if a["source"] == source and a["advice"]["status"] == "usable"]
        usable.sort(key=lambda a: (a["advice"]["effective_reset"],
                                   -a["quota"][WEEK]["remaining_percent"]))
        for rank, a in enumerate(usable, 1):
            a["advice"]["rank"] = rank
