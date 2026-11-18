"""Gemini usage written locally by Codex CLI and the company gateway."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

GEMINI_HOME = Path.home() / ".codex-gemini"
GEMINI_SESSION_DIR = GEMINI_HOME / "sessions"


def is_gemini_model(model: str) -> bool:
    return "gemini" in (model or "").lower()


def iter_gemini_sessions() -> list[Path]:
    if not GEMINI_SESSION_DIR.is_dir():
        return []
    return list(GEMINI_SESSION_DIR.rglob("rollout-*.jsonl"))


def gateway_log_path() -> Path:
    return Path(os.environ.get("GEMINI_GATEWAY_LOG", str(GEMINI_HOME / "gateway-calls.jsonl")))


def parse_gateway_calls(path: Path, _fallback_project: str) -> dict:
    """Group gateway calls into one token-waste-watch session per UTC day."""
    agg: dict = {}
    try:
        with path.open(encoding="utf-8") as lines:
            for line_no, line in enumerate(lines):
                try:
                    call = json.loads(line)
                    ts = float(call["ts"])
                    model = call["model"]
                    input_tokens = int(call["input_tokens"])
                    output_tokens = int(call["output_tokens"])
                    if (not isinstance(model, str) or not is_gemini_model(model)
                            or input_tokens < 0 or output_tokens < 0):
                        continue
                    day = datetime.fromtimestamp(ts, timezone.utc).date().isoformat()
                except (ValueError, TypeError, KeyError, OverflowError):
                    continue
                session_id = f"gemini-gateway:{day}"
                project = agg.setdefault(day, {}).setdefault("token-waste-watch", {
                    "sessions": set(), "messages": 0, "tool_calls": 0,
                    "models": {}, "requests": [],
                })
                project["sessions"].add(session_id)
                project["messages"] += 1
                project["requests"].append({
                    "key": f"gemini:gateway:{line_no}", "session_id": session_id,
                    "model": model, "input": input_tokens, "output": output_tokens,
                    "cache_read": 0, "cache_create": 0,
                })
                totals = project["models"].setdefault(model, [0, 0, 0, 0])
                totals[0] += input_tokens
                totals[1] += output_tokens
    except OSError:
        return {}
    for day in agg.values():
        for project in day.values():
            project["sessions"] = sorted(project["sessions"])
    return agg
