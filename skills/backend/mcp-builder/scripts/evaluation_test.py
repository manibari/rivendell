"""Regression tests for the MCP evaluation agent loop."""

import copy
import importlib
import sys
import types
import unittest


try:
    importlib.import_module("anthropic")
except ImportError:
    anthropic = types.ModuleType("anthropic")
    anthropic.Anthropic = type("Anthropic", (), {})
    sys.modules["anthropic"] = anthropic

try:
    importlib.import_module("connections")
except ImportError:
    connections = types.ModuleType("connections")
    connections.create_connection = lambda **kwargs: None
    sys.modules["connections"] = connections

import evaluation


def tool_use(tool_id, name, tool_input):
    return types.SimpleNamespace(type="tool_use", id=tool_id, name=name, input=tool_input)


def text_block(value):
    return types.SimpleNamespace(type="text", text=value)


def response(stop_reason, content):
    return types.SimpleNamespace(stop_reason=stop_reason, content=content)


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []
        self.messages = types.SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        self.requests.append(copy.deepcopy(kwargs))
        return next(self.responses)


class FakeConnection:
    def __init__(self, failures=()):
        self.calls = []
        self.failures = set(failures)

    async def call_tool(self, name, tool_input):
        self.calls.append((name, tool_input))
        if name in self.failures:
            raise RuntimeError("tool failed")
        return {"name": name}


class AgentLoopTests(unittest.IsolatedAsyncioTestCase):
    async def test_multiple_tool_uses_share_one_user_message(self):
        client = FakeClient([
            response("tool_use", [
                tool_use("first-id", "lookup", {"key": 1}),
                tool_use("second-id", "lookup", {"key": 2}),
            ]),
            response("end_turn", [text_block("done")]),
        ])
        connection = FakeConnection()

        result, metrics = await evaluation.agent_loop(client, "model", "question", [], connection)

        self.assertEqual(result, "done")
        self.assertEqual(connection.calls, [
            ("lookup", {"key": 1}),
            ("lookup", {"key": 2}),
        ])
        self.assertEqual(len(client.requests), 2)
        second_messages = client.requests[1]["messages"]
        self.assertEqual(second_messages[-1]["role"], "user")
        tool_results = second_messages[-1]["content"]
        self.assertEqual([block["type"] for block in tool_results], ["tool_result", "tool_result"])
        self.assertEqual([block["tool_use_id"] for block in tool_results], ["first-id", "second-id"])
        self.assertEqual(metrics["lookup"]["count"], 2)
        self.assertEqual(len(metrics["lookup"]["durations"]), 2)

    async def test_failed_tool_result_is_marked_and_loop_continues(self):
        client = FakeClient([
            response("tool_use", [
                tool_use("failed-id", "broken", {}),
                tool_use("good-id", "working", {}),
            ]),
            response("end_turn", [text_block("finished")]),
        ])
        connection = FakeConnection(failures={"broken"})

        result, metrics = await evaluation.agent_loop(client, "model", "question", [], connection)

        self.assertEqual(result, "finished")
        self.assertEqual([name for name, _ in connection.calls], ["broken", "working"])
        tool_results = client.requests[1]["messages"][-1]["content"]
        self.assertEqual(tool_results[0]["tool_use_id"], "failed-id")
        self.assertTrue(tool_results[0]["is_error"])
        self.assertIn("Error executing tool broken: tool failed", tool_results[0]["content"])
        self.assertEqual(tool_results[1]["tool_use_id"], "good-id")
        self.assertEqual(metrics["broken"]["count"], 1)
        self.assertEqual(metrics["working"]["count"], 1)

    async def test_final_text_blocks_are_joined(self):
        client = FakeClient([
            response("end_turn", [
                text_block("<summary>evidence</summary>"),
                text_block("<feedback>useful</feedback><response>answer</response>"),
            ]),
        ])

        result, metrics = await evaluation.agent_loop(client, "model", "question", [], FakeConnection())

        self.assertEqual(
            result,
            "<summary>evidence</summary>\n<feedback>useful</feedback><response>answer</response>",
        )
        self.assertEqual(evaluation.extract_xml_content(result, "summary"), "evidence")
        self.assertEqual(evaluation.extract_xml_content(result, "feedback"), "useful")
        self.assertEqual(evaluation.extract_xml_content(result, "response"), "answer")
        self.assertEqual(metrics, {})

    def test_prompt_requests_evidence_from_tool_outputs(self):
        self.assertIn(
            "  - The evidence from the tool outputs that supports the response",
            evaluation.EVALUATION_PROMPT,
        )


if __name__ == "__main__":
    unittest.main()
