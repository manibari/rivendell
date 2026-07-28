import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server


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
                self.assertEqual(server._parse_compose_host_port(spec), expected)

    def test_api_ports_marks_live_drift_and_wild(self) -> None:
        compose = """
services:
  dashboard-api:
    container_name: sk-dashboard-api
    ports:
      - "8000:8000"
  dashboard-web:
    container_name: sk-dashboard-web
    ports:
      - "3000:3000"
"""

        with tempfile.TemporaryDirectory() as tmp:
            compose_path = Path(tmp) / "docker-compose.yml"
            compose_path.write_text(compose, encoding="utf-8")

            with patch.dict(os.environ, {"COMPOSE_FILE": str(compose_path)}):
                with patch.object(
                    server,
                    "_listening_tcp_ports",
                    return_value=(
                        {
                            8000: {
                                "command": "python",
                                "pid": "100",
                                "name": "127.0.0.1:8000",
                            },
                            3011: {
                                "command": "node",
                                "pid": "200",
                                "name": "*:3011",
                            },
                        },
                        None,
                    ),
                ):
                    data = asyncio.run(server.api_ports())

        by_port = {entry["port"]: entry for entry in data["ports"]}
        self.assertEqual(by_port[8000]["status"], "live")
        self.assertEqual(by_port[3000]["status"], "drift")
        self.assertEqual(by_port[3011]["status"], "wild")
        self.assertTrue(by_port[8000]["declared"])
        self.assertFalse(by_port[3011]["declared"])


if __name__ == "__main__":
    unittest.main()
