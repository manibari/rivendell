"""Cross-module operational issues read model."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from lib.agents import list_agents

router = APIRouter()
REPO_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent

# ── Issues ───────────────────────────────────────────────────────────

@router.get("/api/issues", tags=["Overview"])
def api_issues() -> dict[str, Any]:
    """Aggregate pending issues from multiple sources."""
    import re

    issues: list[dict[str, Any]] = []

    # 1. Agent errors — exit_code != 0 and not running
    agents = list_agents()
    for a in agents:
        if a.exit_code is not None and a.exit_code != 0 and a.pid is None:
            issues.append({
                "source": "agent",
                "severity": "error",
                "title": f"Agent {a.name} 執行失敗",
                "detail": f"exit code {a.exit_code} — {a.project}/{a.name}",
                "label": a.label,
            })
        elif a.installed and not a.loaded:
            issues.append({
                "source": "agent",
                "severity": "warning",
                "title": f"Agent {a.name} 未載入",
                "detail": f"已安裝但未載入 — {a.project}/{a.name}",
                "label": a.label,
            })

    # 2. .learnings/ERRORS.md — group entries by ## heading
    seen_dirs: set[str] = set()
    for agent in agents:
        if agent.working_directory:
            seen_dirs.add(agent.working_directory)

    for wd in seen_dirs:
        errors_md = Path(wd) / ".learnings" / "ERRORS.md"
        if not errors_md.exists():
            continue
        project_name = Path(wd).name
        content = errors_md.read_text()

        # Parse by ## sections
        sections = re.split(r"^## ", content, flags=re.MULTILINE)
        for section in sections[1:]:  # skip content before first ##
            lines = section.strip().splitlines()
            if not lines:
                continue
            heading = lines[0].strip()
            body_lines = [line.strip() for line in lines[1:] if line.strip() and not line.strip().startswith("#")]

            # Check if resolved
            full_text = " ".join(body_lines).lower()
            if "[x]" in full_text or "✅" in heading.lower():
                continue

            # Extract detail from bullet points
            detail_parts = []
            for bl in body_lines[:3]:  # first 3 bullets as detail
                cleaned = re.sub(r"^-\s*(\*\*[^*]+\*\*:\s*)?", "", bl).strip()
                if cleaned:
                    detail_parts.append(cleaned)
            detail = " | ".join(detail_parts) if detail_parts else ""

            issues.append({
                "source": "learnings",
                "severity": "error",
                "title": heading,
                "detail": detail or f"from {project_name}/.learnings/ERRORS.md",
                "label": project_name,
            })

    # 3. Skill deployment — missing symlinks
    skills_dir = REPO_DIR / "skills"
    deploy_target = Path.home() / ".claude" / "skills"
    if skills_dir.exists() and deploy_target.exists():
        for skill_md in skills_dir.glob("*/*/SKILL.md"):
            name = skill_md.parent.name
            target = deploy_target / name
            if not target.exists() and not target.is_symlink():
                issues.append({
                    "source": "skill",
                    "severity": "warning",
                    "title": f"Skill {name} 未部署",
                    "detail": "執行 sk deploy 修復",
                    "label": name,
                })
        # Dangling symlinks
        for link in deploy_target.iterdir():
            if link.is_symlink() and not link.exists():
                issues.append({
                    "source": "skill",
                    "severity": "warning",
                    "title": f"Skill {link.name} symlink 已失效",
                    "detail": f"指向 {link.resolve()} 但目標不存在",
                    "label": link.name,
                })

    # 4. Missing .env — check sibling projects with .env.example but no matching env file.
    # Next.js projects conventionally use .env.local; accept either.
    # Python/Node projects conventionally use .env; accept either.
    # Skip when the example points users to a different target ("Copy to .env.local").
    projects_dir = REPO_DIR.parent
    for env_example in projects_dir.glob("*/.env.example"):
        proj_dir = env_example.parent
        # Accept any of these as "configured"
        candidate_files = [".env", ".env.local", ".env.development", ".env.production"]
        if any((proj_dir / f).exists() for f in candidate_files):
            continue
        # Peek at the example to see which target it recommends
        try:
            example_head = env_example.read_text(errors="ignore")[:400]
        except Exception:
            example_head = ""
        recommended = ".env"
        if ".env.local" in example_head:
            recommended = ".env.local"
        issues.append({
            "source": "env",
            "severity": "warning",
            "title": f"{proj_dir.name} 缺少 {recommended}",
            "detail": f"有 .env.example 但沒有 {recommended} — cp {env_example.name} {recommended} 後填值",
            "label": proj_dir.name,
        })

    # Sort: errors first, then warnings
    severity_order = {"error": 0, "warning": 1, "info": 2}
    issues.sort(key=lambda x: severity_order.get(x["severity"], 9))

    return {
        "total": len(issues),
        "errors": sum(1 for i in issues if i["severity"] == "error"),
        "warnings": sum(1 for i in issues if i["severity"] == "warning"),
        "issues": issues,
    }
