"""Regression tests for the manual form checker."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "check_manual.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "manual"
spec = importlib.util.spec_from_file_location("check_manual", SCRIPT)
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


class RuleTests(unittest.TestCase):
    def assert_rule(self, code, bad, good, options=None, path="<text>"):
        with self.subTest(code=code, bad=bad):
            self.assertTrue(
                any(item.code == code for item in checker.check_text(bad, path, options)),
                (code, bad),
            )
            self.assertFalse(
                any(item.code == code for item in checker.check_text(good, path, options)),
                (code, good),
            )

    def test_each_rule_has_positive_and_near_miss(self):
        cases = [
            ("MW101", "中文,English", "`中文,English`"),
            ("MW102", "（內容）", "(內容)"),
            ("MW103", "輸入**Q**", "輸入 **Q**"),
            ("MW104", "中文[報價]", "中文[報價](/manual/quotes)"),
            ("MW105", "內容──說明", "內容-說明"),
            ("MW106", "請按一下。", "請以滑鼠右鍵按一下。"),
            ("MW107", "**[報價]**", "[報價]"),
            ("MW108", "[報價…]", "[報價]"),
            ("MW109", "[甲]>[乙]", "[甲] > [乙]"),
            ("MW110", "選取「儲存」", "選取 [儲存]"),
            ("MW111", "你可以查看報價。", "你們可以查看報價。"),
            ("MW112", "它會顯示。", "其會顯示。"),
            ("MW113", "系統當機。", "系統停止回應。"),
            ("MW114", "`localhost`", "`example.com`"),
            ("MW115", "完成\U0001f600", "完成。"),
            ("MW116", "## 名稱。", "## 名稱"),
            ("MW117", "# 標題\n\n## 小節", "# 標題\n\n內文。\n\n## 小節"),
            ("MW118", "\n".join(f"{i}. 步驟" for i in range(1, 14)), "\n".join(f"{i}. 步驟" for i in range(1, 13))),
            ("MW119", "\n".join(f"{i}. 步驟" for i in range(1, 9)), "\n".join(f"{i}. 步驟" for i in range(1, 8))),
            ("MW120", "1. 選取資料，輸入數量，開啟頁面。", "1. 選取資料。"),
            ("MW121", "![](quote.png)", "![螢幕擷取畫面：報價](quote.png)"),
            ("MW122", "> **提示：** 查看內容。", "> **注意：** 查看內容。"),
            ("MW123", "| 名稱 | 值 |\n| --- | --- |\n| 甲 | - |", "| 名稱 | 值 |\n| --- | --- |\n| 甲 | 不適用 |"),
            ("MW124", "說明如下：\n\n| 名稱 | 值 |\n| --- | --- |\n| 甲 | 乙 |", "說明如下。\n\n| 名稱 | 值 |\n| --- | --- |\n| 甲 | 乙 |"),
            ("MW125", "中文 ，內容", "中文，內容"),
            ("MW126", "( 內容)", "(內容)"),
            ("MW127", "*中文*", "**中文**"),
        ]
        for code, bad, good in cases:
            self.assert_rule(code, bad, good)

    def test_suppressed_prose_and_raw_development_address(self):
        text = "```\n中文,English\nlocalhost\n```\n<!-- 你 -->\n`中文,English`\nhttps://example.com/中文,English\n"
        findings = checker.check_text(text)
        self.assertEqual([(item.code, item.level) for item in findings], [("MW114", "E")])

    def test_positions_after_frontmatter(self):
        text = "---\ntitle: ignored\n---\n中文A\n中文,內容\n"
        findings = checker.check_text(text)
        self.assertIn((4, 3), {(f.line, f.col) for f in findings if f.code == "MW103"})
        self.assertIn((5, 3), {(f.line, f.col) for f in findings if f.code == "MW101"})

    def test_rule_variants_and_options(self):
        self.assert_rule("MW104", "中文(說明)", "中文 (說明)")
        self.assert_rule("MW107", "__[報價]__", "[報價]")
        self.assert_rule("MW108", "[報價:]", "[報價]")
        self.assert_rule("MW109", "[甲] **>** [乙]", "[甲] > [乙]")
        self.assert_rule("MW120", "1. 選取甲，或乙。", "1. 選取甲或乙。")
        self.assert_rule("MW121", "<img src='quote.png'>", "![螢幕擷取畫面：報價](quote.png)")
        self.assert_rule("MW122", "> **注意：** 甲\n\n> **重要：** 乙", "> **注意：** 甲\n\n內文。\n\n> **重要：** 乙")
        self.assert_rule("MW116", "# 標題", "## 標題", {"no_h1": True})
        self.assertFalse(any(f.code == "MW114" for f in checker.check_text("API", options={"allow_term": ["API"]})))
        self.assertTrue(any(f.code == "MW114" and f.level == "W" for f in checker.check_text("API")))
        # Only the MW114 error reads code spans; the word warning reads prose (review, 2026-11-20).
        self.assertFalse(any(f.code == "MW114" and f.level == "W" for f in checker.check_text("`API`")))
        self.assertTrue(any(f.code == "MW114" and f.level == "E" for f in checker.check_text("`localhost`")))
        self.assertTrue(any(f.code == "MW114" and f.level == "E" for f in checker.check_text("https://host:1234")))
        self.assertTrue(any(f.code == "MW116" for f in checker.check_text("# `名稱`")))
        self.assertTrue(any(f.code == "MW116" for f in checker.check_text("## 章節\n\n內容。\n\n#### 跳級")))
        self.assertTrue(any(f.code == "MW123" for f in checker.check_text("名稱 | 值\n--- | ---\n甲 | -")))
        self.assertTrue(any(f.code == "MW123" for f in checker.check_text("| 名稱 | 值 |\n| --- | --- |\n| 甲 ||")))
        self.assertFalse(any(f.code in {"MW104", "MW107", "MW108", "MW109"} for f in checker.check_text("中文[報價](/manual/quotes)")))


class ReviewRegressionTests(unittest.TestCase):
    """Defects found in the 2026-11-20 review."""

    def codes(self, text):
        return [(item.line, item.col, item.level, item.code) for item in checker.check_text(text)]

    def test_alt_text_warning_does_not_crash(self):
        findings = checker.check_text("![報價頁面](quote.png)\n")
        self.assertEqual([(item.level, item.code) for item in findings], [("W", "MW121")])
        self.assertEqual(findings[0].message, checker.MESSAGES["MW121W"])

    def test_table_cell_padding_is_not_mw125(self):
        table = "下表說明狀態。\n\n| 狀態 | 說明 |\n| --- | --- |\n| 草稿 | 尚未送出。 |\n"
        self.assertEqual(self.codes(table), [])

    def test_developer_word_in_code_span_is_not_mw114_warning(self):
        self.assertEqual(self.codes("請參考 `API` 設定。\n"), [])
        self.assertEqual(self.codes("請參考 API 設定。\n"), [(1, 5, "W", "MW114")])

    def test_one_finding_across_emphasis_markers(self):
        self.assertEqual(self.codes("輸入**Q**。\n"), [(1, 5, "E", "MW103")])


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, check=False)

    def test_good_article(self):
        result = self.run_cli(FIXTURES / "good.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "0 個錯誤，0 個警告")

    def test_error_warning_strict_and_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            error = root / "error.md"
            warning = root / "warning.md"
            error.write_text("你可以查看。", encoding="utf-8")
            warning.write_text("它會顯示。", encoding="utf-8")
            self.assertEqual(self.run_cli(error).returncode, 1)
            self.assertEqual(self.run_cli(warning).returncode, 0)
            self.assertEqual(self.run_cli(warning, "--strict").returncode, 1)
            data = json.loads(self.run_cli(error, "--json").stdout)
            self.assertEqual(data[0]["code"], "MW111")
            self.assertEqual(set(data[0]), {"path", "line", "col", "level", "code", "message"})

    def test_directory_readme_and_disable(self):
        self.assertEqual(self.run_cli(FIXTURES).returncode, 0)
        included = self.run_cli(FIXTURES, "--include-readme")
        self.assertEqual(included.returncode, 1)
        self.assertIn("README.md", included.stdout)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mixed.md"
            path.write_text("中文API", encoding="utf-8")
            ordinary = self.run_cli(path)
            disabled = self.run_cli(path, "--disable", "MW103")
            self.assertIn("MW103", ordinary.stdout)
            self.assertNotIn("MW103", disabled.stdout)


if __name__ == "__main__":
    unittest.main()
