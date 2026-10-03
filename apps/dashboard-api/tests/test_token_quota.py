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
        self.assertEqual(q["resets_at"], quota._hour(resets))
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
        self.assertEqual(accts["two@x.y"]["quota"]["10080"]["resets_at"],
                         quota._hour(self.now + 5 * 86400))

    def test_no_logs_gives_an_empty_answer(self) -> None:
        quota.refresh(self.now)
        result = quota.get_quota(self.now)
        self.assertEqual((result["accounts"], result["windows"]), ([], []))
        self.assertFalse(result["claude_log_present"])


if __name__ == "__main__":
    unittest.main()
