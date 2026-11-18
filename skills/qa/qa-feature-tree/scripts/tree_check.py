#!/usr/bin/env python3
"""CLI for validating and checking a feature tree."""

import argparse
import json
import sys
from pathlib import Path

from feature_tree import folders, fmt, report, routes, schema, screens, tests_check
from feature_tree.common import read_json


def parser():
    root = argparse.ArgumentParser(description="檢查功能樹")
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("validate", "fmt", "init", "adopt", "folders", "routes", "screens", "tests", "render", "report"):
        command = commands.add_parser(name)
        command.add_argument("tree")
        command.add_argument("--repo", default=".")
        command.add_argument("--json", action="store_true")
        if name == "fmt":
            command.add_argument("--check", action="store_true")
        if name in ("adopt", "screens", "report"):
            command.add_argument("--scan")
        if name in ("tests", "report"):
            command.add_argument("--e2e-report")
        if name in ("render", "report"):
            command.add_argument("--out", required=True)
        if name == "report":
            command.add_argument("--strict", action="store_true")
    return root


def output(rows, machine):
    if machine:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif isinstance(rows, list):
        if not rows:
            print("沒有問題")
        for item in rows:
            print(f"{item['code']} {item['place']}：{item['detail']}")
    elif isinstance(rows, dict):
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(rows)


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        tree_path = Path(args.tree)
        tree = read_json(tree_path)
        if not isinstance(tree, dict) or tree.get("schema") != 1:
            raise ValueError("樹的 schema 版本必須是 1")
        repo = Path(args.repo).resolve()
        if args.command == "fmt":
            canonical = fmt.canonical(tree)
            if args.check:
                equal = tree_path.read_text(encoding="utf-8") == canonical
                output({"canonical": equal} if args.json else ("格式正確" if equal else "格式不符合標準"), args.json)
                return 0 if equal else 1
            tree_path.write_text(canonical, encoding="utf-8")
            output("已格式化", args.json)
            return 0
        if args.command == "validate":
            rows = schema.validate(tree)
            output(rows, args.json)
            return 1 if rows else 0
        if args.command == "init":
            unclaimed = routes.initialize(tree, repo)
            tree_path.write_text(fmt.canonical(tree), encoding="utf-8")
            output({"unclaimed": unclaimed} if args.json else "未認領來源檔案：\n" + "\n".join(unclaimed), args.json)
            return 0
        if args.command in ("adopt", "screens"):
            if not args.scan:
                raise ValueError("需要 --scan <scan.json>")
            scan = read_json(args.scan)
            if args.command == "adopt":
                count = screens.adopt(tree, scan)
                tree_path.write_text(fmt.canonical(tree), encoding="utf-8")
                output({"added": count} if args.json else f"已新增 {count} 個草稿控制項", args.json)
                return 0
            rows = screens.check(tree, scan)
        elif args.command == "folders":
            rows = folders.check(tree, repo)
        elif args.command == "routes":
            rows = routes.check(tree, repo)
        elif args.command == "tests":
            report_path = Path(args.e2e_report) if args.e2e_report else repo / tree.get("config", {}).get("e2e_report", "")
            if args.e2e_report and not report_path.is_file():
                raise FileNotFoundError(report_path)
            result = read_json(report_path) if report_path.is_file() else None
            rows, statuses = tests_check.check(tree, repo, result)
            output({"rows": rows, "leaves": statuses} if args.json else rows, args.json)
            return 0
        elif args.command == "render":
            Path(args.out).write_text(report.render(tree), encoding="utf-8")
            output("已寫入功能樹", args.json)
            return 0
        elif args.command == "report":
            report_path = Path(args.e2e_report) if args.e2e_report else repo / tree.get("config", {}).get("e2e_report", "")
            if args.e2e_report and not report_path.is_file():
                raise FileNotFoundError(report_path)
            result = read_json(report_path) if report_path.is_file() else None
            sections = [schema.validate(tree), folders.check(tree, repo), routes.check(tree, repo),
                        screens.check(tree, read_json(args.scan)) if args.scan else [], None]
            sections[4], statuses = tests_check.check(tree, repo, result)
            if not args.scan:
                from feature_tree.common import row
                sections[3].append(row("NOT_SCANNED", "--scan", "未掃描畫面", "yellow"))
            content = report.build(tree, sections, statuses)
            Path(args.out).write_text(content, encoding="utf-8")
            if args.json:
                output({"sections": sections, "leaves": statuses}, True)
            else:
                print(content.splitlines()[0])
            return 1 if args.strict and any(item["severity"] == "red" for section in sections for item in section) else 0
        output(rows, args.json)
        return 0
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as error:
        print(f"輸入錯誤：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
