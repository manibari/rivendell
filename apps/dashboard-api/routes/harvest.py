"""Harvest candidates and decisions API."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
REPO_DIR = Path(__file__).resolve().parent.parent.parent.parent

# ── Harvest ──────────────────────────────────────────────────────────

_REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", str(REPO_DIR / "reports")))
HARVEST_DECISIONS_FILE = _REPORTS_DIR / ".harvest-decisions.json"


def _load_harvest_decisions() -> dict[str, str]:
    """Load user decisions {candidate_key: "accepted"|"dismissed"}."""
    if HARVEST_DECISIONS_FILE.exists():
        import json
        return json.loads(HARVEST_DECISIONS_FILE.read_text())
    return {}


def _save_harvest_decisions(decisions: dict[str, str]) -> None:
    import json
    HARVEST_DECISIONS_FILE.write_text(json.dumps(decisions, indent=2, ensure_ascii=False))


def _parse_harvest_reports() -> list[dict[str, Any]]:
    """Parse all harvest-*.md reports and extract skill candidates."""
    import re

    reports_dir = _REPORTS_DIR
    candidates: list[dict[str, Any]] = []

    for md_file in sorted(reports_dir.glob("harvest-*.md")):
        # Extract date from filename
        m = re.search(r"harvest-(\d{4}-\d{2}-\d{2})", md_file.name)
        if not m:
            continue
        report_date = m.group(1)
        content = md_file.read_text()

        # Split into sections by ### headers
        sections = re.split(r"^### ", content, flags=re.MULTILINE)

        for section in sections[1:]:
            lines = section.strip().splitlines()
            if not lines:
                continue
            heading = lines[0].strip()

            # Determine strength from heading
            strength = ""
            heading_lower = heading.lower()
            # Skip non-candidate sections
            if "結論" in heading_lower or "重複模式" in heading_lower or "跨 session" in heading_lower:
                continue
            if "strong" in heading_lower or "強烈" in heading_lower:
                strength = "strong"
            elif "moderate" in heading_lower or "中等" in heading_lower:
                strength = "moderate"
            elif "weak" in heading_lower or "不建議" in heading_lower:
                strength = "weak"
            else:
                continue  # Not a candidate section
            # Skip "無" entries like "Strong — 無"
            if re.search(r"[—–-]\s*無", heading):
                continue

            # Check for sub-candidates (#### headers within this section)
            body = "\n".join(lines[1:])

            # Skip sections whose body explicitly says "no candidates found"
            # e.g. "**(本次無 Strong 候選)**" under a Strong taxonomy heading
            if re.search(r"本次無\s*\w*\s*候選", body):
                continue

            # Check for table-format candidates (| 名稱 | 用途 | ... |)
            if re.search(r"^\|\s*名稱\s*\|", body, re.MULTILINE):
                for row in body.splitlines():
                    row = row.strip()
                    if not row.startswith("|") or row.startswith("|--") or "名稱" in row:
                        continue
                    cols = [c.strip() for c in row.split("|")[1:-1]]
                    if len(cols) >= 2 and cols[0]:
                        candidates.append({
                            "key": f"{report_date}:{cols[0]}",
                            "name": cols[0],
                            "strength": strength,
                            "purpose": cols[1] if len(cols) > 1 else "",
                            "trigger": "",
                            "category": "",
                            "reasoning": cols[2] if len(cols) > 2 else "",
                            "conclusion": "",
                            "report_date": report_date,
                        })
                continue

            sub_sections = re.split(r"^#### ", body, flags=re.MULTILINE)

            if len(sub_sections) > 1:
                # Multiple candidates under one strength heading
                for sub in sub_sections[1:]:
                    candidate = _parse_candidate_section(sub, strength, report_date)
                    if candidate:
                        candidates.append(candidate)
            else:
                # Single candidate in this ### section
                candidate = _parse_candidate_section(
                    heading + "\n" + body, strength, report_date
                )
                if candidate:
                    candidates.append(candidate)

    return candidates


def _parse_candidate_section(text: str, strength: str, report_date: str) -> dict[str, Any] | None:
    """Parse a single candidate section into structured data."""
    import re

    lines = text.strip().splitlines()
    if not lines:
        return None

    # Extract name from heading — look for backtick-wrapped name or parenthesized name
    heading = lines[0].strip()
    # Clean emoji/markers
    heading = re.sub(r"^[✅🟡🔴⚪\s]+", "", heading).strip()

    # Skip meta-headings that aren't actual candidates
    skip_patterns = ["排除的候選", "不建立原因", "觀察到但不建議"]
    if any(p in heading for p in skip_patterns):
        return None

    body = "\n".join(lines[1:])

    # Check body for **名稱** table row (table-format candidates)
    name_from_table = re.search(r"\*\*名稱\*\*[：:|\s]*`([^`]+)`", body)

    # Extract name — prefer backtick in heading, then table, then heading text
    name_match = re.search(r"`([^`]+)`", heading)
    if name_match:
        name = name_match.group(1)
    elif name_from_table:
        name = name_from_table.group(1)
    else:
        name = re.sub(r"^(Strong|Moderate|Weak|強烈建議建立|中等|不建議獨立 skill)[：:\s—–-]*", "", heading, flags=re.IGNORECASE).strip()
        name = re.split(r"\s*[—–(（]", name)[0].strip()

    if not name or len(name) > 80 or name == "無":
        return None

    # Extract fields — support both "**用途**: text" and "| **用途** | text |" formats
    def _extract(field_names: list[str]) -> str:
        for fn in field_names:
            # Inline format: **field**: value
            m = re.search(rf"\*\*{fn}\*\*[：:|\s]+(.+?)(?:\s*\|?\s*$)", body, re.MULTILINE)
            if m:
                val = m.group(1).strip().strip("|").strip()
                if val:
                    return val
        return ""

    purpose = _extract(["目的", "用途", "Purpose"])
    trigger = _extract(["觸發條件", "觸發", "Trigger"])
    category = _extract(["建議分類", "分類", "Category"]).strip("`")

    # Extract reasoning — supports Chinese (理由) and English (Rationale/Reasoning)
    reasoning = ""
    reason_match = re.search(
        r"\*\*(?:理由|Rationale|Reasoning)\*\*[：:]\s*\n?((?:[\s\S]*?)(?=\n\*\*|\n---|\n###|\Z))",
        body,
    )
    if reason_match:
        reasoning = reason_match.group(1).strip()
        # Truncate to first 300 chars
        if len(reasoning) > 300:
            reasoning = reasoning[:300] + "..."

    # Extract conclusion — supports Chinese (結論) and English (Conclusion)
    conclusion = ""
    concl_match = re.search(r"\*\*(?:結論|Conclusion)\*\*[：:]\s*(.+)", body)
    if concl_match:
        conclusion = concl_match.group(1).strip()

    # Build unique key
    key = f"{report_date}:{name}"

    return {
        "key": key,
        "name": name,
        "strength": strength,
        "purpose": purpose,
        "trigger": trigger,
        "category": category,
        "reasoning": reasoning,
        "conclusion": conclusion,
        "report_date": report_date,
    }


@router.get("/api/harvest", tags=["Overview"])
def api_harvest() -> dict[str, Any]:
    """Return all skill candidates from harvest reports with user decisions."""
    candidates = _parse_harvest_reports()
    decisions = _load_harvest_decisions()

    for c in candidates:
        c["decision"] = decisions.get(c["key"], "pending")

    # Stats
    pending = [c for c in candidates if c["decision"] == "pending"]
    accepted = [c for c in candidates if c["decision"] == "accepted"]
    dismissed = [c for c in candidates if c["decision"] == "dismissed"]

    return {
        "total": len(candidates),
        "pending_count": len(pending),
        "accepted_count": len(accepted),
        "dismissed_count": len(dismissed),
        "candidates": candidates,
    }


class HarvestDecision(BaseModel):
    key: str
    decision: str  # "accepted" | "dismissed" | "pending"


_CATEGORY_DIRS = {
    "backend": "backend",
    "frontend": "frontend",
    "workflow": "workflow",
    "quality": "quality",
    "meta": "meta",
    "git": "git",
    "docs": "docs",
}


def _slugify(name: str) -> str:
    """Convert skill name to filesystem-safe slug."""
    import re
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def _generate_skill_md(candidate: dict[str, Any]) -> str:
    """Generate SKILL.md content from a harvest candidate."""
    name = candidate.get("name", "unknown")
    purpose = candidate.get("purpose", "")
    trigger = candidate.get("trigger", "")
    category = candidate.get("category", "workflow")
    # candidate["reasoning"] is deliberately not emitted — see the stub comment
    # below: the harvest digest does not belong in the generated SKILL.md.

    # Single model-facing description with TRIGGER (Claude Code triggers on
    # `description`; a separate when_to_use line is non-standard and redundant).
    description = purpose[:200] if purpose else f"{name} skill"
    trig = trigger[:200] if trigger else f"when working with {name}"

    # Clean category -> tag; strip any path slash so the YAML stays valid
    # (this was the source of '[backend/]' / '[workflow/]' malformed tags).
    cat = (category or "workflow").split("/")[0].strip() or "workflow"

    # Emit a clean, lintable stub: valid frontmatter + a scaffolded Gotchas
    # section (the highest-signal content) + 待補 markers. No Overview/When-to-Use
    # duplication, no raw harvest-digest dump, no TODO boilerplate.
    lines = [
        "---",
        f"name: {name}",
        "description: >",
        f"  {description}",
        f"  TRIGGER: {trig}",
        "  SKIP: 待補 — add negative triggers vs competing skills.",
        f"tags: [{cat}]",
        "version: 0.1.0",
        "source: harvest-auto",
        "---",
        "",
        f"# {name}",
        "",
        "> ⚠️ Harvest stub — fill before use, then flip `source:` to `manual`.",
        f"> Validate with `sk lint {name}`.",
        "",
        "## What this does",
        "",
        purpose or "待補",
        "",
        "## Workflow",
        "",
        "待補 — concrete steps.",
        "",
        "## Gotchas",
        "",
        "待補 — highest-signal section. Add real failure points as they surface.",
        "",
    ]

    return "\n".join(lines)


def _auto_create_skill(candidate: dict[str, Any]) -> dict[str, Any]:
    """Create skill directory + SKILL.md + deploy symlink. Returns result dict."""
    name = candidate.get("name", "")
    if not name:
        return {"created": False, "error": "no name"}

    slug = _slugify(name)
    category = candidate.get("category", "workflow")
    cat_dir = _CATEGORY_DIRS.get(category, "workflow")

    repo_dir = REPO_DIR
    skill_dir = repo_dir / "skills" / cat_dir / slug
    deploy_target = Path.home() / ".claude" / "skills" / slug

    # Check if already exists
    if skill_dir.exists():
        return {
            "created": False,
            "already_exists": True,
            "skill_path": str(skill_dir),
            "deploy_path": str(deploy_target),
        }

    # Create skill directory + SKILL.md
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(_generate_skill_md(candidate))

    # Deploy symlink
    deploy_target.parent.mkdir(parents=True, exist_ok=True)
    if not deploy_target.exists() and not deploy_target.is_symlink():
        deploy_target.symlink_to(skill_dir)
        deployed = True
    else:
        deployed = False

    return {
        "created": True,
        "skill_path": str(skill_dir),
        "deploy_path": str(deploy_target) if deployed else None,
        "deployed": deployed,
        "slug": slug,
        "category": cat_dir,
    }


@router.post("/api/harvest/decide", tags=["Overview"])
def api_harvest_decide(body: HarvestDecision) -> dict[str, Any]:
    """Record user decision on a skill candidate. Auto-creates skill when accepted."""
    if body.decision not in ("accepted", "dismissed", "pending"):
        raise HTTPException(400, "decision must be accepted, dismissed, or pending")

    decisions = _load_harvest_decisions()
    if body.decision == "pending":
        decisions.pop(body.key, None)
    else:
        decisions[body.key] = body.decision
    _save_harvest_decisions(decisions)

    result: dict[str, Any] = {"ok": True, "key": body.key, "decision": body.decision}

    # Auto-create skill when accepted
    if body.decision == "accepted":
        candidates = _parse_harvest_reports()
        candidate = next((c for c in candidates if c["key"] == body.key), None)
        if candidate:
            result["skill_created"] = _auto_create_skill(candidate)

    return result
