import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import LIB_DIR  # noqa: F401  (puts dashboard-legacy on sys.path)
from lib import system_history as history


class HistoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.conn = history.connect(self.dir)

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def fill(self, start: int, seconds: int, value=lambda i: float(i)) -> None:
        for i, ts in enumerate(range(start, start + seconds, history.SAMPLE_SEC)):
            history.write(self.conn, ts, {"cpu.total": value(i), "temp.cpu": 50.0})

    def test_no_store_is_unavailable_not_empty(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            res = history.query(0, 60, db_dir=Path(other))
        self.assertEqual(res["status"], "unavailable")

    def test_rollup_only_finished_minutes_and_is_idempotent(self) -> None:
        t0 = 1_800_000_000 // 3600 * 3600
        self.fill(t0, 150)  # 2.5 minutes: 30 samples
        now = t0 + 150
        self.assertEqual(history.rollup(self.conn, now)["1m"], 2)
        self.assertEqual(history.rollup(self.conn, now)["1m"], 0)
        rows = self.conn.execute("SELECT ts, n, avg, min, max FROM metrics_1m ORDER BY ts").fetchall()
        self.assertEqual([r[0] for r in rows], [t0, t0 + 60])
        ts, n, avg, mn, mx = rows[0]
        self.assertEqual(n, 12)
        self.assertEqual(history._unpack(avg)["cpu.total"], 5.5)  # mean of 0..11
        self.assertEqual(history._unpack(mn)["cpu.total"], 0.0)
        self.assertEqual(history._unpack(mx)["cpu.total"], 11.0)

    def test_hour_rollup_weights_by_sample_count(self) -> None:
        t0 = 1_800_000_000 // 3600 * 3600
        self.fill(t0, 3600, value=lambda i: 10.0 if i < 360 else 20.0)
        history.rollup(self.conn, t0 + 3600)
        n, avg = self.conn.execute("SELECT n, avg FROM metrics_1h").fetchone()
        self.assertEqual(n, 720)
        self.assertEqual(history._unpack(avg)["cpu.total"], 15.0)

    def test_query_buckets_keeps_gaps_and_filters_keys(self) -> None:
        now = int(time.time()) // 60 * 60
        start = now - 600
        self.fill(start, 120)             # first 2 minutes
        self.fill(start + 480, 120)       # last 2 minutes; 4-minute gap between
        res = history.query(start, now, keys=["cpu.total"], points=10, db_dir=self.dir)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["tier"], "5s")
        self.assertEqual(res["step"], 60)
        self.assertEqual(list(res["avg"]), ["cpu.total"])
        series = res["avg"]["cpu.total"]
        self.assertEqual(len(series), 10)
        self.assertIsNotNone(series[0])
        self.assertEqual(series[2:8], [None] * 6)
        self.assertEqual(res["max"]["cpu.total"][1], 23.0)

    def test_long_range_reads_rollup_tier(self) -> None:
        now = int(time.time())
        with patch.object(history, "MAX_ROWS", 100):
            self.assertEqual(history._pick_tier(self.conn, now - 3600, now), "1m")
        self.assertEqual(history._pick_tier(self.conn, now - 30 * 86400, now), "1h")
        # 5 s rows are gone after 7 days even if the window is short.
        self.assertEqual(history._pick_tier(self.conn, now - 8 * 86400, now - 8 * 86400 + 600), "1m")

    def test_prune_respects_retention(self) -> None:
        now = 1_800_000_000
        history.write(self.conn, now - 8 * 86400, {"x": 1.0})
        history.write(self.conn, now - 86400, {"x": 1.0})
        self.assertEqual(history.prune(self.conn, now)["5s"], 1)

    def test_flatten_skips_unreadable_values(self) -> None:
        snap = {
            "cpu": {"total_active": 12.5, "clusters": [{"id": "PCPU", "active": 20.0, "watts": None, "cores": [
                {"id": "PCPU0", "active": 20.0, "freq_mhz": None, "watts": 0.5}]}]},
            "gpu": {"device_util": 3, "active": None, "freq_mhz": None, "watts": 0.1},
            "battery": {"status": "ok", "percent": 80, "amperage_ma": -1200, "external_connected": False},
            "fans": [{"id": 0, "rpm": 2300}],
        }
        flat = history.flatten(snap)
        self.assertEqual(flat["core.PCPU0.w"], 0.5)
        self.assertNotIn("core.PCPU0.mhz", flat)
        self.assertNotIn("cpu.PCPU.w", flat)
        self.assertNotIn("gpu.active", flat)
        self.assertEqual(flat["bat.ma"], -1200.0)
        self.assertEqual(flat["bat.ac"], 0.0)
        self.assertEqual(flat["fan.0"], 2300.0)


if __name__ == "__main__":
    unittest.main()
