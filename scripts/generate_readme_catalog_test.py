"""Regression tests for the README catalog generator."""

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("generate-readme-catalog.py")
SPEC = importlib.util.spec_from_file_location("generate_readme_catalog", MODULE_PATH)
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


class CatalogTest(unittest.TestCase):
    def test_intro_prose_is_preserved(self):
        intro = (
            "## Skills Catalog (1 skills)\n\n"
            "> First line\n"
            "技能包本體仍在 `skills/*/*/SKILL.md`。\n"
            "修改工作定義後執行 `./bin/sk check workflows`。\n"
            "> Last line\n\n"
        )
        readme = intro + "### platform/ — 平台自我改善\n"
        result = catalog.generate_catalog_section(
            {"platform": [
                ("example", {"description": "Short description."}),
                ("second", {"description": "Another short description."}),
            ]},
            {},
            readme,
        )
        self.assertTrue(result.startswith(intro.replace("(1 skills)", "(2 skills)")))

    def test_tokens_are_not_split(self):
        for token in ("Next.js", "timeleft.com", "storyline.md", "e.g."):
            with self.subTest(token=token):
                desc = "A short introduction to " + token + " and many more useful details about the project and its implementation."
                result = catalog.shorten_description(desc, 29)
                self.assertFalse(result.endswith(token.split(".")[0] + "."))
                self.assertLessEqual(len(result), 29)

    def test_unclosed_brackets_are_removed(self):
        for opening in ("(", "（"):
            with self.subTest(opening=opening):
                desc = "Conventions for apps " + opening + "PdfCraft, CADCraft, and more systems built for users everywhere."
                result = catalog.shorten_description(desc, 42)
                self.assertNotIn(opening, result)
                self.assertTrue(result.endswith("…"))

    def test_short_descriptions_are_unchanged(self):
        desc = "A short description with Next.js (and tools)."
        self.assertEqual(catalog.shorten_description(desc), desc)
        self.assertEqual(catalog.extract_auto_description({"description": desc}, "example"), desc)

    def test_new_skill_frontmatter(self):
        for name, token in (
            ("gcp-vm-deploy", "Next.js"),
            ("timeleft-style", "timeleft.com"),
            ("artcraft-conventions", "Artcraft"),
        ):
            with self.subTest(name=name):
                path = next(MODULE_PATH.parent.parent.glob(f"skills/*/{name}/SKILL.md"))
                fm = catalog.parse_frontmatter(path.read_text())
                result = catalog.extract_auto_description(fm, name)
                self.assertIn(token, result)
                self.assertLessEqual(len(result), 80)
                self.assertEqual(result.count("("), result.count(")"))


if __name__ == "__main__":
    unittest.main()
