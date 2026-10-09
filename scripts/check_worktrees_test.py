"""Tests for the read-only worktree check."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check-worktrees.py")


class CheckWorktreesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.worktree = self.root / "linked"
        self.now = int(time.time())
        self.old = self.now - 5 * 86400
        self.git("init", "-b", "main", str(self.repo), cwd=self.root)
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")
        (self.repo / "tracked.txt").write_text("initial\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.commit("initial")

    def git(self, *args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
        result = subprocess.run(
            ["git", *args], cwd=cwd or self.repo, env=env,
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()

    def commit(self, message: str, cwd: Path | None = None) -> None:
        env = os.environ.copy()
        date = f"{self.old} +0000"
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        self.git("commit", "-m", message, cwd=cwd, env=env)

    def add_worktree(self) -> None:
        self.git("worktree", "add", "-b", "topic", str(self.worktree))

    def check(self, *args: str, as_json: bool = True) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--now", str(self.now)]
        if as_json:
            command.append("--json")
        return subprocess.run(command + list(args), capture_output=True, text=True, check=False)

    def result(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        process = self.check(*args)
        return process, json.loads(process.stdout)

    def test_no_extra_worktrees(self) -> None:
        process = self.check(as_json=False)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout.strip(), "0 worktrees")

    def test_old_clean_worktree_is_safe(self) -> None:
        self.add_worktree()
        process, data = self.result()
        self.assertEqual(process.returncode, 1)
        self.assertEqual((data["stale"], data["safe"]), (1, 1))
        item = data["worktrees"][0]
        self.assertEqual((item["ahead"], item["dirty"]), (0, 0))
        self.assertGreater(item["idle_days"], 3)
        text = self.check(as_json=False).stdout
        self.assertIn(f"git worktree remove {self.worktree.resolve()} && git branch -D topic", text)

    def test_commit_not_in_main_is_kept(self) -> None:
        self.add_worktree()
        (self.worktree / "tracked.txt").write_text("changed\n", encoding="utf-8")
        self.git("add", "tracked.txt", cwd=self.worktree)
        self.commit("topic commit", cwd=self.worktree)
        process, data = self.result()
        self.assertEqual(process.returncode, 1)
        item = data["worktrees"][0]
        self.assertEqual((item["ahead"], item["dirty"]), (1, 0))
        self.assertTrue(item["stale"])
        self.assertFalse(item["safe_to_remove"])
        self.assertIn("keep: 1 commits not in main", self.check(as_json=False).stdout)

    def test_recent_changed_file_is_active(self) -> None:
        self.add_worktree()
        changed = self.worktree / "tracked.txt"
        changed.write_text("changed\n", encoding="utf-8")
        os.utime(changed, (self.now, self.now))
        process, data = self.result()
        self.assertEqual(process.returncode, 0)
        item = data["worktrees"][0]
        self.assertEqual(item["dirty"], 1)
        self.assertFalse(item["stale"])
        self.assertEqual(item["idle_days"], 0.0)

    def test_missing_worktree_is_safe_and_prunable(self) -> None:
        self.add_worktree()
        shutil.rmtree(self.worktree)
        process, data = self.result()
        self.assertEqual(process.returncode, 1)
        item = data["worktrees"][0]
        self.assertTrue(item["missing"])
        self.assertTrue(item["safe_to_remove"])
        self.assertIsNone(item["ahead"])
        self.assertIsNone(item["dirty"])
        self.assertIn("remove: git worktree prune", self.check(as_json=False).stdout)

    def test_broken_symlink_does_not_crash(self) -> None:
        self.add_worktree()
        link = self.worktree / "broken-link"
        link.symlink_to("missing-target")
        process, data = self.result()
        self.assertEqual(process.returncode, 0)
        self.assertEqual(data["worktrees"][0]["dirty"], 1)
        self.assertFalse(data["worktrees"][0]["stale"])

    def test_worktree_without_git_link_is_broken_not_safe(self) -> None:
        self.add_worktree()
        (self.worktree / ".git").unlink()
        (self.worktree / ".env").write_text("x")
        process, data = self.result()
        self.assertEqual(process.returncode, 1)
        item = data["worktrees"][0]
        self.assertEqual((item["broken"], item["stale"], item["safe_to_remove"]), (True, True, False))
        self.assertIn("no .git link", self.check(as_json=False).stdout)

    def test_repeated_run_has_same_idle_days(self) -> None:
        self.add_worktree()
        first, first_data = self.result()
        second, second_data = self.result()
        self.assertEqual((first.returncode, second.returncode), (1, 1))
        self.assertEqual(first_data["worktrees"][0]["idle_days"], second_data["worktrees"][0]["idle_days"])


if __name__ == "__main__":
    unittest.main()
