"""Tests for collect.py. Run: python3 -m unittest collect_test (in scripts/)."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import collect

T0 = datetime(2026, 11, 17, 20, 0).astimezone()
START = T0 - timedelta(hours=2)
END = T0 + timedelta(hours=5)


def iso(dt: datetime) -> str:
    return dt.isoformat()


def assistant(dt, msg_id, usage, tools=()):
    content = [{"type": "tool_use", "name": n, "input": i} for n, i in tools]
    return {"type": "assistant", "timestamp": iso(dt), "cwd": "/Users/x/Code/Personal/demo",
            "message": {"id": msg_id, "model": "claude-opus-5-5", "usage": usage, "content": content}}


def usage(inp=0, cw=0, cr=0, out=0):
    return {"input_tokens": inp, "cache_creation_input_tokens": cw,
            "cache_read_input_tokens": cr, "output_tokens": out}


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


class ClaudeSessionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        sid = "abcdef12-0000-0000-0000-000000000000"
        rows = [
            {"type": "custom-title", "customTitle": "demo-session"},
            {"type": "user", "timestamp": iso(T0), "message": {"content": "use sk-abcdefgh12345678 and mail a@b.co"}},
            # one API response written as two lines (streaming): count it once
            assistant(T0 + timedelta(minutes=1), "m1", usage(10, 100_000, 0, 5), [("Bash", {"command": "git status"})]),
            assistant(T0 + timedelta(minutes=1), "m1", usage(10, 100_000, 0, 5)),
            {"type": "user", "timestamp": iso(T0 + timedelta(minutes=2)),
             "message": {"content": [{"type": "tool_result", "is_error": True, "content": "boom"}]}},
            # more than one hour idle, then a big cache write: one rebuild
            assistant(T0 + timedelta(hours=2), "m2", usage(5, 60_000, 100_000, 7), [("Bash", {"command": "git status"})]),
            {"type": "system", "subtype": "compact_boundary", "timestamp": iso(T0 + timedelta(hours=2, minutes=1))},
        ]
        for k in range(3):
            rows.append(assistant(T0 + timedelta(hours=2, minutes=2 + k), f"r{k}", usage(1, 0, 160_000, 1),
                                  [("Bash", {"command": "git status"})]))
        # outside the window: ignored
        rows.append(assistant(END + timedelta(hours=1), "late", usage(999, 999, 999, 999)))
        proj = root / "-Users-x-Code-Personal-demo"
        write_jsonl(proj / f"{sid}.jsonl", rows)
        write_jsonl(proj / sid / "subagents" / "agent-1.jsonl",
                    [assistant(T0 + timedelta(minutes=5), "s1", usage(3, 0, 250_000, 2))])
        self.rows = collect.claude_sessions(START, END, root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_one_session_with_name_and_project(self):
        self.assertEqual(len(self.rows), 1)
        s = self.rows[0]
        self.assertEqual(s["session"], "abcdef12")
        self.assertEqual(s["name"], "demo-session")
        self.assertEqual(s["project"], "demo")

    def test_streamed_lines_count_once_and_window_applies(self):
        s = self.rows[0]
        self.assertEqual(s["api_calls"], 5)  # m1, m2, r0-r2; "late" is outside
        self.assertEqual(s["tokens"]["cache_write"], 160_000)
        self.assertEqual(s["peak_context"], 160_005)

    def test_rebuild_compaction_errors_repeats(self):
        s = self.rows[0]
        self.assertEqual(s["cache_rebuilds_after_idle_1h"], 1)
        self.assertEqual(s["rebuild_tokens"], 60_000)
        self.assertEqual(s["compactions"], 1)
        self.assertEqual(s["tool_errors"], 1)
        self.assertEqual(s["repeated_bash"], [{"cmd": "git status", "n": 5}])

    def test_subagent_is_counted_under_parent(self):
        sa = self.rows[0]["subagent"]
        self.assertEqual((sa["files"], sa["api_calls"], sa["peak_ctx"]), (1, 1, 250_003))

    def test_prompt_is_masked(self):
        snippet = self.rows[0]["prompt_snippets"][0]
        self.assertNotIn("sk-abcdefgh", snippet)
        self.assertNotIn("a@b.co", snippet)
        self.assertIn("***", snippet)


class CodexAndRunsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_codex_counts_only_the_delta_inside_the_window(self):
        def tc(dt, inp, cached, out):
            return {"type": "event_msg", "timestamp": iso(dt), "payload": {"type": "token_count", "info": {
                "total_token_usage": {"input_tokens": inp, "cached_input_tokens": cached, "output_tokens": out}}}}
        sessions = self.root / ".codex" / "sessions"
        write_jsonl(sessions / "2026" / "rollout-x.jsonl", [
            {"type": "session_meta", "payload": {"cwd": "/Users/x/Code/Chimes/ChimesERP", "model": "gpt-6-sol"}},
            tc(START - timedelta(hours=1), 1000, 800, 10),   # before the window: baseline only
            tc(T0, 5000, 4000, 50),
            {"type": "response_item", "timestamp": iso(T0), "payload": {"type": "function_call"}},
        ])
        rows = collect.codex_sessions(START, END, [sessions])
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["project"], r["requests"], r["tool_calls"]), ("ChimesERP", 1, 1))
        self.assertEqual((r["input_tokens_incl_cached"], r["cached_input_tokens"], r["output_tokens"]), (4000, 3200, 40))

    def test_code_runs_window_summary_and_running(self):
        runs = self.root / "code-runs"
        inside = runs / f"{T0.strftime('%Y%m%d-%H%M%S')}-codex-codex-a"
        inside.mkdir(parents=True)
        (inside / "summary.json").write_text(json.dumps({
            "executor": "codex", "exit": 1, "seconds": 10, "attempts": 2, "stalls": ["x"],
            "error": "workspace routing discovery failed", "usage": {"input_tokens": 7}, "changed": []}))
        (runs / f"{(T0 + timedelta(minutes=5)).strftime('%Y%m%d-%H%M%S')}-codex-codex-b").mkdir()
        (runs / f"{(START - timedelta(days=1)).strftime('%Y%m%d-%H%M%S')}-codex-codex-old").mkdir()
        rows = collect.code_runs(START, END, runs)
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[0]["exit"], rows[0]["attempts"], rows[0]["stalls"]), (1, 2, 1))
        self.assertEqual(rows[1]["status"], "running or no summary")


class MaskTest(unittest.TestCase):
    def test_mask_keys_jwt_assignments_email(self):
        text = "curl -H 'Bearer eyJhbGciOiJIUzI1NiJ9abcdefghijklmn' password=hunter2 x@y.com"
        out = collect.mask(text, 500)
        for secret in ("eyJhbGci", "hunter2", "x@y.com"):
            self.assertNotIn(secret, out)


if __name__ == "__main__":
    unittest.main()
