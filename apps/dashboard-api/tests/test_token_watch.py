import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server
from routes.monitoring import token_watch


class TokenWatchTest(unittest.TestCase):
    def test_routes_appear_in_openapi(self) -> None:
        paths = server.app.openapi()["paths"]
        self.assertIn("/api/tokens/waste-reports", paths)
        self.assertIn("/api/tokens/waste-reports/{name}", paths)

    def test_list_filters_parses_and_orders_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = root / "token-watch-2026-11-17-laptop.md"
            older.write_text("# Report\n", encoding="utf-8")
            early = root / "token-watch-2026-11-18-dev-box.md"
            early.write_text("- 資料區間：2026-11-17 09:00 到 2026-11-18 09:00\n", encoding="utf-8")
            latest = root / "token-watch-2026-11-18-laptop.md"
            latest.write_text("## 判讀失敗\n", encoding="utf-8")
            (root / "token-analysis-2026-11-18-laptop.md").write_text("ignored", encoding="utf-8")
            (root / "token-watch-2026-11-18-Bad.md").write_text("ignored", encoding="utf-8")
            os.utime(older, (100, 100))
            os.utime(early, (200, 200))
            os.utime(latest, (300, 300))

            with patch.dict(os.environ, {"REPORTS_DIR": tmp}):
                reports = token_watch.api_token_waste_reports()["reports"]

            self.assertEqual([item["name"] for item in reports],
                             [latest.name, early.name, older.name])
            self.assertEqual(reports[0]["day"], "2026-11-18")
            self.assertEqual(reports[0]["host"], "laptop")
            self.assertEqual(reports[0]["updated_at"],
                             datetime.fromtimestamp(300).isoformat(timespec="minutes"))
            self.assertTrue(reports[0]["failed"])
            self.assertIsNone(reports[0]["window"])
            self.assertEqual(reports[1]["window"],
                             ["2026-11-17 09:00", "2026-11-18 09:00"])
            self.assertFalse(reports[1]["failed"])

    def test_detail_and_invalid_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            name = "token-watch-2026-11-18-dev-box.md"
            (Path(tmp) / name).write_text("## 結論\n\n內容\n", encoding="utf-8")
            with patch.dict(os.environ, {"REPORTS_DIR": tmp}):
                detail = token_watch.api_token_waste_report(name)
                self.assertEqual(detail["name"], name)
                self.assertEqual(detail["markdown"], "## 結論\n\n內容\n")
                self.assertIn("updated_at", detail)
                for invalid in ("../token-watch-2026-11-18-dev-box.md",
                                "..%2Ftoken-watch-2026-11-18-dev-box.md",
                                "token-analysis-2026-11-18-dev-box.md",
                                "token-watch-2026-11-19-missing.md"):
                    with self.subTest(name=invalid), self.assertRaises(HTTPException) as raised:
                        token_watch.api_token_waste_report(invalid)
                    self.assertEqual(raised.exception.status_code, 404)
                    self.assertEqual(raised.exception.detail, "找不到報告。")


if __name__ == "__main__":
    unittest.main()
