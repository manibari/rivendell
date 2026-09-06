"""Parse docs/skills-by-role.md (角色 → 工作 → PDCA) into a structure the dashboard can render.

The markdown stays the source of truth (`sk check` guards that every skill
appears in it); this module only reads the conventions it is written in:

    ## N. 角色名            role
    你在做：...             role intro (first paragraph after the heading)
    ### 1a 工作名 [→ 展開見 [x](loops/y.md)]   job, optional deep-dive link
    | Plan | 用誰 | 說明 |   one row per PDCA stage
    `skill-name`            skill reference (links to /skills/<name>)
    ★ **text** / ★ text     a step with no skill (gap)
    (gstack)                external skill marker
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ROLE_DOC = Path(__file__).parent.parent.parent / "docs" / "skills-by-role.md"

_ROLE_RE = re.compile(r"^## (\d+)\. (.+?)\s*$")
_JOB_RE = re.compile(r"^### (\d+[a-z]) (.+?)\s*$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_CODE_RE = re.compile(r"`([^`]+)`")
_STAGES = ("Plan", "Do", "Check", "Act")


def _cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def _strip_md(text: str) -> str:
    text = _LINK_RE.sub(r"\1", text)
    text = text.replace("**", "")
    return text.strip()


def _parse_who(cell: str, known: set[str] | None = None) -> dict[str, Any]:
    """Split a 用誰 cell into skill refs, gap labels, and the readable form.

    `known` limits skill refs to deployed skill names, so code spans like
    `status: signed-off` or `check-html-figure.mjs` stay plain text.
    """
    codes = _CODE_RE.findall(cell)
    skills = [c for c in codes if known is None or c in known]
    # Three segments separated by ｜: main line, "視情況：" (conditional),
    # "自動：" (hooks / gates that fire on their own). Skill refs are bucketed
    # by which segment they sit in so the UI can style them apart.
    core: list[str] = []
    conditional: list[str] = []
    automatic: list[str] = []
    for part in cell.split("｜"):
        stripped = part.strip()
        bucket = core
        if stripped.startswith("視情況"):
            bucket = conditional
        elif stripped.startswith("自動"):
            bucket = automatic
        for c in _CODE_RE.findall(part):
            if (known is None or c in known) and c not in bucket:
                bucket.append(c)
    gaps: list[str] = []
    # Segments are separated by · or →; a segment starting with ★ is a gap.
    # (Do not split on "/" — gap text such as "won / lost / no-bid" uses it.)
    for seg in re.split(r"\s*[·→｜]\s*", cell):
        seg = seg.strip()
        if seg.startswith("★"):
            g = _strip_md(seg.lstrip("★").strip()).replace("`", "")
            gaps.append(g)
    external = [s for s in skills if s.startswith("gstack")]
    return {
        "text": _strip_md(cell).replace("`", ""),
        "skills": skills,
        "core": core,
        "conditional": conditional,
        "automatic": automatic,
        "gaps": gaps,
        "external": external,
    }


def parse_roles(path: Path | None = None, known: set[str] | None = None) -> dict[str, Any]:
    p = path or ROLE_DOC
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()

    updated = ""
    m = re.search(r"更新：(\d{4}-\d{2}-\d{2})", text)
    if m:
        updated = m.group(1)

    roles: list[dict[str, Any]] = []
    role: dict[str, Any] | None = None
    job: dict[str, Any] | None = None
    shared: list[str] = []
    in_index = False

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("## 角色索引"):
            in_index = True
            continue
        if line.startswith("## 覆蓋檢查"):
            role = None
            job = None
            in_index = False
            continue

        rm = _ROLE_RE.match(line)
        if rm:
            in_index = False
            role = {"id": rm.group(1), "title": rm.group(2), "intro": "", "notes": [], "jobs": []}
            roles.append(role)
            job = None
            continue

        if in_index:
            if line.startswith("橫向共用") or line.startswith("畫圖"):
                shared.append(_strip_md(line).replace("`", ""))
            continue

        if role is None:
            continue

        jm = _JOB_RE.match(line)
        if jm:
            title = jm.group(2)
            deep = None
            lm = _LINK_RE.search(title)
            if lm:
                deep = {"label": lm.group(1), "href": lm.group(2)}
                title = re.sub(r"\s*→\s*展開見\s*\[.*?\]\(.*?\)\s*$", "", title).strip()
            job = {"id": jm.group(1), "title": title, "deep_dive": deep, "stages": []}
            role["jobs"].append(job)
            continue

        if line.startswith("|") and job is not None:
            cells = _cells(line)
            if not cells or cells[0] in ("", "---", "—") or set(cells[0]) <= {"-"}:
                continue
            stage = cells[0]
            if stage not in _STAGES:
                continue
            who = cells[1] if len(cells) > 1 else ""
            note = cells[2] if len(cells) > 2 else ""
            entry = _parse_who(who, known)
            entry["stage"] = stage
            entry["note"] = _strip_md(note).replace("`", "")
            job["stages"].append(entry)
            continue

        if job is None and line and not line.startswith("|") and not line.startswith("#"):
            # Role-level prose: first paragraph is the intro, later ones are notes.
            clean = _strip_md(line.lstrip("> ").strip()).replace("`", "")
            if not clean:
                continue
            if not role["intro"]:
                role["intro"] = clean
            else:
                role["notes"].append(clean)
            continue

        if job is not None and line and not line.startswith(("|", "#", "---")):
            # Prose after a job table: how the jobs connect, 常搭配, caveats.
            role["notes"].append(_strip_md(line.lstrip("> ").strip()).replace("`", ""))

    # Fill missing stages so the UI always has four columns.
    for r in roles:
        for j in r["jobs"]:
            have = {s["stage"] for s in j["stages"]}
            for st in _STAGES:
                if st not in have:
                    j["stages"].append({"stage": st, "text": "", "skills": [], "core": [], "conditional": [], "automatic": [], "gaps": [], "external": [], "note": "", "empty": True})
            j["stages"].sort(key=lambda s: _STAGES.index(s["stage"]))
            j["gap_count"] = sum(len(s["gaps"]) for s in j["stages"])
        r["job_count"] = len(r["jobs"])
        r["gap_count"] = sum(j["gap_count"] for j in r["jobs"])

    return {
        "path": str(p),
        "updated": updated,
        "shared": shared,
        "roles": roles,
        "totals": {
            "roles": len(roles),
            "jobs": sum(r["job_count"] for r in roles),
            "gaps": sum(r["gap_count"] for r in roles),
        },
    }
