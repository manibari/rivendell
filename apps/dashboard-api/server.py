"""FastAPI backend — thin wrapper around existing dashboard/lib/ modules."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add dashboard lib to path
LIB_DIR = Path(os.environ.get(
    "RIVENDELL_LIB_DIR",
    str(Path(__file__).resolve().parent.parent.parent / "apps" / "dashboard-legacy"),
))
sys.path.insert(0, str(LIB_DIR))

from lib.db import init_db  # noqa: E402

app = FastAPI(
    title="rivendell API",
    openapi_tags=[
        {"name": "Overview", "description": "Dashboard overview metrics"},
        {"name": "Agents", "description": "Agent lifecycle & scheduling"},
        {"name": "Projects", "description": "Project CRUD & detail"},
        {"name": "Tokens", "description": "Token usage & cost analytics"},
        {"name": "Skills", "description": "Skills catalog"},
        {"name": "Collaboration", "description": "Learnings & error tracking"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


from routes.deployment import (  # noqa: E402, F401
    router as deployment_router,
    api_ports,
    _parse_compose_host_port,
    _listening_tcp_ports,
)
app.include_router(deployment_router)


from routes.workflows import router as workflow_router  # noqa: E402
from routes.skills import router as skills_router  # noqa: E402
from routes.projects import router as projects_router  # noqa: E402
from routes.agents.api import router as agents_router  # noqa: E402
from routes.overview import router as overview_router  # noqa: E402
from routes.collaboration import router as collaboration_router  # noqa: E402
from routes.harvest import router as harvest_router  # noqa: E402
from routes.monitoring.issues import router as issues_router  # noqa: E402
app.include_router(workflow_router)
app.include_router(skills_router)
app.include_router(projects_router)
app.include_router(agents_router)
app.include_router(overview_router)
app.include_router(collaboration_router)
app.include_router(harvest_router)


from routes.monitoring.overview import router as health_router  # noqa: E402
from routes.monitoring.usage import router as usage_router  # noqa: E402
from routes.monitoring.disk import router as disk_router  # noqa: E402
from routes.monitoring.errors import router as errors_router  # noqa: E402
from routes.monitoring.git import router as git_router  # noqa: E402
from routes.monitoring.sensors import router as sensors_router  # noqa: E402

for monitoring_router in (health_router, disk_router, errors_router, git_router, usage_router, issues_router, sensors_router):
    app.include_router(monitoring_router)
