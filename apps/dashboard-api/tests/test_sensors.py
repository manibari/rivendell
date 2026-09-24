import platform
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import LIB_DIR  # noqa: F401  (puts dashboard-legacy on sys.path)
from lib import system_sensors as sensors
from routes.monitoring.sensors import api_sensors

RAW = {
    "smc": {
        "Tp00": 50.0, "Tp04": 60.0, "Te05": 40.0, "Tg0C": 45.5, "TH0a": 38.0,
        "TB1T": 33.0, "TaLP": 36.0, "TVMD": 1.0, "TABC": -127.0, "TZZZ": 41.0,
        "FNum": 2, "F0Ac": 2318.0, "F0Mn": 2317.0, "F0Mx": 7826.0, "F0Tg": 2317.0, "F0md": 0,
        "F1Ac": 3913.0, "F1Mn": 2317.0, "F1Mx": 7826.0, "F1Tg": 3913.0, "F1md": 1,
        "PSTR": 14.2, "PDTR": 14.1, "PPBR": 0.57, "PHPC": 6.19,
    },
    "energy": {"interval_ms": 250, "watts": {
        "CPU Energy": 2.7, "GPU Energy": 0.13, "ANE": 0.0, "DRAM": 0.36,
        "MCPU0": 0.1, "PCPU": 1.0, "MCPU1_0": 0.2,
    }},
}


class SensorsTest(unittest.TestCase):
    def snap(self, raw=RAW) -> dict:
        with patch.object(sensors, "read_raw", return_value=raw):
            return sensors.snapshot()

    def test_temperature_groups_and_placeholders(self) -> None:
        temps = self.snap()["temperatures"]
        groups = {g["id"]: g for g in temps["groups"]}
        self.assertEqual(groups["cpu"]["avg"], 50.0)
        self.assertEqual(groups["cpu"]["max"], 60.0)
        self.assertEqual(sorted(groups), ["airflow_l", "battery", "cpu", "gpu", "ssd"])
        # Placeholder values are dropped; unknown live keys stay raw.
        self.assertEqual(temps["other"], {"TZZZ": 41.0})

    def test_fans(self) -> None:
        fans = self.snap()["fans"]
        self.assertEqual([f["rpm"] for f in fans], [2318, 3913])
        self.assertEqual([f["mode"] for f in fans], ["auto", "forced"])
        self.assertEqual(fans[1]["percent"], 50)

    def test_power(self) -> None:
        power = self.snap()["power"]
        self.assertEqual([p["id"] for p in power["system"]], ["PSTR", "PDTR", "PPBR"])
        self.assertEqual({p["id"]: p["watts"] for p in power["components"]}["CPU Energy"], 2.7)
        self.assertEqual(power["clusters"], {"MCPU0": 0.1, "PCPU": 1.0})
        self.assertEqual(power["rails"], {"PHPC": 6.19})

    def test_smc_error_is_unavailable(self) -> None:
        result = self.snap({"smc": {"error": "cannot open AppleSMC"}, "energy": {}})
        self.assertEqual(result, {"status": "unavailable", "error": "cannot open AppleSMC"})

    def test_helper_failure_is_unavailable(self) -> None:
        with patch.object(sensors.platform, "system", return_value="Linux"):
            result = api_sensors(250)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("macOS", result["error"])

    @unittest.skipUnless(platform.system() == "Darwin" and platform.machine() == "arm64", "Apple Silicon only")
    def test_live_read(self) -> None:
        result = sensors.snapshot(100)
        self.assertEqual(result["status"], "ok", result.get("error"))
        self.assertTrue(result["temperatures"]["groups"])
        self.assertTrue(result["power"]["system"] or result["power"]["components"])


if __name__ == "__main__":
    unittest.main()
