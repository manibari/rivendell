#!/usr/bin/env python3
"""Recover context from a previous planning session.

Usage: session-catchup.py [project_dir]
"""

import subprocess
import sys
from pathlib import Path


def read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError):
        return None


def git_diff_stat(project_dir: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD~5..HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


def extract_current_phase(plan_text: str) -> str:
    """Find the first in_progress phase from task_plan.md."""
    lines = plan_text.splitlines()
    for i, line in enumerate(lines):
        if "in_progress" in line.lower():
            # Look for the nearest heading above
            for j in range(i, -1, -1):
                if lines[j].startswith("#"):
                    return lines[j].lstrip("#").strip()
            return line.strip()
    return "No active phase found"


def extract_recent_progress(progress_text: str, max_lines: int = 15) -> str:
    """Get the last session entries from progress.md."""
    lines = progress_text.splitlines()
    # Find last "## Session" heading
    last_session_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("## Session") or line.startswith("## session"):
            last_session_idx = i
    if last_session_idx >= 0:
        return "\n".join(lines[last_session_idx : last_session_idx + max_lines])
    # Fallback: last N lines
    return "\n".join(lines[-max_lines:])


def main() -> None:
    project_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    plan = read_file(project_dir / "task_plan.md")
    findings = read_file(project_dir / "findings.md")
    progress = read_file(project_dir / "progress.md")

    if not any([plan, findings, progress]):
        print("[planning-with-files] No planning files found. Starting fresh.")
        return

    print("=" * 60)
    print("  SESSION CATCHUP REPORT")
    print("=" * 60)

    if plan:
        phase = extract_current_phase(plan)
        print(f"\n## Current Phase: {phase}")

    diff = git_diff_stat(project_dir)
    if diff:
        print(f"\n## Recent Git Changes (last 5 commits):\n{diff}")

    if progress:
        recent = extract_recent_progress(progress)
        print(f"\n## Last Session Progress:\n{recent}")

    if findings:
        finding_lines = findings.splitlines()
        heading_count = sum(1 for l in finding_lines if l.startswith("##"))
        print(f"\n## Findings: {heading_count} topic(s) recorded in findings.md")

    print("\n" + "=" * 60)
    print("  Review planning files and git diff before proceeding.")
    print("=" * 60)


if __name__ == "__main__":
    main()
