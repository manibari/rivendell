"""Regression tests for weekly quota attribution."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dashboard-legacy"))
from lib.tokens_quota_attribution import active_account, attribute_rows


def row(at, account, used, reset=100000):
    return {"ts": at, "account_id": account, "label": account + "-label",
            "plan": account + "-plan", "limits": {"seven_day": {
                "used_percentage": used, "resets_at": reset}}}


def test_alternating_labels_one_rising_series():
    rows = [row(1000 + i * 60, "a" if i % 2 == 0 else "b", 7 + i)
            for i in range(11)]
    result = attribute_rows(rows)
    assert {item["account_id"] for item in result} == {"a"}
    assert sum(bool(item.get("relabeled")) for item in result) == 5
    assert result[1]["original_account_id"] == "b"
    assert result[1]["label"] == "a-label"
    assert rows[1]["account_id"] == "b"
    assert active_account(result, 1120) == "a"
    assert active_account(result, 1120 + 7 * 3600) is None


def test_distinct_series_with_same_reset_are_ambiguous():
    rows = [row(1000, "a", 10), row(1060, "b", 40), row(1120, "a", 11)]
    result = attribute_rows(rows)
    assert all(item["ambiguous"] for item in result)
    assert [item["account_id"] for item in result] == ["a", "b", "a"]


def test_tie_is_ambiguous_and_no_weekly_row_is_unchanged():
    rows = [row(1000, "a", 10), row(1060, "b", 10),
            {"ts": 1120, "account_id": "c", "label": "c", "limits": {}}]
    result = attribute_rows(rows)
    assert result[0]["ambiguous"] and result[1]["ambiguous"]
    assert result[2] == rows[2]


def test_reset_times_within_one_minute_round_to_same_track():
    rows = [row(1000, "a", 10, 100001), row(1060, "b", 11, 100020),
            row(1120, "a", 12, 100005)]
    result = attribute_rows(rows)
    assert [item["account_id"] for item in result] == ["a", "a", "a"]
