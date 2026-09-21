import tempfile
import unittest
from pathlib import Path

from lib import registry
from lib.registry import RegistryAgent


def _write(dir_path: Path, name: str, text: str) -> Path:
    p = dir_path / f"{name}.md"
    p.write_text(text)
    return p


SCRIPT_AGENT = """---
schema_version: 2
name: harvest
kind: script
enabled: true
project: rivendell
entry: bin/sk-harvest-cron
schedule:
  type: interval
  value: 28800
log_dir: reports
---

## Mission
Harvest skill candidates.
"""

SERVICE_AGENT = """---
name: api
kind: service
project: rivendell
entry: dashboard-next/start-api.sh
label: com.sk.dashboard.api
schedule:
  type: keepalive
  value: "-"
log_dir: logs
---
"""

OODA_AGENT = """---
name: quality-minister
kind: ooda
enabled: false
project: rivendell
pdca_role: check
mission: worker 報告有人判讀，異常一個心跳內變奏摺
mission_metric: 每次醒來未判讀報告數 == 0
memory_dir: agents/state/quality-minister/
observe:
  - reports/
skills:
  - session-harvest
schedule:
  type: interval
  value: 3600
---

## Mission
品質官敘述層。
"""


class ParseTest(unittest.TestCase):
    def test_parse_script_agent(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _write(Path(d), "harvest", SCRIPT_AGENT)
            a = registry.parse_registry_file(p)
        self.assertEqual(a.name, "harvest")
        self.assertEqual(a.kind, "script")
        self.assertTrue(a.enabled)
        self.assertEqual(a.schedule_type, "interval")
        self.assertEqual(a.schedule_value, "28800")
        self.assertIn("Harvest skill candidates", a.body)

    def test_label_derivation_and_override(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            harvest = registry.parse_registry_file(_write(Path(d), "harvest", SCRIPT_AGENT))
            api = registry.parse_registry_file(_write(Path(d), "api", SERVICE_AGENT))
        self.assertEqual(harvest.label, "com.sk.agent.rivendell.harvest")
        self.assertEqual(api.label, "com.sk.dashboard.api")  # override wins

    def test_conf_tuple_matches_columns(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            a = registry.parse_registry_file(_write(Path(d), "harvest", SCRIPT_AGENT))
        self.assertEqual(
            a.to_conf_tuple(),
            ("com.sk.agent.rivendell.harvest", "rivendell", "bin/sk-harvest-cron",
             "interval", "28800", "reports", ""),
        )

    def test_missing_frontmatter_raises(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _write(Path(d), "bad", "no frontmatter here")
            with self.assertRaises(ValueError):
                registry.parse_registry_file(p)


class ValidateTest(unittest.TestCase):
    def test_valid_script_agent_passes(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            a = registry.parse_registry_file(_write(Path(d), "harvest", SCRIPT_AGENT))
        self.assertEqual(registry.validate(a), [])

    def test_filename_must_equal_name(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            a = registry.parse_registry_file(_write(Path(d), "wrongname", SCRIPT_AGENT))
        fails = [f for f in registry.validate(a) if f.level == "FAIL"]
        self.assertTrue(any("filename" in f.message for f in fails))

    def test_bad_kind_fails(self) -> None:
        a = RegistryAgent(name="x", kind="banana", project="rivendell",
                          schedule_type="interval", schedule_value="60", entry="e")
        fails = [f for f in registry.validate(a) if f.level == "FAIL"]
        self.assertTrue(any("kind must be one of" in f.message for f in fails))

    def test_script_requires_entry(self) -> None:
        a = RegistryAgent(name="x", kind="script", project="rivendell",
                          schedule_type="interval", schedule_value="60")
        fails = [f for f in registry.validate(a) if f.level == "FAIL"]
        self.assertTrue(any("requires entry" in f.message for f in fails))

    def test_ooda_disabled_passes_but_enabled_fails_without_executor(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            a = registry.parse_registry_file(_write(Path(d), "quality-minister", OODA_AGENT))
        # enabled:false → no executor complaint
        self.assertEqual([f for f in registry.validate(a) if f.level == "FAIL"], [])
        # flip enabled:true → D6 guard fires
        a.enabled = True
        fails = [f for f in registry.validate(a) if f.level == "FAIL"]
        self.assertTrue(any("executor" in f.message for f in fails))

    def test_ooda_requires_mission_and_role(self) -> None:
        a = RegistryAgent(name="m", kind="ooda", project="rivendell",
                          schedule_type="interval", schedule_value="3600", enabled=False)
        fails = [f for f in registry.validate(a) if f.level == "FAIL"]
        msgs = " ".join(f.message for f in fails)
        self.assertIn("pdca_role", msgs)
        self.assertIn("mission", msgs)
        self.assertIn("memory_dir", msgs)

    def test_skill_whitelist_existence(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            a = registry.parse_registry_file(_write(Path(d), "quality-minister", OODA_AGENT))
        fails = registry.validate(a, known_skills={"skill-creator"})  # session-harvest absent
        self.assertTrue(any("not found" in f.message for f in fails))
        # present → no skill complaint
        ok = registry.validate(a, known_skills={"session-harvest"})
        self.assertFalse(any("not found" in f.message for f in ok))


class CollisionTest(unittest.TestCase):
    def test_duplicate_name_and_label(self) -> None:
        a = RegistryAgent(name="dup", kind="script", project="rivendell",
                          entry="e", schedule_type="interval", schedule_value="60",
                          source_path=Path("a/dup.md"))
        b = RegistryAgent(name="dup", kind="script", project="rivendell",
                          entry="e", schedule_type="interval", schedule_value="60",
                          source_path=Path("b/dup.md"))
        fails = registry.check_label_collisions([a, b])
        self.assertTrue(any("duplicate name" in f.message for f in fails))
        self.assertTrue(any("duplicate label" in f.message for f in fails))


if __name__ == "__main__":
    unittest.main()
