import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import LIB_DIR  # noqa: F401  (puts dashboard-legacy on sys.path)
from lib import tokens
from lib import tokens_qwen as qwen


def rollout(model: str) -> str:
    rows = [
        {"timestamp": "2026-10-06T11:00:00.000Z", "type": "session_meta",
         "payload": {"id": "s-" + model, "cwd": "/tmp/x", "model": None}},
        {"timestamp": "2026-10-06T11:00:00.000Z", "type": "turn_context",
         "payload": {"model": model}},
        {"timestamp": "2026-10-06T11:00:01.000Z", "type": "event_msg",
         "payload": {"type": "token_count", "info": {"total_token_usage": {
             "input_tokens": 100, "cached_input_tokens": 40,
             "output_tokens": 7, "total_tokens": 107}}}},
    ]
    return "".join(json.dumps(r) + "\n" for r in rows)


class QwenSourceTest(unittest.TestCase):
    def test_qwen_model_is_its_own_unpriced_source(self):
        model = "Qwen/Qwen3.8-27B"
        self.assertEqual(tokens.model_source(model), "qwen")
        # Must not fall through to the Claude default price.
        self.assertEqual(tokens._estimate_cost(model, 10**6, 10**6, 0, 0), 0.0)
        self.assertEqual(tokens._BILLING["qwen"], "unpriced")

    def test_mirror_copies_qwen_rollouts_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scratch"
            home = root / "proj" / "sess" / "scratchpad" / "qwen-home" / "sessions" / "2026" / "10" / "06"
            home.mkdir(parents=True)
            (home / "rollout-a.jsonl").write_text(rollout("Qwen/Qwen3.8-27B"))
            (home / "rollout-b.jsonl").write_text(rollout("gpt-6-sol"))
            dest = Path(tmp) / "durable"
            with patch.object(qwen, "_SCRATCH_ROOT", root), \
                    patch.object(qwen, "QWEN_SESSION_DIR", dest):
                self.assertEqual(qwen.mirror_qwen_rollouts(), 1)
                self.assertEqual(qwen.mirror_qwen_rollouts(), 0)  # unchanged: no re-copy
                files = qwen.iter_qwen_sessions()
            self.assertEqual([p.name for p in files], ["rollout-a.jsonl"])
            self.assertEqual(files[0].relative_to(dest), Path("2026/10/06/rollout-a.jsonl"))

    def test_qwen_requests_are_keyed_for_the_source_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-a.jsonl"
            path.write_text(rollout("Qwen/Qwen3.8-27B"))
            agg = tokens._parse_qwen(path, "qwen")
        reqs = [r for day in agg.values() for p in day.values() for r in p["requests"]]
        self.assertEqual(len(reqs), 1)
        self.assertTrue(reqs[0]["key"].startswith("qwen:"))
        self.assertEqual((reqs[0]["input"], reqs[0]["cache_read"], reqs[0]["output"]), (60, 40, 7))


if __name__ == "__main__":
    unittest.main()
