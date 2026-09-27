import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server
from routes import deployment


class PortsTest(unittest.TestCase):
    def test_parse_compose_host_port_short_and_long_syntax(self) -> None:
        cases = [
            ("8000:8000", 8000),
            ("127.0.0.1:3000:3000", 3000),
            ("8501:8501/tcp", 8501),
            ({"published": "3004", "target": 3000}, 3004),
            ("3000", None),
            ({"target": 3000}, None),
        ]

        for spec, expected in cases:
            with self.subTest(spec=spec):
                self.assertEqual(deployment._parse_compose_host_port(spec), expected)

    def _run(self, conf: str, listeners: dict, docker: dict) -> dict:
        from lib import port_registry as pr

        compose = "services: {}\n"
        with tempfile.TemporaryDirectory() as tmp:
            conf_path = Path(tmp) / "ports.conf"
            conf_path.write_text(conf, encoding="utf-8")
            compose_path = Path(tmp) / "docker-compose.yml"
            compose_path.write_text(compose, encoding="utf-8")
            env = {"RIVENDELL_PORTS_CONF": str(conf_path), "COMPOSE_FILE": str(compose_path)}
            with patch.dict(os.environ, env), \
                    patch.object(pr, "listeners", return_value=(listeners, None)), \
                    patch.object(pr, "docker_ports", return_value=(docker, None)), \
                    patch.object(deployment, "_deployment_health", return_value={}):
                data = asyncio.run(deployment.api_ports())
        self.assertIn("/api/ports", server.app.openapi()["paths"])
        return {entry["port"]: entry for entry in data["ports"]}

    def test_live_idle_and_wild(self) -> None:
        from lib.port_registry import Occupant

        conf = (
            "8000 | rivendell | dashboard-api | /srv/rivendell | api\n"
            "3000 | rivendell | dashboard-web | /srv/rivendell | web\n"
        )
        by_port = self._run(conf, {
            8000: Occupant(command="python", pid="100", cwd="/srv/rivendell/apps/api"),
            3011: Occupant(command="node", pid="200", cwd="/srv/other"),
        }, {})
        self.assertEqual(by_port[8000]["status"], "live")
        self.assertEqual(by_port[3000]["status"], "drift")
        self.assertEqual(by_port[3011]["status"], "wild")
        self.assertTrue(by_port[8000]["declared"])
        self.assertFalse(by_port[3011]["declared"])

    def test_port_used_by_someone_other_than_its_claimant_is_a_conflict(self) -> None:
        from lib.port_registry import Occupant

        # the 8081 case: registered to mops_dbs, held by the trip-atlas OTP container
        conf = "8081 | mops_dbs | mops_rev API | /srv/mops_dbs | README\n"
        by_port = self._run(conf, {8081: Occupant(command="com.docke", pid="1")},
                            {8081: Occupant(command="docker", container="trip-atlas-otp",
                                            folder="/srv/trip-atlas/remote")})
        self.assertEqual(by_port[8081]["status"], "conflict")
        self.assertEqual(by_port[8081]["conflict"], "occupied")
        self.assertIn("trip-atlas-otp", by_port[8081]["detail"])

    def test_two_projects_claiming_one_port_is_a_conflict_even_when_idle(self) -> None:
        conf = (
            "8081 | mops_dbs | mops_rev API | /srv/mops_dbs | README\n"
            "8081 | trip-atlas | otp | docker:trip-atlas-otp | OTP\n"
        )
        by_port = self._run(conf, {}, {})
        self.assertEqual(by_port[8081]["status"], "conflict")
        self.assertEqual(by_port[8081]["conflict"], "duplicate")

    def test_owner_rules(self) -> None:
        from lib.port_registry import Claim, Occupant, matches

        occ = Occupant(command="WeChat", pid="9", cwd="/")
        self.assertTrue(matches(Claim(1, "WeChat", "c", "app:wechat"), occ))
        self.assertFalse(matches(Claim(1, "x", "c", "docker:foo"), occ))
        self.assertTrue(matches(Claim(1, "x", "c", "docker:foo"), Occupant(container="foo")))
        self.assertFalse(matches(Claim(1, "x", "c", "/srv/a"), Occupant(cwd="/srv/ab")))
    def test_numbering_rule_and_old_port_during_a_move(self) -> None:
        from lib import port_registry as pr
        from lib.port_registry import Occupant

        conf = (
            "@id | 15 | Rightek-CRM\n"
            "8150 | Rightek-CRM | backend | /srv/crm | was 8100\n"
            "3100 | Rightek-CRM | frontend | /srv/crm | off the rule\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ports.conf"
            path.write_text(conf, encoding="utf-8")
            with patch.object(pr, "listeners", return_value=(
                    {8100: Occupant(command="python", pid="5", cwd="/srv/crm/backend")}, None)), \
                    patch.object(pr, "docker_ports", return_value=({}, None)):
                states, errs = pr.evaluate(path)
        by_port = {s.port: s for s in states}
        self.assertEqual(by_port[8100].status, "moving")
        self.assertEqual(by_port[8100].moved_to.port, 8150)
        self.assertEqual(len(errs["off_rule"]), 1)
        self.assertIn("3100", errs["off_rule"][0])


if __name__ == "__main__":
    unittest.main()
