"""Minute / hour token usage timeline for the live chart on /tokens.

token_usage.py aggregates per DAY (it keeps only ts[:10]); this module keeps the
full timestamp and buckets the recent window by minute or hour, split by account.

Bounded on purpose. A full-tree parse once starved the API past the watchdog
probe (see token_usage._file_agg_cached), so this never parses a whole file:
  - only files modified inside the window are opened
  - the first read binary-searches to the window start by timestamp
  - later reads continue from the last byte offset (live polling reads only
    what was appended since the previous poll)

Account attribution:
  - Codex rollouts carry `creator_account_id` in session_meta -> exact, per session
  - Claude Code rows carry no account; they are matched by timestamp against the
    login intervals kept by token_accounts. A row outside every interval has
    account=None (shown as 未判讀) — never guessed from the current login.

`group` picks what a series is: one per account, or one per model.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from lib import tokens_accounts as accounts
from lib.tokens import PROJECTS_DIR
from lib.tokens_codex import (CODEX_SESSION_DIRS, UNKNOWN_CODEX_MODEL, _provenance_model,
                              _usage_delta)

# bucket -> (seconds per bucket, default span, max span)
BUCKETS: dict[str, tuple[int, int, int]] = {
    "minute": (60, 60, 360),
    "hour": (3600, 24, 48),
}
RATE_WINDOW_S = 300  # "current rate" = tokens per minute over the last 5 minutes
_SEEK_STOP = 1 << 16  # stop the binary search once the range is under 64KB
_KEEP_S = BUCKETS["hour"][0] * BUCKETS["hour"][2] + 3600

GROUPS = ("account", "model")
_FIELDS = ("input", "output", "cache_read", "cache_create")


@dataclass
class _Tail:
    """Incremental read state for one JSONL file."""
    kind: str                      # "claude" | "codex"
    inode: int = 0
    offset: int = 0
    covered_from: float = 0.0      # records are complete from this epoch onward
    account: str = ""              # codex only; claude is resolved by timestamp
    model: str = "unknown"         # codex only; claude rows name their own model
    session_id: str = ""
    prev_total: dict | None = None  # codex cumulative counter; None = need a baseline
    # key -> (epoch, in, out, cache_read, cache_create, model)
    records: dict[str, tuple] = field(default_factory=dict)


_TAILS: dict[str, _Tail] = {}
_LOCK = threading.Lock()


def _epoch(ts: str) -> float | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None


def _line_epoch(raw: bytes) -> float | None:
    try:
        return _epoch(json.loads(raw).get("timestamp", ""))
    except (json.JSONDecodeError, AttributeError):
        return None


def _seek_offset(f, size: int, since: float) -> int:
    """Byte offset of a line start at or before the first row with ts >= since.

    Rows are appended in time order, so a binary search on the byte offset finds
    the window start in ~log2(size/64KB) probes instead of scanning the file.
    """
    lo, hi = 0, size
    while hi - lo > _SEEK_STOP:
        mid = (lo + hi) // 2
        f.seek(mid)
        f.readline()  # discard the partial line
        found = None
        while f.tell() < size:
            found = _line_epoch(f.readline())
            if found is not None:
                break
        if found is None or found >= since:
            hi = mid
        else:
            lo = mid
    if lo == 0:
        return 0
    f.seek(lo)
    f.readline()
    return f.tell()


def _codex_head(f, tail: _Tail, fallback_id: str) -> None:
    """Read session_meta (first rows) for the session id, account and model."""
    f.seek(0)
    tail.model = UNKNOWN_CODEX_MODEL
    for _ in range(5):
        raw = f.readline()
        if not raw:
            break
        if b'"session_meta"' not in raw:
            continue
        try:
            payload = json.loads(raw).get("payload") or {}
        except json.JSONDecodeError:
            continue
        tail.session_id = payload.get("id") or payload.get("session_id") or fallback_id
        tail.account = payload.get("creator_account_id") or ""
        tail.model = payload.get("model") or _provenance_model(payload) or tail.model
        break
    tail.session_id = tail.session_id or fallback_id


def _read_claude(raw: bytes, tail: _Tail, line_key: str) -> None:
    if b'"usage"' not in raw:
        return
    try:
        entry = json.loads(raw)
    except json.JSONDecodeError:
        return
    msg = entry.get("message") or {}
    usage = msg.get("usage") if isinstance(msg, dict) else None
    at = _epoch(entry.get("timestamp", ""))
    if not usage or at is None:
        return
    # One row per displayed block repeats the same request usage; last row wins
    # (same rule as token_usage._parse_jsonl_granular).
    key = entry.get("requestId") or msg.get("id") or line_key
    tail.records[key] = (
        at,
        usage.get("input_tokens", 0) or 0,
        usage.get("output_tokens", 0) or 0,
        usage.get("cache_read_input_tokens", 0) or 0,
        usage.get("cache_creation_input_tokens", 0) or 0,
        msg.get("model") or "unknown",
    )


def _read_codex(raw: bytes, tail: _Tail, line_key: str) -> None:
    if b'"token_count"' not in raw and b'"turn_context"' not in raw:
        return
    try:
        entry = json.loads(raw)
    except json.JSONDecodeError:
        return
    payload = entry.get("payload") or {}
    if entry.get("type") == "turn_context":
        tail.model = payload.get("model") or tail.model
        return
    if entry.get("type") != "event_msg" or payload.get("type") != "token_count":
        return
    total = (payload.get("info") or {}).get("total_token_usage")
    at = _epoch(entry.get("timestamp", ""))
    if not total or at is None:
        return
    if tail.prev_total is None:
        # Started mid-file: the counter is cumulative, so the first event is only
        # a baseline. Counting it would book the whole session into one bucket.
        tail.prev_total = total
        return
    delta = _usage_delta(tail.prev_total, total)
    tail.prev_total = total
    cached = delta["cached_input_tokens"]
    fresh = max(0, delta["input_tokens"] - cached)
    output = delta["output_tokens"]
    if fresh == 0 and output == 0 and cached == 0:
        fresh = delta["total_tokens"]
    if fresh + output + cached + delta["cache_write_input_tokens"] == 0:
        return
    tail.records[f"codex:{tail.session_id}:{line_key}"] = (
        at, fresh, output, cached, delta["cache_write_input_tokens"], tail.model,
    )


def _advance(path: Path, kind: str, since: float) -> _Tail | None:
    """Bring one file's tail up to date and return it."""
    try:
        st = path.stat()
    except OSError:
        return None
    key = str(path)
    tail = _TAILS.get(key)
    stale = (tail is None or tail.inode != st.st_ino or st.st_size < tail.offset
             or since < tail.covered_from)
    try:
        with open(path, "rb") as f:
            if stale:
                tail = _Tail(kind=kind, inode=st.st_ino, covered_from=since)
                if kind == "codex":
                    _codex_head(f, tail, path.stem)
                tail.offset = _seek_offset(f, st.st_size, since)
                if kind == "codex" and tail.offset == 0:
                    tail.prev_total = {}  # whole file is in the window: count from zero
                _TAILS[key] = tail
            reader = _read_codex if kind == "codex" else _read_claude
            f.seek(tail.offset)
            for raw in f:
                if not raw.endswith(b"\n"):
                    break  # row still being written; pick it up on the next poll
                line_key = f"{key}:{tail.offset}"
                tail.offset += len(raw)
                reader(raw, tail, line_key)
    except OSError:
        return None
    return tail


def _recent_files(since: float) -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    roots = [(PROJECTS_DIR, "claude")] + [(d, "codex") for d in CODEX_SESSION_DIRS]
    for root, kind in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.jsonl"):
            try:
                if path.stat().st_mtime >= since:
                    found.append((path, kind))
            except OSError:
                continue
    return found


def _collect(since: float) -> dict[str, tuple[str, str, tuple]]:
    """request key -> (source, codex account id, record), deduplicated across files."""
    merged: dict[str, tuple[str, str, tuple]] = {}
    live = set()
    for path, kind in _recent_files(since):
        tail = _advance(path, kind, since)
        if tail is None:
            continue
        live.add(str(path))
        for key, rec in tail.records.items():
            if rec[0] >= since:
                merged.setdefault(key, (tail.kind, tail.account, rec))
    cutoff = time.time() - _KEEP_S
    for key in [k for k in _TAILS if k not in live]:
        del _TAILS[key]
    for tail in _TAILS.values():
        if tail.records and min(r[0] for r in tail.records.values()) < cutoff:
            tail.records = {k: r for k, r in tail.records.items() if r[0] >= cutoff}
    return merged


def _zero() -> dict[str, int]:
    return dict.fromkeys((*_FIELDS, "requests"), 0)


def get_timeline(bucket: str = "minute", span: int | None = None,
                 group: str = "account") -> dict[str, Any]:
    """Token usage for the last `span` buckets, zero-filled, one series per
    account or per model."""
    if bucket not in BUCKETS:
        raise ValueError(f"bucket must be one of {sorted(BUCKETS)}")
    if group not in GROUPS:
        raise ValueError(f"group must be one of {list(GROUPS)}")
    size, default, cap = BUCKETS[bucket]
    span = min(max(int(span or default), 1), cap)
    now = time.time()
    end = (int(now) // size + 1) * size
    start = end - span * size

    with _LOCK:
        merged = _collect(float(start))
    logins = accounts.intervals("claude", float(start))
    names = accounts.labels()

    points: dict[int, dict[str, dict[str, int]]] = {
        start + i * size: {} for i in range(span)
    }
    meta: dict[str, dict[str, Any]] = {}
    recent: dict[str, int] = {}
    for source, codex_account, rec in merged.values():
        at, model = rec[0], rec[5]
        if not any(rec[1:5]):
            continue  # "<synthetic>" rows (client-side errors) carry no usage
        slot = start + int((at - start) // size) * size
        if slot not in points:
            continue
        account = codex_account or None if source == "codex" else accounts.account_at(logins, at)
        account_name = names.get((source, account)) if account else None
        if group == "model":
            series_id, other = f"model:{model}", f"{source}:{account or ''}"
        else:
            series_id, other = f"{source}:{account or ''}", model
        entry = meta.setdefault(series_id, {
            "id": series_id, "source": source,
            "account": account if group == "account" else None,
            "label": account_name if group == "account" else None,
            "model": model if group == "model" else None,
            "totals": _zero(), "breakdown": {},
        })
        cell = points[slot].setdefault(series_id, _zero())
        for name, value in zip(_FIELDS, rec[1:5]):
            cell[name] += value
            entry["totals"][name] += value
        cell["requests"] += 1
        entry["totals"]["requests"] += 1
        part = entry["breakdown"].setdefault(other, {
            "source": source, "account": account, "label": account_name,
            "model": model, "tokens": 0, "cache_tokens": 0,
        })
        part["tokens"] += rec[1] + rec[2]
        part["cache_tokens"] += rec[3] + rec[4]
        if at >= now - RATE_WINDOW_S:
            recent[series_id] = recent.get(series_id, 0) + rec[1] + rec[2]

    series = sorted(meta.values(),
                    key=lambda m: -(m["totals"]["input"] + m["totals"]["output"]))
    for entry in series:
        entry["tokens_per_minute"] = round(recent.get(entry["id"], 0) / (RATE_WINDOW_S / 60))
        entry["breakdown"] = sorted(entry["breakdown"].values(), key=lambda p: -p["tokens"])

    return {
        "bucket": bucket,
        "bucket_seconds": size,
        "span": span,
        "group": group,
        "from": start,
        "to": end,
        "generated_at": int(now),
        "rate_window_seconds": RATE_WINDOW_S,
        "account_log_from": logins[0][0] if logins else None,
        "series": series,
        "points": [{"t": t, "series": cells} for t, cells in sorted(points.items())],
    }
