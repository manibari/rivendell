#!/usr/bin/env python3
"""Validate canonical workflow definitions and their human-readable role view."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "dashboard-legacy"))

from lib.capabilities import load_definitions, project_roles, validate  # noqa: E402
from lib.roles import parse_roles  # noqa: E402


def main() -> int:
    errors = validate()
    _, jobs = load_definitions()
    local = {p.parent.name for p in (ROOT / "skills").glob("*/*/SKILL.md")}
    external = {
        ref["name"]
        for job in jobs.values()
        for step in job["steps"]
        for ref in step["skill_refs"]
        if ref["source"] == "gstack"
    }
    doc = parse_roles(ROOT / "docs" / "skills-by-role.md", local | external)
    canonical = project_roles()
    if doc != canonical:
        errors.append("docs/skills-by-role.md differs from capability definitions")
    covered = {
        ref["name"]
        for job in jobs.values()
        for step in job["steps"]
        for ref in step["skill_refs"]
        if ref["source"] == "rivendell"
    }
    if missing := local - covered:
        errors.append(f"local skills without a role workflow: {', '.join(sorted(missing))}")
    for error in errors:
        print(f"workflow: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"workflow: {canonical['totals']['roles']} roles, {canonical['totals']['jobs']} jobs, 4 playbooks, {len(covered)} local skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
