import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import LIB_DIR  # noqa: F401  (puts dashboard-legacy on sys.path)
from lib import system_sensors  # noqa: F401  (puts platform/monitoring/system on sys.path)
import battery  # noqa: E402
import cores  # noqa: E402

M_TABLE = (1000.0, 2000.0, 3000.0)
P_TABLE = (1500.0, 3000.0, 4500.0, 4600.0)

RESIDENCY = {
    # Performance cluster 0, core 0: half the window at 1000 MHz, half idle.
    "MCPU00": {"DOWN": 0, "IDLE": 50, "V0P2": 50, "V1P1": 0, "V2P0": 0},
    "MCPU01": {"DOWN": 100, "IDLE": 0, "V0P2": 0, "V1P1": 0, "V2P0": 0},
    "MCPU10": {"DOWN": 0, "IDLE": 0, "V0P2": 0, "V1P1": 50, "V2P0": 50},
    "PCPU0": {"DOWN": 0, "IDLE": 75, "V0P3": 0, "V1P2": 0, "V2P1": 0, "V3P0": 25},
    "GPUPH": {"OFF": 90, "P1": 10, "P2": 0},
}
WATTS = {"MCPU0_0": 0.2, "MCPU0_0_SRAM": 0.05, "PACC_0": 1.0, "PCPU0_SRAM": 0.1,
         "MCPU0": 0.4, "PCPU": 1.5, "GPU Energy": 0.3}


class CoresTest(unittest.TestCase):
    def setUp(self) -> None:
        patches = [
            patch.object(cores, "freq_tables", return_value=(M_TABLE, P_TABLE)),
            patch.object(cores, "perf_levels", return_value={1: "Super", 3: "Performance"}),
            patch.object(cores, "_ioreg", return_value=[{"gpu-core-count": 20, "PerformanceStatistics": {
                "Device Utilization %": 7, "Renderer Utilization %": 6, "Tiler Utilization %": 5}}]),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_per_core_load_frequency_and_power(self) -> None:
        cpu = cores.cpu(RESIDENCY, WATTS)
        self.assertEqual([c["id"] for c in cpu["clusters"]], ["PCPU", "MCPU0", "MCPU1"])
        self.assertEqual([c["label"] for c in cpu["clusters"]], ["Super", "Performance 0", "Performance 1"])
        self.assertEqual(cpu["core_count"], 4)
        p0 = cpu["clusters"][0]["cores"][0]
        self.assertEqual((p0["active"], p0["freq_mhz"], p0["watts"]), (25.0, 4600, 1.1))
        m00, m01 = cpu["clusters"][1]["cores"]
        self.assertEqual((m00["active"], m00["freq_mhz"], m00["watts"]), (50.0, 1000, 0.25))
        # Fully parked core: 0 % active, no frequency, no energy channel.
        self.assertEqual((m01["active"], m01["freq_mhz"], m01["watts"]), (0.0, None, None))
        self.assertEqual(cpu["clusters"][2]["cores"][0]["freq_mhz"], 2500)

    def test_ambiguous_or_missing_table_gives_no_frequency(self) -> None:
        with patch.object(cores, "freq_tables", return_value=(M_TABLE, (1.0, 2.0, 3.0))):
            self.assertIsNone(cores._load({"IDLE": 1, "A": 1, "B": 1, "C": 1})["freq_mhz"])
        self.assertIsNone(cores._load({"IDLE": 1, "A": 1, "B": 1})["freq_mhz"])

    def test_gpu_is_whole_unit_with_reason(self) -> None:
        gpu = cores.gpu(RESIDENCY, WATTS)
        self.assertEqual((gpu["core_count"], gpu["device_util"], gpu["active"]), (20, 7, 10.0))
        self.assertIsNone(gpu["per_core"])
        self.assertTrue(gpu["per_core_reason"])
        # GPU table must stay under the GPU clock ceiling: CPU tables never match.
        self.assertIsNone(gpu["freq_mhz"])


BATTERY = {
    "CurrentCapacity": 62, "IsCharging": False, "ExternalConnected": False, "FullyCharged": False,
    "Voltage": 12000, "InstantAmperage": (1 << 64) - 1500, "Temperature": 3150,
    "AvgTimeToEmpty": 185, "AvgTimeToFull": 65535, "DesignCapacity": 6000, "AppleRawMaxCapacity": 5700,
    "AppleRawCurrentCapacity": 3500, "CycleCount": 120, "Serial": "SECRET",
    "BatteryData": {"CellVoltage": [4000, 4001, 3999]},
    "PowerTelemetryData": {"SystemLoad": 18000},
}


class BatteryTest(unittest.TestCase):
    def test_discharging_units_and_no_serial(self) -> None:
        with patch.object(battery, "_read", return_value=BATTERY):
            b = battery.snapshot()
        self.assertEqual((b["state"], b["amperage_ma"], b["battery_watts"]), ("discharging", -1500, -18.0))
        self.assertEqual((b["temperature_c"], b["health_percent"]), (31.5, 95.0))
        self.assertEqual((b["minutes_to_empty"], b["minutes_to_full"]), (185, None))
        self.assertEqual(b["cell_voltages_v"], [4.0, 4.001, 3.999])
        self.assertNotIn("SECRET", repr(b))

    def test_plugged_not_charging_shows_raw_reason(self) -> None:
        raw = {**BATTERY, "ExternalConnected": True, "InstantAmperage": 0,
               "ChargerData": {"NotChargingReason": 0x400001}}
        with patch.object(battery, "_read", return_value=raw):
            b = battery.snapshot()
        self.assertEqual(b["state"], "not_charging")
        self.assertIn("0x400001", b["state_label"])

    def test_plugged_in_but_draining_is_not_reported_full(self) -> None:
        raw = {**BATTERY, "ExternalConnected": True, "FullyCharged": True, "InstantAmperage": (1 << 64) - 822}
        with patch.object(battery, "_read", return_value=raw):
            b = battery.snapshot()
        self.assertEqual((b["state"], b["amperage_ma"]), ("assisting", -822))

    def test_no_battery_is_unavailable(self) -> None:
        with patch.object(battery, "_read", return_value=None):
            self.assertEqual(battery.snapshot()["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
