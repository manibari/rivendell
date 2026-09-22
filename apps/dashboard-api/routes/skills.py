"""Skill catalog and role documentation API."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from lib.skills import list_skills
from lib.capabilities import project_roles, skill_workflows

router = APIRouter()
REPO_DIR = Path(__file__).resolve().parent.parent.parent.parent

# ── Skills ────────────────────────────────────────────────────────────

@router.get("/api/skills", tags=["Skills"])
def api_skills() -> list[dict[str, Any]]:
    skills = list_skills()
    return [
        {
            "name": s.name,
            "category": s.category,
            "summary": s.summary,
            "line_count": s.line_count,
            "invocable": s.invocable,
            "lifecycle": s.lifecycle,
            "source": s.source,
            "folder": s.folder,
            "loop": s.loop,
            "pdca": s.pdca,
        }
        for s in skills
    ]


@router.get("/api/skills/roles", tags=["Skills"])
def api_skills_roles() -> dict[str, Any]:
    """角色 → 工作 → PDCA, projected from capability definitions.

    Declared before /api/skills/{name} so the static segment wins. `content`
    is the raw markdown for a "原文" view; `roles` is the parsed structure.
    """
    path = REPO_DIR / "docs" / "skills-by-role.md"
    if not path.is_file():
        raise HTTPException(404, "docs/skills-by-role.md not found")
    data = project_roles()
    data["content"] = path.read_text(encoding="utf-8")
    return data


_DOCS_ROOT = (REPO_DIR / "docs").resolve()


@router.get("/api/docs-asset/{asset_path:path}", tags=["Skills"])
def api_doc_asset(asset_path: str) -> FileResponse:
    """Images referenced by markdown under rivendell/docs/ (png/svg/jpg only)."""
    target = (_DOCS_ROOT / asset_path).resolve()
    if _DOCS_ROOT not in target.parents or not target.is_file() or target.suffix.lower() not in (".png", ".svg", ".jpg", ".jpeg", ".gif"):
        raise HTTPException(404, f"docs/{asset_path} not found")
    return FileResponse(str(target))


@router.get("/api/docs/{doc_path:path}", tags=["Skills"])
def api_doc(doc_path: str) -> dict[str, Any]:
    """Serve one markdown file from rivendell/docs/ (deep-dive pages such as
    docs/loops/gov-tender.md). Path is confined to docs/; nothing else."""
    if not doc_path.endswith(".md"):
        doc_path += ".md"
    target = (_DOCS_ROOT / doc_path).resolve()
    if _DOCS_ROOT not in target.parents or not target.is_file():
        raise HTTPException(404, f"docs/{doc_path} not found")
    return {"path": str(target.relative_to(_DOCS_ROOT.parent)), "content": target.read_text(encoding="utf-8")}


# Cache for skill usage scan (recompute at most every 10 min)
_usage_cache: dict[str, Any] = {}


def _parse_skill_usage() -> dict[str, list[dict[str, Any]]]:
    """Scan Claude Code session JSONL files.

    Counts two signals per skill per day:
    - ``Read`` tool calls where file_path ends with SKILL.md (auto-triggered skills)
    - ``Skill`` tool calls with ``skill`` input matching the skill name (manual /skill invocations)
    """
    import json as _json
    import time as _time

    cache_ts: float = _usage_cache.get("ts", 0.0)
    if _time.time() - cache_ts < 600 and "data" in _usage_cache:
        return _usage_cache["data"]  # type: ignore[return-value]

    raw: dict[str, dict[str, int]] = {}  # {skill_name: {date: count}}
    projects_dir = Path.home() / ".claude" / "projects"

    def _add(skill_name: str, date: str) -> None:
        if skill_name not in raw:
            raw[skill_name] = {}
        raw[skill_name][date] = raw[skill_name].get(date, 0) + 1

    if projects_dir.exists():
        for jsonl_file in projects_dir.rglob("*.jsonl"):
            try:
                with open(jsonl_file, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = _json.loads(line)
                        except Exception:
                            continue
                        timestamp = obj.get("timestamp", "")
                        if not timestamp:
                            continue
                        date = str(timestamp)[:10]
                        msg = obj.get("message", {})
                        content = msg.get("content", [])
                        if not isinstance(content, list):
                            continue
                        for item in content:
                            if not isinstance(item, dict):
                                continue
                            if item.get("type") != "tool_use":
                                continue
                            tool_name = item.get("name", "")
                            inp = item.get("input", {})

                            if tool_name == "Read":
                                # Auto-triggered: Claude reads SKILL.md
                                file_path = str(inp.get("file_path", ""))
                                if not file_path.endswith("SKILL.md"):
                                    continue
                                parts = file_path.replace("\\", "/").split("/")
                                try:
                                    idx = parts.index("SKILL.md")
                                    skill_name = parts[idx - 1] if idx > 0 else None
                                except ValueError:
                                    skill_name = None
                                if skill_name:
                                    _add(skill_name, date)

                            elif tool_name == "Skill":
                                # Manual /skill-name invocation
                                skill_name = str(inp.get("skill", "")).strip()
                                if skill_name:
                                    _add(skill_name, date)
            except Exception:
                continue

    result: dict[str, list[dict[str, Any]]] = {
        name: sorted(
            [{"date": d, "count": c} for d, c in daily.items()],
            key=lambda x: x["date"],
        )
        for name, daily in raw.items()
    }
    _usage_cache["data"] = result
    _usage_cache["ts"] = _time.time()
    return result


@router.get("/api/skills/usage", tags=["Skills"])
def api_skills_usage() -> dict[str, Any]:
    """Return per-skill SKILL.md read counts from Claude Code session JSONL files."""
    return _parse_skill_usage()


@router.get("/api/skills/{name}", tags=["Skills"])
def api_skill_content(name: str) -> dict[str, Any]:
    """Return SKILL.md content + metadata for a single skill.

    Built-in Claude Code skills (category="builtin") have no SKILL.md on
    disk — synthesize a placeholder content from the metadata we have.
    """
    meta: dict[str, Any] = {}
    for s in list_skills():
        if s.name == name:
            meta = {
                "category": s.category,
                "summary": s.summary,
                "line_count": s.line_count,
                "invocable": s.invocable,
                "lifecycle": s.lifecycle,
            }
            break

    if meta.get("category") == "builtin":
        content = (
            f"# {name}\n\n"
            f"> Built-in Claude Code skill — no SKILL.md on disk. "
            f"Compiled into the `claude` binary itself.\n\n"
            f"## Description\n\n"
            f"{meta.get('summary') or '(description not surfaced in binary)'}\n\n"
            f"## How to invoke\n\n"
            f"`/{name}` — same as any other slash command.\n\n"
            f"## Why no source file\n\n"
            f"Built-in skills ship with Claude Code itself rather than as files in this repo. "
            f"They auto-update with each Claude Code version bump (no `./bin/sk deploy` needed). "
            f"To inspect the source, decompile the binary at `$(which claude)` — but it's not "
            f"meant to be modified by users.\n\n"
            f"See README.md → \"Built-in Claude Code Skills\" section for the full inventory.\n"
        )
        return {"name": name, "content": content, "workflows": skill_workflows(name), **meta}

    skill_md = Path.home() / ".claude" / "skills" / name / "SKILL.md"
    if not skill_md.is_file():
        raise HTTPException(404, f"Skill '{name}' not found")
    content = skill_md.read_text(encoding="utf-8")
    return {"name": name, "content": content, "workflows": skill_workflows(name), **meta}
