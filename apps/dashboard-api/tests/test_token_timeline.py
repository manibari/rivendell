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
from lib import tokens_timeline as timeline


def iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def claude_row(epoch: float, request: str, output: int, pad: int = 0,
               model: str = "claude-opus-5-5") -> str:
    return json.dumps({
        "timestamp": iso(epoch), "requestId": request, "sessionId": "s1",
        "message": {"role": "assistant", "model": model, "content": "x" * pad, "usage": {
            "input_tokens": 1, "output_tokens": output,
            "cache_read_input_tokens": 10, "cache_creation_input_tokens": 5}},
    }) + "\n"


def codex_row(epoch: float, total_in: int, total_out: int, pad: int = 0) -> str:
    return json.dumps({
        "timestamp": iso(epoch), "type": "event_msg", "pad": "x" * pad,
        "payload": {"type": "token_count", "info": {"total_token_usage": {
            "input_tokens": total_in, "cached_input_tokens": 0,
            "output_tokens": total_out, "total_tokens": total_in + total_out}}},
    }) + "\n"


def codex_meta(account: str, model: str = "gpt-5.5") -> str:
    return json.dumps({"timestamp": iso(0), "type": "session_meta",
                       "payload": {"id": "c1", "creator_account_id": account,
                                   "model": model}}) + "\n"


def codex_turn(epoch: float, model: str) -> str:
    return json.dumps({"timestamp": iso(epoch), "type": "turn_context",
                       "payload": {"model": model}}) + "\n"


class TimelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.claude = root / "claude" / "proj"
        self.codex = root / "codex"
        self.claude.mkdir(parents=True)
        self.codex.mkdir()
        timeline._TAILS.clear()
        self.patches = [
            patch.object(timeline, "PROJECTS_DIR", root / "claude"),
            patch.object(timeline, "CODEX_SESSION_DIRS", (self.codex,)),
            patch.object(accounts, "_history_db_path", lambda: root / "test.db"),
            patch.object(accounts, "CLAUDE_CONFIG", root / "claude.json"),
            patch.object(accounts, "CODEX_AUTH", root / "codex-auth.json"),
        ]
        self.root = root
        for p in self.patches:
            p.start()
        self.now = time.time()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        timeline._TAILS.clear()
        self.tmp.cleanup()

    def series(self, result: dict, series_id: str) -> dict:
        return next(s for s in result["series"] if s["id"] == series_id)

    def test_minute_buckets_are_zero_filled_and_split_by_minute(self) -> None:
        (self.claude / "a.jsonl").write_text(
            claude_row(self.now - 130, "r1", 100) + claude_row(self.now - 10, "r2", 40))
        result = timeline.get_timeline("minute", 10)
        self.assertEqual(len(result["points"]), 10)
        filled = [p for p in result["points"] if p["series"]]
        self.assertEqual(len(filled), 2)
        self.assertEqual(self.series(result, "claude:")["totals"]["output"], 140)
        self.assertEqual(self.series(result, "claude:")["totals"]["requests"], 2)

    def test_repeated_request_rows_count_once_last_wins(self) -> None:
        (self.claude / "a.jsonl").write_text(
            claude_row(self.now - 20, "r1", 5) + claude_row(self.now - 19, "r1", 50))
        totals = self.series(timeline.get_timeline("minute", 5), "claude:")["totals"]
        self.assertEqual((totals["requests"], totals["output"]), (1, 50))

    def test_poll_picks_up_appended_rows_and_skips_a_partial_row(self) -> None:
        path = self.claude / "a.jsonl"
        path.write_text(claude_row(self.now - 30, "r1", 10))
        timeline.get_timeline("minute", 5)
        half = claude_row(self.now - 5, "r3", 99)
        with open(path, "a") as f:
            f.write(claude_row(self.now - 8, "r2", 20) + half[:40])
        totals = self.series(timeline.get_timeline("minute", 5), "claude:")["totals"]
        self.assertEqual((totals["requests"], totals["output"]), (2, 30))
        with open(path, "a") as f:
            f.write(half[40:])
        totals = self.series(timeline.get_timeline("minute", 5), "claude:")["totals"]
        self.assertEqual((totals["requests"], totals["output"]), (3, 129))

    def test_rows_before_the_window_are_left_out_of_a_large_file(self) -> None:
        old = "".join(claude_row(self.now - 7200 + i, f"old{i}", 1, pad=4000) for i in range(60))
        (self.claude / "a.jsonl").write_text(old + claude_row(self.now - 30, "new", 7))
        totals = self.series(timeline.get_timeline("minute", 10), "claude:")["totals"]
        self.assertEqual((totals["requests"], totals["output"]), (1, 7))

    def test_codex_series_is_per_account_and_counts_deltas(self) -> None:
        (self.codex / "rollout.jsonl").write_text(
            codex_meta("acct-1") + codex_row(self.now - 90, 100, 10)
            + codex_row(self.now - 20, 160, 40))
        result = timeline.get_timeline("minute", 10)
        entry = self.series(result, "codex:acct-1")
        self.assertEqual(entry["account"], "acct-1")
        self.assertEqual((entry["totals"]["input"], entry["totals"]["output"]), (160, 40))

    def test_codex_started_mid_file_takes_baseline_from_before_the_window(self) -> None:
        old = "".join(codex_row(self.now - 7200 + i, 1000 * (i + 1), 0, pad=4000)
                      for i in range(60))
        (self.codex / "rollout.jsonl").write_text(
            codex_meta("acct-1") + old + codex_row(self.now - 40, 60_500, 0)
            + codex_row(self.now - 20, 60_900, 30))
        entry = self.series(timeline.get_timeline("minute", 10), "codex:acct-1")
        # 60_000 (last counter before the window) is the baseline, so the first
        # in-window step 60_000 -> 60_500 is counted too.
        self.assertEqual(entry["totals"]["input"], 900)
        self.assertEqual(entry["totals"]["output"], 30)

    def test_codex_cache_write_is_netted_out_of_input(self) -> None:
        row = json.loads(codex_row(self.now - 20, 1000, 10))
        row["payload"]["info"]["total_token_usage"].update(
            cached_input_tokens=600, cache_write_input_tokens=300)
        (self.codex / "rollout.jsonl").write_text(codex_meta("acct-1") + json.dumps(row) + "\n")
        t = self.series(timeline.get_timeline("minute", 10), "codex:acct-1")["totals"]
        self.assertEqual((t["input"], t["cache_read"], t["cache_create"], t["output"]),
                         (100, 600, 300, 10))

    def test_rate_and_breakdown_count_all_four_categories(self) -> None:
        (self.claude / "a.jsonl").write_text(claude_row(self.now - 10, "r1", 4))
        entry = self.series(timeline.get_timeline("minute", 5), "claude:")
        # input 1 + output 4 + cache_read 10 + cache_create 5
        self.assertEqual(entry["breakdown"][0]["tokens"], 20)
        self.assertEqual(entry["breakdown"][0]["output"], 4)
        self.assertEqual(entry["breakdown"][0]["cache_tokens"], 10)
        self.assertEqual(entry["tokens_per_minute"], 4)  # 20 over a 5-minute window

    def login(self, email: str, uuid: str, at: float) -> None:
        (self.root / "claude.json").write_text(json.dumps(
            {"oauthAccount": {"accountUuid": uuid, "emailAddress": email}}))
        accounts.observe(at)

    def test_codex_rows_follow_the_login_after_a_switch(self) -> None:
        (self.root / "codex-auth.json").write_text(json.dumps({"tokens": {"account_id": "acct-2"}}))
        for at in range(int(self.now - 60), int(self.now), 20):
            accounts.observe(at)
        (self.codex / "rollout.jsonl").write_text(
            codex_meta("acct-1") + codex_row(self.now - 300, 100, 10)
            + codex_row(self.now - 200, 150, 20) + codex_row(self.now - 30, 400, 50))
        result = timeline.get_timeline("minute", 10)
        # before any sighting: the creator; inside acct-2's sighting: acct-2
        self.assertEqual(self.series(result, "codex:acct-1")["totals"]["output"], 20)
        self.assertEqual(self.series(result, "codex:acct-2")["totals"]["output"], 30)

    def test_claude_rows_without_a_login_record_stay_unattributed(self) -> None:
        (self.claude / "a.jsonl").write_text(claude_row(self.now - 10, "r1", 1))
        entry = self.series(timeline.get_timeline("minute", 5), "claude:")
        self.assertIsNone(entry["account"])
        self.assertIsNone(entry["label"])

    def test_claude_rows_follow_the_login_that_covers_their_time(self) -> None:
        self.login("a@example.com", "uuid-a", self.now - 400)
        self.login("a@example.com", "uuid-a", self.now - 380)
        self.login("b@example.com", "uuid-b", self.now - 200)
        self.login("b@example.com", "uuid-b", self.now - 170)
        (self.claude / "a.jsonl").write_text(
            claude_row(self.now - 1000, "before", 1)     # nobody was watching yet
            + claude_row(self.now - 390, "a1", 10)
            + claude_row(self.now - 180, "b1", 200)
            + claude_row(self.now - 20, "late", 3000))   # past the last sighting + grace
        result = timeline.get_timeline("minute", 30)
        self.assertEqual(self.series(result, "claude:uuid-a")["totals"]["output"], 10)
        self.assertEqual(self.series(result, "claude:uuid-a")["label"], "a@example.com")
        self.assertEqual(self.series(result, "claude:uuid-b")["totals"]["output"], 200)
        self.assertEqual(self.series(result, "claude:")["totals"]["output"], 3001)

    def test_a_gap_in_sightings_opens_a_new_interval(self) -> None:
        self.login("a@example.com", "uuid-a", self.now - 5000)
        self.login("a@example.com", "uuid-a", self.now - 100)
        spans = accounts.intervals("claude", self.now - 6000)
        self.assertEqual(len(spans), 2)
        self.assertIsNone(accounts.account_at(spans, self.now - 2000))

    def test_group_by_model_and_account_breakdown(self) -> None:
        (self.claude / "a.jsonl").write_text(
            claude_row(self.now - 30, "r1", 10, model="claude-opus-5-5")
            + claude_row(self.now - 20, "r2", 5, model="claude-fable-5-1"))
        (self.codex / "rollout.jsonl").write_text(
            codex_meta("acct-1", "gpt-5.5") + codex_row(self.now - 90, 100, 10)
            + codex_turn(self.now - 50, "gpt-6-sol") + codex_row(self.now - 20, 160, 40))
        by_model = timeline.get_timeline("minute", 10, "model")
        self.assertEqual(
            {s["id"] for s in by_model["series"]},
            {"model:claude-opus-5-5", "model:claude-fable-5-1", "model:gpt-5.5", "model:gpt-6-sol"})
        self.assertEqual(self.series(by_model, "model:gpt-6-sol")["totals"]["output"], 30)
        by_account = timeline.get_timeline("minute", 10)
        models = [p["model"] for p in self.series(by_account, "claude:")["breakdown"]]
        self.assertEqual(models, ["claude-opus-5-5", "claude-fable-5-1"])

    def test_span_is_capped_and_bucket_is_validated(self) -> None:
        self.assertEqual(timeline.get_timeline("hour", 9999)["span"], timeline.BUCKETS["hour"][2])
        with self.assertRaises(ValueError):
            timeline.get_timeline("second")
        with self.assertRaises(ValueError):
            timeline.get_timeline("minute", 5, "project")


if __name__ == "__main__":
    unittest.main()
