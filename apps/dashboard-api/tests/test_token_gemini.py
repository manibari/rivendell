import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import LIB_DIR  # noqa: F401
from lib import tokens, tokens_codex, tokens_gemini, tokens_qwen
from routes.monitoring import usage


def rollout(model: str, session_id: str) -> str:
    rows = [
        {"timestamp": "2026-11-18T11:00:00Z", "type": "session_meta",
         "payload": {"id": session_id, "cwd": "/tmp/example", "model_provider": "company"}},
        {"timestamp": "2026-11-18T11:00:00Z", "type": "turn_context",
         "payload": {"model": model}},
        {"timestamp": "2026-11-18T11:00:01Z", "type": "event_msg",
         "payload": {"type": "token_count", "info": {"total_token_usage": {
             "input_tokens": 100, "cached_input_tokens": 40,
             "output_tokens": 7, "total_tokens": 107}}}},
    ]
    return "".join(json.dumps(row) + "\n" for row in rows)


class GeminiSourceTest(unittest.TestCase):
    def test_api_counts_all_sources_and_gateway_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            projects = root / ".claude" / "projects"
            projects.mkdir(parents=True)
            gemini = root / ".codex-gemini" / "sessions" / "2026" / "11" / "18"
            qwen = root / ".codex-qwen" / "sessions" / "2026" / "11" / "18"
            codex = root / ".codex" / "sessions" / "2026" / "11" / "18"
            for folder, model, sid in ((gemini, "gemini-4-argon", "gemini-1"),
                                       (qwen, "Qwen/Qwen3.8-27B", "qwen-1"),
                                       (codex, "gpt-6-sol", "codex-1")):
                folder.mkdir(parents=True)
                (folder / f"rollout-{sid}.jsonl").write_text(rollout(model, sid))
            gateway = root / ".codex-gemini" / "gateway-calls.jsonl"
            gateway.write_text(json.dumps({"ts": 1795000000, "model": "gemini-4-argon",
                                           "input_tokens": 20, "output_tokens": 3,
                                           "caller": "token-waste-watch"}) + "\n{broken\n")
            with patch.object(tokens, "PROJECTS_DIR", projects), \
                    patch.object(tokens_gemini, "GEMINI_SESSION_DIR", root / ".codex-gemini" / "sessions"), \
                    patch.object(tokens_qwen, "QWEN_SESSION_DIR", root / ".codex-qwen" / "sessions"), \
                    patch.object(tokens_qwen, "_SCRATCH_ROOT", root / "scratch"), \
                    patch.object(tokens_codex, "CODEX_SESSION_DIRS", (root / ".codex" / "sessions",)), \
                    patch.object(tokens, "iter_codex_sessions", tokens_codex.iter_codex_sessions), \
                    patch.object(tokens, "iter_qwen_sessions", tokens_qwen.iter_qwen_sessions), \
                    patch.object(tokens, "iter_gemini_sessions", tokens_gemini.iter_gemini_sessions), \
                    patch.object(tokens, "gateway_log_path", return_value=gateway), \
                    patch.object(tokens, "_history_db_path", return_value=root / "history.sqlite"), \
                    patch.object(usage, "get_all_time_usage", side_effect=tokens.get_filtered_usage), \
                    patch.object(usage, "get_daily_usage", return_value=[]):
                tokens._FILTERED_CACHE.clear()
                tokens._FILE_AGG_CACHE.clear()
                result = usage.api_tokens()
            rows = {row["model"]: row for row in result["models"]}
            self.assertEqual((rows["gemini-4-argon"]["source"], rows["gemini-4-argon"]["billing"],
                              rows["gemini-4-argon"]["cost_usd"]), ("gemini", "gateway", 0))
            self.assertEqual((rows["Qwen/Qwen3.8-27B"]["source"], rows["gpt-6-sol"]["source"]),
                             ("qwen", "codex"))
            self.assertEqual(result["sources"]["gemini"]["tokens"], 90)
            self.assertEqual(result["sources"]["gemini"]["cache_tokens"], 40)
            self.assertEqual(result["sources"]["gemini"]["sessions"], 2)
            self.assertEqual(result["sources"]["qwen"]["tokens"], 67)
            self.assertEqual(result["sources"]["codex"]["tokens"], 67)
            self.assertEqual(next(p for p in result["projects"] if p["project"] == "token-waste-watch")["tokens_total"], 23)


if __name__ == "__main__":
    unittest.main()
