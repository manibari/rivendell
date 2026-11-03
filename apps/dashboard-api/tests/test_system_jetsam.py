"""Tests for the standalone JetsamEvent inspector."""

from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[3] / "platform/monitoring/system/jetsam.py"
spec = importlib.util.spec_from_file_location("jetsam", MODULE_PATH)
jetsam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jetsam)

TZ = timezone(timedelta(hours=8))
PAGE_SIZE = 16384
TICKS_PER_SECOND = 24_000_000


def process(name, age_seconds, coalition=1, resident=0, compressed=0, reason=None):
    item = {
        "name": name,
        "pid": age_seconds,
        "age": age_seconds * TICKS_PER_SECOND,
        "coalition": coalition,
        "rpages": resident,
        "states": [],
    }
    if compressed:
        item["physicalPages"] = {"internal": [0, compressed]}
    if reason:
        item["reason"] = reason
    return item


def write_report(directory, stamp, processes):
    path = Path(directory) / f"JetsamEvent-{stamp:%Y-%m-%d-%H%M%S}.ips"
    date = stamp.strftime("%Y-%m-%d %H:%M:%S.00 %z")
    header = {"bug_type": "298", "timestamp": date}
    body = {
        "date": date,
        "largestProcess": "node",
        "memoryStatus": {
            "pageSize": PAGE_SIZE,
            "compressorSize": 65536,
            "uncompressed": 131072,
            "memoryPages": {"wired": 32768, "free": 16384},
        },
        "processes": processes,
    }
    path.write_text(json.dumps(header) + "\n" + json.dumps(body), encoding="utf-8")
    return path


class JetsamTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.earlier_time = datetime(2026, 11, 2, 16, 40, tzinfo=TZ)
        self.report_time = datetime(2026, 11, 2, 16, 49, tzinfo=TZ)
        self.earlier = write_report(self.root, self.earlier_time, [
            process("node", 10), process("zsh", 20),
        ])
        self.latest = write_report(self.root, self.report_time, [
            process("node", 283, resident=65536, compressed=32768),
            process("node", 220, resident=32768, compressed=16384, reason="jettisoned"),
            process("node", 160, resident=0, reason="vm-compressor-space-shortage"),
            process("iTerm2", 300), process("zsh", 280),
            process("other", 1, coalition=2),
        ])
        self.boot = datetime(2026, 11, 2, 16, 56, tzinfo=TZ)

    def inspect(self):
        return jetsam.inspect(
            [self.earlier, self.latest], current_boot=self.boot,
            timebase=(125, 3),
        )

    def test_header_body_and_age_conversion(self):
        report = jetsam.parse_report(self.latest)
        self.assertEqual(report["header"]["bug_type"], "298")
        self.assertEqual(report["body"]["largestProcess"], "node")
        self.assertEqual(report["time"], self.report_time)
        self.assertEqual(jetsam.age_seconds(283 * TICKS_PER_SECOND, (125, 3)), 283)

    def test_grouping_growth_starts_coalitions_and_kills(self):
        detail = self.inspect()["detail"]
        self.assertEqual(detail["top_names"][0]["name"], "node")
        self.assertEqual(detail["top_names"][0]["count"], 3)
        self.assertAlmostEqual(detail["top_names"][0]["resident_gb"], 1.5)
        self.assertAlmostEqual(detail["top_names"][0]["compressed_gb"], 0.75)
        self.assertEqual(detail["growth"][0], {
            "name": "node", "old": 1, "new": 3, "increase": 2,
        })
        profile = detail["multiplied"]
        self.assertEqual(profile["first_start"], "2026-11-02T16:44:17+08:00")
        self.assertEqual(profile["last_start"], "2026-11-02T16:46:20+08:00")
        self.assertEqual(profile["starts_per_minute"], {
            "2026-11-02 16:44": 1,
            "2026-11-02 16:45": 1,
            "2026-11-02 16:46": 1,
        })
        self.assertAlmostEqual(profile["average_per_second"], 3 / 123)
        self.assertEqual(profile["coalitions"][0]["count"], 3)
        self.assertEqual(profile["coalitions"][0]["other_names"], [
            {"name": "iTerm2", "count": 1}, {"name": "zsh", "count": 1},
        ])
        self.assertEqual(detail["killed_by_reason"], {
            "jettisoned": 1, "vm-compressor-space-shortage": 1,
        })

    def test_burst_ignores_old_processes_of_the_same_name(self):
        # Two node processes are weeks old; 30 start within 15 s before the report.
        old = [process("node", 40 * 86400), process("node", 20 * 86400)]
        spawned = [process("node", 15 - i * 0.5) for i in range(30)]
        report = write_report(self.root, self.report_time + timedelta(minutes=1), old + spawned)
        detail = jetsam.inspect(
            [self.latest, report], current_boot=None, timebase=(125, 3),
        )["detail"]
        profile = detail["multiplied"]
        self.assertEqual(profile["count"], 32)
        self.assertEqual(profile["burst"]["count"], 30)
        self.assertEqual(profile["burst"]["first_start"], "2026-11-02T16:49:45+08:00")
        self.assertAlmostEqual(profile["burst"]["per_second"], 30 / 14.5)
        text = jetsam.render({"overview": [], "detail": detail})
        self.assertIn("集中啟動：2026-11-02 16:49:45 到 16:49:59，共 30 個", text)

    def test_no_burst_when_starts_are_spread_out(self):
        self.assertIsNone(self.inspect()["detail"]["multiplied"]["burst"])

    def test_boot_mark_and_selected_report(self):
        data = self.inspect()
        self.assertIsNone(data["overview"][0]["minutes_before_boot"])
        self.assertEqual(data["overview"][1]["minutes_before_boot"], 7)
        self.assertEqual(
            jetsam.boot_mark(self.report_time + timedelta(seconds=16),
                             self.boot + timedelta(seconds=13)), 7,
        )
        self.assertEqual(data["detail"]["path"], str(self.latest))
        self.assertIn("開機前 7 分鐘", jetsam.render(data))
        selected = jetsam.inspect(
            [self.earlier, self.latest], self.earlier, current_boot=self.boot,
            timebase=(125, 3),
        )
        self.assertIsNone(selected["detail"]["growth"])

    def test_no_report_exits_two(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = jetsam.main([], roots=[self.root / "empty"], current_boot=self.boot)
        self.assertEqual(code, 2)
        self.assertEqual(output.getvalue().strip(), "找不到 JetsamEvent 記憶體報告（未判讀）")

    def test_unreadable_report_does_not_hide_good_report(self):
        bad = self.root / "JetsamEvent-2026-11-02-164500.ips"
        bad.write_text("invalid JSON", encoding="utf-8")
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = jetsam.main(
                ["--json"], roots=[self.root], current_boot=self.boot,
                timebase=(125, 3),
            )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["detail"]["path"], str(self.latest))
        self.assertIn(str(bad), errors.getvalue())
        with redirect_stderr(io.StringIO()):
            fallback = jetsam.inspect(
                [bad, self.latest], selected_path=bad, current_boot=self.boot,
                timebase=(125, 3),
            )
        self.assertEqual(fallback["detail"]["path"], str(self.latest))

    def test_cli_file_renders_overview_and_detail(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = jetsam.main(
                ["--file", str(self.latest)], roots=[self.root],
                current_boot=self.boot, timebase=(125, 3),
            )
        self.assertEqual(code, 0)
        self.assertIn("JetsamEvent 記憶體報告", output.getvalue())
        self.assertIn("詳細報告：", output.getvalue())
        self.assertIn("iTerm2", output.getvalue())


if __name__ == "__main__":
    unittest.main()
