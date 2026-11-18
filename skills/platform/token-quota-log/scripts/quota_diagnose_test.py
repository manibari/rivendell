"""Tests for the weekly Claude quota diagnosis report."""

import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import quota_diagnose as diagnose


class QuotaDiagnoseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.quota = self.root / "quota.jsonl"
        self.mapping = self.root / "map.json"
        self.projects = self.root / "projects"
        self.projects.mkdir()
        self.start = 1_780_000_000
        self.reset = self.start + diagnose.WEEK

    def write_jsonl(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    def reading(self, hour, used, reset=None, account="acct"):
        return {"ts": self.start + hour * 3600, "account_id": account,
                "label": "owner@example.com", "limits": {"seven_day": {
                    "used_percentage": used, "resets_at": reset or self.reset}}}

    def usage(self, hour, message_id, request_id, tokens=10_000_000, model="claude-test"):
        stamp = datetime.fromtimestamp(self.start + hour * 3600, timezone.utc).isoformat()
        return {"timestamp": stamp, "requestId": request_id,
                "message": {"id": message_id, "model": model,
                            "usage": {"input_tokens": tokens, "output_tokens": 0,
                                      "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}}

    def test_window_grouping_hit_and_overlap(self):
        other_reset = self.reset + 2 * 86400
        rows = [self.reading(1, 20), self.reading(24, 100),
                self.reading(60, 5, other_reset)]
        self.write_jsonl(self.quota, rows)
        loaded = diagnose.load_readings(self.quota)
        windows = diagnose.build_windows(loaded, "acct", 3, self.reset + 86400)
        self.assertEqual(len(windows), 2)
        self.assertTrue(windows[0]["overlap"])
        self.assertEqual(windows[1]["hit"], self.start + 24 * 3600)
        self.assertEqual((windows[1]["hit"] - windows[1]["start"]) / 86400, 1)

    def test_slots_carry_forward_readings(self):
        rows = diagnose.load_readings(self._quota_rows([self.reading(2, 10), self.reading(8, 25)]))
        window = diagnose.build_windows(rows, "acct", 1, self.start + 13 * 3600)[0]
        slots = diagnose.build_slots(window, [], 6, self.start + 13 * 3600)
        self.assertEqual([slot["delta"] for slot in slots], [10, 15, 0])

    def _quota_rows(self, rows):
        self.write_jsonl(self.quota, rows)
        return self.quota

    def test_usage_dedup_subagents_account_and_title(self):
        project = self.projects / "-Users-dev-work"
        main = project / "parent-uuid.jsonl"
        sub = project / "parent-uuid" / "subagents" / "worker.jsonl"
        other = project / "other-uuid.jsonl"
        self.write_jsonl(main, [self.usage(1, "a", "r"), self.usage(1, "a", "r"),
                                {"type": "custom-title", "customTitle": "Main task"}])
        self.write_jsonl(sub, [self.usage(2, "b", "r")])
        self.write_jsonl(other, [self.usage(3, "c", "r")])
        mapping = {"parent-uuid": {"account_id": "acct"},
                   "other-uuid": {"account_id": "another"}}
        events, sessions = diagnose.load_usage(self.projects, mapping, "acct", self.start)
        self.assertEqual(len(events), 2)
        self.assertEqual(sum(event["tokens"] for event in events), 20_000_000)
        self.assertEqual({event["session"] for event in events}, {"parent-uuid"})
        self.assertEqual(sessions["parent-uuid"]["title"], "Main task")
        self.assertEqual(sessions["parent-uuid"]["project"], "work")

    def test_ratio_and_flagged_other_source(self):
        slots = [{"delta": 2, "local": 10_000_000},
                 {"delta": 4, "local": 20_000_000},
                 {"delta": 6, "local": 30_000_000},
                 {"delta": 10, "local": 0}]
        ratio, count = diagnose.tokens_per_percent([{"slots": slots}])
        self.assertEqual((ratio, count), (5_000_000, 3))
        diagnose.assess_slots(slots, ratio)
        self.assertTrue(slots[-1]["flagged"])
        self.assertEqual(slots[-1]["delta"] - slots[-1]["explained"], 10)

    def test_unknown_ratio(self):
        slots = [{"delta": 5, "local": 0}]
        ratio, count = diagnose.tokens_per_percent([{"slots": slots}])
        self.assertEqual((ratio, count), (None, 0))
        diagnose.assess_slots(slots, ratio)
        self.assertIsNone(slots[0]["explained"])

    def test_report_headings_unmapped_share_and_other_source(self):
        rows = [self.reading(1, 2), self.reading(6, 4), self.reading(12, 8),
                self.reading(18, 14), self.reading(24, 24), self.reading(30, 100)]
        self.write_jsonl(self.quota, rows)
        project = self.projects / "-Users-dev-project"
        self.write_jsonl(project / "unmapped-uuid.jsonl", [
            self.usage(2, "a", "1", 10_000_000),
            self.usage(8, "b", "2", 20_000_000),
            self.usage(14, "c", "3", 30_000_000)])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = diagnose.main(["--quota-log", str(self.quota), "--sessions-map", str(self.mapping),
                                    "--projects-root", str(self.projects), "--now", str(self.start + 36 * 3600)])
        report = output.getvalue()
        self.assertEqual(result, 0)
        for heading in ("# Claude 額度診斷", "## 各週一覽", "### 判讀",
                        "### 額度跳最快的時段", "### 這台用最多的 session",
                        "### 12 小時內用最多", "### 模型比例"):
            self.assertIn(heading, report)
        self.assertIn("未對應帳號的 session 佔這台用量的 100%", report)
        self.assertIn("其他來源可能", report)
        self.assertIn("10.0%", report)

    def test_unknown_ratio_in_report_and_missing_log(self):
        self.write_jsonl(self.quota, [self.reading(6, 5)])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = diagnose.main(["--quota-log", str(self.quota), "--projects-root", str(self.projects),
                                  "--sessions-map", str(self.mapping), "--now", str(self.start + 7 * 3600)])
        self.assertEqual(code, 0)
        self.assertIn("未判讀", output.getvalue())
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            code = diagnose.main(["--quota-log", str(self.root / "missing.jsonl")])
        self.assertEqual(code, 1)
        self.assertIn("找不到額度紀錄檔", error.getvalue())

    def test_off_cycle_window_keeps_regular_windows(self):
        # Regression: an off-cycle reset took one of the `--weeks` places and pushed the
        # oldest regular window out of the report (seen on real data, 2026-11-18).
        week = diagnose.WEEK
        rows = [self.reading(1, 10), self.reading(1 + 168, 10, self.reset + week),
                self.reading(1 + 100, 10, self.reset + 4 * 86400),
                self.reading(1 + 336, 10, self.reset + 2 * week)]
        loaded = diagnose.load_readings(self._quota_rows(rows))
        now = self.start + 3 * week - 3600
        windows = diagnose.build_windows(loaded, "acct", 3, now)
        self.assertEqual(len(windows), 4)
        self.assertEqual(windows[-1]["start"], self.start)

    def test_summary_rows_come_before_details(self):
        week = diagnose.WEEK
        rows = [self.reading(1, 10), self.reading(1 + 168, 20, self.reset + week)]
        self.write_jsonl(self.quota, rows)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            diagnose.main(["--quota-log", str(self.quota), "--sessions-map", str(self.mapping),
                           "--projects-root", str(self.projects), "--now", str(self.start + week + 7200)])
        lines = output.getvalue().splitlines()
        summary_rows = [i for i, line in enumerate(lines) if line.startswith("| ") and "–" in line
                        and line.count("|") == 8]
        first_detail = next(i for i, line in enumerate(lines) if line.startswith("## ") and "各週一覽" not in line)
        self.assertEqual(len(summary_rows), 2)
        self.assertTrue(all(i < first_detail for i in summary_rows))

    def test_reset_shared_with_another_account(self):
        # Two accounts can reset at the same time; only an off-cycle window with the
        # other account's reset is a sign of a wrong label (seen on real data, 2026-11-18).
        off_reset = self.reset + 4 * 86400
        rows = [self.reading(1, 10), self.reading(30, 20),
                self.reading(2, 30, account="other"),
                self.reading(100, 40, off_reset), self.reading(101, 45, off_reset, account="other")]
        self.write_jsonl(self.quota, rows)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            diagnose.main(["--quota-log", str(self.quota), "--sessions-map", str(self.mapping),
                           "--projects-root", str(self.projects), "--account", "acct",
                           "--now", str(self.start + 110 * 3600)])
        summary = [line for line in output.getvalue().splitlines()
                   if line.startswith("| ") and line.count("|") == 8 and "–" in line]
        self.assertEqual(len(summary), 2)
        off, regular = summary
        self.assertIn("可能標錯帳號", off)
        self.assertIn("和另一個週期重疊", off)
        self.assertNotIn("可能標錯帳號", regular)
        self.assertNotIn("和另一個週期重疊", regular)

    def test_bad_rows_are_skipped(self):
        self.quota.write_text("not json\n" + json.dumps(self.reading(1, 10)) + "\n", encoding="utf-8")
        self.assertEqual(len(diagnose.load_readings(self.quota)), 1)


if __name__ == "__main__":
    unittest.main()
