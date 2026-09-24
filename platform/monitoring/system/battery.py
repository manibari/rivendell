"""Battery, charge / discharge and adapter readings from AppleSmartBattery.

Read from the IORegistry (`ioreg -rn AppleSmartBattery`), no root. Units are
normalised here so the UI never has to know the raw ones: mV -> V, mA stays
mA (positive = charging, negative = discharging), 1/100 deg C -> deg C.

`status: unavailable` when the machine has no battery (desktop Mac) or the
node cannot be read; the serial number is deliberately never returned.
"""
from __future__ import annotations

import plistlib
import subprocess
from typing import Any

# 0xFFFF is AppleSmartBattery's "not applicable / still estimating".
NO_ESTIMATE = 65535


def _read() -> dict[str, Any] | None:
    try:
        # Absolute path: launchd services run without /usr/sbin on PATH.
        res = subprocess.run(["/usr/sbin/ioreg", "-rn", "AppleSmartBattery", "-a"],
                             capture_output=True, timeout=5)
        nodes = plistlib.loads(res.stdout) if res.stdout else []
    except (OSError, subprocess.TimeoutExpired, plistlib.InvalidFileException):
        return None
    return nodes[0] if nodes else None


def _signed(v: Any) -> int | None:
    # Some firmware reports negative currents as unsigned 64-bit.
    if not isinstance(v, int):
        return None
    return v - (1 << 64) if v >= 1 << 63 else v


def _minutes(v: Any) -> int | None:
    return v if isinstance(v, int) and 0 < v < NO_ESTIMATE else None


# Below this (mA) on AC, the battery is topping up a load the adapter can't carry.
ASSIST_MA = -50


def _state(b: dict[str, Any], amps: int | None) -> tuple[str, str]:
    external = bool(b.get("ExternalConnected"))
    if b.get("IsCharging"):
        return "charging", "充電中"
    if not external:
        return "discharging", "使用電池"
    if amps is not None and amps <= ASSIST_MA:
        # FullyCharged can still be set here; the current is what is true now.
        return "assisting", "接電源，但負載超過充電器，電池放電補足"
    if b.get("FullyCharged"):
        return "full", "已充飽（接電源）"
    # NotChargingReason bits are undocumented: show the raw code, not a guess.
    reason = (b.get("ChargerData") or {}).get("NotChargingReason")
    return "not_charging", "接電源、未充電" + (f"（原因碼 {reason:#x}）" if reason else "")


def snapshot() -> dict[str, Any]:
    b = _read()
    if b is None:
        return {"status": "unavailable", "error": "找不到 AppleSmartBattery（桌上型 Mac 或無法讀取）"}
    data = b.get("BatteryData") or {}
    telem = b.get("PowerTelemetryData") or {}
    adapter = b.get("AdapterDetails") or {}
    amps = _signed(b.get("InstantAmperage"))
    if amps is None:
        amps = _signed(b.get("Amperage"))
    volts = b.get("Voltage")
    watts = round(volts * amps / 1e6, 2) if isinstance(volts, int) and amps is not None else None
    state, label = _state(b, amps)
    design = b.get("DesignCapacity")
    full = b.get("AppleRawMaxCapacity")
    temp = b.get("Temperature")
    cells = data.get("CellVoltage") or []
    return {
        "status": "ok",
        "percent": b.get("CurrentCapacity"),
        "state": state,
        "state_label": label,
        "external_connected": bool(b.get("ExternalConnected")),
        "amperage_ma": amps,
        "voltage_v": round(volts / 1000, 3) if isinstance(volts, int) else None,
        # + = into the battery, - = out of it.
        "battery_watts": watts,
        "system_watts": round(telem["SystemLoad"] / 1000, 2) if "SystemLoad" in telem else None,
        "adapter_in_watts": round(telem["SystemPowerIn"] / 1000, 2) if "SystemPowerIn" in telem else None,
        "adapter": {
            "watts": adapter.get("Watts"),
            "description": adapter.get("Description"),
            "voltage_v": round(adapter["AdapterVoltage"] / 1000, 1) if "AdapterVoltage" in adapter else None,
            "current_ma": adapter.get("Current"),
        } if adapter else None,
        "minutes_to_full": _minutes(b.get("AvgTimeToFull")) if state == "charging" else None,
        "minutes_to_empty": _minutes(b.get("AvgTimeToEmpty")) if state in ("discharging", "assisting") else None,
        "capacity_mah": b.get("AppleRawCurrentCapacity"),
        "full_capacity_mah": full,
        "design_capacity_mah": design,
        "health_percent": round(100 * full / design, 1) if full and design else None,
        "cycle_count": b.get("CycleCount"),
        "design_cycle_count": b.get("DesignCycleCount9C"),
        "temperature_c": round(temp / 100, 1) if isinstance(temp, int) and temp > 0 else None,
        "cell_voltages_v": [round(v / 1000, 3) for v in cells if isinstance(v, int)],
        "charger": {
            "charging_current_ma": (b.get("ChargerData") or {}).get("ChargingCurrent"),
            "charging_voltage_mv": (b.get("ChargerData") or {}).get("ChargingVoltage"),
        },
        "daily_soc": {"min": data.get("DailyMinSoc"), "max": data.get("DailyMaxSoc")},
        "permanent_failure": bool(b.get("PermanentFailureStatus")),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
