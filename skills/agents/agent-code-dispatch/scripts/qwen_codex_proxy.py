"""Responses-stream shim: codex exec -> GMI Qwen.

GMI answers /v1/responses correctly without streaming, but its stream sends
only "data: [DONE]". Codex 0.160 accepts only a Responses stream. This shim
asks GMI without streaming and replays the finished response as SSE events.

Other adaptations:
  - Freeform (custom) tools become one-string function tools upstream, and
    their calls are turned back into custom tool calls for codex.
  - Replayed reasoning items are dropped (upstream rejects them).
  - A curl User-Agent avoids the Cloudflare 1010 block on the default one.

Moved 2026-10-06 from a Yellow-Chick session scratchpad (ticket
DEV-QWEN-EXECUTOR-SHIM) into rivendell, which owns it for all projects.

Config is environment only, so the key never reaches argv or a file:
  GMI_API_KEY      required
  GMI_BASE_URL     default https://api.gmi-serving.com/v1
  QWEN_PROXY_PORT  default 8004 (registered in platform/deployment/ports.conf)
  QWEN_PROXY_LOG   default ~/.codex-qwen/proxy.log (one JSON object per line)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEFAULT_BASE_URL = "https://api.gmi-serving.com/v1"
DEFAULT_PORT = 8004
DROP_TOOL_TYPES = {"web_search", "web_search_preview", "image_generation"}
DROP_BODY_KEYS = ("include", "prompt_cache_key", "client_metadata")
# A client socket that sends nothing for this long is dropped. Without it, a
# stalled read held a codex run for 74 min (2026-10-07, Yellow-Chick).
CLIENT_READ_TIMEOUT_S = 60
UPSTREAM_TIMEOUT_S = 600


def adapt_tools(body: dict, custom: set) -> None:
    """Keep function tools; turn freeform custom tools into one-string function tools."""
    tools = []
    for tool in body.get("tools") or []:
        kind = tool.get("type")
        if kind in DROP_TOOL_TYPES:
            continue
        if kind == "custom":
            tools.append({"type": "function", "name": tool["name"],
                          "description": tool.get("description", ""),
                          "parameters": {"type": "object",
                                         "properties": {"input": {"type": "string"}},
                                         "required": ["input"]}})
            custom.add(tool["name"])
            continue
        tools.append(tool)
    if tools:
        body["tools"] = tools
    else:
        body.pop("tools", None)
        body.pop("tool_choice", None)


def adapt_input(body: dict) -> None:
    """Earlier custom tool calls go back upstream as function calls."""
    items = []
    for item in body.get("input") or []:
        kind = item.get("type")
        if kind == "custom_tool_call":
            item = {"type": "function_call", "call_id": item["call_id"], "name": item["name"],
                    "arguments": json.dumps({"input": item.get("input", "")})}
        elif kind == "custom_tool_call_output":
            item = {"type": "function_call_output", "call_id": item["call_id"],
                    "output": item.get("output", "")}
        elif kind == "reasoning":
            continue  # upstream cannot use replayed reasoning
        items.append(item)
    body["input"] = items


def adapt_output(item: dict, custom: set) -> dict:
    """Function calls to a freeform tool go back to codex as custom tool calls."""
    if item.get("type") == "function_call" and item.get("name") in custom:
        try:
            text = json.loads(item.get("arguments") or "{}").get("input", "")
        except json.JSONDecodeError:
            text = item.get("arguments", "")
        return {"type": "custom_tool_call", "call_id": item["call_id"], "name": item["name"],
                "input": text, "status": "completed"}
    return item


def sse_events(result: dict) -> list[tuple[str, dict]]:
    """The Responses stream codex expects, replayed from one finished response."""
    output = result.get("output") or []
    events = [("response.created", {"type": "response.created",
                                    "response": {**result, "output": [], "status": "in_progress"}})]
    for index, item in enumerate(output):
        events.append(("response.output_item.added", {"type": "response.output_item.added",
                                                      "output_index": index, "item": item}))
        events.append(("response.output_item.done", {"type": "response.output_item.done",
                                                     "output_index": index, "item": item}))
    events.append(("response.completed", {"type": "response.completed",
                                          "response": {**result, "status": "completed"}}))
    return events


def _item_label(item: dict) -> str:
    kind = item.get("type", "")
    return kind + (":" + item.get("name", "") if "call" in kind else "")


def make_handler(upstream: str, key: str, log):
    custom: set = set()  # freeform tool names seen in requests, shared by all requests

    class Handler(BaseHTTPRequestHandler):
        timeout = CLIENT_READ_TIMEOUT_S

        def log_message(self, *args):
            pass

        def _send_json(self, status: int, payload: dict) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())

        def do_GET(self):
            if self.path.rstrip("/") == "/health":
                self._send_json(200, {"ok": True})
            else:
                self._send_json(404, {"error": {"message": "not found"}})

        def do_POST(self):
            try:
                self._post()
            except Exception as exc:  # always answer, never leave codex waiting
                log(event="proxy_fail", detail=f"{type(exc).__name__}: {exc}"[:300])
                try:
                    self._send_json(500, {"error": {"message": "proxy error"}})
                except OSError:
                    pass

        def _post(self):
            length = int(self.headers.get("Content-Length") or 0)
            log(event="request", bytes=length,
                encoding=self.headers.get("Content-Encoding") or "",
                chunked="chunked" in (self.headers.get("Transfer-Encoding") or ""))
            if length <= 0 or self.headers.get("Content-Encoding"):
                self._send_json(400, {"error": {"message": "proxy needs a plain JSON body with Content-Length"}})
                return
            body = json.loads(self.rfile.read(length))
            body["stream"] = False
            body["store"] = False
            for name in DROP_BODY_KEYS:
                body.pop(name, None)
            adapt_tools(body, custom)
            adapt_input(body)
            started = time.time()
            req = urllib.request.Request(
                upstream + "/responses", data=json.dumps(body).encode(), method="POST",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                         "User-Agent": "curl/8.7.1"})
            try:
                with urllib.request.urlopen(req, timeout=UPSTREAM_TIMEOUT_S) as resp:
                    result = json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode(errors="replace")[:500]
                log(event="upstream_error", status=exc.code, detail=detail)
                self._send_json(exc.code, {"error": {"message": detail}})
                return
            except Exception as exc:  # network failure
                log(event="upstream_fail", detail=str(exc)[:300])
                self._send_json(502, {"error": {"message": "upstream unreachable"}})
                return
            result["output"] = [adapt_output(i, custom) for i in result.get("output") or []]
            usage = result.get("usage") or {}
            log(event="ok", model=body.get("model"), seconds=round(time.time() - started, 1),
                input_tokens=usage.get("input_tokens"), output_tokens=usage.get("output_tokens"),
                items=[_item_label(i) for i in result["output"]])
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for event, data in sse_events(result):
                self.wfile.write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())
            self.wfile.flush()

    return Handler


def file_logger(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    out = open(path, "a", buffering=1)

    def log(**fields):
        out.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), **fields},
                             ensure_ascii=False) + "\n")
    return log


def main() -> int:
    key = os.environ.get("GMI_API_KEY", "").strip()
    if not key:
        print("GMI_API_KEY is not set", file=sys.stderr)
        return 2
    upstream = os.environ.get("GMI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    port = int(os.environ.get("QWEN_PROXY_PORT", DEFAULT_PORT))
    log_path = Path(os.environ.get("QWEN_PROXY_LOG",
                                   Path.home() / ".codex-qwen" / "proxy.log"))
    log = file_logger(log_path)
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(upstream, key, log))
    log(event="start", port=port, upstream=upstream)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
