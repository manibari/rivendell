import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server
from routes import skills


class SkillDocsTest(unittest.TestCase):
    def test_docs_route_uses_repository_docs(self) -> None:
        result = skills.api_doc("skills-by-role")

        self.assertEqual(result["path"], "docs/skills-by-role.md")
        self.assertTrue(result["content"].strip())
        self.assertIn("/api/docs/{doc_path}", server.app.openapi()["paths"])
