import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gateway


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps({"output_text": "ok", "usage": {
            "input_tokens": 12, "output_tokens": 5,
        }}).encode()


class GatewayLogTest(unittest.TestCase):
    def test_ask_appends_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "gemini" / "calls.jsonl"
            with patch.dict("os.environ", {"CHIMES_GATEWAY_API_KEY": "test", "GEMINI_GATEWAY_LOG": str(log)}), \
                    patch.object(gateway.urllib.request, "urlopen", return_value=FakeResponse()):
                self.assertEqual(gateway.ask("instruction", "prompt"),
                                 ("ok", {"input_tokens": 12, "output_tokens": 5}))
            row = json.loads(log.read_text().strip())
            self.assertEqual((row["model"], row["input_tokens"], row["output_tokens"], row["caller"]),
                             (gateway.MODEL, 12, 5, "token-waste-watch"))
            self.assertIsInstance(row["ts"], float)

    def test_write_error_does_not_break_ask(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocked = Path(tmp) / "file"
            blocked.write_text("occupied")
            with patch.dict("os.environ", {"CHIMES_GATEWAY_API_KEY": "test", "GEMINI_GATEWAY_LOG": str(blocked / "calls.jsonl")}), \
                    patch.object(gateway.urllib.request, "urlopen", return_value=FakeResponse()):
                self.assertEqual(gateway.ask("instruction", "prompt")[0], "ok")


if __name__ == "__main__":
    unittest.main()
