"""Tests for qwen_codex_proxy against a fake upstream (no network, no key)."""
import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qwen_codex_proxy as proxy  # noqa: E402

KEY = "test-key-should-not-be-logged"


class FakeUpstream(BaseHTTPRequestHandler):
    reply: tuple[int, dict] = (200, {})
    seen: list = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeUpstream.seen.append((self.path, self.headers.get("Authorization"), body))
        status, payload = FakeUpstream.reply
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())


def serve(handler) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def parse_sse(text: str) -> list[tuple[str, dict]]:
    events = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


class ProxyTest(unittest.TestCase):
    def setUp(self):
        FakeUpstream.seen = []
        self.upstream = serve(FakeUpstream)
        self.logged: list[dict] = []
        handler = proxy.make_handler(f"http://127.0.0.1:{self.upstream.server_port}/v1",
                                     KEY, lambda **f: self.logged.append(f))
        self.proxy = serve(handler)

    def tearDown(self):
        self.proxy.shutdown()
        self.upstream.shutdown()

    def post(self, body: dict) -> tuple[int, str]:
        req = urllib.request.Request(f"http://127.0.0.1:{self.proxy.server_port}/v1/responses",
                                     data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()

    def test_replays_a_finished_response_as_a_stream_in_order(self):
        msg = {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "hi"}]}
        call = {"type": "function_call", "call_id": "c1", "name": "exec_command", "arguments": "{}"}
        FakeUpstream.reply = (200, {"id": "r1", "output": [msg, call],
                                    "usage": {"input_tokens": 5, "output_tokens": 2}})
        status, text = self.post({"model": "Qwen/Qwen3.8-27B", "stream": True, "input": [],
                                  "include": ["x"], "prompt_cache_key": "k"})
        self.assertEqual(status, 200)
        names = [e for e, _ in parse_sse(text)]
        self.assertEqual(names, ["response.created",
                                 "response.output_item.added", "response.output_item.done",
                                 "response.output_item.added", "response.output_item.done",
                                 "response.completed"])
        path, auth, sent = FakeUpstream.seen[0]
        self.assertEqual(path, "/v1/responses")
        self.assertEqual(auth, f"Bearer {KEY}")
        self.assertFalse(sent["stream"])
        self.assertNotIn("include", sent)
        self.assertNotIn("prompt_cache_key", sent)

    def test_freeform_tool_round_trip(self):
        FakeUpstream.reply = (200, {"output": [{"type": "function_call", "call_id": "c2",
                                                "name": "apply_patch",
                                                "arguments": json.dumps({"input": "*** patch"})}]})
        body = {"model": "q", "tools": [{"type": "custom", "name": "apply_patch"},
                                        {"type": "web_search"}],
                "input": [{"type": "reasoning", "summary": []},
                          {"type": "custom_tool_call", "call_id": "c0", "name": "apply_patch",
                           "input": "old"},
                          {"type": "custom_tool_call_output", "call_id": "c0", "output": "ok"}]}
        _, text = self.post(body)
        sent = FakeUpstream.seen[0][2]
        self.assertEqual([t["type"] for t in sent["tools"]], ["function"])
        self.assertEqual([i["type"] for i in sent["input"]], ["function_call", "function_call_output"])
        self.assertEqual(json.loads(sent["input"][0]["arguments"]), {"input": "old"})
        done = [d for e, d in parse_sse(text) if e == "response.output_item.done"][0]["item"]
        self.assertEqual((done["type"], done["input"]), ("custom_tool_call", "*** patch"))

    def test_upstream_error_keeps_its_status_code(self):
        FakeUpstream.reply = (429, {"error": {"message": "rate limited"}})
        status, text = self.post({"model": "q", "input": []})
        self.assertEqual(status, 429)
        self.assertIn("rate limited", text)
        self.assertEqual(self.logged[-1]["event"], "upstream_error")

    def test_a_body_it_cannot_read_gets_an_answer_not_a_hang(self):
        req = urllib.request.Request(f"http://127.0.0.1:{self.proxy.server_port}/v1/responses",
                                     data=b"\x28\xb5\x2f\xfd", method="POST",
                                     headers={"Content-Encoding": "zstd"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 400)
        self.assertEqual(self.logged[0]["event"], "request")
        self.assertEqual(self.logged[0]["encoding"], "zstd")
        self.assertEqual(FakeUpstream.seen, [])

    def test_bad_json_gets_a_500_and_a_log_line(self):
        req = urllib.request.Request(f"http://127.0.0.1:{self.proxy.server_port}/v1/responses",
                                     data=b"{not json", method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 500)
        self.assertEqual(self.logged[-1]["event"], "proxy_fail")

    def test_key_is_never_logged(self):
        FakeUpstream.reply = (200, {"output": [], "usage": {}})
        self.post({"model": "q", "input": []})
        FakeUpstream.reply = (401, {"error": {"message": "bad key"}})
        self.post({"model": "q", "input": []})
        self.assertTrue(self.logged)
        self.assertNotIn(KEY, json.dumps(self.logged))


if __name__ == "__main__":
    unittest.main()
