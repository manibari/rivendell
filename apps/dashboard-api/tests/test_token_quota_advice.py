import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import LIB_DIR  # noqa: F401  (puts dashboard-legacy on sys.path)
from lib.tokens_quota_advice import advise

NOW = 1_800_000_000.0
HOUR, DAY = 3600, 86400


def reading(used: float, resets_in: float, first_ago: float = 0, used_from: float | None = None,
            read_ago: float = 0, reset_since_read: bool = False) -> dict:
    return {"used_percent": used, "remaining_percent": max(0.0, 100 - used),
            "resets_at": NOW + resets_in, "read_at": NOW - read_ago,
            "reset_since_read": reset_since_read,
            "window_first_at": NOW - first_ago,
            "window_used_from": used if used_from is None else used_from}


def account(source: str, name: str, week: dict, session: dict | None = None) -> dict:
    quota = {"10080": week}
    if session:
        quota["300"] = session
    return {"source": source, "account_id": name, "label": name, "quota": quota}


class AdviceTest(unittest.TestCase):
    def test_soonest_reset_goes_first_and_used_up_is_blocked(self) -> None:
        later = account("codex", "later", reading(10, 6 * DAY))
        sooner = account("codex", "sooner", reading(50, 2 * DAY))
        empty = account("codex", "empty", reading(100, 5 * DAY))
        advise([later, sooner, empty], NOW)
        self.assertEqual((sooner["advice"]["rank"], later["advice"]["rank"]), (1, 2))
        self.assertEqual(empty["advice"]["status"], "blocked")
        self.assertEqual(empty["advice"]["blocked_by"], "week")
        self.assertEqual(empty["advice"]["blocked_until"], NOW + 5 * DAY)

    def test_claude_session_limit_blocks_until_the_session_resets(self) -> None:
        a = account("claude", "a", reading(10, 6 * DAY), session=reading(100, 2 * HOUR))
        b = account("claude", "b", reading(20, 6 * DAY + HOUR), session=reading(5, 3 * HOUR))
        advise([a, b], NOW)
        self.assertEqual((a["advice"]["status"], a["advice"]["blocked_by"]), ("blocked", "session"))
        self.assertEqual(a["advice"]["blocked_until"], NOW + 2 * HOUR)
        self.assertEqual(b["advice"]["rank"], 1)

    def test_rate_projects_when_it_runs_out_and_the_pace_to_last(self) -> None:
        # 20% -> 40% over 10 hours = 2%/h; 60% left runs out 30h after the reading
        fast = account("codex", "fast", reading(40, 6 * DAY, first_ago=10 * HOUR, used_from=20))
        advise([fast], NOW)
        adv = fast["advice"]
        self.assertEqual(adv["rate_per_hour"], 2.0)
        self.assertEqual(adv["exhaust_at"], NOW + 30 * HOUR)
        self.assertEqual(adv["pace_per_day"], 10.0)   # 60% over 6 days

    def test_slow_use_that_lasts_to_the_reset_has_no_exhaust_time(self) -> None:
        slow = account("codex", "slow", reading(11, 2 * DAY, first_ago=10 * HOUR, used_from=10))
        advise([slow], NOW)
        self.assertIsNone(slow["advice"]["exhaust_at"])

    def test_a_reset_window_is_full_and_least_urgent(self) -> None:
        stale = account("codex", "stale", reading(0, -DAY, reset_since_read=True))
        live = account("codex", "live", reading(30, 5 * DAY))
        advise([stale, live], NOW)
        self.assertEqual((live["advice"]["rank"], stale["advice"]["rank"]), (1, 2))

    def test_unknown_accounts_get_no_rank(self) -> None:
        nobody = {"source": "codex", "account_id": None, "label": None,
                  "quota": {"10080": reading(0, DAY)}}
        unread = {"source": "claude", "account_id": "x", "label": "x", "quota": {}}
        advise([nobody, unread], NOW)
        self.assertEqual([nobody["advice"]["status"], unread["advice"]["status"]],
                         ["unknown", "unknown"])


if __name__ == "__main__":
    unittest.main()
