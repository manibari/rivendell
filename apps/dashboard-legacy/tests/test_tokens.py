import json
import tempfile
import unittest
from pathlib import Path

from lib import tokens


class TokenParserTest(unittest.TestCase):
    def test_repeated_request_usage_is_counted_once(self) -> None:
        usage = {
            "input_tokens": 10,
            "output_tokens": 20,
            "cache_read_input_tokens": 30,
            "cache_creation_input_tokens": 40,
        }
        base = {
            "timestamp": "2026-07-19T01:02:03.000Z",
            "requestId": "req_same",
            "sessionId": "session-a",
            "cwd": str(Path.home() / "code" / "rivendell"),
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-8",
                "usage": usage,
            },
        }

        rows = []
        for block in (
            {"type": "thinking", "thinking": ""},
            {"type": "text", "text": "done"},
            {"type": "tool_use", "id": "toolu_1", "name": "Read", "input": {}},
        ):
            row = json.loads(json.dumps(base))
            row["message"]["content"] = [block]
            rows.append(row)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            parsed = tokens._parse_jsonl_granular(path, "fallback")

        project = parsed["2026-07-19"]["rivendell"]
        self.assertEqual(project["messages"], 1)
        self.assertEqual(project["tool_calls"], 1)
        self.assertEqual(project["models"]["claude-opus-4-8"], [10, 20, 30, 40])

    def test_last_usage_for_request_wins(self) -> None:
        rows = []
        for output_tokens in (3, 5):
            rows.append({
                "timestamp": "2026-07-19T01:02:03.000Z",
                "requestId": "req_partial",
                "sessionId": "session-a",
                "cwd": str(Path.home() / "code" / "rivendell"),
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "model": "claude-sonnet-5",
                    "content": [{"type": "text", "text": "x"}],
                    "usage": {
                        "input_tokens": 1,
                        "output_tokens": output_tokens,
                        "cache_read_input_tokens": 0,
                        "cache_creation_input_tokens": 0,
                    },
                },
            })

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            parsed = tokens._parse_jsonl_granular(path, "fallback")

        project = parsed["2026-07-19"]["rivendell"]
        self.assertEqual(project["messages"], 1)
        self.assertEqual(project["models"]["claude-sonnet-5"], [1, 5, 0, 0])



class CodexParserTest(unittest.TestCase):
    def _rollout(self, events: list[dict]) -> str:
        return "".join(json.dumps(e) + "\n" for e in events)

    def test_cumulative_token_count_becomes_per_request_deltas(self) -> None:
        cwd = str(Path.home() / "code" / "rivendell")
        events = [
            {"timestamp": "2026-09-23T06:37:52.510Z", "type": "session_meta",
             "payload": {"id": "sess-1", "cwd": cwd, "model": "gpt-6-sol"}},
            {"timestamp": "2026-09-23T06:37:52.837Z", "type": "turn_context",
             "payload": {"cwd": cwd, "model": "gpt-6-sol"}},
            {"timestamp": "2026-09-23T06:38:00.000Z", "type": "response_item",
             "payload": {"type": "function_call", "name": "shell"}},
            {"timestamp": "2026-09-23T06:38:03.410Z", "ordinal": 17, "type": "event_msg",
             "payload": {"type": "token_count", "info": {"total_token_usage": {
                 "input_tokens": 1000, "cached_input_tokens": 600,
                 "cache_write_input_tokens": 0, "output_tokens": 50, "total_tokens": 1050}}}},
            # duplicate emission with no progress must not count
            {"timestamp": "2026-09-23T06:38:03.500Z", "ordinal": 18, "type": "event_msg",
             "payload": {"type": "token_count", "info": {"total_token_usage": {
                 "input_tokens": 1000, "cached_input_tokens": 600,
                 "cache_write_input_tokens": 0, "output_tokens": 50, "total_tokens": 1050}}}},
            {"timestamp": "2026-09-23T06:39:00.000Z", "ordinal": 25, "type": "event_msg",
             "payload": {"type": "token_count", "info": {"total_token_usage": {
                 "input_tokens": 1500, "cached_input_tokens": 1000,
                 "cache_write_input_tokens": 20, "output_tokens": 80, "total_tokens": 1600}}}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-2026-09-23T14-37-50-sess-1.jsonl"
            path.write_text(self._rollout(events), encoding="utf-8")
            parsed = tokens._parse_codex(path, "codex")

        project = parsed["2026-09-23"]["rivendell"]
        self.assertEqual(project["sessions"], ["sess-1"])
        self.assertEqual(project["messages"], 2)
        self.assertEqual(project["tool_calls"], 1)
        # request 1: input 1000-600=400, out 50, cache_read 600, cache_create 0
        # request 2: input 500-400=100, out 30, cache_read 400, cache_create 20
        self.assertEqual(project["models"]["gpt-6-sol"], [500, 80, 1000, 20])
        self.assertTrue(all(r["key"].startswith("codex:sess-1:") for r in project["requests"]))

    def test_old_rollout_model_comes_from_provenance(self) -> None:
        events = [
            {"timestamp": "2026-08-19T01:32:33.000Z", "type": "session_meta",
             "payload": {"id": "sess-old", "cwd": "/Users/x/Rightek",
                         "base_instructions": {"text": "...", "provenance": {"type": "model", "model": "gpt-5.6-sol"}}}},
            {"timestamp": "2026-08-19T01:32:34.000Z", "type": "event_msg",
             "payload": {"type": "token_count", "info": {"total_token_usage": {
                 "input_tokens": 0, "cached_input_tokens": 0, "cache_write_input_tokens": 0,
                 "output_tokens": 0, "total_tokens": 17386}}}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-old.jsonl"
            path.write_text(self._rollout(events), encoding="utf-8")
            parsed = tokens._parse_codex(path, "codex")
        project = parsed["2026-08-19"]["Rightek"]
        self.assertEqual(list(project["models"]), ["gpt-5.6-sol"])
        self.assertEqual(project["models"]["gpt-5.6-sol"], [17386, 0, 0, 0])

    def test_codex_models_are_subscription_billed(self) -> None:
        self.assertEqual(tokens._estimate_cost(tokens.UNKNOWN_CODEX_MODEL, 1_000_000, 0, 0, 0), 0.0)
        self.assertEqual(tokens._estimate_cost("gpt-6-sol", 1_000_000, 1_000_000, 0, 0), 0.0)
        self.assertEqual(tokens.model_source("gpt-5.6-luna"), "codex")
        self.assertEqual(tokens.model_source("claude-fable-5-1"), "claude")
        self.assertGreater(tokens._estimate_cost("claude-fable-5-1", 1_000_000, 0, 0, 0), 0.0)

if __name__ == "__main__":
    unittest.main()
