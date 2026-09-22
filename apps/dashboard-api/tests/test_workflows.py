import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from routes import workflows
from lib.capabilities import project_roles, validate
from lib.roles import parse_roles


class WorkflowTest(unittest.TestCase):
    def test_workflow_map_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "workflow-map.json"
            data = {"skillMeta": {"example": {}}, "tracks": [{"name": "example"}]}

            with patch.object(workflows, "_WORKFLOW_JSON", target):
                self.assertEqual(workflows.api_workflow_update(data), {"status": "ok"})
                self.assertEqual(workflows._load_workflow(), data)

        self.assertEqual(workflows._WORKFLOW_JSON, workflows.REPO_DIR / "platform" / "capabilities" / "workflows" / "workflow-map.json")

    def test_capability_definitions_preserve_role_contract(self) -> None:
        self.assertEqual(validate(), [])
        root = Path(__file__).resolve().parents[3]
        role_doc = root / "docs" / "skills-by-role.md"
        local = {path.parent.name for path in (root / "skills").glob("*/*/SKILL.md")}
        external = {ref["name"] for job in workflows.load_definitions()[1].values() for step in job["steps"] for ref in step["skill_refs"] if ref["source"] == "gstack"}
        self.assertEqual(project_roles(), parse_roles(role_doc, local | external))
        self.assertEqual(project_roles()["totals"]["jobs"], 44)

    def test_capability_playbooks_and_lookup(self) -> None:
        for flow_id in ("ui", "backend", "slide", "maintenance"):
            self.assertEqual(workflows.api_capability_playbook(flow_id)["workflow"]["id"], flow_id)
        self.assertEqual(workflows.api_capability_workflow("1a")["workflow"]["id"], "1a")
        self.assertEqual(len(workflows.api_capability_workflows()["workflows"]), 44)
