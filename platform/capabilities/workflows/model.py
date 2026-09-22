"""Canonical capability workflow definitions and read projections."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFINITIONS = Path(__file__).resolve().parent / "definitions"
PLAYBOOKS = Path(__file__).resolve().parent / "playbooks"
STAGES = ("Plan", "Do", "Check", "Act")
PLAYBOOK_IDS = ("ui", "backend", "slide", "maintenance")
MODES = {"core", "conditional", "automatic"}


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_definitions() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    roles = _read(DEFINITIONS / "roles.json")
    jobs = {p.stem: _read(p) for p in sorted((DEFINITIONS / "jobs").glob("*.json"))}
    return roles, jobs


def load_playbook(flow_id: str) -> dict[str, Any]:
    if flow_id not in PLAYBOOK_IDS:
        raise KeyError(flow_id)
    return _read(PLAYBOOKS / f"{flow_id}.json")


def skill_details() -> dict[str, Any]:
    return _read(Path(__file__).resolve().parent.parent / "catalog" / "playbook-skill-details.json")


def _playbook_chips(value: Any) -> list[dict[str, str]]:
    if isinstance(value, list):
        return [chip for item in value for chip in _playbook_chips(item)]
    if isinstance(value, dict):
        if "key" in value and "category" in value:
            return [value]
        return [chip for item in value.values() for chip in _playbook_chips(item)]
    return []


def validate() -> list[str]:
    """Return all definition errors so CI and the API can report the same drift."""
    errors: list[str] = []
    roles, jobs = load_definitions()
    skills_dir = Path(os.environ.get("RIVENDELL_SKILLS_DIR", str(ROOT / "skills")))
    local = {p.parent.name for p in skills_dir.glob("*/*/SKILL.md")}
    role_ids = [role["id"] for role in roles["roles"]]
    if len(role_ids) != len(set(role_ids)):
        errors.append("duplicate role id")
    referenced_jobs: list[str] = []
    for role in roles["roles"]:
        referenced_jobs.extend(role["jobs"])
        for job_id in role["jobs"]:
            if job_id not in jobs:
                errors.append(f"role {role['id']}: missing job {job_id}")
            elif jobs[job_id]["role_id"] != role["id"]:
                errors.append(f"job {job_id}: wrong role_id")
    if len(referenced_jobs) != len(set(referenced_jobs)):
        errors.append("duplicate job reference")
    for job_id, job in jobs.items():
        if job_id not in referenced_jobs or job["id"] != job_id:
            errors.append(f"job {job_id}: unreferenced or mismatched id")
        step_ids = [step["id"] for step in job["steps"]]
        if len(step_ids) != len(set(step_ids)):
            errors.append(f"job {job_id}: duplicate step id")
        if [step["stage"] for step in job["steps"]] != list(STAGES):
            errors.append(f"job {job_id}: stages must be Plan, Do, Check, Act")
        for order, step in enumerate(job["steps"], 1):
            if step["order"] != order:
                errors.append(f"job {job_id}: step order mismatch")
            if not isinstance(step.get("action"), str) or "condition" not in step or "gate" not in step:
                errors.append(f"job {job_id}: missing step action, condition, or gate")
            for ref in step["skill_refs"]:
                name, source = ref.get("name"), ref.get("source")
                if ref.get("mode") not in MODES:
                    errors.append(f"job {job_id}: invalid mode for {name}")
                if source == "rivendell" and name not in local:
                    errors.append(f"job {job_id}: unknown local skill {name}")
                elif source == "gstack" and not str(name).startswith("gstack"):
                    errors.append(f"job {job_id}: invalid gstack skill {name}")
                elif source not in {"rivendell", "gstack"}:
                    errors.append(f"job {job_id}: invalid source {source}")
    for flow_id in PLAYBOOK_IDS:
        flow = load_playbook(flow_id)
        if flow.get("id") != flow_id:
            errors.append(f"playbook {flow_id}: id mismatch")
        for chip in _playbook_chips(flow):
            name, category = chip["key"], chip["category"]
            if name not in local and not name.startswith("gstack"):
                errors.append(f"playbook {flow_id}: unknown skill {name}")
            if category == "gstack" and not name.startswith("gstack"):
                errors.append(f"playbook {flow_id}: invalid gstack category {name}")
    return errors


def project_roles() -> dict[str, Any]:
    """Preserve the existing /api/skills/roles response shape and telemetry join."""
    from lib.roles import _telemetry

    definitions, jobs = load_definitions()
    telemetry = _telemetry()
    result_roles = []
    for role in definitions["roles"]:
        item = {key: value for key, value in role.items() if key != "jobs"}
        item["jobs"] = []
        item["runs"] = 0
        for job_id in role["jobs"]:
            job = jobs[job_id]
            record = {key: job[key] for key in ("id", "title", "deep_dive")}
            record["stages"] = []
            for step in job["steps"]:
                stage = {key: value for key, value in step.items() if key not in {"id", "order", "skill_refs", "action", "condition", "gate"}}
                refs = step["skill_refs"]
                stage["skills"] = [ref["name"] for ref in refs]
                for mode in MODES:
                    stage[mode] = [ref["name"] for ref in refs if ref["mode"] == mode]
                stage["external"] = [ref["name"] for ref in refs if ref["source"] == "gstack"]
                record["stages"].append(stage)
            run = telemetry.get(job_id, {"runs": 0, "by_stage": {}, "last_run": ""})
            record["runs"] = run["runs"]
            record["by_stage"] = run["by_stage"]
            record["last_run"] = run["last_run"]
            record["gap_count"] = sum(len(stage["gaps"]) for stage in record["stages"])
            item["jobs"].append(record)
            item["runs"] += record["runs"]
        item["job_count"] = len(item["jobs"])
        item["gap_count"] = sum(job["gap_count"] for job in item["jobs"])
        result_roles.append(item)
    return {
        "path": str(ROOT / "docs" / "skills-by-role.md"),
        "updated": definitions["updated"],
        "shared": definitions["shared"],
        "tiers": definitions["tiers"],
        "roles": result_roles,
        "totals": {
            "roles": len(result_roles),
            "jobs": sum(role["job_count"] for role in result_roles),
            "gaps": sum(role["gap_count"] for role in result_roles),
            "jobs_run": sum(job["runs"] > 0 for role in result_roles for job in role["jobs"]),
            "runs": sum(role["runs"] for role in result_roles),
        },
    }


def skill_workflows(name: str) -> list[dict[str, str]]:
    _, jobs = load_definitions()
    uses = []
    for job in jobs.values():
        for step in job["steps"]:
            if any(ref["name"] == name for ref in step["skill_refs"]):
                uses.append({"workflow_id": job["id"], "role_id": job["role_id"], "title": job["title"], "step_id": step["id"], "stage": step["stage"]})
    return uses
