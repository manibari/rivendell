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


def claude_row(at: float, request: str, output: int, model: str = "claude-opus-5-5") -> str:
    return json.dumps({
        "timestamp": iso(at), "requestId": request,
        "message": {"model": model, "usage": {
            "input_tokens": 1, "output_tokens": output,
            "cache_read_input_tokens": 100, "cache_creation_input_tokens": 10}},
    }) + "\n"


def codex_turn(at: float, model: str) -> str:
    return json.dumps({"timestamp": iso(at), "type": "event_msg",
                       "payload": {"type": "turn_context", "model": model}}) + "\n"


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

    def test_two_step_weeks_use_the_current_cycle_per_percent(self) -> None:
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
        # The older cycle has a different value and does not affect this one.
        self.assertEqual(a["week_estimate"], {
            "per_percent": 4_000_000, "week_tokens": 400_000_000,
            "basis": "top_steps", "steps": 6, "rough": True, "model": None,
            "by_model": []})
        self.assertEqual(a["week_estimate_resets_at"], resets)
        self.assertEqual({w["week_estimate"]["per_percent"] for w in quota.get_quota(self.now)["windows"]},
                         {4_000_000, 6_000_000})

    def test_fourteen_steps_use_the_ten_largest_ratios(self) -> None:
        resets = self.now + 3 * 86400
        totals = [0]
        for ratio in range(1, 15):
            totals.append(totals[-1] + ratio * 1000)
        self.codex_steps([(self.now - 150 + i * 10, total, 10 + i)
                          for i, total in enumerate(totals)], resets)
        quota.refresh(self.now)
        w = self.window(quota.get_quota(self.now), "codex")
        self.assertEqual(w["step_ratios"], [i * 1000 for i in range(1, 15)])
        self.assertEqual(w["week_estimate"]["per_percent"], 9500)
        self.assertEqual(w["week_estimate"]["steps"], 10)
        self.assertFalse(w["week_estimate"]["rough"])

    def test_closed_cycle_keeps_its_estimate_but_account_has_none(self) -> None:
        resets = self.now + HOUR
        self.codex_steps([(self.now - 60 + i * 10, 1000 * i, 10 + i)
                          for i in range(7)], resets)
        quota.refresh(self.now)
        result = quota.get_quota(resets)
        self.assertEqual(self.window(result, "codex")["week_estimate"]["per_percent"], 1000)
        self.assertIsNone(result["accounts"][0]["week_estimate"])
        self.assertIsNone(result["accounts"][0]["week_estimate_resets_at"])

    def test_old_row_uses_model_ratios_when_step_ratios_are_empty(self) -> None:
        import sqlite3
        resets = self.now + 3 * 86400
        self.codex_steps([(self.now - 60 + i * 10, 1000 * i, 10 + i)
                          for i in range(7)], resets)
        quota.refresh(self.now)
        with sqlite3.connect(self.root / "test.db") as conn:
            conn.execute("UPDATE token_quota_window SET step_ratios = '[]', "
                         "step_ratios_by_model = ?", (json.dumps({"model-a": [3000] * 5}),))
        w = self.window(quota.get_quota(self.now), "codex")
        self.assertEqual(w["week_estimate"]["per_percent"], 3000)
        self.assertEqual(w["week_estimate"]["basis"], "top_steps")

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
        # The 50% jump is not a clean step, so no per-model entry; the jump's
        # tokens still count toward the account's model.
        self.assertEqual(a["week_estimate"], {
            "per_percent": 8_000_000, "week_tokens": 800_000_000,
            "basis": "average", "steps": 0, "rough": True,
            "model": None, "by_model": []})

    def test_ten_clean_ratios_are_not_rough(self) -> None:
        window = {"step_ratios": [1000] * 10, "step_ratios_by_model": {},
                  "tokens_per_percent": 1000, "used_from": 0, "used_to": 10,
                  "model_tokens": {}, "main_model": None}
        est = quota._cycle_estimate(window)
        self.assertEqual(est["steps"], 10)
        self.assertFalse(est["rough"])

    def test_fewer_than_ten_clean_ratios_are_rough(self) -> None:
        window = {"step_ratios": [1000, 2000, 3000], "step_ratios_by_model": {},
                  "tokens_per_percent": 1000, "used_from": 0, "used_to": 3,
                  "model_tokens": {}, "main_model": None}
        est = quota._cycle_estimate(window)
        self.assertEqual((est["per_percent"], est["steps"]), (2000, 3))
        self.assertTrue(est["rough"])

    def test_session_windows_are_ignored_for_the_estimate(self) -> None:
        session_reset = self.now + 2 * HOUR + 1234
        self.log.write_text(json.dumps({"ts": self.now - 60, "account_id": "u-1",
                                        "limits": {
            "five_hour": {"used_percentage": 56, "resets_at": session_reset},
            "seven_day": {"used_percentage": 54, "resets_at": self.now + 86400}}}) + "\n")
        quota.refresh(self.now)
        a = quota.get_quota(self.now)["accounts"][0]
        self.assertIsNone(a["week_estimate"])
        session = next(w for w in quota.get_quota(self.now)["windows"] if w["window_min"] == 300)
        self.assertIsNone(session["week_estimate"])

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
        # the per-model columns migrated too, and the old rows decoded fine
        conn = sqlite3.connect(db)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(token_quota_window)")}
        conn.close()
        self.assertIn("step_ratios_by_model", cols)
        self.assertIn("step_ratios", cols)
        self.assertIn("model_tokens", cols)
        self.assertEqual(w["model_tokens"], {})
        self.assertEqual(w["step_ratios_by_model"], {})
        self.assertEqual(w["step_ratios"], [1000] * 6)
        self.assertIsNone(w["main_model"])


class ModelSplitTest(QuotaTest):
    """The weekly estimate split by the model that spent each clean 1% step."""

    def test_one_model_week_gives_a_model_basis_estimate(self) -> None:
        resets = self.now + 3 * 86400
        # six clean 1% steps, all after a turn_context on model A
        events = codex_meta("acct-1") + codex_turn(self.now - 300, "model-a")
        for i in range(7):
            events += codex_event(self.now - 300 + i * 10, 1000 * i, 0, 0, 10 + i, resets)
        (self.codex / "r.jsonl").write_text(events)
        _, usage = quota._parse_codex(self.codex / "r.jsonl")
        self.assertEqual({u[6] for u in usage}, {"model-a"})
        quota.refresh(self.now)
        result = quota.get_quota(self.now)
        w = self.window(result, "codex")
        self.assertEqual(w["model_tokens"], {"model-a": 6000})
        self.assertEqual(w["step_ratios_by_model"], {"model-a": [1000] * 6})
        self.assertEqual(w["main_model"], "model-a")
        est = result["accounts"][0]["week_estimate"]
        self.assertEqual((est["basis"], est["model"]), ("top_steps", "model-a"))
        self.assertEqual(est["by_model"], [{
            "model": "model-a", "per_percent": 1000, "week_tokens": 100_000,
            "steps": 6, "rough": True}])
        self.assertEqual((est["per_percent"], est["week_tokens"]), (1000, 100_000))

    def test_two_models_split_by_model_and_the_bigger_one_leads(self) -> None:
        resets = self.now + 3 * 86400
        # five clean 1% steps on model A at 4M each, then six on model B at 1M
        events = codex_meta("acct-1") + codex_turn(self.now - 600, "model-a")
        for i in range(6):
            events += codex_event(self.now - 600 + i * 10, 4_000_000 * i, 0, 0, 40 + i, resets)
        events += codex_turn(self.now - 540, "model-b")
        for i in range(1, 7):
            events += codex_event(self.now - 540 + i * 10, 20_000_000 + 1_000_000 * i,
                                  0, 0, 45 + i, resets)
        (self.codex / "r.jsonl").write_text(events)
        quota.refresh(self.now)
        result = quota.get_quota(self.now)
        w = self.window(result, "codex")
        self.assertEqual(w["model_tokens"], {"model-a": 20_000_000, "model-b": 6_000_000})
        est = result["accounts"][0]["week_estimate"]
        by_model = {e["model"]: e for e in est["by_model"]}
        self.assertEqual(set(by_model), {"model-a", "model-b"})
        self.assertEqual(by_model["model-a"]["per_percent"], 4_000_000)
        self.assertEqual(by_model["model-b"]["per_percent"], 1_000_000)
        self.assertEqual((by_model["model-a"]["steps"], by_model["model-b"]["steps"]), (5, 6))
        self.assertEqual(est["model"], "model-a")   # 20M of its tokens vs 6M
        self.assertEqual(est["basis"], "top_steps")
        self.assertEqual((est["per_percent"], est["week_tokens"]), (2_500_000, 250_000_000))
        self.assertEqual([e["model"] for e in est["by_model"]],
                         ["model-a", "model-b"])   # sorted by tokens desc

    def test_a_step_split_between_two_models_counts_for_neither(self) -> None:
        resets = self.now + 3 * 86400
        # each clean 1% step is half model A, half model B (the token events
        # carry no reading; the reading comes after both), so no model
        # reaches the 80% bar and the step feeds the all-model ratio only
        events = codex_meta("acct-1")
        events += codex_event(self.now - 600, 0, 0, 0, 10, resets)
        total = 0
        for k in range(6):
            for m in ("model-a", "model-b"):
                events += codex_turn(self.now - 590 + k * 100, m)
                total += 1_000_000
                events += codex_event(self.now - 590 + k * 100, total, 0, 0, None, resets)
            events += codex_event(self.now - 560 + k * 100, total, 0, 0, 11 + k, resets)
        (self.codex / "r.jsonl").write_text(events)
        quota.refresh(self.now)
        result = quota.get_quota(self.now)
        w = self.window(result, "codex")
        self.assertEqual(w["clean_steps"], 6)
        self.assertEqual(w["step_tokens_per_percent"], 2_000_000)
        self.assertEqual(w["step_ratios_by_model"], {})
        self.assertEqual(w["model_tokens"], {"model-a": 6_000_000, "model-b": 6_000_000})
        est = result["accounts"][0]["week_estimate"]
        self.assertEqual(est["by_model"], [])
        self.assertEqual(est["basis"], "top_steps")     # the mixed result stands
        self.assertEqual(est["per_percent"], 2_000_000)
        self.assertIn(est["model"], ("model-a", "model-b"))

    def test_claude_rows_carry_the_model_and_synthetic_is_unknown(self) -> None:
        resets, resets2 = self.now + 86400, self.now + 86400 + 3600
        self.log.write_text(
            quota_row(self.now - 950, "", 5, resets2)
            + quota_row(self.now - 850, "", 6, resets2)
            + quota_row(self.now - 300, "", 10, resets)
            + quota_row(self.now - 100, "", 11, resets))
        (self.claude / "a.jsonl").write_text(
            claude_row(self.now - 900, "r1", 3, model="<synthetic>")
            + claude_row(self.now - 250, "r0", 5))
        quota.refresh(self.now)
        windows = {w["resets_at"]: w for w in quota.get_quota(self.now)["windows"]
                   if w["source"] == "claude"}
        w_opus = windows[quota._hour(resets)]
        w_unknown = windows[quota._hour(resets2)]
        self.assertEqual(w_opus["model_tokens"], {"claude-opus-5-5": 116})
        self.assertEqual(w_opus["step_ratios_by_model"], {"claude-opus-5-5": [116]})
        self.assertEqual(w_opus["main_model"], "claude-opus-5-5")
        # <synthetic> is not a real model: unknown rows count for no model
        self.assertEqual(w_unknown["model_tokens"], {})
        self.assertIsNone(w_unknown["main_model"])
        self.assertEqual(w_unknown["step_ratios_by_model"], {})
        self.assertIsNone(w_unknown["main_model"])
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
