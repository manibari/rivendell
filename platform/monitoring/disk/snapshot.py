#!/usr/bin/env python3
"""Disk-usage snapshot for the dashboard 磁碟容量 (WizTree-like) treemap.

Runs `du` over $HOME, builds a nested size tree, and writes JSON to
dashboard/data/disk-tree.json. Every folder down to DEPTH is listed. Below that,
down to MAX_DEPTH, only folders of at least MIN_MB are listed, so a large folder
can be opened level by level without a huge file. Meant to run from sk-disk-monitor-cron
(daily): du is slow on large trees, so the dashboard reads this cached snapshot
instead of scanning on the request path (user chose "cron 預掃快照").

Env overrides:
  SK_DISK_SNAPSHOT_ROOT   default $HOME
  SK_DISK_SNAPSHOT_DEPTH  default 3 (every folder to this depth; sizes include the full subtree)
  SK_DISK_SNAPSHOT_MAX_DEPTH  default 8 (du -d depth for the large folders)
  SK_DISK_SNAPSHOT_MIN_MB     default 100 (smallest folder listed below DEPTH)
  SK_DISK_SNAPSHOT_TIMEOUT_SEC  default 10800 (stop du; keep the previous snapshot)
  REPO_DIR                default <this script>/..
"""
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = os.environ.get("SK_DISK_SNAPSHOT_ROOT", os.path.expanduser("~"))
DEPTH = int(os.environ.get("SK_DISK_SNAPSHOT_DEPTH", "3"))
MAX_DEPTH = max(DEPTH, int(os.environ.get("SK_DISK_SNAPSHOT_MAX_DEPTH", "8")))
MIN_KB = int(os.environ.get("SK_DISK_SNAPSHOT_MIN_MB", "100")) * 1024
TIMEOUT_SEC = int(os.environ.get("SK_DISK_SNAPSHOT_TIMEOUT_SEC", "10800"))
TASKPOLICY = "/usr/sbin/taskpolicy"  # not on the launchd PATH
REPO_DIR = Path(os.environ.get("REPO_DIR", str(Path(__file__).resolve().parent.parent.parent.parent)))
OUT = REPO_DIR / "apps" / "dashboard-legacy" / "data" / "disk-tree.json"


def run_du(root: str, depth: int) -> list[tuple[int, str]]:
    """`du -k -d<depth> <root>` → [(size_kb, path)]. Ignores stderr warnings."""
    # An `open` on some folders can wait without end (seen 2026-11-02: du stopped
    # for over 10 minutes in open(); a 2026-11-01 run took 14.5 h). On timeout the
    # previous snapshot stays.
    cmd = ["du", "-k", "-d", str(depth), root]
    # The launchd agent runs at background I/O priority: du took 7 h there and
    # 4 min in a shell (2026-11-02). Ask for normal I/O priority. The
    # background scope accepts only utility or default.
    if os.path.exists(TASKPOLICY):
        cmd = [TASKPOLICY, "-d", "important", "-g", "utility"] + cmd
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SEC,
    )
    out: list[tuple[int, str]] = []
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        try:
            size_str, path = line.split("\t", 1)
            out.append((int(size_str), path))
        except ValueError:
            continue
    return out


def keep_lines(lines: list[tuple[int, str]], root: str, depth: int, min_kb: int) -> list[tuple[int, str]]:
    """Keep every folder down to `depth`, and deeper folders of at least `min_kb`.

    A kept deep folder always has a kept parent: the parent is at least as large.
    """
    base = root.rstrip("/").count("/")
    return [
        (size_kb, path)
        for size_kb, path in lines
        if path.rstrip("/").count("/") - base <= depth or size_kb >= min_kb
    ]


def build_tree(lines: list[tuple[int, str]], root: str) -> dict | None:
    """Link the flat du list into a nested {name,path,size_kb,children} tree."""
    nodes: dict[str, dict] = {}
    for size_kb, path in lines:
        nodes[path] = {
            "name": os.path.basename(path) or path,
            "path": path,
            "size_kb": size_kb,
            "children": [],
        }
    for path, node in nodes.items():
        if path == root:
            continue
        parent = os.path.dirname(path)
        if parent in nodes:
            nodes[parent]["children"].append(node)
    for node in nodes.values():
        node["children"].sort(key=lambda c: c["size_kb"], reverse=True)
    return nodes.get(root)


def df_summary(root: str) -> dict:
    res = subprocess.run(["df", "-k", root], capture_output=True, text=True)
    fields = res.stdout.strip().splitlines()[-1].split()
    # Filesystem 1024-blocks Used Avail Capacity ... MountedOn
    return {
        "size_kb": int(fields[1]),
        "used_kb": int(fields[2]),
        "avail_kb": int(fields[3]),
        "percent": int(fields[4].rstrip("%")),
        "mount": fields[-1],
    }


def main() -> None:
    start = time.time()
    try:
        raw = run_du(ROOT, MAX_DEPTH)
    except subprocess.TimeoutExpired:
        raise SystemExit(f"du did not finish in {TIMEOUT_SEC}s; kept the previous snapshot {OUT}")
    lines = keep_lines(raw, ROOT, DEPTH, MIN_KB)
    tree = build_tree(lines, ROOT)
    payload = {
        "root": ROOT,
        "depth": DEPTH,
        "max_depth": MAX_DEPTH,
        "min_kb": MIN_KB,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration_sec": round(time.time() - start, 1),
        "df": df_summary(ROOT),
        "tree": tree,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload))
    tmp.replace(OUT)  # atomic
    print(f"Wrote {OUT} ({len(lines)} dirs, {payload['duration_sec']}s)")


if __name__ == "__main__":
    main()
