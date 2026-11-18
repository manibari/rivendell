"""Call Gemini through the Chimes GPT Gateway (Responses API).

The key comes from $CHIMES_GATEWAY_API_KEY or the Keychain item "sk-chimes-gateway-key"
(the same item that agent-code-dispatch uses). The key is never printed.
"""
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

GATEWAY_URL = os.environ.get("CHIMES_GATEWAY_BASE_URL", "https://gpt-gateway.chimes.ai/v1")
MODEL = os.environ.get("TOKEN_WATCH_MODEL", "gemini-4-argon")
KEYCHAIN_SERVICE = "sk-chimes-gateway-key"


def _key() -> str:
    key = os.environ.get("CHIMES_GATEWAY_API_KEY")
    if key:
        return key
    out = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
                         capture_output=True, text=True)
    if out.returncode != 0 or not out.stdout.strip():
        raise RuntimeError(f"no gateway key: Keychain item '{KEYCHAIN_SERVICE}' not found")
    return out.stdout.strip()


def extract_text(data: dict) -> str:
    """Join the output text parts of one Responses API reply."""
    texts = []
    for item in data.get("output") or []:
        for part in item.get("content") or []:
            if part.get("type") in ("output_text", "text") and part.get("text"):
                texts.append(part["text"])
    if not texts and data.get("output_text"):
        texts.append(data["output_text"])
    return "\n".join(texts).strip()


def ask(instructions: str, prompt: str, timeout: int = 600) -> tuple[str, dict]:
    body = json.dumps({"model": MODEL, "instructions": instructions, "input": prompt}).encode()
    req = urllib.request.Request(f"{GATEWAY_URL}/responses", data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {_key()}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"gateway HTTP {e.code}: {e.read()[:300].decode(errors='replace')}") from None
    usage = data.get("usage") or {}
    log_path = Path(os.environ.get("GEMINI_GATEWAY_LOG", str(Path.home() / ".codex-gemini" / "gateway-calls.jsonl")))
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(json.dumps({
                "ts": time.time(), "model": MODEL,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "caller": "token-waste-watch",
            }) + "\n")
    except OSError:
        pass
    return extract_text(data), usage


if __name__ == "__main__":
    text, usage = ask("Answer in one word.", "Say ok.", timeout=120)
    print(repr(text), {k: usage.get(k) for k in ("input_tokens", "output_tokens")})
