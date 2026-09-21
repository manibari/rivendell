FROM python:3.11-slim
WORKDIR /app

COPY apps/dashboard-api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/dashboard-api/server.py ./
COPY apps/dashboard-api/routes/ ./routes/
COPY apps/dashboard-legacy/lib/ /dashboard/lib/
COPY platform/agent_fleet/agent_registry.py /platform/agent_fleet/agent_registry.py
COPY platform/agent_fleet/agents.py /platform/agent_fleet/agents.py
COPY platform/monitoring/usage/token_usage.py /platform/monitoring/usage/token_usage.py
COPY platform/projects/projects.py /platform/projects/projects.py
COPY platform/skill_catalog/skills.py /platform/skill_catalog/skills.py
COPY platform/skill_catalog/hooks.py /platform/skill_catalog/hooks.py
COPY platform/workflows/roles.py /platform/workflows/roles.py
COPY platform/workflows/workflow-map.json /platform/workflows/workflow-map.json
COPY docs/skills-by-role.md /docs/skills-by-role.md
ENV RIVENDELL_LIB_DIR=/dashboard
ENV RIVENDELL_DB_PATH=/dashboard/data/rivendell.db
ENV RIVENDELL_DB_DIR=/dashboard/data
ENV RIVENDELL_SKILL_SUMMARIES=/data/skill-summaries-zh.tsv

EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
