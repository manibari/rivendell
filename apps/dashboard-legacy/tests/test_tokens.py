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


if __name__ == "__main__":
    unittest.main()
