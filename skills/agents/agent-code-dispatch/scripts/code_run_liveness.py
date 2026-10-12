"""Is a codex run still moving? Three signals, sampled every few seconds.

A codex run is alive when at least one of these moved during the last window:
  events   codex wrote an event (an item started or finished)
  cpu      the run's process tree used CPU (a command runs, or codex parses a stream)
  network  the process tree received bytes (the model thinks or writes a reply)

A quiet events file alone is not a stall: one model call can take minutes with no
event. The signals are judged over a window (default one minute), not per sample,
because long thinking moves slowly. Measured 2026-10-12 on codex (reasoning high):
  thinking 75 s, no event:  codex CPU +0.26 s  (about 0.2 s per minute)
  idle process after a run: CPU +0.10 s in 8 min (about 0.012 s per minute)
nettop reported 0 bytes for that run, so network is a bonus signal, not the main one.
A hung model call waits on a socket and looks like the idle case on all three.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

CPU_PER_MIN_S = 0.05   # CPU seconds per minute that count as thinking (idle ~0.012, thinking ~0.2)


def tree_pids(root: int) -> list[int]:
    """`root` and every live descendant, found by parent pid.

    A command codex runs sits in its own process group (2026-10-12: a killed run left
    `sleep 300` behind with parent 1), so the process group is not enough.
    """
    out = subprocess.run(["ps", "-A", "-o", "pid=,ppid="], capture_output=True, text=True,
                         check=False).stdout
    children: dict[int, list[int]] = {}
    alive: set[int] = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            pid, ppid = int(parts[0]), int(parts[1])
            alive.add(pid)
            children.setdefault(ppid, []).append(pid)
    found, todo = [], [root]
    while todo:
        pid = todo.pop()
        if pid in alive and pid not in found:
            found.append(pid)
            todo.extend(children.get(pid, []))
    return found


def parse_cputime(text: str) -> float:
    """`ps -o time=` on macOS: `M:SS.ss`, `MM:SS.ss` or `H:MM:SS`. Unknown text is 0."""
    try:
        fields = [float(part) for part in text.strip().split(":")]
    except ValueError:
        return 0.0
    seconds = 0.0
    for value in fields:
        seconds = seconds * 60 + value
    return seconds


def cpu_seconds(pids: list[int]) -> float:
    if not pids:
        return 0.0
    out = subprocess.run(["ps", "-o", "time=", "-p", ",".join(map(str, pids))],
                         capture_output=True, text=True, check=False).stdout
    return sum(parse_cputime(line) for line in out.splitlines() if line.strip())


def parse_nettop(text: str, pids: list[int]) -> int:
    """Sum `bytes_in` of the rows `<name>.<pid>` that belong to `pids` (nettop -P -x CSV)."""
    wanted = {str(pid) for pid in pids}
    total = 0
    for line in text.splitlines():
        cols = line.split(",")
        if len(cols) < 6 or "." not in cols[1]:
            continue
        if cols[1].rsplit(".", 1)[1] in wanted and cols[4].isdigit():
            total += int(cols[4])
    return total


def bytes_in(pids: list[int]) -> int | None:
    """Bytes the processes received so far; None when nettop is not usable here."""
    if not pids:
        return 0
    try:
        out = subprocess.run(["nettop", "-P", "-L", "1", "-x"], capture_output=True,
                             text=True, check=False, timeout=8).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_nettop(out, pids)


@dataclass(frozen=True)
class Sample:
    events_mtime: float
    cpu: float
    received: int | None


def sample(root: int, events: Path) -> Sample:
    pids = tree_pids(root)
    try:
        mtime = events.stat().st_mtime
    except OSError:
        mtime = 0.0
    return Sample(mtime, cpu_seconds(pids), bytes_in(pids))


def moved(before: Sample, after: Sample, window_s: float) -> list[str]:
    """Which signals moved between two samples `window_s` apart; empty means a stall."""
    signals = []
    if after.events_mtime > before.events_mtime:
        signals.append("events")
    if after.cpu - before.cpu >= CPU_PER_MIN_S * window_s / 60:
        signals.append("cpu")
    if (before.received is not None and after.received is not None
            and after.received > before.received):
        signals.append("network")
    return signals
