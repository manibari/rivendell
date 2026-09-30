"""System-wide macOS memory readings for the system monitor."""
from __future__ import annotations

import platform
import re
import subprocess
import threading
import time
from typing import Any

TIMEOUT_S = 3
PAGE_SIZE_RE = re.compile(r"page size of ([0-9,]+) bytes")
TOTAL_RE = re.compile(r"The system has ([0-9,]+) \(([0-9,]+) pages")
FREE_RE = re.compile(r"System-wide memory free percentage:\s*([0-9.]+)%")
PAGE_RE = re.compile(r"Pages ([a-zA-Z ]+):\s*([0-9,]+)")
SWAP_RE = re.compile(r"total = ([0-9.]+)([KMG])\s+used = ([0-9.]+)([KMG])\s+free = ([0-9.]+)([KMG])")
UNITS = {"K": 1024, "M": 1024**2, "G": 1024**3}
# kern.memorystatus_vm_pressure_level: the same level Activity Monitor's pressure graph uses.
PRESSURE_LEVELS = {1: "normal", 2: "warn", 4: "critical"}
# Absolute paths: launchd services run with a PATH that omits /usr/sbin.
VM_STAT, MEMORY_PRESSURE, SYSCTL = "/usr/bin/vm_stat", "/usr/bin/memory_pressure", "/usr/sbin/sysctl"
_CACHE_SEC = 5
_cache_lock = threading.Lock()
_cache_until = 0.0
_cache: dict[str, Any] | None = None


def _run(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=TIMEOUT_S)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"{args[0]} exited {result.returncode}")
    return result.stdout


def _swap_bytes(text: str) -> tuple[int, int, int] | None:
    match = SWAP_RE.search(text)
    if not match:
        return None
    vals = [int(float(match.group(i)) * UNITS[match.group(i + 1)]) for i in (1, 3, 5)]
    return vals[0], vals[1], vals[2]


def _read_snapshot() -> dict[str, Any]:
    if platform.system() != "Darwin":
        return {"status": "unavailable", "error": "memory readings need macOS"}
    try:
        vm = _run(VM_STAT)
        pressure = _run(MEMORY_PRESSURE, "-Q")
    except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
        return {"status": "unavailable", "error": str(exc)}

    page_match = PAGE_SIZE_RE.search(vm)
    pressure_match = FREE_RE.search(pressure)
    pages = {key.strip(): int(value.replace(",", "")) for key, value in PAGE_RE.findall(vm)}
    if not page_match or not pressure_match:
        return {"status": "unavailable", "error": "macOS memory output was not recognized"}

    page_size = int(page_match.group(1).replace(",", ""))
    total_match = TOTAL_RE.search(pressure)
    total_bytes = int(total_match.group(1).replace(",", "")) if total_match else None
    available_pct = float(pressure_match.group(1))
    available_bytes = round(total_bytes * available_pct / 100) if total_bytes is not None else None
    used_bytes = total_bytes - available_bytes if total_bytes is not None and available_bytes is not None else None
    compressed_bytes = pages.get("occupied by compressor")
    compressed_bytes = compressed_bytes * page_size if compressed_bytes is not None else None

    try:
        swap = _swap_bytes(_run(SYSCTL, "vm.swapusage"))
    except (OSError, subprocess.TimeoutExpired, RuntimeError):
        swap = None

    try:
        raw_level = int(_run(SYSCTL, "-n", "kern.memorystatus_vm_pressure_level").strip())
    except (OSError, subprocess.TimeoutExpired, RuntimeError, ValueError):
        raw_level = None

    return {
        "status": "ok",
        "pressure_level": PRESSURE_LEVELS.get(raw_level) if raw_level is not None else None,
        "pressure_level_raw": raw_level,
        "total_bytes": total_bytes,
        "used_bytes": used_bytes,
        "available_bytes": available_bytes,
        "available_percent": available_pct,
        "compressed_bytes": compressed_bytes,
        "swap_total_bytes": swap[0] if swap else None,
        "swap_used_bytes": swap[1] if swap else None,
        "swap_free_bytes": swap[2] if swap else None,
        "page_size_bytes": page_size,
        "source": "vm_stat + memory_pressure + sysctl",
    }


def snapshot() -> dict[str, Any]:
    """Return a cached five-second sample to keep subprocess overhead low."""
    global _cache, _cache_until
    with _cache_lock:
        now = time.monotonic()
        if _cache is not None and now < _cache_until:
            return dict(_cache)
        _cache = _read_snapshot()
        _cache_until = now + _CACHE_SEC
        return dict(_cache)
