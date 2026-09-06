"""Merge TSV metadata + SKILL.md files for rivendell.

Also surfaces Claude Code's compiled-in built-in skills (e.g. update-config,
fewer-permission-prompts, /insights) that have no SKILL.md on disk — by
scanning the `claude` binary with `strings`. Without this, the dashboard
silently hides ~16 skills that ship with the CLI itself.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SKILLS_DIR = Path.home() / ".claude" / "skills"
TSV_PATH = Path(__file__).parent.parent.parent / "data" / "skill-summaries-zh.tsv"

# Descriptions for built-ins where the binary stores them via getter / split string
# (so the strings(1) regex misses them). Updated when Claude Code ships new built-ins.
_BUILTIN_FALLBACK_DESC: dict[str, str] = {
    "update-config": "Configure .claude/settings.json — hooks, permissions, env vars. Required for any \"from now on when X\" automation (memory cannot enforce hooks).",
    "keybindings-help": "Customize keyboard shortcuts in ~/.claude/keybindings.json.",
    "loop": "Run a prompt or slash command on a recurring interval (e.g. /loop 5m /foo).",
    "schedule": "Cron-style scheduled remote agents (routines).",
    "claude-api": "Build, debug, and optimize Claude API / Anthropic SDK apps with prompt caching.",
    "dream": "(Description not surfaced in binary — likely feature-gated.)",
    "init": "Initialize a new CLAUDE.md file with codebase documentation.",
}


@dataclass
class SkillInfo:
    name: str
    category: str
    summary: str
    line_count: int
    invocable: bool
    lifecycle: str  # "manual" | "hook" | "agent" | "unknown"
    source: str = "external"   # "rivendell" | "gstack" | "external" | "builtin"
    folder: str = ""           # rivendell skills/<folder>/ the symlink resolves into
    loop: str = ""             # frontmatter loop: sales|gov|invest|hr|knowledge|platform|dev|shared
    pdca: str = ""             # frontmatter pdca: plan|do|check|act


RIVENDELL_SKILLS = Path(__file__).parent.parent.parent / "skills"


def _locate(skill_dir: Path) -> tuple[str, str]:
    """Where does this deployed skill actually live?

    ~/.claude/skills/<name> is a symlink for everything `sk deploy` owns; the
    target path tells us the rivendell folder (skills/<folder>/<name>). gstack
    ships as its own pack; anything else is a hand-installed external skill.
    """
    name = skill_dir.name
    if name.startswith("gstack") or name == "gstack":
        return "gstack", ""
    try:
        target = skill_dir.resolve()
    except OSError:
        return "external", ""
    try:
        rel = target.relative_to(RIVENDELL_SKILLS.resolve())
    except ValueError:
        return "external", ""
    parts = rel.parts
    return ("rivendell", parts[0]) if len(parts) >= 2 else ("rivendell", "")


def _description(text: str) -> str:
    """First sentence of the frontmatter description, folded-block aware.

    _parse_frontmatter is single-line and returns ">" for `description: >`
    blocks, which is what most rivendell skills use.
    """
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return ""
    lines = m.group(1).splitlines()
    for i, line in enumerate(lines):
        dm = re.match(r"^description\s*:\s*(.*)$", line)
        if not dm:
            continue
        head = dm.group(1).strip()
        if head and head not in (">", "|", ">-", "|-"):
            return head.strip("\"'")[:200]
        body: list[str] = []
        for cont in lines[i + 1:]:
            if cont and not cont.startswith((" ", "\t")):
                break
            if cont.strip():
                body.append(cont.strip())
        joined = " ".join(body)
        # Stop at the routing boilerplate; the first sentence is the summary.
        cut = re.split(r"\s(?:TRIGGER|SKIP|DO NOT TRIGGER)\b", joined, maxsplit=1)[0]
        return cut.strip()[:200]
    return ""


def _fm_str(frontmatter: dict[str, Any], key: str) -> str:
    v = frontmatter.get(key, "")
    return v.strip() if isinstance(v, str) else ""


def _read_tsv(tsv_path: Path | None = None) -> dict[str, dict[str, str]]:
    """Read TSV file into {name: {category_zh, summary_zh}}."""
    path = tsv_path or TSV_PATH
    if not path.exists():
        return {}

    result: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            result[parts[0]] = {
                "category_zh": parts[1],
                "summary_zh": parts[2],
            }
    return result


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Extract YAML frontmatter values (simple key: value parsing)."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    fm: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        # Handle simple key: value (skip multiline)
        m = re.match(r"^(\w[\w_-]*)\s*:\s*(.+)$", line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            # Parse booleans
            if val.lower() in ("true", "yes"):
                fm[key] = True
            elif val.lower() in ("false", "no"):
                fm[key] = False
            # Parse lists like [tag1, tag2]
            elif val.startswith("[") and val.endswith("]"):
                fm[key] = [v.strip() for v in val[1:-1].split(",")]
            else:
                fm[key] = val
    return fm


def _detect_lifecycle(name: str, frontmatter: dict[str, Any]) -> str:
    """Determine skill lifecycle: manual, hook, agent, or unknown."""
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    # Check tags for hints
    if "hooks" in tags or "hook" in tags:
        return "hook"
    if "agent" in tags:
        return "agent"

    # Check source field
    source = frontmatter.get("source", "")
    if source == "hook":
        return "hook"

    return "manual"


def list_skills(
    skills_dir: Path | None = None,
    tsv_path: Path | None = None,
) -> list[SkillInfo]:
    """Merge TSV metadata with SKILL.md files.

    Skills found in SKILL.md but not in TSV get empty category/summary.
    Skills in TSV but without SKILL.md are skipped (file is source of truth).
    """
    sdir = skills_dir or SKILLS_DIR
    tsv_data = _read_tsv(tsv_path)
    result: list[SkillInfo] = []

    if not sdir.is_dir():
        return result

    for skill_dir in sorted(sdir.iterdir()):
        # Skip hidden dirs, backup dirs (e.g. gstack.bak from upgrades),
        # and regular files (like __pycache__)
        name = skill_dir.name
        if name.startswith(".") or name.endswith(".bak") or name.endswith(".old"):
            continue
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue

        name = skill_dir.name
        text = skill_md.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        frontmatter = _parse_frontmatter(text)

        invocable = frontmatter.get("user_invocable", True)
        if isinstance(invocable, str):
            invocable = invocable.lower() not in ("false", "no")

        lifecycle = _detect_lifecycle(name, frontmatter)

        tsv_entry = tsv_data.get(name, {})
        source, folder = _locate(skill_dir)
        # Folder is the taxonomy of record (README Structure); the TSV label is
        # a legacy hand-written map kept only for skills we do not own.
        category = folder or tsv_entry.get("category_zh", "")
        summary = tsv_entry.get("summary_zh", "")
        if not summary:
            summary = _description(text)
        if not category and source == "gstack":
            category = "gstack"

        result.append(SkillInfo(
            name=name,
            category=category,
            summary=summary,
            line_count=line_count,
            invocable=bool(invocable),
            lifecycle=lifecycle,
            source=source,
            folder=folder,
            loop=_fm_str(frontmatter, "loop"),
            pdca=_fm_str(frontmatter, "pdca"),
        ))

        # Second pass: discover sub-pack skills nested one level deeper
        # (e.g. ~/.claude/skills/gstack/retro/SKILL.md → "gstack-retro").
        # The leaf SKILL.md frontmatter `name` is just "retro"; we prefix with
        # the parent dir to match user-facing slash-command form (/gstack-retro)
        # and avoid name collisions across packs.
        for sub_dir in sorted(skill_dir.iterdir()):
            if not sub_dir.is_dir():
                continue
            sname = sub_dir.name
            if sname.startswith(".") or sname.endswith(".bak") or sname.endswith(".old"):
                continue
            sub_md = sub_dir / "SKILL.md"
            if not sub_md.is_file():
                continue

            display_name = f"{name}-{sname}"
            sub_text = sub_md.read_text(encoding="utf-8")
            sub_line_count = len(sub_text.splitlines())
            sub_fm = _parse_frontmatter(sub_text)

            sub_invocable = sub_fm.get("user_invocable", True)
            if isinstance(sub_invocable, str):
                sub_invocable = sub_invocable.lower() not in ("false", "no")

            sub_lifecycle = _detect_lifecycle(display_name, sub_fm)

            sub_tsv = tsv_data.get(display_name, {})
            sub_category = sub_tsv.get("category_zh", "") or name
            sub_summary = sub_tsv.get("summary_zh", "")
            if not sub_summary:
                sub_summary = _description(sub_text)

            result.append(SkillInfo(
                name=display_name,
                category=sub_category,
                summary=sub_summary,
                line_count=sub_line_count,
                invocable=bool(sub_invocable),
                lifecycle=sub_lifecycle,
                source="gstack" if name.startswith("gstack") else "external",
                folder="",
                loop=_fm_str(sub_fm, "loop"),
                pdca=_fm_str(sub_fm, "pdca"),
            ))

    result.extend(_get_builtins_cached())
    return result


# ─── Built-in skill discovery (compiled into `claude` binary) ───────────────

_BUILTIN_CACHE: list[SkillInfo] | None = None


def _get_builtins_cached() -> list[SkillInfo]:
    """Cache built-ins for process lifetime. Binary doesn't change live —
    api restart picks up new built-ins on Claude Code upgrade.
    """
    global _BUILTIN_CACHE
    if _BUILTIN_CACHE is None:
        _BUILTIN_CACHE = _extract_builtin_skills()
    return _BUILTIN_CACHE


def _extract_builtin_skills() -> list[SkillInfo]:
    """Parse the `claude` binary for compiled-in skills + slash commands.

    Two registration patterns:
    - T$({name:"...",description:"..."})   → 11 skills (update-config etc.)
    - {type:"prompt",name:"...",description:"...",source:"builtin"}  → 5 commands

    Falls back to /usr/bin/strings; if missing or claude not on PATH, returns [].
    """
    claude_path = shutil.which("claude")
    if not claude_path:
        return []
    try:
        out = subprocess.check_output(
            ["strings", claude_path], stderr=subprocess.DEVNULL, timeout=10,
        ).decode("utf-8", errors="replace")
    except Exception:
        return []

    seen: set[str] = set()
    skills: list[SkillInfo] = []

    # Pass 1: discover names. Two registration forms.
    name_pattern_a = re.compile(r'T\$\(\{name:"([a-z][a-z0-9-]+)"')
    name_pattern_b = re.compile(
        r'\{type:"prompt",name:"([a-z][a-z0-9-]+)"[^}]{0,400}source:"builtin"'
    )
    candidate_names: list[str] = []
    for m in name_pattern_a.finditer(out):
        candidate_names.append(m.group(1))
    for m in name_pattern_b.finditer(out):
        candidate_names.append(m.group(1))
    # Always include init (uses a getter for description, doesn't match pattern_b)
    candidate_names.append("init")

    # Pass 2: for each name, try harder to extract description (single OR double
    # quote). If still empty, fall back to the hardcoded dict.
    for name in candidate_names:
        if name in seen:
            continue
        seen.add(name)
        desc = _extract_builtin_description(out, name) or _BUILTIN_FALLBACK_DESC.get(name, "")
        skills.append(SkillInfo(
            name=name, category="builtin", source="builtin",
            summary=desc[:300], line_count=0,
            invocable=True, lifecycle="builtin",
        ))

    return skills


def _extract_builtin_description(blob: str, name: str) -> str:
    """Find the description literal for a built-in skill. Tries both single
    and double quotes; returns first non-empty match."""
    escaped = re.escape(name)
    # Look in 600-char window after the name registration
    for quote in ('"', "'"):
        q = re.escape(quote)
        pat = re.compile(
            rf'name:"{escaped}"[^{q}]{{0,600}}?description:{q}([^{q}]{{1,500}}){q}'
        )
        m = pat.search(blob)
        if m:
            return m.group(1)
    return ""
