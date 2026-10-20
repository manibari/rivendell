"""Tests for the machine work root registry."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("work_roots.py")


class WorkRootsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.conf = self.root / "work-roots.conf"
        self.folder = self.root / "work"
        self.folder.mkdir()
        self.conf.write_text(f"# registry\nTestHost | chimes-work | {self.folder} | test\n", encoding="utf-8")

    def run_script(self, *args: str, host: str = "testhost.local") -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(SK_WORK_ROOTS_CONF=str(self.conf), SK_WORK_ROOTS_HOST=host)
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)

    def test_get_matches_host_without_case(self) -> None:
        result = self.run_script("get", "chimes-work")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), str(self.folder))

    def test_unknown_host_names_host(self) -> None:
        result = self.run_script("get", "chimes-work", host="Other.local")
        self.assertEqual(result.returncode, 1)
        self.assertIn("這台機器（Other）沒有登記 chimes-work", result.stderr)

    def test_missing_path_fails(self) -> None:
        self.folder.rmdir()
        result = self.run_script("get", "chimes-work")
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"chimes-work 登記的路徑不存在：{self.folder}", result.stderr)

    def test_check_existing_missing_and_empty_host(self) -> None:
        existing = self.run_script("check")
        self.assertEqual(existing.returncode, 0)
        self.assertIn("chimes-work |", existing.stdout)
        self.assertIn("work roots: 1 registered for testhost, 0 missing", existing.stdout)
        self.folder.rmdir()
        missing = self.run_script("check")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("不存在", missing.stdout)
        empty = self.run_script("check", host="other")
        self.assertEqual(empty.returncode, 1)
        self.assertIn("work roots: 0 registered for other, 0 missing", empty.stdout)


if __name__ == "__main__":
    unittest.main()
