"""Incremental skill counts from temporary Claude session files."""
import builtins
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from routes import skills


def row(date, tool, value):
    key = "file_path" if tool == "Read" else "skill"
    return json.dumps({"timestamp": date + "T12:00:00Z", "message": {"content": [
        {"type": "tool_use", "name": tool, "input": {key: value}}]}}) + "\n"


class SkillUsageCacheTest(unittest.TestCase):
    def test_reuses_unchanged_files_and_drops_deleted_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            projects = home / ".claude" / "projects" / "example"
            projects.mkdir(parents=True)
            first = projects / "first.jsonl"
            second = projects / "second.jsonl"
            first.write_text(row("2026-10-20", "Skill", "alpha") +
                             row("2026-10-20", "Read", "/skills/beta/SKILL.md") +
                             json.dumps({"timestamp": "2026-10-20", "message": {"content": []}}) + "\n")
            second.write_text(row("2026-10-21", "Skill", "alpha"))
            skills._usage_cache.clear()
            opened = []
            original_open = builtins.open

            def tracked_open(file, *args, **kwargs):
                opened.append(str(file))
                return original_open(file, *args, **kwargs)

            with patch.object(skills.Path, "home", return_value=home), patch("builtins.open", side_effect=tracked_open):
                expected = {"alpha": [{"date": "2026-10-20", "count": 1},
                                      {"date": "2026-10-21", "count": 1}],
                            "beta": [{"date": "2026-10-20", "count": 1}]}
                self.assertEqual(skills._parse_skill_usage(), expected)
                self.assertCountEqual(opened, [str(first), str(second)])
                opened.clear()
                self.assertEqual(skills._parse_skill_usage(), expected)
                self.assertEqual(opened, [])
                first.write_text(first.read_text() + row("2026-10-20", "Skill", "alpha"))
                opened.clear()
                changed = skills._parse_skill_usage()
                self.assertEqual(opened, [str(first)])
                self.assertEqual(changed["alpha"][0]["count"], 2)
                second.unlink()
                opened.clear()
                final = skills._parse_skill_usage()
                self.assertEqual(opened, [])
                self.assertEqual(final["alpha"], [{"date": "2026-10-20", "count": 2}])
            skills._usage_cache.clear()
