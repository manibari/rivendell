#!/usr/bin/env python3
"""
generate-readme-catalog.py
Regenerate the Skills Catalog section of README.md from SKILL.md frontmatter.

Strategy:
- Preserves existing descriptions for known skills (assumed to be carefully written Chinese text)
- Auto-generates English description for NEW skills from their SKILL.md frontmatter
- Detects trigger mode from frontmatter fields (trigger_label > pattern detection > default)
- Replaces only the section between "## Skills Catalog" and the next "## " heading
"""

import re
import sys
from pathlib import Path

RIVENDELL_ROOT = Path(__file__).parent.parent
SKILLS_DIR = RIVENDELL_ROOT / "skills"
README_PATH = RIVENDELL_ROOT / "README.md"

CATEGORY_ORDER = ["meta", "workflow", "quality", "git", "frontend", "backend", "media", "docs"]
CATEGORY_NAMES = {
    "meta": "Claude Code 管理",
    "workflow": "工作流程與規劃",
    "quality": "程式品質",
    "git": "Git/GitHub",
    "frontend": "前端設計、iOS、測試",
    "backend": "後端服務",
    "media": "影音抓讀",
    "docs": "文件處理與 MCP 建置",
}


# ── Frontmatter parser (no external deps) ────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from markdown. Handles scalar, >, and list values."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm_text = text[4:end]
    fm: dict = {}
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith("#"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, raw_val = line.partition(":")
        key = key.strip()
        raw_val = raw_val.strip()

        if raw_val == ">":
            # Block scalar: collect subsequent indented lines
            parts = []
            i += 1
            while i < len(lines) and lines[i] and (lines[i][0] == " " or lines[i][0] == "\t"):
                parts.append(lines[i].strip())
                i += 1
            fm[key] = " ".join(parts)
            continue

        if raw_val.startswith("[") and raw_val.endswith("]"):
            fm[key] = [t.strip().strip("'\"") for t in raw_val[1:-1].split(",") if t.strip()]
        elif raw_val.lower() == "true":
            fm[key] = True
        elif raw_val.lower() == "false":
            fm[key] = False
        else:
            # Strip inline comment
            if " #" in raw_val:
                raw_val = raw_val[: raw_val.index(" #")].strip()
            fm[key] = raw_val.strip("'\"")

        i += 1
    return fm


# ── Trigger detection ─────────────────────────────────────────────────────────

def detect_trigger(fm: dict, skill_name: str) -> str:
    """
    Determine the 觸發方式 label for a skill.
    Priority: trigger_label field > pattern detection > default '自動'
    """
    # 1. Explicit override
    if "trigger_label" in fm:
        return fm["trigger_label"]

    desc = ""
    if isinstance(fm.get("description"), str):
        desc = fm["description"]
    elif isinstance(fm.get("when_to_use"), str):
        desc = fm["when_to_use"]
    desc_lower = desc.lower()

    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    tags_lower = [str(t).lower() for t in tags]

    # 2. Hook detection (PreToolUse / PostToolUse)
    if any(kw in desc_lower for kw in ("pretooluse", "pre_tool_use", "pre-tool-use", "pre tool use")):
        return "Hook (PreToolUse)"
    if any(kw in desc_lower for kw in ("posttooluse", "post_tool_use", "post-tool-use", "post tool use")):
        return "Hook (PostToolUse)"
    # Fallback: check tags for hook type
    if "hook" in tags_lower:
        if any("pre" in t for t in tags_lower):
            return "Hook (PreToolUse)"
        if any("post" in t for t in tags_lower):
            return "Hook (PostToolUse)"

    # 3. User invocable (slash command)
    user_invocable = fm.get("user_invocable", False)
    if user_invocable:
        cmd = f"`/{skill_name}`"
        # Check if also auto-triggered
        if "trigger when" in desc_lower or "automatically" in desc_lower:
            return f"{cmd} 或自動"
        return cmd

    # 4. Default
    return "自動"


# ── Description extraction ────────────────────────────────────────────────────

def extract_auto_description(fm: dict, skill_name: str) -> str:
    """
    Extract a short English description from frontmatter for NEW skills.
    Used as fallback when no existing Chinese description exists in README.
    """
    if "summary" in fm:
        return fm["summary"]

    desc = ""
    if isinstance(fm.get("description"), str):
        desc = fm["description"]
    if not desc:
        return skill_name

    # Strip everything from "TRIGGER when:" onwards
    for cutoff in ("TRIGGER when:", "DO NOT TRIGGER", "TRIGGER WHEN:", "Use this skill", "Use when"):
        pos = desc.find(cutoff)
        if pos > 10:
            desc = desc[:pos].strip()

    # Trim trailing punctuation and whitespace
    desc = desc.rstrip(". \n")

    # Limit length
    if len(desc) > 80:
        for ch in (".", ",", " "):
            pos = desc.rfind(ch, 0, 80)
            if pos > 25:
                desc = desc[: pos + (1 if ch == "." else 0)].strip()
                break
        else:
            desc = desc[:77] + "..."

    return desc


# ── README catalog parser ─────────────────────────────────────────────────────

def parse_existing_catalog(readme_text: str) -> dict:
    """
    Extract existing skill entries from the README catalog tables.
    Returns {skill_name: {'trigger': str, 'description': str}}
    """
    catalog: dict = {}
    pattern = re.compile(r"\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")
    for m in pattern.finditer(readme_text):
        name = m.group(1).strip()
        trigger = m.group(2).strip()
        desc = m.group(3).strip()
        if name and trigger and desc:
            catalog[name] = {"trigger": trigger, "description": desc}
    return catalog


# ── Skill scanner ─────────────────────────────────────────────────────────────

def scan_skills() -> dict:
    """Scan all skills/CAT/NAME/SKILL.md files. Returns {category: [(name, fm), ...]}."""
    result: dict = {cat: [] for cat in CATEGORY_ORDER}
    for cat in CATEGORY_ORDER:
        cat_dir = SKILLS_DIR / cat
        if not cat_dir.exists():
            continue
        for skill_dir in sorted(cat_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            fm = parse_frontmatter(skill_md.read_text())
            if fm:
                result[cat].append((skill_dir.name, fm))
    return result


# ── Catalog section generator ─────────────────────────────────────────────────

def generate_catalog_section(categories: dict, existing: dict) -> str:
    total = sum(len(v) for v in categories.values())
    lines = [f"## Skills Catalog ({total} skills)", ""]

    for cat in CATEGORY_ORDER:
        skills = categories.get(cat, [])
        if not skills:
            continue
        cat_name = CATEGORY_NAMES.get(cat, cat)
        lines += [
            f"### {cat}/ — {cat_name}",
            "",
            "| Skill | 觸發方式 | 說明 |",
            "|-------|---------|------|",
        ]
        for skill_name, fm in skills:
            prior = existing.get(skill_name, {})
            trigger = prior.get("trigger") or detect_trigger(fm, skill_name)
            description = prior.get("description") or extract_auto_description(fm, skill_name)
            lines.append(f"| **{skill_name}** | {trigger} | {description} |")
        lines.append("")

    return "\n".join(lines)


# ── README updater ────────────────────────────────────────────────────────────

def update_readme(new_section: str) -> bool:
    readme_text = README_PATH.read_text()
    start_m = re.search(r"^## Skills Catalog.*$", readme_text, re.MULTILINE)
    if not start_m:
        print("ERROR: '## Skills Catalog' not found in README.md", file=sys.stderr)
        return False
    # Next top-level heading after the catalog
    end_m = re.search(r"^## ", readme_text[start_m.end():], re.MULTILINE)
    if end_m:
        end_pos = start_m.end() + end_m.start()
    else:
        end_pos = len(readme_text)
    updated = readme_text[: start_m.start()] + new_section + "\n\n" + readme_text[end_pos:]
    README_PATH.write_text(updated)
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    readme_text = README_PATH.read_text()
    existing = parse_existing_catalog(readme_text)
    categories = scan_skills()
    section = generate_catalog_section(categories, existing)
    if not update_readme(section):
        return 1
    total = sum(len(v) for v in categories.values())
    cats = sum(1 for v in categories.values() if v)
    print(f"README.md updated: {total} skills in {cats} categories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
