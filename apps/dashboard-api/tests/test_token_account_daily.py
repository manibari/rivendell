import sqlite3
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import LIB_DIR  # noqa: F401  (puts dashboard-legacy on sys.path)
from lib import tokens as usage
from lib import tokens_account_daily as daily
from lib import tokens_accounts as accounts
from lib import tokens_timeline as timeline
from tests.test_token_timeline import claude_row, codex_meta, codex_row


class AccountDailyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.claude = root / "claude" / "proj"
        self.codex = root / "codex"
        self.claude.mkdir(parents=True)
        self.codex.mkdir()
        self.db = root / "test.db"
        timeline._TAILS.clear()
        self.patches = [
            patch.object(timeline, "PROJECTS_DIR", root / "claude"),
            patch.object(timeline, "CODEX_SESSION_DIRS", (self.codex,)),
            patch.object(accounts, "_history_db_path", lambda: self.db),
            patch.object(daily, "_history_db_path", lambda: self.db),
            patch.object(usage, "_history_db_path", lambda: self.db),
        ]
        for p in self.patches:
            p.start()
        midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.yesterday = (midnight - timedelta(days=1)).timestamp()
        self.day = (midnight - timedelta(days=1)).strftime("%Y-%m-%d")

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        timeline._TAILS.clear()
        self.tmp.cleanup()

    def sight(self, source: str, account: str, label: str, start: float, end: float) -> None:
        with accounts._connect() as conn:
            conn.execute(
                "INSERT INTO token_account_log(source, account_id, label, observed_from, observed_to) "
                "VALUES (?, ?, ?, ?, ?)", (source, account, label, start, end))

    def test_rows_are_split_by_account_and_unseen_claude_stays_unattributed(self) -> None:
        t = self.yesterday + 3600
        self.sight("claude", "acct-a", "a@example.com", t, t + 600)
        (self.claude / "s.jsonl").write_text(
            claude_row(t + 60, "r1", 100) + claude_row(t + 7200, "r2", 7))
        (self.codex / "rollout.jsonl").write_text(
            codex_meta("acct-x") + codex_row(t, 100, 10) + codex_row(t + 60, 160, 40))
        self.assertEqual(daily.snapshot(days_back=2), 1)
        rows = {(r["source"], r["account_id"]): r for r in daily.read(self.day, self.day)}
        self.assertEqual(rows[("claude", "acct-a")]["output"], 100)
        self.assertEqual(rows[("claude", "acct-a")]["label"], "a@example.com")
        self.assertEqual(rows[("claude", "")]["output"], 7)
        self.assertEqual(rows[("claude", "")]["label"], "")
        self.assertEqual((rows[("codex", "acct-x")]["input"], rows[("codex", "acct-x")]["output"]),
                         (160, 40))

    def test_today_is_not_stored(self) -> None:
        (self.claude / "s.jsonl").write_text(claude_row(time.time() - 5, "r1", 9))
        self.assertEqual(daily.snapshot(days_back=2), 0)
        self.assertEqual(daily.read(), [])

    def test_a_smaller_reparse_does_not_overwrite_a_stored_day(self) -> None:
        t = self.yesterday + 3600
        (self.claude / "a.jsonl").write_text(claude_row(t, "r1", 100))
        (self.claude / "b.jsonl").write_text(claude_row(t + 60, "r2", 50))
        daily.snapshot(days_back=2)
        (self.claude / "a.jsonl").unlink()  # rotated away
        timeline._TAILS.clear()
        self.assertEqual(daily.snapshot(days_back=2), 0)
        self.assertEqual(sum(r["output"] for r in daily.read(self.day, self.day)), 150)

    def test_daily_total_snapshot_never_shrinks(self) -> None:
        full = usage.DailyUsage("2026-09-01", 2, 20, 0, 1000, 9.0)
        usage.upsert_daily_usage(full)
        usage.upsert_daily_usage(usage.DailyUsage("2026-09-01", 1, 5, 0, 300, 2.0))
        usage.upsert_daily_usage(usage.DailyUsage("2026-09-02", 1, 5, 0, 300, 2.0))
        with sqlite3.connect(self.db) as conn:
            got = dict(conn.execute("SELECT date, tokens_total FROM token_usage").fetchall())
        self.assertEqual(got, {"2026-09-01": 1000, "2026-09-02": 300})
        usage.upsert_daily_usage(usage.DailyUsage("2026-09-01", 3, 30, 0, 1200, 11.0))
        with sqlite3.connect(self.db) as conn:
            got = conn.execute("SELECT tokens_total FROM token_usage WHERE date='2026-09-01'").fetchone()
        self.assertEqual(got[0], 1200)


if __name__ == "__main__":
    unittest.main()
