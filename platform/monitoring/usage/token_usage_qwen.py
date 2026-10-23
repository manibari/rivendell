"""Token usage from Qwen runs driven through the Codex CLI.

Qwen (GMI-hosted Qwen3.x) runs as `codex exec -c model_provider=gmi ...` with
a throwaway CODEX_HOME inside a Claude Code session scratchpad
(/private/tmp/claude-<uid>/<project>/<session>/scratchpad/<home>/sessions/...).
The rollout format is the Codex one, so tokens_codex.parse_codex_session reads
it unchanged. Two gaps this module closes:

  - Discovery: ~/.codex/sessions is the only root the Codex reader scans, and
    the scratchpad is deleted with the session. mirror_qwen_rollouts() copies
    each Qwen rollout it finds there into QWEN_SESSION_DIR, which outlives it.
  - Pricing: a Qwen model name matches no Codex prefix and no Claude price, so
    it fell through to the Claude default price. GMI prices are not recorded
    here, so Qwen cost is 0 and the row is flagged `billing: unpriced`.

Added 2026-10-06 (Peter): the /tokens page must show Qwen usage.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

# Durable home for Qwen rollouts. Also a valid CODEX_HOME: a Qwen run started
# with CODEX_HOME=~/.codex-qwen writes here directly and needs no mirror.
QWEN_HOME = Path.home() / ".codex-qwen"
QWEN_SESSION_DIR = QWEN_HOME / "sessions"

# Claude Code session scratchpads: <root>/<project>/<session>/scratchpad
_SCRATCH_ROOT = Path(f"/private/tmp/claude-{os.getuid()}")
# CODEX_HOME depth under the scratchpad: scratchpad/<home>, scratchpad/<a>/<home>, ...
_HOME_DEPTHS = ("*", "*/*", "*/*/*")
_HEAD_LINES = 40  # session_meta + turn_context sit at the top of a rollout


def is_qwen_model(model: str) -> bool:
    return "qwen" in (model or "").lower()


def _rollout_model(path: Path) -> str:
    """Model named at the top of a rollout (turn_context wins over session_meta)."""
    model = ""
    try:
        with open(path) as f:
            for i, line in enumerate(f):
                if i >= _HEAD_LINES:
                    break
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") in ("session_meta", "turn_context"):
                    model = (entry.get("payload") or {}).get("model") or model
    except OSError:
        return ""
    return model


def _scratch_rollouts() -> list[Path]:
    if not _SCRATCH_ROOT.is_dir():
        return []
    found: list[Path] = []
    for depth in _HOME_DEPTHS:
        pattern = f"*/*/scratchpad/{depth}/sessions/*/*/*/rollout-*.jsonl"
        found.extend(_SCRATCH_ROOT.glob(pattern))
    return found


def mirror_qwen_rollouts() -> int:
    """Copy new or grown Qwen rollouts from scratchpads into QWEN_SESSION_DIR.

    The relative path below `sessions/` is kept, so a rollout keeps one
    destination and an active run is re-copied as it grows. Returns the copy
    count. Rollouts of other models (GPT runs in a temp home) are left alone.
    """
    copied = 0
    for src in _scratch_rollouts():
        rel = Path(*src.parts[src.parts.index("sessions") + 1:])
        dst = QWEN_SESSION_DIR / rel
        try:
            st = src.stat()
            if dst.exists():
                dt = dst.stat()
                if dt.st_size == st.st_size and dt.st_mtime >= st.st_mtime:
                    continue
            elif not is_qwen_model(_rollout_model(src)):
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
        except OSError:
            continue
    return copied


def iter_qwen_sessions() -> list[Path]:
    """Qwen rollouts in the durable home, after a mirror pass."""
    mirror_qwen_rollouts()
    if not QWEN_SESSION_DIR.is_dir():
        return []
    return list(QWEN_SESSION_DIR.rglob("*.jsonl"))
