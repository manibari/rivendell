"""Tests for analyze.py and gateway.extract_text. Run: python3 -m unittest analyze_test (in scripts/)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import analyze
import gateway

SNAP = {
    "window": ["2026-11-17T18:00+08:00", "2026-11-18T09:00+08:00"],
    "claude_sessions": [{
        "session": "abcdef12", "name": "demo", "project": "demo", "api_calls": 40, "user_prompts": 2,
        "tokens_total": 12_000_000, "avg_context": 320_000, "peak_context": 400_000,
        "cache_rebuilds_after_idle_1h": 1, "tool_errors": 0,
        "repeated_bash": [{"cmd": "git status", "n": 12}],
    }],
    "codex_sessions": [{"file": "a", "input_tokens_incl_cached": 555}, {"file": "b", "input_tokens_incl_cached": 1}],
    "code_runs": [{"run": "r1", "exit": 1, "seconds": 9, "input_tokens_incl_cached": 555, "attempts": 2, "error": "x"},
                  {"run": "r2", "status": "running or no summary"}],
}


class AnalyzeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.snap = Path(self.tmp.name) / "snap.json"
        self.snap.write_text(json.dumps(SNAP))
        self.report = Path(self.tmp.name) / "report.md"

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self):
        with mock.patch.object(sys, "argv", ["analyze.py", str(self.snap), str(self.report)]):
            analyze.main()
        return self.report.read_text()

    def test_overlap_marks_codex_session_of_a_code_run(self):
        data = json.loads(json.dumps(SNAP))
        analyze.mark_overlap(data)
        self.assertEqual([s["also_code_run"] for s in data["codex_sessions"]], [True, False])

    def test_report_has_gemini_text_and_raw_appendix(self):
        with mock.patch.object(analyze.gateway, "ask", return_value=("## 結論\n疑似浪費 1 個", {"input_tokens": 1})):
            text = self.run_main()
        self.assertIn("## 結論", text)
        self.assertIn("## 附錄", text)
        self.assertIn("| abcdef12 | demo | demo | 40 |", text)
        self.assertIn("12× `git status`", text)
        self.assertIn("| r2 | 進行中 |", text)

    def test_gemini_failure_is_reported_not_hidden(self):
        with mock.patch.object(analyze.gateway, "ask", side_effect=RuntimeError("gateway HTTP 401: bad key")):
            text = self.run_main()
        self.assertIn("## 判讀失敗", text)
        self.assertIn("gateway HTTP 401", text)
        self.assertIn("## 附錄", text)


class ExtractTextTest(unittest.TestCase):
    def test_output_text_parts_are_joined(self):
        data = {"output": [{"type": "reasoning", "content": []},
                           {"type": "message", "content": [{"type": "output_text", "text": "a"},
                                                           {"type": "output_text", "text": "b"}]}]}
        self.assertEqual(gateway.extract_text(data), "a\nb")

    def test_fallback_to_output_text_field(self):
        self.assertEqual(gateway.extract_text({"output_text": "x"}), "x")


if __name__ == "__main__":
    unittest.main()
