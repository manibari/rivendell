"""Tests for code_run_liveness: python3 -m unittest code_run_liveness_test (in scripts/)."""
import unittest

from code_run_liveness import Sample, moved, parse_cputime, parse_nettop

NETTOP = """time,,interface,state,bytes_in,bytes_out,rx_dupe
15:42:24.511587,codex.46784,,,19075,169431,23
15:42:24.511588,codex.47049,,,0,0,0
15:42:24.511617,node.11531,,,16894,37255,0
"""


class ParseTest(unittest.TestCase):
    def test_cputime_formats(self):
        self.assertAlmostEqual(parse_cputime("0:00.49"), 0.49)
        self.assertAlmostEqual(parse_cputime("12:03.50"), 723.5)
        self.assertAlmostEqual(parse_cputime("1:02:03"), 3723)
        self.assertEqual(parse_cputime("??"), 0.0)

    def test_nettop_sums_only_the_run_pids(self):
        self.assertEqual(parse_nettop(NETTOP, [46784, 11531]), 19075 + 16894)
        self.assertEqual(parse_nettop(NETTOP, [99999]), 0)


class MovedTest(unittest.TestCase):
    def test_long_thinking_counts_as_moving(self):
        # Measured 2026-10-12: 75 s of thinking, no event, +0.26 s CPU.
        before, after = Sample(100.0, 0.88, None), Sample(100.0, 1.14, None)
        self.assertEqual(moved(before, after, 75), ["cpu"])

    def test_idle_timers_are_a_stall(self):
        # The idle process after a run: about 0.012 s per minute.
        before, after = Sample(100.0, 0.04, 0), Sample(100.0, 0.052, 0)
        self.assertEqual(moved(before, after, 60), [])

    def test_an_event_or_bytes_count_as_moving(self):
        self.assertEqual(moved(Sample(1.0, 0, None), Sample(2.0, 0, None), 60), ["events"])
        self.assertEqual(moved(Sample(1.0, 0, 10), Sample(1.0, 0, 11), 60), ["network"])

    def test_unknown_bytes_do_not_count(self):
        self.assertEqual(moved(Sample(1.0, 0, None), Sample(1.0, 0, 500), 60), [])


if __name__ == "__main__":
    unittest.main()
