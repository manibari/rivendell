"""Find leaf tags and combine them with Playwright results."""

import re
from pathlib import Path

from .common import leaves, row

TAG = re.compile(r"@?leaf:([a-z0-9-]+(?:\.[a-z0-9-]+){3})")
SUFFIXES = {".ts", ".tsx", ".js", ".mjs", ".py"}
FAILURE = {"failed", "timedOut", "interrupted", "timedout", "timed-out"}


def file_tags(tree, repo):
    tags = set()
    for directory in tree.get("config", {}).get("e2e_dirs", []):
        base = Path(repo, directory)
        if not base.exists():
            continue
        for file in base.rglob("*"):
            if file.is_file() and file.suffix in SUFFIXES:
                tags.update(TAG.findall(file.read_text(encoding="utf-8")))
    return tags


def result_statuses(report):
    statuses = {}

    def visit(suite):
        for spec in suite.get("specs", []):
            tags = set(TAG.findall(spec.get("title", "")))
            for tag in spec.get("tags", []):
                tags.update(TAG.findall(tag))
            for test in spec.get("tests", []):
                results = test.get("results", [])
                if results:
                    for tag in tags:
                        statuses.setdefault(tag, []).append(results[-1].get("status"))
        for child in suite.get("suites", []):
            visit(child)

    for suite in report.get("suites", []):
        visit(suite)
    return statuses


def check(tree, repo, report=None):
    tags = file_tags(tree, repo)
    statuses = result_statuses(report or {})
    known = dict(leaves(tree))
    rows = [row("STALE", tag, "測試標籤沒有對應的葉子") for tag in sorted(tags - known.keys())]
    leaf_status = {}
    for leaf, case in known.items():
        if case.get("status") == "na":
            status = "na"
        elif leaf in tags and any(result in FAILURE for result in statuses.get(leaf, [])):
            status = "failed"
        elif leaf in tags and "passed" in statuses.get(leaf, []):
            status = "passed"
        elif leaf in tags:
            status = "not-run"
        else:
            status = "no-test"
        leaf_status[leaf] = status
        if status == "failed":
            rows.append(row("FAILED", leaf, "端到端測試失敗"))
        elif status == "not-run":
            rows.append(row("NOT_RUN", leaf, "測試有標籤，但最近報告沒有結果", "yellow"))
        elif status == "no-test":
            rows.append(row("NO_TEST", leaf, "葉子沒有端到端測試"))
    return rows, leaf_status
