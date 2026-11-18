"""Redirect and layout control contract tests."""

import json
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT))
from feature_tree import fmt, report, schema, screens

FIXTURE = Path(__file__).parent / "fixtures" / "py" / "tree.json"


def tree():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def entry(screen, controls=None, **extra):
    return {"module": "demo", "screen": screen, "state": "default", "reached": True,
            "controls": controls or [], **extra}


class RedirectSchemaTests(unittest.TestCase):
    def test_redirect_rules_and_samples(self):
        value = tree()
        screen = value["modules"][0]["screens"][0]
        screen["route"] = "/old/[label]"
        screen["redirect"] = "/new/[label]"
        screen["sample"] = {"label": "demo"}
        screen["controls"] = []
        self.assertEqual(schema.validate(value), [])
        screen["controls"] = [{"id": "item"}]
        self.assertIn("REDIRECT_WITH_CONTROLS", {row["code"] for row in schema.validate(value)})
        screen["controls"] = []
        screen["states"] = [{"id": "open", "steps": []}]
        self.assertIn("REDIRECT_WITH_CONTROLS", {row["code"] for row in schema.validate(value)})
        screen["states"] = []
        screen["redirect"] = "new/[label]"
        self.assertIn("REDIRECT_PATH", {row["code"] for row in schema.validate(value)})
        screen["redirect"] = "/new/[missing]"
        self.assertIn("SAMPLE_MISSING", {row["code"] for row in schema.validate(value)})
        screen["layout"] = True
        screen.pop("route")
        self.assertIn("LAYOUT_REDIRECT", {row["code"] for row in schema.validate(value)})

    def test_format_places_redirect_after_route(self):
        value = {"controls": [], "redirect": "/new", "route": "/old", "id": "main"}
        self.assertEqual(list(fmt.ordered(value, "screens")), ["id", "route", "redirect", "controls"])


class RedirectCheckTests(unittest.TestCase):
    def setUp(self):
        self.value = {"modules": [{"id": "demo", "screens": [
            {"id": "old", "route": "/old/[label]", "redirect": "/new/[label]",
             "sample": {"label": "a b"}, "controls": []}]}]}

    def check(self, entries):
        return screens.check(self.value, {"schema": 1, "screens": entries})

    def test_matching_path_ignores_origin_query_and_trailing_slash(self):
        scanned = entry("old", [{"role": "button", "name": ""}, {"role": "link", "name": "target"}],
                        final_url="https://elsewhere.test/new/a%20b/?q=1")
        self.assertEqual(self.check([scanned]), [])

    def test_wrong_path(self):
        rows = self.check([entry("old", final_url="http://localhost/wrong?q=1")])
        self.assertEqual([row["code"] for row in rows], ["REDIRECT_BROKEN"])
        self.assertIn("/new/a%20b", rows[0]["detail"])
        self.assertIn("/wrong", rows[0]["detail"])
        self.assertEqual(rows[0]["severity"], "red")

    def test_unchecked_old_scan_not_reached_and_missing_entry(self):
        for entries in ([entry("old")], [entry("old", reached=False, final_url="http://localhost/new/a%20b")], []):
            with self.subTest(entries=entries):
                rows = self.check(entries)
                self.assertEqual([row["code"] for row in rows], ["REDIRECT_UNCHECKED"])
                self.assertEqual(rows[0]["severity"], "yellow")

    def test_report_explanations(self):
        for code in ("REDIRECT_BROKEN", "REDIRECT_UNCHECKED", "REDIRECT_WITH_CONTROLS"):
            self.assertIn(code, report.EXPLANATIONS)


class UnlabeledLayoutTests(unittest.TestCase):
    def test_layout_control_is_reported_once_for_three_screens(self):
        value = {"modules": [{"id": "demo", "screens": [
            {"id": "shell", "layout": True, "controls": [{"id": "select", "role": "combobox", "name": ""}]},
            *({"id": name, "route": f"/{name}", "controls": []} for name in ("one", "two", "three"))]}]}
        scan = {"schema": 1, "screens": [entry(name, [{"role": "combobox", "name": ""}])
                                           for name in ("one", "two", "three")]}
        rows = screens.check(value, scan)
        self.assertEqual([row["code"] for row in rows], ["UNLABELED"])
        self.assertEqual(rows[0]["place"], "demo.shell.select")
        self.assertIn("3 個畫面", rows[0]["detail"])

    def test_non_layout_unlabeled_remains_per_entry(self):
        value = {"modules": [{"id": "demo", "screens": [
            {"id": name, "route": f"/{name}", "controls": [{"id": "select", "role": "combobox", "name": ""}]}
            for name in ("one", "two", "three")]}]}
        scan = {"schema": 1, "screens": [entry(name, [{"role": "combobox", "name": ""}])
                                           for name in ("one", "two", "three")]}
        rows = screens.check(value, scan)
        self.assertEqual([row["code"] for row in rows], ["UNLABELED"] * 3)

    def test_page_unlabeled_control_next_to_an_unlabeled_layout_control(self):
        # The layout select takes one unnamed combobox per entry; a second one is the page's.
        value = {"modules": [{"id": "demo", "screens": [
            {"id": "shell", "layout": True, "controls": [{"id": "select", "role": "combobox", "name": ""}]},
            {"id": "one", "route": "/one", "controls": [{"id": "engine", "role": "combobox", "name": ""}]},
            {"id": "two", "route": "/two", "controls": []}]}]}
        scan = {"schema": 1, "screens": [
            entry("one", [{"role": "combobox", "name": ""}, {"role": "combobox", "name": ""}]),
            entry("two", [{"role": "combobox", "name": ""}])]}
        rows = screens.check(value, scan)
        self.assertEqual(sorted((row["code"], row["place"]) for row in rows),
                         [("UNLABELED", "demo.one.default.controls[1]"), ("UNLABELED", "demo.shell.select")])
        layout_row = next(row for row in rows if row["place"] == "demo.shell.select")
        self.assertIn("2 個畫面", layout_row["detail"])


if __name__ == "__main__":
    unittest.main()
