"""Index finished presentation files in a registered work folder."""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from work_roots import WorkRootError, resolve


SKIP_DIRS = {"cache", "workspace", "archive", "封存", "素材", "範本"}
EXTENSIONS = {".pptx", ".pdf", ".key"}


@dataclass(frozen=True)
class Deck:
    path: Path
    date: date
    category: str
    channel: str
    audience: str


def scan(root: Path) -> list[Deck]:
    decks: list[Deck] = []
    for directory, directories, files in os.walk(root):
        directories[:] = sorted(
            name for name in directories if not name.startswith(".") and name not in SKIP_DIRS
        )
        current = Path(directory)
        parts = current.relative_to(root).parts
        if "presentations" not in parts:
            continue
        for name in files:
            path = current / name
            if name.startswith("~$") or path.suffix.lower() not in EXTENSIONS:
                continue
            relative = path.relative_to(root)
            pieces = relative.parts
            if pieces[0] == "客戶" and len(pieces) >= 4:
                category, channel, audience = "客戶", pieces[1], pieces[3]
            elif pieces[0] in {"內部", "產品"} and len(pieces) >= 2:
                category, channel, audience = pieces[0], "—", pieces[1]
            else:
                category = pieces[0]
                channel = "—"
                audience = pieces[1] if len(pieces) >= 2 else "—"
            modified = datetime.fromtimestamp(path.stat().st_mtime).date()
            decks.append(Deck(relative, modified, category, channel, audience))
    return sorted(decks, key=lambda deck: (-deck.date.toordinal(), deck.path.as_posix()))


def render(root: Path, generated_date: date) -> str:
    decks = scan(root)
    lines = [
        "# 簡報索引",
        "",
        f"> 由 rivendell `scripts/deck_index.py` 產生（{generated_date.isoformat()}）。只列 `presentations/` 資料夾裡的檔案，草稿（`cache/`）不列。不要手動修改，重跑 `sk deck-index --write`。",
        "",
    ]
    year = None
    for deck in decks:
        if deck.date.year != year:
            year = deck.date.year
            lines.extend([
                f"## {year}", "", "| 日期 | 類別 | 通路 | 對象 | 檔案 |",
                "|---|---|---|---|---|",
            ])
        target = deck.path.as_posix()
        lines.append(
            f"| {deck.date.isoformat()} | {deck.category} | {deck.channel} | "
            f"{deck.audience} | [{deck.path.name}](<{target}>) |"
        )
    if decks:
        lines.append("")
    lines.append(f"共 {len(decks)} 份。")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="建立已完成簡報的索引")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        root = args.root.expanduser().absolute() if args.root else resolve("chimes-work")
        if not root.is_dir():
            raise ValueError(f"工作資料夾不存在：{root}")
        output = render(root, date.today())
        if args.write:
            target = root / "簡報索引.md"
            target.write_text(output, encoding="utf-8")
            print(f"{target}：共 {len(scan(root))} 份。")
        else:
            print(output, end="")
        return 0
    except (OSError, ValueError, WorkRootError) as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
