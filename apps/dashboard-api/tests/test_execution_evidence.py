import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import LIB_DIR  # noqa: F401  (puts dashboard-legacy on sys.path)
from lib import evidence, roles
from lib.capabilities import project_roles


def _agent_runs(db: Path, rows: list[tuple]) -> None:
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE agent_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, agent_name TEXT, project TEXT, "
        "started_at TEXT, exit_code INTEGER, role TEXT, job TEXT, stage TEXT)"
    )
    conn.executemany(
        "INSERT INTO agent_runs (agent_name, project, started_at, exit_code, job, stage) VALUES (?, ?, ?, 0, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()


def _tags(logs: Path, lines: list[str]) -> None:
    (logs / "rivendell").mkdir(parents=True)
    (logs / "rivendell" / "tasks.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


class ExecutionEvidenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_dir = Path(self.tmp.name) / "data"
        self.db_dir.mkdir()
        self.logs = Path(self.tmp.name) / "logs"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def summary(self) -> dict:
        return evidence.job_summary(self.db_dir, self.logs)

    def test_empty_store_is_empty_not_ok(self) -> None:
        result = self.summary()
        self.assertEqual(result["status"], "empty")
        self.assertEqual(result["jobs"], {})

    def test_import_merges_sources_and_is_rerunnable(self) -> None:
        _agent_runs(self.db_dir / "rivendell.db", [
            ("harvest", "rivendell", "2026-09-20T03:00:00", "4a", "plan"),
            ("audit", "rivendell", "2026-09-21T03:00:00", None, None),
        ])
        _tags(self.logs, [
            json.dumps({"ts": "2026-09-22T10:00:00", "job": "4a", "stage": "do", "note": "x"}),
            json.dumps({"ts": "2026-09-23T10:00:00", "job": "1b", "stage": "Check"}),
        ])
        first = self.summary()
        second = self.summary()
        self.assertEqual(first["jobs"], second["jobs"])
        self.assertEqual(first["status"], "ok")
        self.assertEqual(first["jobs"]["4a"], {
            "runs": 2, "by_stage": {"plan": 1, "do": 1}, "last_run": "2026-09-22",
            "sources": {"agent_runs": 1, "session": 1},
        })
        self.assertEqual(first["jobs"]["1b"]["by_stage"], {"check": 1})
        self.assertEqual(second["sources"]["agent_runs"]["events"], 2)
        self.assertEqual(second["sources"]["agent_runs"]["imported"], 0)
        self.assertEqual(second["sources"]["session"]["imported"], 0)

    def test_new_run_after_cursor_is_imported(self) -> None:
        db = self.db_dir / "rivendell.db"
        _agent_runs(db, [("harvest", "rivendell", "2026-09-20T03:00:00", "4a", "plan")])
        self.summary()
        conn = sqlite3.connect(db)
        conn.execute("INSERT INTO agent_runs (agent_name, project, started_at, job, stage) "
                     "VALUES ('harvest', 'rivendell', '2026-09-24T03:00:00', '4a', 'act')")
        conn.commit()
        conn.close()
        self.assertEqual(self.summary()["jobs"]["4a"]["runs"], 2)

    def test_corrupt_store_is_unavailable_not_zero(self) -> None:
        (self.db_dir / "rivendell.db").write_text("not sqlite", encoding="utf-8")
        result = self.summary()
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("error", result)

    def test_unreadable_session_log_marks_unavailable(self) -> None:
        _tags(self.logs, [json.dumps({"ts": "2026-09-22T10:00:00", "job": "4a", "stage": "do"})])
        (self.logs / "rivendell" / "tasks.jsonl").chmod(0)
        try:
            result = self.summary()
        finally:
            (self.logs / "rivendell" / "tasks.jsonl").chmod(0o644)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["sources"]["session"]["status"], "unavailable")

    def test_bad_line_is_reported(self) -> None:
        _tags(self.logs, ["{broken", json.dumps({"ts": "2026-09-22T10:00:00", "job": "4a", "stage": "do"})])
        result = self.summary()
        self.assertEqual(result["jobs"]["4a"]["runs"], 1)
        self.assertEqual(len(result["sources"]["session"]["bad_lines"]), 1)

    def test_reconcile_lists_legacy_rows_missing_from_current(self) -> None:
        _agent_runs(self.db_dir / "rivendell.db", [("harvest", "rivendell", "2026-09-20T03:00:00", "4a", "plan")])
        legacy = Path(self.tmp.name) / "legacy.db"
        _agent_runs(legacy, [
            ("harvest", "rivendell", "2026-09-20T03:00:00", "4a", "plan"),
            ("old", "rivendell", "2026-08-01T03:00:00", None, None),
        ])
        self.summary()
        result = evidence.reconcile(legacy, self.db_dir)
        self.assertEqual(result["legacy"]["rows"], 2)
        self.assertEqual(result["current"]["rows"], 1)
        self.assertEqual(result["missing_from_current"], [["old", "2026-08-01T03:00:00"]])

    def test_role_projection_carries_unavailable_status(self) -> None:
        (self.db_dir / "rivendell.db").write_text("not sqlite", encoding="utf-8")
        with patch.object(evidence, "DB_DIR", self.db_dir), patch.object(evidence, "SESSION_LOGS", self.logs):
            projected = project_roles()
            parsed = roles.parse_roles()
        self.assertEqual(projected["evidence"]["status"], "unavailable")
        self.assertEqual(parsed["evidence"]["status"], "unavailable")
        self.assertEqual(projected["totals"]["runs"], 0)


if __name__ == "__main__":
    unittest.main()
