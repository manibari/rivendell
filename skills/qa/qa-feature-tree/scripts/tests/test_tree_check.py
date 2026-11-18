"""Contract tests for the feature tree checker."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT))
from feature_tree import folders, fmt, report, routes, schema, screens, tests_check

FIXTURES = Path(__file__).parent / "fixtures" / "py"


def tree():
    return json.loads((FIXTURES / "tree.json").read_text(encoding="utf-8"))


def codes(rows):
    return {item["code"] for item in rows}


class SchemaTests(unittest.TestCase):
    def test_required_and_draft(self):
        value = tree()
        value["modules"][0]["screens"][0]["controls"][0] = {
            "id": "draft", "role": "button", "name": "開啟", "does": "unknown",
            "evidence": "", "success": "", "failure": "", "cases": []}
        found = codes(schema.validate(value))
        self.assertTrue({"UNKNOWN_PURPOSE", "NO_EVIDENCE", "KIND_MISSING"} <= found)

    def test_ids_kinds_states_and_boundary(self):
        value = tree()
        control = value["modules"][0]["screens"][0]["controls"][0]
        control["id"] = "Bad_ID"
        control["state"] = "hidden"
        control["cases"] += [{"id": "happy", "kind": "wrong", "status": "na",
                              "boundary": "recorder", "expect": ""}]
        self.assertTrue({"ID_INVALID", "STATE_UNKNOWN", "ID_DUPLICATE", "KIND_INVALID",
                         "NA_REASON", "BOUNDARY"} <= codes(schema.validate(value)))

    def test_layout_sample_and_steps(self):
        value = tree()
        screen = value["modules"][0]["screens"][0]
        screen["layout"] = True
        screen["route"] = "/agents/[label]"
        screen["states"] = [{"id": "modal", "steps": [{"bad": {}}]}]
        self.assertTrue({"LAYOUT_ROUTE", "SAMPLE_MISSING", "STEP"} <= codes(schema.validate(value)))
        del screen["route"]
        self.assertNotIn("LAYOUT_ROUTE", codes(schema.validate(value)))

    def test_schema_version(self):
        value = tree()
        value["schema"] = 2
        self.assertIn("SCHEMA_VERSION", codes(schema.validate(value)))

    def test_required_fields_and_valid_boundary(self):
        value = tree()
        control = value["modules"][0]["screens"][0]["controls"][0]
        del control["success"]
        self.assertIn("REQUIRED", codes(schema.validate(value)))
        control["success"] = "完成"
        control["cases"].append({"id": "outside", "kind": "side-effect", "expect": "已記錄", "boundary": "recorder"})
        self.assertNotIn("BOUNDARY", codes(schema.validate(value)))


class FormatTests(unittest.TestCase):
    def test_order_and_idempotence(self):
        value = tree()
        value["extra"] = True
        value["aardvark"] = True
        text = fmt.canonical(value)
        self.assertEqual(text, fmt.canonical(json.loads(text)))
        self.assertTrue(text.index('"schema"') < text.index('"system"') < text.index('"config"') < text.index('"modules"'))
        self.assertTrue(text.index('"aardvark"') < text.index('"extra"'))
        self.assertTrue(text.endswith("\n"))


class FolderTests(unittest.TestCase):
    def test_globstar_and_star(self):
        self.assertTrue(folders.glob_match("src/**/page.tsx", "src/page.tsx"))
        self.assertTrue(folders.glob_match("src/**/page.tsx", "src/a/b/page.tsx"))
        self.assertFalse(folders.glob_match("src/*/page.tsx", "src/a/b/page.tsx"))
        self.assertTrue(folders.glob_match("src/*.tsx", "src/a.tsx"))

    def test_all_folder_results_and_planned(self):
        value = tree()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "src").mkdir()
            for name in ("a.ts", "b.ts", "c.ts", "d.ts"):
                (base / "src" / name).write_text("x", encoding="utf-8")
            value["config"]["source_roots"] = ["src"]
            value["modules"] = [{"id": "a", "paths": ["src/a.ts", "src/b.ts", "src/none.ts"]},
                                {"id": "b", "paths": ["src/b.ts", "src/d.ts"]}]
            found = codes(folders.check(value, base))
            self.assertTrue({"UNOWNED", "OVERLAP", "EMPTY_GLOB", "MIXED_FOLDER"} <= found)
            value["modules"][0]["status"] = "planned"
            self.assertNotIn("EMPTY_GLOB", codes(folders.check(value, base)))


class RouteTests(unittest.TestCase):
    def test_next_routes(self):
        examples = {"src/app/(group)/page.tsx": "/", "src/app/a/[x]/page.tsx": "/a/[x]",
                    "src/app/a/[...x]/page.tsx": "/a/[...x]",
                    "src/app/a/[[...x]]/page.tsx": "/a/[[...x]]"}
        for file, expected in examples.items():
            self.assertEqual(routes.route_for(file), expected)

    def test_unmapped_and_missing(self):
        found = codes(routes.check(tree(), FIXTURES / "repo"))
        self.assertIn("UNMAPPED_ROUTE", found)
        value = tree()
        value["modules"][0]["screens"][0]["route"] = "/gone"
        self.assertIn("MISSING_ROUTE", codes(routes.check(value, FIXTURES / "repo")))

    def test_init(self):
        value = tree()
        value.pop("modules")
        unclaimed = routes.initialize(value, FIXTURES / "repo")
        self.assertEqual({module["id"] for module in value["modules"]}, {"home", "agents", "tokens"})
        self.assertEqual(unclaimed, [])
        with self.assertRaises(ValueError):
            routes.initialize(value, FIXTURES / "repo")


class ScreenTests(unittest.TestCase):
    def test_compare_and_adopt(self):
        value = tree()
        value["modules"][0]["screens"][0]["controls"][0]["name"] = "/開.*/"
        scan = {"schema": 1, "screens": [{"module": "home", "screen": "main", "state": "default",
                "reached": True, "controls": [{"role": "button", "name": "開啟"},
                                               {"role": "link", "name": ""},
                                               {"role": "button", "name": "其他"}]}]}
        self.assertTrue({"ORPHAN", "UNLABELED"} <= codes(screens.check(value, scan)))
        self.assertEqual(screens.adopt(value, scan), 2)
        self.assertEqual([c["id"] for c in value["modules"][0]["screens"][0]["controls"][-2:]],
                         ["link-1", "button-1"])

    def test_missing_not_reached_layout_and_states(self):
        value = tree()
        module = value["modules"][0]
        module["screens"].append({"id": "shell", "layout": True, "controls": [
            {"id": "nav", "role": "link", "name": "導覽", "cases": []}]})
        screen = module["screens"][0]
        screen["states"] = [{"id": "modal", "steps": []}]
        screen["controls"].append({"id": "close", "role": "button", "name": "關閉", "state": "modal", "cases": []})
        scan = {"schema": 1, "screens": [{"module": "home", "screen": "main", "state": "default",
                "reached": True, "controls": []}]}
        self.assertTrue({"MISSING", "NOT_REACHED"} <= codes(screens.check(value, scan)))
        scan["screens"][0]["controls"] = [{"role": "link", "name": "導覽"}]
        self.assertEqual(sum(r["code"] == "MISSING" for r in screens.check(value, scan)), 1)

    def test_default_and_layout_match_hidden_state(self):
        value = tree()
        module = value["modules"][0]
        module["screens"].append({"id": "shell", "layout": True, "controls": [
            {"id": "nav", "role": "link", "name": "導覽", "cases": []}]})
        screen = module["screens"][0]
        screen["states"] = [{"id": "modal", "steps": []}]
        screen["controls"].append({"id": "close", "role": "button", "name": "關閉", "state": "modal", "cases": []})
        scan = {"schema": 1, "screens": [
            {"module": "home", "screen": "main", "state": "default", "reached": True,
             "controls": [{"role": "button", "name": "開啟"}, {"role": "link", "name": "導覽"}]},
            {"module": "home", "screen": "main", "state": "modal", "reached": True,
             "controls": [{"role": "button", "name": "開啟"}, {"role": "link", "name": "導覽"},
                          {"role": "button", "name": "關閉"}]}]}
        self.assertEqual(screens.check(value, scan), [])
        scan["screens"][1]["reached"] = False
        self.assertEqual(codes(screens.check(value, scan)), {"NOT_REACHED"})

    def test_adopt_numbering_and_state(self):
        value = tree()
        value["modules"][0]["screens"][0]["states"] = [{"id": "modal", "steps": []}]
        value["modules"][0]["screens"][0]["controls"].append(
            {"id": "button-1", "role": "button", "name": "舊", "state": "modal", "cases": []})
        scan = {"schema": 1, "screens": [{"module": "home", "screen": "main", "state": "modal",
                "reached": True, "controls": [{"role": "button", "name": "新增"}]}]}
        self.assertEqual(screens.adopt(value, scan), 1)
        adopted = value["modules"][0]["screens"][0]["controls"][-1]
        self.assertEqual((adopted["id"], adopted["state"]), ("button-2", "modal"))


class TestCheckTests(unittest.TestCase):
    def test_statuses_stale_and_last_result(self):
        value = tree()
        case = value["modules"][0]["screens"][0]["controls"][0]["cases"]
        case.extend([{"id": "bad", "kind": "invalid-input", "expect": ""},
                     {"id": "na", "kind": "empty", "status": "na", "na_reason": "無資料", "expect": ""}])
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "e2e").mkdir()
            (base / "e2e" / "a.ts").write_text("@leaf:home.main.open.happy @leaf:home.main.open.bad @leaf:old.x.y.z", encoding="utf-8")
            report_data = {"suites": [{"specs": [{"title": "@leaf:home.main.open.happy", "tags": [],
                "tests": [{"results": [{"status": "failed"}, {"status": "passed"}]}]}]}]}
            rows, status = tests_check.check(value, base, report_data)
            self.assertEqual(status["home.main.open.happy"], "passed")
            self.assertEqual(status["home.main.open.bad"], "not-run")
            self.assertEqual(status["home.main.open.na"], "na")
            self.assertTrue({"STALE", "NOT_RUN"} <= codes(rows))
            report_data["suites"][0]["specs"][0]["tests"][0]["results"].append({"status": "timedOut"})
            self.assertEqual(tests_check.check(value, base, report_data)[1]["home.main.open.happy"], "failed")
            (base / "e2e" / "a.ts").write_text("", encoding="utf-8")
            self.assertEqual(tests_check.check(value, base, report_data)[1]["home.main.open.happy"], "no-test")


class CliTests(unittest.TestCase):
    def test_fmt_check_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "tree.json"
            target.write_text(json.dumps(tree(), ensure_ascii=False), encoding="utf-8")
            command = [sys.executable, str(SCRIPT / "tree_check.py"), "fmt", str(target), "--check"]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run(command[:-1], capture_output=True).returncode, 0)
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)

    def test_report_first_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.md"
            result = subprocess.run([sys.executable, str(SCRIPT / "tree_check.py"), "report", str(FIXTURES / "tree.json"),
                                     "--repo", str(FIXTURES / "repo"), "--scan", str(FIXTURES / "scan.json"),
                                     "--e2e-report", str(FIXTURES / "report.json"), "--out", str(out)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(out.read_text(encoding="utf-8").splitlines()[0],
                             r"^葉子 \d+ 片：通過 \d+、失敗 \d+、沒有測試 \d+、未執行 \d+、不適用 \d+。"
                             r"紅燈 \d+ 項，黃燈 \d+ 項。$")


if __name__ == "__main__":
    unittest.main()
