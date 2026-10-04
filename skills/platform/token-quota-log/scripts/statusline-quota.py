#!/usr/bin/env python3
"""Claude Code statusLine: show the subscription quota and log it when it moves.

Claude Code hands the status line a JSON object on stdin; for subscription
users it carries `rate_limits.five_hour` / `rate_limits.seven_day`, each with
`used_percentage` and `resets_at` (epoch seconds). That is the only local place
the official quota appears, so this script appends a row to QUOTA_LOG whenever
the reading changes. The rivendell dashboard (token_quota.py) reads that log to
line quota up against token usage.

The account comes from ~/.claude.json (oauthAccount): identity fields only,
never a token. Stdlib only; any failure still prints a status line.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

QUOTA_DIR = Path.home() / ".claude" / "usage-quota"
QUOTA_LOG = QUOTA_DIR / "claude-rate-limits.jsonl"
LAST_FILE = QUOTA_DIR / ".last-claude.json"
CLAUDE_CONFIG = Path.home() / ".claude.json"
WINDOWS = ("five_hour", "seven_day")


def _account() -> tuple[str, str, str]:
    """(account id, email, plan). Plan is the rate-limit tier, e.g. claude_max_5x."""
    try:
        account = json.loads(CLAUDE_CONFIG.read_text()).get("oauthAccount") or {}
    except (OSError, json.JSONDecodeError):
        return "", "", ""
    account_id = account.get("accountUuid") or ""
    tier = account.get("organizationRateLimitTier") or account.get("organizationType") or ""
    plan = tier[len("default_"):] if tier.startswith("default_") else tier
    return account_id, account.get("emailAddress") or account_id[:8], plan


def _limits(data: dict) -> dict:
    rate = data.get("rate_limits") or {}
    out = {}
    for name in (*WINDOWS, "spend_limit"):
        row = rate.get(name)
        if isinstance(row, dict) and row.get("used_percentage") is not None:
            out[name] = {"used_percentage": row["used_percentage"],
                         "resets_at": row.get("resets_at")}
    return out


def _log(account_id: str, label: str, plan: str, limits: dict) -> None:
    """Append only when the reading differs from the last one for this account."""
    signature = {"account_id": account_id, "plan": plan, "limits": limits}
    try:
        last = json.loads(LAST_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        last = {}
    if last.get(account_id) == signature:
        return
    QUOTA_DIR.mkdir(parents=True, exist_ok=True)
    row = {"ts": round(time.time(), 3), "account_id": account_id, "label": label,
           "plan": plan, "limits": limits}
    with QUOTA_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    last[account_id] = signature
    LAST_FILE.write_text(json.dumps(last))


def _text(data: dict, limits: dict) -> str:
    model = (data.get("model") or {}).get("display_name") or ""
    parts = [model] if model else []
    names = {"five_hour": "5h", "seven_day": "週"}
    for name in WINDOWS:
        row = limits.get(name)
        if not row:
            continue
        piece = f"{names[name]} {row['used_percentage']:.0f}%"
        if name == "seven_day" and row.get("resets_at"):
            piece += f" (重置 {datetime.fromtimestamp(row['resets_at']):%m/%d %H:%M})"
        parts.append(piece)
    return " · ".join(parts)


def main() -> None:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        data = {}
    limits = _limits(data)
    if limits:
        account_id, label, plan = _account()
        try:
            _log(account_id, label, plan, limits)
        except OSError:
            pass  # a full disk must not blank the status line
    print(_text(data, limits))


if __name__ == "__main__":
    main()
