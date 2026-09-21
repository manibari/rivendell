"""Read Claude Code hooks from ~/.claude/settings.json."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


@dataclass
class HookInfo:
    event: str
    matcher: str
    command: str
    script_path: str | None


def _resolve_script_path(command: str) -> str | None:
    """Try to extract the script path from a hook command string."""
    # Expand ~ and check if any token is a file path
    parts = command.split()
    for part in parts:
        expanded = Path(part).expanduser()
        if expanded.is_file():
            return str(expanded)
    return None


def list_hooks(settings_path: Path | None = None) -> list[HookInfo]:
    """Parse hooks section from Claude settings.json.

    Returns a flat list of HookInfo, one per hook command.
    """
    path = settings_path or SETTINGS_PATH
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    hooks_section: dict[str, Any] = data.get("hooks", {})
    result: list[HookInfo] = []

    for event, matchers in hooks_section.items():
        if not isinstance(matchers, list):
            continue
        for matcher_block in matchers:
            matcher = matcher_block.get("matcher", "")
            hook_list = matcher_block.get("hooks", [])
            for hook in hook_list:
                command = hook.get("command", "")
                script_path = _resolve_script_path(command)
                result.append(HookInfo(
                    event=event,
                    matcher=matcher,
                    command=command,
                    script_path=script_path,
                ))
    return result


def backup_settings(settings_path: Path | None = None) -> Path:
    """Create a timestamped backup of settings.json before modifications.

    Returns the backup file path.
    """
    path = settings_path or SETTINGS_PATH
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"settings.json.bak.{timestamp}")
    shutil.copy2(path, backup)
    return backup
