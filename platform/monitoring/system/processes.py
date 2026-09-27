"""Per-process CPU attribution for the system monitor history.

The metrics tiers answer "how busy was the machine"; this answers "who".
Each collector tick reads every process's cumulative CPU time from `ps` and
stores the top consumers by DELTA since the previous tick, so a value is the
real CPU used in that interval (100 = one full core), not ps's decaying
%CPU average.

Command lines are stored for the top rows only, truncated, with values after
secret-looking flags redacted: the store is a local SQLite file but it is
still never allowed to hold a token.

Added 2026-09-27 (Peter): a ~33-minute CPU spike could not be attributed
because history held machine totals only.
"""
from __future__ import annotations

import re
import subprocess
from typing import Any

TOP_N = 10
MIN_PCT = 2.0          # below this a process is noise, not a suspect
ARGS_MAX = 240

_SECRET = re.compile(
    r"((?:--?|\b)[\w.-]*(?:token|secret|password|passwd|apikey|api[_-]key|auth|key|credential)[\w.-]*[=\s:]+)"
    r"(\"[^\"]*\"|'[^']*'|\S+)",
    re.IGNORECASE,
)
_BEARER = re.compile(r"(bearer\s+)\S+", re.IGNORECASE)
_LONG_OPAQUE = re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")


def redact(args: str) -> str:
    s = _BEARER.sub(r"\1***", args)
    s = _SECRET.sub(lambda m: m.group(1) + "***", s)
    s = _LONG_OPAQUE.sub("***", s)
    return s[:ARGS_MAX]


def _cpu_seconds(t: str) -> float:
    """ps TIME: [[D-]H:]MM:SS.ss"""
    days = 0
    if "-" in t:
        d, t = t.split("-", 1)
        days = int(d)
    parts = [float(p) for p in t.split(":")]
    sec = 0.0
    for p in parts:
        sec = sec * 60 + p
    return days * 86400 + sec


def read_cpu_times() -> dict[int, tuple[float, str, int]]:
    """{pid: (cpu_seconds, short_name, ppid)} for every process."""
    out = subprocess.run(["ps", "-Aceo", "pid=,ppid=,time=,comm="],
                         capture_output=True, text=True, timeout=5).stdout
    procs: dict[int, tuple[float, str, int]] = {}
    for line in out.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        try:
            procs[int(parts[0])] = (_cpu_seconds(parts[2]), parts[3].strip(), int(parts[1]))
        except ValueError:
            continue
    return procs


def _args_for(pids: list[int]) -> dict[int, str]:
    if not pids:
        return {}
    out = subprocess.run(["ps", "-o", "pid=,args=", "-p", ",".join(map(str, pids))],
                         capture_output=True, text=True, timeout=5).stdout
    res: dict[int, str] = {}
    for line in out.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            res[int(parts[0])] = redact(parts[1])
    return res


class Sampler:
    """Holds the previous reading so each call returns per-interval usage."""

    def __init__(self) -> None:
        self._prev: dict[int, tuple[float, str, int]] | None = None
        self._prev_t = 0.0

    def sample(self, now: float) -> list[dict[str, Any]] | None:
        cur = read_cpu_times()
        prev, prev_t = self._prev, self._prev_t
        self._prev, self._prev_t = cur, now
        if prev is None or now - prev_t <= 0:
            return None  # first tick only primes the baseline
        dt = now - prev_t
        rows = []
        for pid, (sec, name, ppid) in cur.items():
            before = prev.get(pid)
            # A new pid (or a reused one with a different name) started inside
            # this interval: all of its CPU time belongs to the interval.
            base = before[0] if before and before[1] == name else 0.0
            pct = (sec - base) / dt * 100
            if pct >= MIN_PCT:
                rows.append({"pid": pid, "ppid": ppid, "name": name, "cpu": round(pct, 1)})
        rows.sort(key=lambda r: r["cpu"], reverse=True)
        rows = rows[:TOP_N]
        args = _args_for([r["pid"] for r in rows])
        parent_names = {r["ppid"]: cur.get(r["ppid"], (0, "", 0))[1] for r in rows}
        for r in rows:
            r["args"] = args.get(r["pid"], "")
            r["parent"] = parent_names.get(r["ppid"], "")
        return rows
