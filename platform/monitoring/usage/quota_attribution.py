"""Attribute Claude quota rows by their weekly reset window."""

from __future__ import annotations

import bisect
import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable


def attribute_rows(rows: list[dict]) -> list[dict]:
    """Return copies of rows with consistent account identities per weekly track."""
    result = [dict(row) for row in rows]
    tracks = defaultdict(list)
    for row in result:
        weekly = (row.get("limits") or {}).get("seven_day") or {}
        try:
            reset = float(weekly["resets_at"])
            used = float(weekly["used_percentage"])
            stamp = float(row["ts"])
            if not all(math.isfinite(value) for value in (reset, used, stamp)):
                continue
        except (KeyError, TypeError, ValueError):
            continue
        tracks[math.floor(reset / 60 + 0.5)].append(row)

    for track in tracks.values():
        by_account = defaultdict(list)
        for row in track:
            by_account[row.get("account_id") or ""].append(row)
        if len(by_account) < 2:
            continue
        counts = Counter({account: len(items) for account, items in by_account.items()})
        largest = counts.most_common()
        if len(largest) > 1 and largest[0][1] == largest[1][1]:
            for row in track:
                row["ambiguous"] = True
            continue
        winner = largest[0][0]
        reference = by_account[winner]
        differences = []
        for account, items in by_account.items():
            if account == winner:
                continue
            for row in items:
                nearest = min(reference, key=lambda ref: abs(float(ref["ts"]) - float(row["ts"])))
                differences.append(abs(float(row["limits"]["seven_day"]["used_percentage"])
                                       - float(nearest["limits"]["seven_day"]["used_percentage"])))
        if statistics.median(differences) > 3:
            for row in track:
                row["ambiguous"] = True
            continue
        identity = max(reference, key=lambda row: float(row["ts"]))
        for row in track:
            if row.get("account_id") != winner:
                row["original_account_id"] = row.get("account_id")
                row["account_id"] = winner
                row["label"] = identity.get("label")
                row["plan"] = identity.get("plan")
                row["relabeled"] = True
    return result


ACTIVE_WINDOW_SECONDS = 6 * 3600


def active_account_index(rows: list[dict]) -> Callable[[float], str | None]:
    """Sort the rows once; the returned lookup finds the nearest row by bisection.

    A diagnosis run looks up one time per usage event (tens of thousands), so a
    linear scan per lookup made it 5x slower (2026-11-19: 15.8 s against 2.8 s).
    """
    ordered = sorted(rows, key=lambda row: float(row["ts"]))
    stamps = [float(row["ts"]) for row in ordered]

    def lookup(at: float) -> str | None:
        if not ordered:
            return None
        index = bisect.bisect_left(stamps, at)
        candidates = [i for i in (index - 1, index) if 0 <= i < len(ordered)]
        nearest = min(candidates, key=lambda i: abs(stamps[i] - at))
        if abs(stamps[nearest] - at) > ACTIVE_WINDOW_SECONDS:
            return None
        return ordered[nearest].get("account_id")

    return lookup


def active_account(rows: list[dict], at: float) -> str | None:
    """Return the closest attributed account within six hours of a timestamp."""
    return active_account_index(rows)(at)
