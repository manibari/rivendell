"""Resident collector: one system snapshot every SAMPLE_SEC into history.

Runs under launchd (agents/registry/metrics-collector.md, keepalive), so the
history keeps growing whether or not the dashboard is open. Each minute it
rolls finished 5 s samples up to 1 m / 1 h; each hour it prunes by retention.

A failed reading is logged and skipped, never written as zeros. Log lines are
flushed per line so `tail -f` on the launchd log shows progress.
"""
from __future__ import annotations

import signal
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import history  # noqa: E402
import sensors  # noqa: E402

_stop = False


def _log(msg: str) -> None:
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)


def _on_signal(signum: int, _frame: object) -> None:
    global _stop
    _stop = True
    _log(f"signal {signum}, stopping")


def run_once(conn: sqlite3.Connection, ts: int) -> str | None:
    """Take and store one sample. Returns an error string instead of raising."""
    snap = sensors.snapshot()
    if snap.get("status") != "ok":
        return snap.get("error", "unavailable")
    metrics = history.flatten(snap)
    if not metrics:
        return "snapshot had no numeric readings"
    history.write(conn, ts, metrics)
    return None


def main() -> int:
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)
    conn = history.connect()
    _log(f"collector started, every {history.SAMPLE_SEC}s -> {history.DB_DIR / history.DB_NAME}")
    last_error: str | None = None
    last_rollup = last_prune = 0
    written = 0
    while not _stop:
        now = time.time()
        ts = int(now // history.SAMPLE_SEC * history.SAMPLE_SEC)
        try:
            err = run_once(conn, ts)
        except sqlite3.Error as exc:
            err = f"sqlite: {exc}"
        if err != last_error:
            _log(f"sample failed: {err}" if err else "sampling ok")
            last_error = err
        written += err is None
        try:
            if now - last_rollup >= 60:
                done = history.rollup(conn)
                last_rollup = now
                if any(done.values()):
                    _log(f"rollup {done}, {written} samples since last")
                    written = 0
            if now - last_prune >= 3600:
                _log(f"prune {history.prune(conn)}")
                last_prune = now
        except sqlite3.Error as exc:
            _log(f"rollup/prune failed: {exc}")
        # Sleep to the next sample boundary so timestamps stay aligned.
        time.sleep(max(0.5, ts + history.SAMPLE_SEC - time.time()))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
