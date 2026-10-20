"""Check storyline approval and slide review before moving a deck."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "skills/docs/slide-workflow/scripts/storyline-gate-hook.sh"


def locate(deck_dir: Path, name: str) -> Path | None:
    for path in (deck_dir / name, deck_dir / "cache" / name):
        if path.is_file():
            return path
    return None


def hook_reason(stderr: str) -> str:
    content = stderr.strip()
    try:
        return str(json.loads(content)["reason"])
    except (ValueError, KeyError, TypeError):
        return content or "storyline gate 未提供原因"


def check_storyline(deck_dir: Path) -> tuple[bool, str]:
    path = locate(deck_dir, "storyline.md")
    if path is None:
        return False, f"storyline：未判讀（找不到 storyline.md）；路徑：{deck_dir / 'storyline.md'}"
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(deck_dir / "_preflight.pptx")},
        "cwd": str(deck_dir),
    }
    env = os.environ.copy()
    env.pop("SK_SKIP_STORYLINE_GATE", None)
    env["GIT_CEILING_DIRECTORIES"] = str(deck_dir.parent)
    if shutil.which("jq") is None:
        return False, f"storyline：未通過（找不到 jq，無法執行 storyline gate）；路徑：{path}"
    try:
        result = subprocess.run(
            [str(HOOK)], input=json.dumps(payload), text=True, capture_output=True,
            cwd=deck_dir, env=env, check=False,
        )
    except OSError as exc:
        return False, f"storyline：未通過（無法執行檢查：{exc}）；路徑：{path}"
    if result.returncode == 0:
        return True, f"storyline：通過；路徑：{path}"
    reason = hook_reason(result.stderr) if result.returncode == 2 else f"hook 結束碼 {result.returncode}：{result.stderr.strip()}"
    return False, f"storyline：未通過（{reason}）；路徑：{path}"


def review_status(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    status = None
    for line in lines[1:]:
        if line.strip() == "---":
            return status
        key, separator, value = line.partition(":")
        if separator and key.strip() == "status":
            status = value.strip().strip("\"'")
    return None


def check_review(deck_dir: Path) -> tuple[bool, str]:
    path = locate(deck_dir, "review.md")
    if path is None:
        return False, f"review：未判讀（找不到 review.md）；路徑：{deck_dir / 'review.md'}"
    try:
        status = review_status(path)
    except OSError as exc:
        return False, f"review：未通過（無法讀取 review.md：{exc}）；路徑：{path}"
    if status == "passed":
        return True, f"review：通過；路徑：{path}"
    return False, f"review：未通過（status 是「{status or '缺 status'}」，不是 passed）；路徑：{path}"


def main() -> int:
    parser = argparse.ArgumentParser(description="檢查簡報定稿條件")
    parser.add_argument("deck_dir", type=Path)
    args = parser.parse_args()
    deck_dir = args.deck_dir.expanduser().absolute()
    if not deck_dir.is_dir():
        print(f"簡報資料夾不存在：{deck_dir}", file=sys.stderr)
        return 1
    storyline_ok, storyline_line = check_storyline(deck_dir)
    review_ok, review_line = check_review(deck_dir)
    print(storyline_line)
    print(review_line)
    return 0 if storyline_ok and review_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
