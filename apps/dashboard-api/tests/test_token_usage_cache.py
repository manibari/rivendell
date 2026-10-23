"""Cache behavior with an isolated session tree and history database."""
import json
import os
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import LIB_DIR  # noqa: F401
from lib import tokens


class TokenUsageCacheTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.projects = root / "projects"
        self.projects.mkdir()
        self.session = self.projects / "project" / "session.jsonl"
        self.session.parent.mkdir()
        self.db = root / "history.db"
        self.patches = [
            patch.object(tokens, "PROJECTS_DIR", self.projects),
            patch.object(tokens, "_history_db_path", lambda: self.db),
            patch.object(tokens, "iter_codex_sessions", lambda: []),
            patch.object(tokens, "iter_qwen_sessions", lambda: []),
        ]
        for item in self.patches:
            item.start()
        tokens._FILTERED_CACHE.clear()
        tokens._FILE_AGG_CACHE.clear()
        self.write_row(5)

    def tearDown(self):
        for item in self.patches:
            item.stop()
        tokens._FILTERED_CACHE.clear()
        tokens._FILE_AGG_CACHE.clear()
        self.tmp.cleanup()

    def write_row(self, output):
        row = {"timestamp": "2026-10-20T00:00:00Z", "requestId": "r1",
               "sessionId": "s1", "message": {"role": "assistant", "model": "claude-opus-4-6",
               "content": [], "usage": {"input_tokens": 2, "output_tokens": output,
               "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}}
        self.session.write_text(json.dumps(row) + "\n")

    def test_same_range_merges_once_for_concurrent_calls(self):
        original = tokens._compute_filtered_usage
        with patch.object(tokens, "_compute_filtered_usage", wraps=original) as merge:
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: tokens.get_filtered_usage("2026-10-01", "2026-10-23"), range(4)))
            self.assertTrue(all(result is results[0] for result in results))
            self.assertEqual(merge.call_count, 1)

    def test_unchanged_files_avoid_sqlite_and_parser_after_result_expiry(self):
        tokens.get_filtered_usage("2026-10-01", "2026-10-23")
        tokens._FILTERED_CACHE.clear()
        with patch.object(tokens.sqlite3, "connect", wraps=tokens.sqlite3.connect) as connect, \
                patch.object(tokens, "_parse_jsonl_granular", side_effect=AssertionError("reparsed")):
            result = tokens.get_filtered_usage("2026-10-01", "2026-10-23")
        self.assertEqual(connect.call_count, 0)
        self.assertEqual(result.total_sessions, 1)

    def test_changed_file_parses_again_and_unchanged_file_does_not(self):
        with patch.object(tokens, "_parse_jsonl_granular", wraps=tokens._parse_jsonl_granular) as parser:
            tokens._file_agg_cached(self.session, "project", parser=parser)
            tokens._file_agg_cached(self.session, "project", parser=parser)
            self.assertEqual(parser.call_count, 1)
            self.write_row(50)
            os.utime(self.session, None)
            tokens._file_agg_cached(self.session, "project", parser=parser)
            self.assertEqual(parser.call_count, 2)
