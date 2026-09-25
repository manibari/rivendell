"""bin/sk-watchdog overload hold: failures under a saturated machine wait, a hung service still restarts."""
import subprocess
import tempfile
import unittest
from pathlib import Path

WATCHDOG = Path(__file__).resolve().parents[3] / "bin" / "sk-watchdog"

# Source the script, stub the probe (always failing) and the restart (records
# the call), then run one check. Everything else is the real script.
HARNESS = """
source "$WATCHDOG"
probe_url() { return 1; }
svc_restart() { echo "$1" >> "$SK_WATCHDOG_STATE_DIR/restarts"; }
check_and_restart api http://localhost:1/none com.sk.dashboard.api
"""


class WatchdogOverloadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_checks(self, times: int, load: str | None, cpus: str = "18") -> None:
        env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "WATCHDOG": str(WATCHDOG),
               "SK_WATCHDOG_STATE_DIR": str(self.dir), "SK_WATCHDOG_CPUS": cpus}
        if load is not None:
            env["SK_WATCHDOG_LOAD"] = load
        for _ in range(times):
            res = subprocess.run(["bash", "-c", HARNESS], env=env, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stderr)

    def restarts(self) -> int:
        f = self.dir / "restarts"
        return len(f.read_text().splitlines()) if f.exists() else 0

    def log(self) -> str:
        return (self.dir / "watchdog.log").read_text()

    def test_normal_load_restarts_after_threshold(self) -> None:
        self.run_checks(3, load="3.5")
        self.assertEqual(self.restarts(), 1)
        self.assertNotIn("HOLD", self.log())

    def test_overload_holds_restart(self) -> None:
        self.run_checks(9, load="28.4")
        self.assertEqual(self.restarts(), 0)
        self.assertIn("HOLD com.sk.dashboard.api (system overloaded, load 28.4/18", self.log())

    def test_hung_service_still_restarts_after_max_wait(self) -> None:
        self.run_checks(10, load="28.4")
        self.assertEqual(self.restarts(), 1)

    def test_unreadable_load_falls_back_to_restart(self) -> None:
        self.run_checks(3, load="")
        self.assertEqual(self.restarts(), 1)

    def test_ratio_boundary(self) -> None:
        # 18 cores x 1.2 = 21.6: at the line is not overloaded.
        self.run_checks(3, load="21.6")
        self.assertEqual(self.restarts(), 1)


if __name__ == "__main__":
    unittest.main()
