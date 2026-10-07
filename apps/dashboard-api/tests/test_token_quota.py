import json
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import LIB_DIR  # noqa: F401  (puts dashboard-legacy on sys.path)
from lib import tokens_accounts as accounts
from lib import tokens_quota as quota

HOUR = 3600


def iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def codex_event(at: float, total_in: int, cached: int, out: int, used: float | None,
                resets_at: float, plan: str = "prolite") -> str:
    payload = {"type": "token_count", "info": {"total_token_usage": {
        "input_tokens": total_in, "cached_input_tokens": cached,
        "output_tokens": out, "total_tokens": total_in + out}}}
    if used is not None:
        payload["rate_limits"] = {"primary": {"used_percent": used, "window_minutes": 10080,
                                              "resets_at": resets_at}, "plan_type": plan}
    return json.dumps({"timestamp": iso(at), "type": "event_msg", "payload": payload}) + "\n"


def codex_meta(account: str) -> str:
    return json.dumps({"timestamp": iso(0), "type": "session_meta",
                       "payload": {"id": "c1", "creator_account_id": account}}) + "\n"


def claude_row(at: float, request: str, output: int) -> str:
    return json.dumps({
        "timestamp": iso(at), "requestId": request,
        "message": {"model": "claude-opus-5-5", "usage": {
            "input_tokens": 1, "output_tokens": output,
            "cache_read_input_tokens": 100, "cache_creation_input_tokens": 10}},
    }) + "\n"


def quota_row(at: float, account: str, week_used: float, resets_at: float) -> str:
    return json.dumps({"ts": at, "account_id": account, "label": "a@b.c", "limits": {
        "seven_day": {"used_percentage": week_used, "resets_at": resets_at}}}) + "\n"


class QuotaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = self.root = Path(self.tmp.name)
        self.claude = root / "claude" / "proj"
        self.codex = root / "codex"
        self.claude.mkdir(parents=True)
        self.codex.mkdir()
        self.log = root / "claude-rate-limits.jsonl"
        quota._codex_cache.clear()
        quota._claude_tails.clear()
        db = root / "test.db"
        self.patches = [
            patch.object(quota, "PROJECTS_DIR", root / "claude"),
            patch.object(quota, "CODEX_SESSION_DIRS", (self.codex,)),
            patch.object(quota, "CLAUDE_QUOTA_LOG", self.log),
            patch.object(quota, "_history_db_path", lambda: db),
            patch.object(accounts, "_history_db_path", lambda: db),
            patch.object(accounts, "CLAUDE_CONFIG", root / "claude.json"),
            patch.object(accounts, "CODEX_AUTH", root / "codex-auth.json"),
        ]
        for p in self.patches:
            p.start()
        self.now = time.time()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def window(self, result: dict, source: str) -> dict:
        return next(w for w in result["windows"] if w["source"] == source)

    def test_codex_window_counts_tokens_between_first_and_last_reading(self) -> None:
        resets = self.now + 3 * 86400
        (self.codex / "r.jsonl").write_text(
            codex_meta("acct-1")
            + codex_event(self.now - 300, 1000, 800, 10, 10, resets)
            # the server jitters resets_at by seconds; still the same window
            + codex_event(self.now - 200, 3000, 2600, 30, 11, resets + 7)
            + codex_event(self.now - 100, 6000, 5000, 60, 12, resets - 4))
        quota.refresh(self.now)
        w = self.window(quota.get_quota(self.now), "codex")
        self.assertEqual((w["used_from"], w["used_to"], w["readings"]), (10, 12, 3))
        # only the two events after the first reading count, input net of cached
        self.assertEqual((w["input"], w["cache_read"], w["output"]), (800, 4200, 50))
        self.assertEqual(w["tokens"], 5050)
        self.assertEqual(w["tokens_per_percent"], 2525)
        self.assertEqual(w["plan"], "prolite")

    def test_account_shows_remaining_and_reset_time(self) -> None:
        resets = self.now + 86400
        (self.codex / "r.jsonl").write_text(
            codex_meta("acct-1") + codex_event(self.now - 60, 100, 0, 1, 84, resets))
        quota.refresh(self.now)
        a = quota.get_quota(self.now)["accounts"][0]
        q = a["quota"]["10080"]
        self.assertEqual((a["source"], a["account_id"]), ("codex", "acct-1"))
        self.assertEqual((q["used_percent"], q["remaining_percent"]), (84, 16))
        self.assertEqual(q["resets_at"], resets)  # the server's exact time, not the hour key
        self.assertFalse(q["reset_since_read"])
        # after the reset time passes the quota is full again until a new reading
        later = quota.get_quota(resets + 2 * HOUR)["accounts"][0]["quota"]["10080"]
        self.assertEqual((later["remaining_percent"], later["reset_since_read"]), (100, True))

    def test_claude_window_uses_the_login_that_covers_each_row(self) -> None:
        (self.root / "claude.json").write_text(json.dumps(
            {"oauthAccount": {"accountUuid": "u-1", "emailAddress": "a@b.c"}}))
        for at in range(int(self.now - 400), int(self.now), 20):
            accounts.observe(at)
        resets = self.now + 2 * 86400
        self.log.write_text(quota_row(self.now - 300, "u-1", 40, resets)
                            + quota_row(self.now - 50, "u-1", 42, resets))
        (self.claude / "a.jsonl").write_text(
            claude_row(self.now - 350, "r0", 999)      # before the first reading
            + claude_row(self.now - 200, "r1", 5)
            + claude_row(self.now - 100, "r2", 7))
        quota.refresh(self.now)
        result = quota.get_quota(self.now)
        w = self.window(result, "claude")
        self.assertEqual((w["output"], w["cache_read"], w["cache_create"]), (12, 200, 20))
        self.assertEqual(w["tokens_per_percent"], 117)  # (2 + 12 + 200 + 20) / 2
        self.assertEqual(w["label"], "a@b.c")
        self.assertTrue(result["claude_log_present"])

    def test_claude_session_window_reports_its_exact_reset(self) -> None:
        session_reset = self.now + 2 * HOUR + 1234
        self.log.write_text(json.dumps({"ts": self.now - 60, "account_id": "u-1",
                                        "plan": "claude_max_5x", "limits": {
            "five_hour": {"used_percentage": 56, "resets_at": session_reset},
            "seven_day": {"used_percentage": 54, "resets_at": self.now + 86400}}}) + "\n")
        quota.refresh(self.now)
        q = quota.get_quota(self.now)["accounts"][0]["quota"]
        self.assertEqual((q["300"]["used_percent"], q["300"]["remaining_percent"]), (56, 44))
        self.assertEqual(q["300"]["resets_at"], session_reset)
        self.assertEqual(q["10080"]["used_percent"], 54)
        self.assertEqual(quota.get_quota(self.now)["accounts"][0]["plan"], "claude_max_5x")

    def test_a_closed_claude_window_keeps_its_stored_tokens(self) -> None:
        resets = self.now + HOUR
        self.log.write_text(quota_row(self.now - 300, "", 1, resets)
                            + quota_row(self.now - 50, "", 3, resets))
        (self.claude / "a.jsonl").write_text(claude_row(self.now - 100, "r1", 5))
        quota.refresh(self.now)
        quota.refresh(resets + 2 * HOUR)  # window closed; its logs are not read again
        self.assertEqual(self.window(quota.get_quota(), "claude")["output"], 5)

    def login_codex(self, account: str, email: str, start: float, end: float) -> None:
        import base64
        body = base64.urlsafe_b64encode(json.dumps({"email": email}).encode()).decode().rstrip("=")
        (self.root / "codex-auth.json").write_text(json.dumps(
            {"tokens": {"account_id": account, "id_token": f"h.{body}.s"}}))
        for at in range(int(start), int(end), 20):
            accounts.observe(at)

    def test_codex_readings_follow_the_login_not_the_session_creator(self) -> None:
        # One session created by acct-1; the login switches to acct-2 halfway and
        # Codex keeps the same session running on the new account.
        self.login_codex("acct-1", "one@x.y", self.now - 600, self.now - 300)
        self.login_codex("acct-2", "two@x.y", self.now - 300, self.now)
        (self.codex / "r.jsonl").write_text(
            codex_meta("acct-1")
            + codex_event(self.now - 500, 100, 0, 1, 99, self.now + 86400)
            + codex_event(self.now - 450, 200, 0, 2, 100, self.now + 86400)
            + codex_event(self.now - 200, 300, 0, 3, 0, self.now + 5 * 86400)
            + codex_event(self.now - 100, 400, 0, 4, 1, self.now + 5 * 86400))
        quota.refresh(self.now)
        accts = {a["label"]: a for a in quota.get_quota(self.now)["accounts"]}
        self.assertEqual(accts["one@x.y"]["quota"]["10080"]["used_percent"], 100)
        self.assertEqual(accts["two@x.y"]["quota"]["10080"]["used_percent"], 1)
        self.assertEqual(accts["two@x.y"]["quota"]["10080"]["resets_at"], self.now + 5 * 86400)

    def test_accounts_idle_over_a_month_are_not_listed(self) -> None:
        old = self.now - 40 * 86400
        (self.codex / "old.jsonl").write_text(
            codex_meta("acct-old") + codex_event(old, 100, 0, 1, 5, old + 86400))
        (self.codex / "new.jsonl").write_text(
            codex_meta("acct-new") + codex_event(self.now - 60, 100, 0, 1, 5, self.now + 86400))
        quota.refresh(self.now)
        result = quota.get_quota(self.now)
        self.assertEqual([a["account_id"] for a in result["accounts"]], ["acct-new"])
        self.assertEqual(result["hidden_idle_accounts"], 1)
        self.assertEqual(result["accounts"][0]["advice"]["rank"], 1)

    def test_no_logs_gives_an_empty_answer(self) -> None:
        quota.refresh(self.now)
        result = quota.get_quota(self.now)
        self.assertEqual((result["accounts"], result["windows"]), ([], []))
        self.assertFalse(result["claude_log_present"])


def week_estimate_test_case() -> tuple:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    codex = root / "codex"
    codex.mkdir(parents=True)
    patches = [
        patch.object(quota, "CODEX_SESSION_DIRS", (codex,)),
        patch.object(quota, "_history_db_path", lambda: root / "test.db"),
    ]
    for p in patches:
        p.start()
    return tmp, codex, patches


class StepEstimateTest(QuotaTest):
    """step_tokens_per_percent: median of single 1% steps, not the whole window."""

    def codex_steps(self, steps: list[tuple], resets: float, extra: str = "") -> None:
        """steps: (at, total_in, used) cumulative, each 1% above the previous."""
        events = codex_meta("acct-1")
        for at, total_in, used in steps:
            events += codex_event(at, total_in, 0, 0, used, resets)
        (self.codex / "r.jsonl").write_text(events + extra)

    def test_six_one_percent_steps_with_equal_tokens(self) -> None:
        resets = self.now + 3 * 86400
        self.codex_steps([(self.now - 60 + i * 10, 1000 * i, 10 + i) for i in range(7)], resets)
        quota.refresh(self.now)
        w = self.window(quota.get_quota(self.now), "codex")
        self.assertEqual(w["clean_steps"], 6)
        self.assertEqual(w["step_tokens_per_percent"], 1000)
        self.assertEqual(w["tokens_per_percent"], 1000)
        self.assertEqual(w["local_percent"], 6.0)      # 6000 tokens / 1000 per 1%
        self.assertEqual(w["other_percent"], 0.0)

    def test_a_five_percent_jump_with_no_local_tokens_counts_as_other(self) -> None:
        resets = self.now + 3 * 86400
        # the jump lands after the last reading: same cumulative totals, so the
        # local logs show no tokens for it
        jump = codex_event(self.now - 60 + 7 * 10, 6000, 0, 0, 21, resets)
        self.codex_steps([(self.now - 60 + i * 10, 1000 * i, 10 + i) for i in range(7)],
                         resets, extra=jump)
        quota.refresh(self.now)
        w = self.window(quota.get_quota(self.now), "codex")
        self.assertEqual((w["used_from"], w["used_to"]), (10, 21))
        self.assertEqual(w["clean_steps"], 6)   # the 5% jump is not a clean step
        self.assertEqual(w["step_tokens_per_percent"], 1000)
        self.assertEqual(w["tokens_per_percent"], 545)  # 6000 / 11, the old average
        self.assertEqual(w["local_percent"], 6.0)
        self.assertAlmostEqual(w["other_percent"], 5.0, delta=0.5)

    def test_stale_readings_only_count_new_highs(self) -> None:
        resets = self.now + 3 * 86400
        # 10, 11, 10, 11, 12: the dips and repeats are stale, only 10->11 and
        # 11->12 are steps
        (self.codex / "r.jsonl").write_text(
            codex_meta("acct-1")
            + codex_event(self.now - 50, 0, 0, 0, 10, resets)
            + codex_event(self.now - 40, 1000, 0, 0, 11, resets)
            + codex_event(self.now - 30, 2000, 0, 0, 10, resets)
            + codex_event(self.now - 20, 3000, 0, 0, 11, resets)
            + codex_event(self.now - 10, 4000, 0, 0, 12, resets))
        quota.refresh(self.now)
        w = self.window(quota.get_quota(self.now), "codex")
        self.assertEqual(w["clean_steps"], 2)
        self.assertIsNone(w["step_tokens_per_percent"])
        self.assertIsNone(w["local_percent"])
        self.assertIsNone(w["other_percent"])

    def test_fewer_than_five_clean_steps_gives_none(self) -> None:
        resets = self.now + 3 * 86400
        self.codex_steps([(self.now - 20 + i * 10, 1000 * i, 10 + i) for i in range(3)], resets)
        quota.refresh(self.now)
        w = self.window(quota.get_quota(self.now), "codex")
        self.assertEqual(w["clean_steps"], 2)
        self.assertIsNone(w["step_tokens_per_percent"])
        self.assertIsNone(w["local_percent"])
        self.assertIsNone(w["other_percent"])

    def test_two_step_weeks_give_the_median_per_percent(self) -> None:
        resets = self.now + 3 * 86400
        # six clean 1% steps per week: 4M tokens per step in week one, 6M in week two
        self.codex_steps([(self.now - 300 + i * 10, 4_000_000 * i, 44 + i) for i in range(7)],
                         resets,
                         extra="".join(
                             codex_event(self.now - 200 + i * 10, 40_000_000 + 6_000_000 * i,
                                          0, 0, 60 + i, resets - 7 * 86400)
                             for i in range(1, 7)))
        quota.refresh(self.now)
        a = quota.get_quota(self.now)["accounts"][0]
        self.assertEqual(a["week_estimate"], {
            "per_percent": 5_000_000, "week_tokens": 500_000_000,
            "basis": "steps", "weeks": 2, "rough": True})

    def test_step_estimate_falls_back_to_a_moved_average(self) -> None:
        resets = self.now + 3 * 86400
        (self.codex / "r.jsonl").write_text(
            codex_meta("acct-1")
            + codex_event(self.now - 200, 0, 0, 0, 25, resets)
            # one 50% jump: too big to be a clean step, so the whole-window
            # average stands in; 400M tokens over 50 points is 8M per 1%
            + codex_event(self.now - 100, 400_000_000, 0, 0, 75, resets))
        quota.refresh(self.now)
        a = quota.get_quota(self.now)["accounts"][0]
        self.assertEqual(a["week_estimate"], {
            "per_percent": 8_000_000, "week_tokens": 800_000_000,
            "basis": "average", "weeks": 1, "rough": True})

    def test_two_weeks_that_moved_far_enough_are_not_rough(self) -> None:
        week = lambda reset, step: {"window_min": quota.WEEK_MIN, "used_from": 0, "used_to": 15,
                                    "step_tokens_per_percent": step, "tokens_per_percent": step}
        est = quota._week_estimate([week(1, 4_000_000), week(2, 6_000_000)])
        self.assertFalse(est["rough"])
        self.assertTrue(quota._week_estimate([week(1, 4_000_000)])["rough"])

    def test_session_windows_are_ignored_for_the_estimate(self) -> None:
        session_reset = self.now + 2 * HOUR + 1234
        self.log.write_text(json.dumps({"ts": self.now - 60, "account_id": "u-1",
                                        "limits": {
            "five_hour": {"used_percentage": 56, "resets_at": session_reset},
            "seven_day": {"used_percentage": 54, "resets_at": self.now + 86400}}}) + "\n")
        quota.refresh(self.now)
        a = quota.get_quota(self.now)["accounts"][0]
        self.assertIsNone(a["week_estimate"])

    def test_a_small_move_with_no_steps_gives_none(self) -> None:
        tmp, codex, patches = week_estimate_test_case()
        try:
            resets = time.time() + 3 * 86400
            (codex / "r.jsonl").write_text(
                codex_meta("acct-1")
                + codex_event(time.time() - 200, 100, 0, 0, 50, resets)
                + codex_event(time.time() - 100, 1_000, 0, 0, 53, resets))
            quota.refresh()
            result = quota.get_quota()
            self.assertEqual(result["accounts"][0]["week_estimate"], None)
        finally:
            for p in patches:
                p.stop()
            tmp.cleanup()

    def test_a_pre_migration_db_gets_the_new_columns_on_connect(self) -> None:
        import sqlite3
        db = self.root / "test.db"
        conn = sqlite3.connect(db)
        conn.execute("""
            CREATE TABLE token_quota_window (
                source TEXT NOT NULL, account_id TEXT NOT NULL,
                window_min INTEGER NOT NULL, resets_at INTEGER NOT NULL,
                plan TEXT NOT NULL DEFAULT '', first_at REAL NOT NULL,
                last_at REAL NOT NULL, used_from REAL NOT NULL, used_to REAL NOT NULL,
                readings INTEGER NOT NULL, input INTEGER NOT NULL,
                output INTEGER NOT NULL, cache_read INTEGER NOT NULL,
                cache_create INTEGER NOT NULL,
                PRIMARY KEY (source, account_id, window_min, resets_at))""")
        conn.close()
        resets = self.now + 3 * 86400
        self.codex_steps([(self.now - 60 + i * 10, 1000 * i, 10 + i) for i in range(7)], resets)
        quota.refresh(self.now)
        w = self.window(quota.get_quota(self.now), "codex")
        self.assertEqual((w["clean_steps"], w["step_tokens_per_percent"]), (6, 1000))


def limit_hit_event(at: float, kind: str = "task_complete",
                    info: str = "usage_limit_exceeded") -> str:
    return json.dumps({"timestamp": iso(at), "type": "event_msg", "payload": {
        "type": kind,
        "error": {"message": "You've hit your usage limit.",
                  "codex_error_info": info}}}) + "\n"


def quota_setup() -> tuple:
    """Same patches as QuotaTest.setUp, without a test case to subclass."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    claude = root / "claude" / "proj"
    codex = root / "codex"
    claude.mkdir(parents=True)
    codex.mkdir()
    log = root / "claude-rate-limits.jsonl"
    quota._codex_cache.clear()
    quota._claude_tails.clear()
    db = root / "test.db"
    patches = [
        patch.object(quota, "PROJECTS_DIR", root / "claude"),
        patch.object(quota, "CODEX_SESSION_DIRS", (codex,)),
        patch.object(quota, "CLAUDE_QUOTA_LOG", log),
        patch.object(quota, "_history_db_path", lambda: db),
        patch.object(accounts, "_history_db_path", lambda: db),
        patch.object(accounts, "CLAUDE_CONFIG", root / "claude.json"),
        patch.object(accounts, "CODEX_AUTH", root / "codex-auth.json"),
    ]
    for item in patches:
        item.start()
    return tmp, root, codex, log, db, patches


class UsageLimitHitTest(unittest.TestCase):
    """A usage_limit_exceeded error event counts as a 100% reading."""

    def setUp(self) -> None:
        self.tmp, self.root, self.codex, self.log, self.db, self.patches = quota_setup()
        self.now = time.time()

    def tearDown(self) -> None:
        for patch in self.patches:
            patch.stop()
        self.tmp.cleanup()

    def window(self, result: dict, source: str) -> dict:
        return next(w for w in result["windows"] if w["source"] == source)

    def account_quota(self, result: dict, account: str, window: str) -> dict:
        return next(a for a in result["accounts"] if a["account_id"] == account)["quota"][window]

    def test_a_limit_hit_fills_the_open_window(self) -> None:
        resets = self.now + 3 * 86400
        (self.codex / "r.jsonl").write_text(
            codex_meta("acct-1")
            + codex_event(self.now - 600, 1000, 800, 10, 98, resets)
            + codex_event(self.now - 300, 3000, 2600, 30, 99, resets + 7)
            + limit_hit_event(self.now))
        quota.refresh(self.now)
        result = quota.get_quota(self.now)
        w = self.window(result, "codex")
        self.assertEqual((w["window_min"], w["used_to"]), (10080, 100))
        q = self.account_quota(result, "acct-1", "10080")
        self.assertEqual((q["used_percent"], q["remaining_percent"]), (100, 0))
        self.assertFalse(q["reset_since_read"])

    def test_a_limit_hit_with_no_earlier_reading_adds_no_window(self) -> None:
        (self.codex / "r.jsonl").write_text(
            codex_meta("acct-1") + limit_hit_event(self.now))
        quota.refresh(self.now)
        result = quota.get_quota(self.now)
        self.assertEqual(result["windows"], [])

    def test_a_limit_hit_after_the_reset_adds_nothing(self) -> None:
        resets = self.now + HOUR
        (self.codex / "r.jsonl").write_text(
            codex_meta("acct-1")
            + codex_event(self.now - 600, 1000, 800, 10, 99, resets)
            + limit_hit_event(resets + HOUR))
        quota.refresh(self.now)
        result = quota.get_quota(self.now)
        w = self.window(result, "codex")
        self.assertEqual(w["used_to"], 99)   # the old window is untouched
        self.assertEqual(result["windows"], [w])

    def test_other_error_infos_are_ignored(self) -> None:
        resets = self.now + 3 * 86400
        (self.codex / "r.jsonl").write_text(
            codex_meta("acct-1")
            + codex_event(self.now - 300, 1000, 800, 10, 99, resets)
            + limit_hit_event(self.now, info="server_overloaded"))
        quota.refresh(self.now)
        w = self.window(quota.get_quota(self.now), "codex")
        self.assertEqual((w["used_to"], w["readings"]), (99, 1))


if __name__ == "__main__":
    unittest.main()
