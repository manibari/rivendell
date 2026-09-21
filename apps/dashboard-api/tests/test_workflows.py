import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from routes import workflows


class WorkflowTest(unittest.TestCase):
    def test_workflow_map_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "workflow-map.json"
            data = {"skillMeta": {"example": {}}, "tracks": [{"name": "example"}]}

            with patch.object(workflows, "_WORKFLOW_JSON", target):
                self.assertEqual(workflows.api_workflow_update(data), {"status": "ok"})
                self.assertEqual(workflows._load_workflow(), data)

        self.assertEqual(
            workflows.REPO_DIR / "platform" / "workflows" / "workflow-map.json",
            Path(__file__).resolve().parents[3] / "platform" / "workflows" / "workflow-map.json",
        )
