"""Tests for the finished deck index."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from deck_index import render, scan


SCRIPT = Path(__file__).with_name("deck_index.py")


class DeckIndexTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def add(self, relative: str, day: date) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"deck")
        stamp = datetime(day.year, day.month, day.day, 12).timestamp()
        os.utime(path, (stamp, stamp))
        return path

    def test_scan_metadata_exclusions_and_order(self) -> None:
        older = "內部/訓練/presentations/old.pdf"
        newer = "客戶/中華電/提案/甲/1-presales/presentations/sub/New.PPTX"
        product = "產品/平台/presentations/demo.key"
        other = "其他/對象/presentations/a.pdf"
        self.add(older, date(2025, 12, 1))
        self.add(newer, date(2026, 7, 7))
        self.add(product, date(2026, 7, 6))
        self.add(other, date(2026, 7, 5))
        for folder in ("cache", "workspace", "archive", "封存", "素材", "範本", ".hidden"):
            self.add(f"{folder}/presentations/skip.pdf", date(2026, 8, 1))
        self.add("客戶/甲/提案/乙/presentations/~$lock.pptx", date(2026, 8, 1))
        self.add("客戶/甲/提案/乙/draft.pdf", date(2026, 8, 1))
        decks = scan(self.root)
        self.assertEqual([deck.path.as_posix() for deck in decks], [newer, product, other, older])
        self.assertEqual((decks[0].category, decks[0].channel, decks[0].audience), ("客戶", "中華電", "甲"))
        self.assertEqual((decks[1].category, decks[1].channel, decks[1].audience), ("產品", "—", "平台"))
        self.assertEqual((decks[2].category, decks[2].channel, decks[2].audience), ("其他", "—", "對象"))
        output = render(self.root, date(2026, 10, 20))
        self.assertLess(output.index("## 2026"), output.index("## 2025"))
        self.assertIn(f"[New.PPTX](<{newer}>)", output)
        self.assertIn("共 4 份。", output)

    def test_empty_and_write(self) -> None:
        self.assertIn("共 0 份。", render(self.root, date(2026, 10, 20)))
        self.assertNotIn("## 2026", render(self.root, date(2026, 10, 20)))
        self.add("內部/團隊/presentations/deck.pdf", date(2026, 2, 3))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), "--write"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("共 1 份。", result.stdout)
        self.assertIn("deck.pdf", (self.root / "簡報索引.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
