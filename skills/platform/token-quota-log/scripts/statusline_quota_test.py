#!/usr/bin/env python3
"""Unit tests for statusline-quota.py: per-session account binding.

The script file name carries a dash, so it is loaded with
importlib.machinery.SourceFileLoader. All paths the script touches are
patched into a temp dir; no service or real ~/.claude.json is needed.
"""

from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).with_name("statusline-quota.py")

loader = importlib.machinery.SourceFileLoader("statusline_quota", str(SCRIPT))
_spec = importlib.util.spec_from_loader(loader.name, loader)
mod = importlib.util.module_from_spec(_spec)
loader.exec_module(mod)


class StatusLineQuotaTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.quota_dir = root / "usage-quota"
        self.quota_dir.mkdir()
        self.config = root / ".claude.json"
        for name, value in [
            ("QUOTA_DIR", self.quota_dir),
            ("QUOTA_LOG", self.quota_dir / "claude-rate-limits.jsonl"),
            ("LAST_FILE", self.quota_dir / ".last-claude.json"),
            ("SESSIONS_FILE", self.quota_dir / ".sessions-claude.json"),
            ("CLAUDE_CONFIG", self.config),
        ]:
            patcher = mock.patch.object(mod, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_config(self, account_id: str, email: str, plan: str) -> None:
        self.config.write_text(json.dumps({"oauthAccount": {
            "accountUuid": account_id,
            "emailAddress": email,
            "organizationRateLimitTier": plan,
        }}))

    def render(self, session_id: str, five_hour: float, now: float) -> str:
        data = {"rate_limits": {"five_hour": {
            "used_percentage": five_hour, "resets_at": 1}}}
        if session_id:
            data["session_id"] = session_id
        with mock.patch.object(sys, "stdin", io.StringIO(json.dumps(data))), \
                mock.patch.object(mod, "time") as fake_time:
            fake_time.time.return_value = now
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                mod.main()
        return captured.getvalue()

    def rows(self) -> list:
        log = self.quota_dir / "claude-rate-limits.jsonl"
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text().splitlines()
                if line.strip()]

    def test_session_keeps_first_account_after_login_switch(self):
        self.write_config("acct-a", "a@example.com", "claude_max_5x")
        first = self.render("S1", 50.0, now=1000.0)
        self.assertIn("5h 50%", first)
        self.write_config("acct-b", "b@example.com", "claude_max_5x")
        second = self.render("S1", 73.0, now=2000.0)
        self.assertIn("5h 73%", second)
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["account_id"], "acct-a")
        self.assertEqual(rows[1]["account_id"], "acct-a")
        self.assertEqual(rows[1]["label"], "a@example.com")

    def test_new_session_started_after_switch_gets_new_account(self):
        self.write_config("acct-a", "a@example.com", "claude_max_5x")
        self.render("S1", 50.0, now=1000.0)
        self.write_config("acct-b", "b@example.com", "claude_max_5x")
        self.render("S2", 10.0, now=2000.0)
        rows = self.rows()
        self.assertEqual(rows[-1]["account_id"], "acct-b")
        self.assertEqual(rows[-1]["label"], "b@example.com")

    def test_empty_session_id_uses_current_config_account(self):
        self.write_config("acct-a", "a@example.com", "claude_max_5x")
        self.render("", 50.0, now=1000.0)
        self.write_config("acct-b", "b@example.com", "claude_max_5x")
        self.render("", 73.0, now=2000.0)
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["account_id"], "acct-b")

    def test_same_limits_rendered_twice_writes_one_row(self):
        self.write_config("acct-a", "a@example.com", "claude_max_5x")
        self.render("S1", 50.0, now=1000.0)
        self.render("S1", 50.0, now=1100.0)
        self.assertEqual(len(self.rows()), 1)

    def test_stale_session_entries_dropped_on_next_write(self):
        sessions_path = self.quota_dir / ".sessions-claude.json"
        sessions_path.write_text(json.dumps({"S1": {
            "account_id": "acct-a", "label": "a@example.com",
            "plan": "claude_max_5x", "first_seen": 1000.0}}))
        self.write_config("acct-b", "b@example.com", "claude_max_5x")
        self.render("S2", 10.0, now=1000.0 + 31 * 86400)
        stored = json.loads(sessions_path.read_text())
        self.assertNotIn("S1", stored)
        self.assertIn("S2", stored)

    def test_broken_sessions_file_does_not_raise(self):
        sessions_path = self.quota_dir / ".sessions-claude.json"
        sessions_path.write_text("this is not json")
        self.write_config("acct-b", "b@example.com", "claude_max_5x")
        output = self.render("S1", 50.0, now=1000.0)
        self.assertIn("5h 50%", output)
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["account_id"], "acct-b")
        stored = json.loads(sessions_path.read_text())
        self.assertIn("S1", stored)


if __name__ == "__main__":
    unittest.main()
