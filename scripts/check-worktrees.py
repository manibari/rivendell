#!/usr/bin/env python3
"""List stale linked git worktrees without changing them.

Usage: check-worktrees.py [--repo PATH] [--days N] [--json] [--now EPOCH]
Exit:  0 no stale worktrees; 1 any stale worktree; 2 git error.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class GitError(Exception):
    pass


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        # --no-optional-locks: `git status` must not rewrite another session's index.
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise GitError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def worktree_entries(output: str) -> list[dict[str, str | bool]]:
    entries: list[dict[str, str | bool]] = []
    for block in output.strip().split("\n\n"):
        if not block:
            continue
        entry: dict[str, str | bool] = {}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            entry[key] = value if value else True
        entries.append(entry)
    return entries


def status_path(line: str) -> str:
    path = line[3:]
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[1]
    if path.startswith('"') and path.endswith('"'):
        path = ast.literal_eval(path)
    return path


def display_name(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo.resolve()))
    except ValueError:
        return str(path)


def inspect(repo: Path, days: float, now: float) -> list[dict[str, object]]:
    entries = worktree_entries(git(repo, "worktree", "list", "--porcelain"))
    if not entries:
        return []
    main_ref = entries[0].get("branch")
    if not isinstance(main_ref, str):
        raise GitError("main worktree has no branch")
    main_branch = main_ref.removeprefix("refs/heads/")
    results: list[dict[str, object]] = []
    for entry in entries[1:]:
        if "bare" in entry:
            continue
        path = Path(str(entry["worktree"]))
        head = str(entry["HEAD"])
        missing = not path.exists()
        # The directory is there but its .git link is gone: git cannot read it.
        # Files may still sit in it (.env, work), so it is never safe to remove.
        broken = not missing and not (path / ".git").exists()
        branch_ref = entry.get("branch")
        branch = branch_ref.removeprefix("refs/heads/") if isinstance(branch_ref, str) else None
        detached_repo = missing or broken
        commit_time = int(git(repo if detached_repo else path, "log", "-1", "--format=%ct",
                              head if detached_repo else "HEAD").strip())
        if broken:
            ahead = None
            dirty = None
            last_active = max(commit_time, path.lstat().st_mtime)
        elif missing:
            ahead = None
            dirty = None
            last_active = commit_time
        else:
            ahead = int(git(path, "rev-list", "--count", f"{main_branch}..HEAD").strip())
            changes = git(path, "status", "--porcelain").splitlines()
            dirty = len(changes)
            last_active = commit_time
            for change in changes:
                changed_path = path / status_path(change)
                try:
                    last_active = max(last_active, changed_path.lstat().st_mtime)
                except FileNotFoundError:
                    pass
        idle_days = round((now - last_active) / 86400, 1)
        stale = missing or broken or idle_days >= days
        results.append({
            "path": str(path),
            "branch": branch,
            "head": head[:7],
            "ahead": ahead,
            "dirty": dirty,
            "last_active": last_active,
            "idle_days": idle_days,
            "stale": stale,
            "missing": missing,
            "broken": broken,
            "safe_to_remove": bool(missing or (stale and ahead == 0 and dirty == 0)),
        })
    return sorted(results, key=lambda item: float(item["idle_days"]), reverse=True)


def print_text(worktrees: list[dict[str, object]], repo: Path) -> None:
    for item in worktrees:
        name = display_name(Path(str(item["path"])), repo)
        mark = "STALE " if item["stale"] else "ok    "
        suffix = ""
        if item["safe_to_remove"]:
            suffix = "  safe to remove"
        elif item["broken"]:
            suffix = "  keep: no .git link, check the files by hand"
        elif item["stale"]:
            reasons = []
            if item["ahead"]:
                reasons.append(f"{item['ahead']} commits not in main")
            if item["dirty"]:
                reasons.append(f"{item['dirty']} changed files")
            suffix = "  keep: " + ", ".join(reasons)
        print(
            f"  {mark}  {name}  {item['branch'] or '(detached)'}"
            f"  idle {item['idle_days']:.1f}d  ahead {item['ahead']}"
            f"  dirty {item['dirty']}{suffix}"
        )
    for item in worktrees:
        if not item["safe_to_remove"]:
            continue
        if item["missing"]:
            print("  remove: git worktree prune")
        else:
            command = f"git worktree remove {shlex.quote(str(item['path']))}"
            if item["branch"]:
                command += f" && git branch -D {shlex.quote(str(item['branch']))}"
            print(f"  remove: {command}")
    count = len(worktrees)
    if not count:
        print("0 worktrees")
    else:
        stale = sum(bool(item["stale"]) for item in worktrees)
        safe = sum(bool(item["safe_to_remove"]) for item in worktrees)
        print(f"{count} worktrees, {stale} stale ({safe} safe to remove)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--days", type=float, default=3)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--now", type=float, default=None)
    args = parser.parse_args()
    try:
        worktrees = inspect(args.repo, args.days, time.time() if args.now is None else args.now)
    except GitError as error:
        print(error, file=sys.stderr)
        return 2
    stale = sum(bool(item["stale"]) for item in worktrees)
    safe = sum(bool(item["safe_to_remove"]) for item in worktrees)
    if args.json:
        print(json.dumps({"worktrees": worktrees, "stale": stale, "safe": safe}))
    else:
        print_text(worktrees, args.repo)
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
