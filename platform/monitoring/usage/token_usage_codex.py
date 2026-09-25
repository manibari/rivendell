"""Token usage from Codex CLI session rollouts.

Codex (ChatGPT subscription) writes one JSONL per session under
~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl. Unlike Claude Code it does not
log per-request usage; it emits `token_count` events carrying a CUMULATIVE
`total_token_usage`, so per-request usage is the delta between consecutive
events. The output shape is identical to tokens._parse_jsonl_granular so the
same cache, merge and date filter apply to both sources.

Added 2026-09-26 (Peter): the /tokens page counted Claude Code only, and the
ask was one combined total with Codex models listed alongside Claude models.
Codex is subscription-billed, so its cost is reported as 0 and flagged
`billing: subscription` rather than priced at an invented API rate.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Callable

CODEX_HOME = Path.home() / ".codex"
CODEX_SESSION_DIRS = (CODEX_HOME / "sessions", CODEX_HOME / "archived_sessions")

# Models that come through Codex. Anything matching is subscription-billed.
CODEX_MODEL_PREFIXES = ("gpt-", "o1", "o3", "o4", "codex")

# response_item payload types that are tool invocations
_TOOL_CALL_TYPES = {"function_call", "custom_tool_call", "local_shell_call", "web_search_call"}

_USAGE_KEYS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
               "output_tokens", "total_tokens")


UNKNOWN_CODEX_MODEL = "codex-unknown-model"


def _provenance_model(session_meta: dict) -> str:
    """Pre-0.150 rollouts (2026-08) name the model only under
    base_instructions.provenance, not on session_meta / turn_context."""
    base = session_meta.get("base_instructions")
    if isinstance(base, dict):
        prov = base.get("provenance")
        if isinstance(prov, dict):
            return prov.get("model") or ""
    return ""


def is_codex_model(model: str) -> bool:
    return model.startswith(CODEX_MODEL_PREFIXES)


def iter_codex_sessions() -> list[Path]:
    files: list[Path] = []
    for root in CODEX_SESSION_DIRS:
        if root.is_dir():
            files.extend(root.rglob("*.jsonl"))
    return files


def _usage_delta(prev: dict, cur: dict) -> dict:
    """Difference of two cumulative usage dicts, never negative (a counter
    reset after compaction would otherwise subtract)."""
    return {k: max(0, (cur.get(k) or 0) - (prev.get(k) or 0)) for k in _USAGE_KEYS}


def parse_codex_session(path: Path, fallback_project: str,
                        cwd_to_project: Callable[[str], str]) -> dict:
    """Parse one Codex rollout into the date→project granular aggregate.

    Shape: {date: {project: {"sessions": [ids], "messages": n, "tool_calls": n,
                             "models": {model: [input, output, cache_read, cache_create]},
                             "requests": [...]}}}
    Same as tokens._parse_jsonl_granular. Field mapping (OpenAI convention:
    cached tokens are a subset of input_tokens):
      input        = input_tokens - cached_input_tokens
      cache_read   = cached_input_tokens
      cache_create = cache_write_input_tokens
      output       = output_tokens (reasoning tokens are already inside it)
    """
    agg: dict = {}
    tool_counts: dict[tuple[str, str], int] = defaultdict(int)
    session_id = path.stem
    cwd = ""
    # Never plain "unknown": that would fall through to Claude API pricing.
    model = UNKNOWN_CODEX_MODEL
    prev_total: dict = {}
    requests: list[dict] = []
    try:
        with open(path) as f:
            for line_no, line in enumerate(f):
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = entry.get("type")
                payload = entry.get("payload") or {}
                ts = entry.get("timestamp", "")
                date_str = ts[:10]

                if kind == "session_meta":
                    session_id = payload.get("id") or payload.get("session_id") or session_id
                    cwd = payload.get("cwd") or cwd
                    model = payload.get("model") or _provenance_model(payload) or model
                    continue
                if kind == "turn_context":
                    cwd = payload.get("cwd") or cwd
                    model = payload.get("model") or model
                    continue
                if not date_str:
                    continue
                project = cwd_to_project(cwd) if cwd else ""
                if not project:
                    project = fallback_project

                if kind == "response_item":
                    if payload.get("type") in _TOOL_CALL_TYPES:
                        tool_counts[(date_str, project)] += 1
                    continue
                if kind != "event_msg" or payload.get("type") != "token_count":
                    continue

                info = payload.get("info") or {}
                total = info.get("total_token_usage")
                if not total:
                    continue
                delta = _usage_delta(prev_total, total)
                prev_total = total
                input_new = max(0, delta["input_tokens"] - delta["cached_input_tokens"])
                output = delta["output_tokens"]
                # Older Codex builds logged only total_tokens; keep that as input
                # so the session is not silently dropped.
                if input_new == 0 and output == 0 and delta["cached_input_tokens"] == 0:
                    input_new = delta["total_tokens"]
                if input_new + output + delta["cached_input_tokens"] + delta["cache_write_input_tokens"] == 0:
                    continue
                requests.append({
                    "key": f"codex:{session_id}:{entry.get('ordinal', line_no)}",
                    "date": date_str,
                    "project": project,
                    "session_id": session_id,
                    "model": model,
                    "input": input_new,
                    "output": output,
                    "cache_read": delta["cached_input_tokens"],
                    "cache_create": delta["cache_write_input_tokens"],
                })
    except Exception:
        pass

    def _slot(date_str: str, project: str) -> dict:
        return agg.setdefault(date_str, {}).setdefault(project, {
            "sessions": set(), "messages": 0, "tool_calls": 0,
            "models": {}, "requests": [],
        })

    for item in requests:
        p = _slot(item["date"], item["project"])
        p["sessions"].add(item["session_id"])
        p["messages"] += 1
        p["requests"].append({k: item[k] for k in
                              ("key", "session_id", "model", "input", "output",
                               "cache_read", "cache_create")})
        m = p["models"].setdefault(item["model"], [0, 0, 0, 0])
        m[0] += item["input"]
        m[1] += item["output"]
        m[2] += item["cache_read"]
        m[3] += item["cache_create"]
    for (date_str, project), n in tool_counts.items():
        _slot(date_str, project)["tool_calls"] += n
    for day in agg.values():
        for p in day.values():
            p["sessions"] = sorted(p["sessions"])
    return agg
