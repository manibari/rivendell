"""Tests for the deck approval preflight."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("deck_preflight.py")


class DeckPreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("jq") is None:
            raise RuntimeError("jq is required to run deck preflight tests")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name: str, status: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nstatus: {status}\n---\n", encoding="utf-8")
        return path

    def run_script(self, *, skip_gate: bool = False) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if skip_gate:
            env["SK_SKIP_STORYLINE_GATE"] = "1"
        else:
            env.pop("SK_SKIP_STORYLINE_GATE", None)
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.root)], env=env,
            capture_output=True, text=True,
        )

    def test_draft_fails_with_hook_reason_even_when_skip_is_set(self) -> None:
        self.write("storyline.md", "draft")
        self.write("review.md", "passed")
        result = self.run_script(skip_gate=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("storyline：未通過（storyline gate:", result.stdout)
        self.assertIn("review：通過", result.stdout)

    def test_signed_off_without_signed_by_passes(self) -> None:
        self.write("storyline.md", "signed-off")
        self.write("review.md", "passed")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("storyline：通過", result.stdout)
        self.assertIn("review：通過", result.stdout)

    def test_missing_files_are_unread(self) -> None:
        self.write("review.md", "passed")
        no_story = self.run_script()
        self.assertEqual(no_story.returncode, 1)
        self.assertIn("storyline：未判讀（找不到 storyline.md）", no_story.stdout)
        (self.root / "review.md").unlink()
        self.write("storyline.md", "signed-off")
        no_review = self.run_script()
        self.assertEqual(no_review.returncode, 1)
        self.assertIn("review：未判讀（找不到 review.md）", no_review.stdout)

    def test_failed_review_and_cached_storyline(self) -> None:
        cached = self.write("cache/storyline.md", "signed-off")
        self.write("review.md", "failed-needs-user")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"storyline：通過；路徑：{cached}", result.stdout)
        self.assertIn("review：未通過", result.stdout)

    def test_cached_draft_in_deep_git_tree_is_blocked(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.root = self.root / "a/b/c/d/e"
        self.root.mkdir(parents=True)
        self.write("cache/storyline.md", "draft")
        self.write("review.md", "passed")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("storyline：未通過（storyline gate:", result.stdout)


if __name__ == "__main__":
    unittest.main()
