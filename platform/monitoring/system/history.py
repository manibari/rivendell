"""Persistent history for the system monitor (CPU / GPU / temperatures / power / battery).

Three tiers in one SQLite file, each row one timestamp with every metric as a
zlib-compressed JSON object {metric: value}:

    metrics_5s   raw samples from the collector      kept 7 days
    metrics_1m   per-minute avg / min / max          kept 90 days
    metrics_1h   per-hour avg / min / max            kept forever

Rollups are built from the tier below only for buckets that have fully ended,
so re-running `rollup` never double counts. Gaps (sleep, collector down) stay
gaps: `query` returns None for empty buckets instead of interpolating.

`flatten` is the single place that decides which live readings are stored and
under what key; the UI reads the same keys back.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import zlib
from pathlib import Path
from typing import Any, Iterable

REPO_DIR = Path(__file__).resolve().parents[3]
DB_DIR = Path(os.environ.get("RIVENDELL_DB_DIR", str(REPO_DIR / "apps" / "dashboard-legacy" / "data")))
DB_NAME = "system-metrics.db"

SAMPLE_SEC = 5
TIERS = {"5s": SAMPLE_SEC, "1m": 60, "1h": 3600}
RETENTION = {"5s": 7 * 86400, "1m": 90 * 86400, "1h": None}
# A query reads the finest tier that covers the window within this many rows.
MAX_ROWS = 12000
# The collector writes every SAMPLE_SEC; older than this means it is not running.
STALE_SEC = 60

SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics_5s (ts INTEGER PRIMARY KEY, data BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS metrics_1m (ts INTEGER PRIMARY KEY, n INTEGER NOT NULL,
    avg BLOB NOT NULL, min BLOB NOT NULL, max BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS metrics_1h (ts INTEGER PRIMARY KEY, n INTEGER NOT NULL,
    avg BLOB NOT NULL, min BLOB NOT NULL, max BLOB NOT NULL);
"""


def connect(db_dir: Path | None = None) -> sqlite3.Connection:
    path = (db_dir or DB_DIR) / DB_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def _pack(d: dict[str, float]) -> bytes:
    return zlib.compress(json.dumps(d, separators=(",", ":")).encode())


def _unpack(b: bytes) -> dict[str, float]:
    return json.loads(zlib.decompress(b))


def flatten(snap: dict[str, Any]) -> dict[str, float]:
    """Live snapshot -> {metric key: number}. Unreadable values are left out, never 0."""
    out: dict[str, float] = {}

    def put(key: str, v: Any) -> None:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out[key] = round(float(v), 3)

    cpu = snap.get("cpu") or {}
    put("cpu.total", cpu.get("total_active"))
    for c in cpu.get("clusters", []):
        put(f"cpu.{c['id']}", c.get("active"))
        put(f"cpu.{c['id']}.w", c.get("watts"))
        for core in c.get("cores", []):
            put(f"core.{core['id']}", core.get("active"))
            put(f"core.{core['id']}.mhz", core.get("freq_mhz"))
            put(f"core.{core['id']}.w", core.get("watts"))
    gpu = snap.get("gpu") or {}
    put("gpu.util", gpu.get("device_util"))
    put("gpu.active", gpu.get("active"))
    put("gpu.mhz", gpu.get("freq_mhz"))
    put("gpu.w", gpu.get("watts"))
    for g in (snap.get("temperatures") or {}).get("groups", []):
        put(f"temp.{g['id']}", g.get("avg"))
        put(f"temp.{g['id']}.max", g.get("max"))
    for f in snap.get("fans") or []:
        put(f"fan.{f['id']}", f.get("rpm"))
    power = snap.get("power") or {}
    for p in power.get("system", []) + power.get("components", []):
        put(f"power.{p['id']}", p.get("watts"))
    bat = snap.get("battery") or {}
    if bat.get("status") == "ok":
        put("bat.pct", bat.get("percent"))
        put("bat.ma", bat.get("amperage_ma"))
        put("bat.v", bat.get("voltage_v"))
        put("bat.w", bat.get("battery_watts"))
        put("bat.temp", bat.get("temperature_c"))
        put("bat.sys_w", bat.get("system_watts"))
        put("bat.in_w", bat.get("adapter_in_watts"))
        put("bat.ac", 1 if bat.get("external_connected") else 0)
        put("bat.health", bat.get("health_percent"))
        put("bat.cycles", bat.get("cycle_count"))
    return out


def write(conn: sqlite3.Connection, ts: int, metrics: dict[str, float]) -> None:
    conn.execute("INSERT OR REPLACE INTO metrics_5s (ts, data) VALUES (?, ?)", (ts, _pack(metrics)))
    conn.commit()


Row = tuple[int, dict[str, float], dict[str, float], dict[str, float]]


def _aggregate(rows: Iterable[Row]) -> Row:
    """rows of (n, avg, min, max) -> combined (n, avg, min, max), avg weighted by n."""
    n_total = 0
    sums: dict[str, float] = {}
    weights: dict[str, int] = {}
    lo: dict[str, float] = {}
    hi: dict[str, float] = {}
    for n, avg, mn, mx in rows:
        n_total += n
        for k, v in avg.items():
            sums[k] = sums.get(k, 0.0) + v * n
            weights[k] = weights.get(k, 0) + n
        for k, v in mn.items():
            lo[k] = min(lo.get(k, v), v)
        for k, v in mx.items():
            hi[k] = max(hi.get(k, v), v)
    avg_out = {k: round(sums[k] / weights[k], 3) for k in sums}
    return n_total, avg_out, lo, hi


def _rollup_tier(conn: sqlite3.Connection, src: str, dst: str, now: int) -> int:
    step = TIERS[dst]
    done = conn.execute(f"SELECT MAX(ts) FROM metrics_{dst}").fetchone()[0]
    first = conn.execute(f"SELECT MIN(ts) FROM metrics_{src}").fetchone()[0]
    if first is None:
        return 0
    start = done + step if done is not None else first // step * step
    end = now // step * step  # only buckets that have fully ended
    if start >= end:
        return 0
    if src == "5s":
        cur = conn.execute("SELECT ts, data FROM metrics_5s WHERE ts >= ? AND ts < ? ORDER BY ts", (start, end))
        rows = ((ts, 1, d, d, d) for ts, b in cur for d in [_unpack(b)])
    else:
        cur = conn.execute(f"SELECT ts, n, avg, min, max FROM metrics_{src} WHERE ts >= ? AND ts < ? ORDER BY ts",
                           (start, end))
        rows = ((ts, n, _unpack(a), _unpack(mn), _unpack(mx)) for ts, n, a, mn, mx in cur)
    buckets: dict[int, list[Row]] = {}
    for ts, n, avg, mn, mx in rows:
        buckets.setdefault(ts // step * step, []).append((n, avg, mn, mx))
    for bts, items in buckets.items():
        n, avg, mn, mx = _aggregate(items)
        conn.execute(f"INSERT OR REPLACE INTO metrics_{dst} (ts, n, avg, min, max) VALUES (?, ?, ?, ?, ?)",
                     (bts, n, _pack(avg), _pack(mn), _pack(mx)))
    conn.commit()
    return len(buckets)


def rollup(conn: sqlite3.Connection, now: int | None = None) -> dict[str, int]:
    now = int(now if now is not None else time.time())
    return {"1m": _rollup_tier(conn, "5s", "1m", now), "1h": _rollup_tier(conn, "1m", "1h", now)}


def prune(conn: sqlite3.Connection, now: int | None = None) -> dict[str, int]:
    now = int(now if now is not None else time.time())
    removed = {}
    for tier, keep in RETENTION.items():
        if keep is None:
            continue
        cur = conn.execute(f"DELETE FROM metrics_{tier} WHERE ts < ?", (now - keep,))
        removed[tier] = cur.rowcount
    conn.commit()
    return removed


def _pick_tier(conn: sqlite3.Connection, since: int, until: int) -> str:
    now = int(time.time())
    for tier, step in TIERS.items():
        keep = RETENTION[tier]
        if keep is not None and since < now - keep:
            continue
        if (until - since) / step <= MAX_ROWS:
            return tier
    return "1h"


def query(since: int, until: int, keys: list[str] | None = None, points: int = 600,
          db_dir: Path | None = None) -> dict[str, Any]:
    """Bucketed series for [since, until): {tier, step, ts, avg: {k: [...]}, max: {k: [...]}}.

    `status` is ok, empty (no rows in the window) or unavailable (no store).
    `collector` reports whether new samples are still arriving.
    """
    path = (db_dir or DB_DIR) / DB_NAME
    if not path.exists():
        return {"status": "unavailable", "error": f"尚未建立歷史資料庫（{DB_NAME}）：收集程式從未執行"}
    try:
        conn = connect(db_dir)
    except sqlite3.Error as exc:
        return {"status": "unavailable", "error": f"無法開啟歷史資料庫：{exc}"}
    try:
        tier = _pick_tier(conn, since, until)
        latest = conn.execute("SELECT MAX(ts) FROM metrics_5s").fetchone()[0]
        if tier == "5s":
            cur = conn.execute("SELECT ts, data, NULL FROM metrics_5s WHERE ts >= ? AND ts < ? ORDER BY ts",
                               (since, until))
        else:
            cur = conn.execute(f"SELECT ts, avg, max FROM metrics_{tier} WHERE ts >= ? AND ts < ? ORDER BY ts",
                               (since, until))
        rows = cur.fetchall()
    finally:
        conn.close()
    step = max(TIERS[tier], -(-(until - since) // max(points, 1)))
    step = -(-step // TIERS[tier]) * TIERS[tier]  # whole multiples of the tier step
    start = since // step * step
    n = (until - start + step - 1) // step
    ts_axis = [start + i * step for i in range(n)]
    sums: dict[str, list[float]] = {}
    counts: dict[str, list[int]] = {}
    peaks: dict[str, list[float | None]] = {}
    want = set(keys) if keys else None
    for ts, a, m in rows:
        i = (ts - start) // step
        avg = _unpack(a)
        mx = avg if m is None else _unpack(m)
        for k, v in avg.items():
            if want is not None and k not in want:
                continue
            if k not in sums:
                sums[k], counts[k], peaks[k] = [0.0] * n, [0] * n, [None] * n
            sums[k][i] += v
            counts[k][i] += 1
            pv = mx.get(k, v)
            peaks[k][i] = pv if peaks[k][i] is None else max(peaks[k][i], pv)
    avg_out = {k: [round(s / c, 3) if c else None for s, c in zip(sums[k], counts[k])] for k in sums}
    now = int(time.time())
    return {
        "status": "ok" if rows else "empty",
        "tier": tier,
        "step": step,
        "since": since,
        "until": until,
        "ts": ts_axis,
        "avg": avg_out,
        "max": peaks,
        "collector": {
            "last_sample": latest,
            "running": latest is not None and now - latest <= STALE_SEC,
        },
    }
