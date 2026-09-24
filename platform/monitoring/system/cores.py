"""Per-core CPU and whole-GPU load from IOReport DVFS residency.

sk-sensors reports, for one sampling window, how long every CPU core (and the
GPU as a whole) spent in each performance state. From that:

- active %  = time in a V*/P* state / time in all states (IDLE, DOWN, OFF
  count as not running);
- frequency = residency-weighted average of the state frequencies, taken from
  the pmgr `voltage-states*` tables in the IORegistry. A table is only used
  when exactly one distinct table has as many states as the channel; anything
  else reports frequency as None rather than a guess.

Per-GPU-core load is not exposed by macOS (IOReport and the AGX driver only
report the GPU as one unit), so `gpu.per_core` is always None with a reason.
"""
from __future__ import annotations

import plistlib
import re
import struct
import subprocess
from typing import Any

IDLE_STATES = {"IDLE", "DOWN", "OFF"}
CORE_NAME = re.compile(r"^([A-Z]CPU)(\d)(\d)?$")
# Frequencies outside this band are voltage or placeholder tables, not clocks.
MHZ_RANGE = (200, 6000)
GPU_MHZ_MAX = 2500
# Absolute paths: launchd services (the dashboard API) run without /usr/sbin on PATH.
IOREG = "/usr/sbin/ioreg"
SYSCTL = "/usr/sbin/sysctl"
GPU_PER_CORE_REASON = "macOS 未提供每個 GPU 核心的使用率（IOReport 與 AGX 驅動只回報整顆 GPU）"


def _ioreg(args: list[str]) -> list[dict[str, Any]]:
    try:
        res = subprocess.run([IOREG, *args, "-a"], capture_output=True, timeout=5)
        return plistlib.loads(res.stdout) if res.stdout else []
    except (OSError, subprocess.TimeoutExpired, plistlib.InvalidFileException):
        return []


def _to_mhz(raw: int) -> float:
    return raw / 1e6 if raw > 1e8 else raw / 1e3


_cache: dict[str, Any] = {}


def freq_tables() -> tuple[tuple[float, ...], ...]:
    """Distinct plausible clock tables (MHz, ascending state order) from pmgr.

    Cached once non-empty; a failed read is retried on the next call instead
    of pinning "no frequency" for the life of the process.
    """
    if _cache.get("freq"):
        return _cache["freq"]
    nodes = _ioreg(["-rn", "pmgr"])
    tables: set[tuple[float, ...]] = set()
    for key, val in (nodes[0] if nodes else {}).items():
        if not key.startswith("voltage-states") or not isinstance(val, bytes):
            continue
        freqs = [struct.unpack_from("<I", val, i)[0] for i in range(0, len(val) - 7, 8)]
        mhz = tuple(round(_to_mhz(f)) for f in freqs if f)
        if mhz and all(MHZ_RANGE[0] <= f <= MHZ_RANGE[1] for f in mhz):
            tables.add(mhz)
    _cache["freq"] = tuple(sorted(tables))
    return _cache["freq"]


def _table_for(n_states: int, max_mhz: float = MHZ_RANGE[1]) -> tuple[float, ...] | None:
    hits = [t for t in freq_tables() if len(t) == n_states and max(t) <= max_mhz]
    return hits[0] if len(hits) == 1 else None


def _load(states: dict[str, int], max_mhz: float = MHZ_RANGE[1]) -> dict[str, Any]:
    total = sum(states.values())
    active = [(k, v) for k, v in states.items() if k not in IDLE_STATES]
    busy = sum(v for _, v in active)
    table = _table_for(len(active), max_mhz)
    freq = None
    if table and busy:
        freq = round(sum(v * f for (_, v), f in zip(active, table)) / busy)
    return {
        "active": round(100 * busy / total, 1) if total else None,
        "freq_mhz": freq,
        "freq_max_mhz": table[-1] if table else None,
    }


def perf_levels() -> dict[int, str]:
    """{physical core count: level name}, e.g. {6: 'Super', 12: 'Performance'}."""
    if _cache.get("levels"):
        return _cache["levels"]
    out: dict[int, str] = {}
    for lvl in range(4):
        try:
            name = subprocess.run([SYSCTL, "-n", f"hw.perflevel{lvl}.name"],
                                  capture_output=True, text=True, timeout=2).stdout.strip()
            count = subprocess.run([SYSCTL, "-n", f"hw.perflevel{lvl}.physicalcpu"],
                                   capture_output=True, text=True, timeout=2).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            break
        if not name or not count.isdigit():
            break
        # Two levels with the same core count would be ambiguous: drop both.
        out[int(count)] = "" if int(count) in out else name
    _cache["levels"] = {k: v for k, v in out.items() if v}
    return _cache["levels"]


def _core_watts(watts: dict[str, float], cluster: str, core: int, name: str) -> float | None:
    # Energy channel names differ per cluster type: MCPU0_3 vs PACC_3.
    main = next((watts[k] for k in (f"{cluster}_{core}", f"{cluster.replace('CPU', 'ACC')}_{core}")
                 if k in watts), None)
    if main is None:
        return None
    sram = next((watts[k] for k in (f"{cluster}_{core}_SRAM", f"{name}_SRAM") if k in watts), 0.0)
    return round(main + sram, 3)


def cpu(residency: dict[str, dict[str, int]], watts: dict[str, float]) -> dict[str, Any]:
    """{clusters: [{id, kind, label, cores: [...], active, watts}], total_active}."""
    clusters: dict[str, dict[str, Any]] = {}
    for name, states in residency.items():
        m = CORE_NAME.match(name)
        if not m:
            continue
        prefix, a, b = m.groups()
        cluster, core = (f"{prefix}{a}", int(b)) if b is not None else (prefix, int(a))
        c = clusters.setdefault(cluster, {"id": cluster, "prefix": prefix, "cores": []})
        c["cores"].append({"id": name, "core": core, **_load(states),
                           "watts": _core_watts(watts, cluster, core, name)})
    per_prefix: dict[str, int] = {}
    for c in clusters.values():
        per_prefix[c["prefix"]] = per_prefix.get(c["prefix"], 0) + len(c["cores"])
    levels = perf_levels()
    out = []
    for cid in sorted(clusters, key=lambda k: (k[0] != "P", k)):
        c = clusters[cid]
        c["cores"].sort(key=lambda x: x["core"])
        kind = levels.get(per_prefix[c["prefix"]], c["prefix"])
        loads = [x["active"] for x in c["cores"] if x["active"] is not None]
        out.append({
            "id": cid, "kind": kind,
            "label": f"{kind} {cid[-1]}" if cid[-1].isdigit() else kind,
            "cores": c["cores"],
            "active": round(sum(loads) / len(loads), 1) if loads else None,
            "watts": round(watts[cid], 3) if cid in watts else None,
        })
    all_loads = [x["active"] for c in out for x in c["cores"] if x["active"] is not None]
    return {
        "clusters": out,
        "core_count": sum(len(c["cores"]) for c in out),
        "total_active": round(sum(all_loads) / len(all_loads), 1) if all_loads else None,
    }


def gpu(residency: dict[str, dict[str, int]], watts: dict[str, float]) -> dict[str, Any]:
    acc = next((a for a in _ioreg(["-rc", "IOAccelerator"]) if "PerformanceStatistics" in a), {})
    stats = acc.get("PerformanceStatistics", {})
    states = residency.get("GPUPH")
    load = _load(states, GPU_MHZ_MAX) if states else {"active": None, "freq_mhz": None, "freq_max_mhz": None}
    return {
        "core_count": acc.get("gpu-core-count"),
        "device_util": stats.get("Device Utilization %"),
        "renderer_util": stats.get("Renderer Utilization %"),
        "tiler_util": stats.get("Tiler Utilization %"),
        "memory_in_use": stats.get("In use system memory"),
        **load,
        "watts": round(watts["GPU Energy"], 3) if "GPU Energy" in watts else None,
        "per_core": None,
        "per_core_reason": GPU_PER_CORE_REASON,
    }
