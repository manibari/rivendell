"""Resolve machine-specific work folders from the shared registry."""
from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path


DEFAULT_CONF = Path(__file__).resolve().parents[1] / "data/work-roots.conf"


class WorkRootError(Exception):
    """A requested work root cannot be used."""


def current_host() -> str:
    return os.environ.get("SK_WORK_ROOTS_HOST", socket.gethostname()).split(".", 1)[0]


def config_path() -> Path:
    return Path(os.environ.get("SK_WORK_ROOTS_CONF", str(DEFAULT_CONF))).expanduser()


def rows_for_host(host: str) -> list[tuple[str, Path]]:
    try:
        lines = config_path().read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise WorkRootError(f"無法讀取 work roots 設定：{config_path()}（{exc.strerror}）") from exc

    rows: list[tuple[str, Path]] = []
    for number, line in enumerate(lines, 1):
        fields = [field.strip() for field in line.split("#", 1)[0].split("|")]
        if len(fields) == 1 and not fields[0]:
            continue
        if len(fields) != 4 or not all(fields[:3]):
            raise WorkRootError(f"work roots 設定第 {number} 行格式錯誤：{config_path()}")
        if fields[0].casefold() == host.casefold():
            rows.append((fields[1], Path(fields[2]).expanduser().absolute()))
    return rows


def resolve(key: str) -> Path:
    host = current_host()
    for row_key, path in rows_for_host(host):
        if row_key == key:
            if not path.is_dir():
                raise WorkRootError(f"{key} 登記的路徑不存在：{path}")
            return path
    raise WorkRootError(
        f"這台機器（{host}）沒有登記 {key}。請在 data/work-roots.conf 加一行："
        f"{host} | {key} | <路徑> | <說明>"
    )


def check() -> int:
    host = current_host()
    rows = rows_for_host(host)
    missing = 0
    for key, path in rows:
        exists = path.is_dir()
        missing += not exists
        print(f"{key} | {path} | {'存在' if exists else '不存在'}")
    print(f"work roots: {len(rows)} registered for {host}, {missing} missing")
    return 1 if not rows or missing else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="查詢這台機器登記的工作資料夾")
    subcommands = parser.add_subparsers(dest="command", required=True)
    get_parser = subcommands.add_parser("get", help="取得工作資料夾路徑")
    get_parser.add_argument("key")
    subcommands.add_parser("check", help="檢查登記的工作資料夾")
    args = parser.parse_args()
    try:
        if args.command == "check":
            return check()
        print(resolve(args.key))
        return 0
    except WorkRootError as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
