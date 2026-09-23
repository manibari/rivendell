"""Temperature, fan and power readings for the dashboard (exelban/stats parity).

The C helper `sensors.c` returns raw SMC keys and IOReport energy channels;
this module builds it on demand, caches the SMC key list (enumerating all keys
costs ~1 s, reading a known list ~0.3 s) and groups raw keys the way Stats
labels them. Keys without a known meaning are reported under "other" by raw
name instead of being guessed at.

Same contract as execution evidence: `status` is ok / unavailable, and an
unreadable sensor is never shown as 0.
"""
from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import threading
from pathlib import Path
from statistics import mean
from typing import Any

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "sensors.c"
BINARY = Path(os.environ.get("SK_SENSORS_BIN", str(HERE / "build" / "sk-sensors")))
BUILD = ["clang", "-O2", "-framework", "IOKit", "-framework", "CoreFoundation", "-lIOReport"]
TIMEOUT_S = 10

# Temperature groups. Prefixes follow Stats' Apple Silicon sensor table;
# a group only appears when the chip actually has matching keys.
TEMP_GROUPS: list[tuple[str, str, re.Pattern[str]]] = [
    ("cpu", "CPU 核心", re.compile(r"^T[pe]\w\w$")),
    ("gpu", "GPU", re.compile(r"^Tg\w\w$")),
    ("ssd", "SSD (NAND)", re.compile(r"^TH0\w$")),
    ("battery", "電池", re.compile(r"^TB\dT$")),
    ("airflow", "出風口", re.compile(r"^Ta[LR][PTFW]$")),
    ("wifi", "Wi-Fi", re.compile(r"^TW0P$")),
    ("palm", "掌托", re.compile(r"^Ts[01]P$")),
]
# SMC power rails with a documented meaning; everything else stays raw.
SMC_POWER = {"PSTR": "系統總功耗", "PDTR": "DC 輸入", "PPBR": "電池"}
# IOReport Energy Model channels.
ENERGY = {"CPU Energy": "CPU", "GPU Energy": "GPU", "ANE": "ANE (神經引擎)", "DRAM": "DRAM"}
CLUSTER = re.compile(r"^[A-Z]CPU\d?$")
# Readings outside this band are unpopulated or placeholder keys (seen: 0,
# 1.0 on TVMD, -127 on absent probes), not temperatures.
TEMP_RANGE = (5.0, 130.0)

_lock = threading.Lock()
_keys: list[str] | None = None


class SensorsUnavailable(RuntimeError):
    pass


def _ensure_binary() -> Path:
    if platform.system() != "Darwin":
        raise SensorsUnavailable("sensors need macOS (AppleSMC / IOReport)")
    if BINARY.is_file() and BINARY.stat().st_mtime >= SOURCE.stat().st_mtime:
        return BINARY
    BINARY.parent.mkdir(parents=True, exist_ok=True)
    try:
        res = subprocess.run([*BUILD, "-o", str(BINARY), str(SOURCE)],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SensorsUnavailable(f"cannot build sk-sensors: {exc}") from exc
    if res.returncode != 0:
        raise SensorsUnavailable(f"cannot build sk-sensors: {res.stderr.strip()[-400:]}")
    return BINARY


def _run(keys: list[str] | None, interval_ms: int) -> dict[str, Any]:
    cmd = [str(_ensure_binary()), "-i", str(interval_ms), *(keys or [])]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
        return json.loads(res.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise SensorsUnavailable(f"sk-sensors failed: {exc}") from exc


def read_raw(interval_ms: int = 250) -> dict[str, Any]:
    """Raw helper output, using the cached key list after the first call."""
    global _keys
    with _lock:
        raw = _run(_keys, interval_ms)
        smc = raw.get("smc", {})
        if _keys is None and "error" not in smc:
            _keys = sorted(smc)
        elif _keys is not None and not smc:
            # Key list went stale (e.g. different machine image): re-enumerate.
            _keys = None
            raw = _run(None, interval_ms)
    return raw


def _temps(smc: dict[str, float]) -> dict[str, Any]:
    lo, hi = TEMP_RANGE
    live = {k: v for k, v in smc.items() if k.startswith("T") and lo <= v <= hi}
    groups = []
    claimed: set[str] = set()
    for gid, label, pattern in TEMP_GROUPS:
        keys = sorted(k for k in live if pattern.match(k))
        if not keys:
            continue
        claimed.update(keys)
        values = [live[k] for k in keys]
        groups.append({"id": gid, "label": label, "avg": round(mean(values), 1),
                       "max": round(max(values), 1), "sensors": {k: round(live[k], 1) for k in keys}})
    other = {k: round(v, 1) for k, v in sorted(live.items()) if k not in claimed}
    return {"groups": groups, "other": other}


def _fans(smc: dict[str, float]) -> list[dict[str, Any]]:
    fans = []
    for i in range(int(smc.get("FNum", 0))):
        actual = smc.get(f"F{i}Ac")
        if actual is None:
            continue
        lo, hi = smc.get(f"F{i}Mn"), smc.get(f"F{i}Mx")
        fans.append({
            "id": i, "rpm": round(actual), "min": lo and round(lo), "max": hi and round(hi),
            "target": smc.get(f"F{i}Tg") and round(smc[f"F{i}Tg"]),
            # F{i}md: 0 = system-controlled; anything else is a forced mode.
            "mode": "auto" if not smc.get(f"F{i}md") else "forced",
            "percent": round(100 * actual / hi) if hi else None,
        })
    return fans


def _power(smc: dict[str, float], energy: dict[str, Any]) -> dict[str, Any]:
    watts = energy.get("watts", {})
    return {
        "system": [{"id": k, "label": v, "watts": round(smc[k], 2)} for k, v in SMC_POWER.items() if k in smc],
        "components": [{"id": k, "label": v, "watts": round(watts[k], 2)} for k, v in ENERGY.items() if k in watts],
        "clusters": {k: round(v, 2) for k, v in sorted(watts.items()) if CLUSTER.match(k)},
        "rails": {k: round(v, 2) for k, v in sorted(smc.items()) if k.startswith("P") and k not in SMC_POWER},
        "energy_error": energy.get("error"),
        "interval_ms": energy.get("interval_ms"),
    }


def snapshot(interval_ms: int = 250) -> dict[str, Any]:
    """{status, temperatures, fans, power} or {status: unavailable, error}."""
    try:
        raw = read_raw(interval_ms)
    except SensorsUnavailable as exc:
        return {"status": "unavailable", "error": str(exc)}
    smc = raw.get("smc", {})
    if "error" in smc:
        return {"status": "unavailable", "error": smc["error"]}
    return {
        "status": "ok",
        "temperatures": _temps(smc),
        "fans": _fans(smc),
        "power": _power(smc, raw.get("energy", {})),
    }


if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
