#!/usr/bin/env python3
"""Disk-usage snapshot for the dashboard 磁碟容量 (WizTree-like) treemap.

Runs `du` over $HOME to a bounded depth, builds a nested size tree, and writes
JSON to dashboard/data/disk-tree.json. Meant to run from sk-disk-monitor-cron
(daily): du is slow on large trees, so the dashboard reads this cached snapshot
instead of scanning on the request path (user chose "cron 預掃快照").

Env overrides:
  SK_DISK_SNAPSHOT_ROOT   default $HOME
  SK_DISK_SNAPSHOT_DEPTH  default 3 (du -d depth; sizes still include full subtree)
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
REPO_DIR = Path(os.environ.get("REPO_DIR", str(Path(__file__).resolve().parent.parent.parent.parent)))
OUT = REPO_DIR / "apps" / "dashboard-legacy" / "data" / "disk-tree.json"


def run_du(root: str, depth: int) -> list[tuple[int, str]]:
    """`du -k -d<depth> <root>` → [(size_kb, path)]. Ignores stderr warnings."""
    res = subprocess.run(
        ["du", "-k", "-d", str(depth), root],
        capture_output=True,
        text=True,
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
    lines = run_du(ROOT, DEPTH)
    tree = build_tree(lines, ROOT)
    payload = {
        "root": ROOT,
        "depth": DEPTH,
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
