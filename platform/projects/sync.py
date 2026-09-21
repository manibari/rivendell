#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sk-projects-sync — regenerate ~/.claude/projects.json from sources of truth.

WHY THIS EXISTS

~/.claude/projects.json lives outside the repo, so it does not travel with a
clone. On a fresh machine it is simply absent, and everything downstream
degrades quietly: `sk check ssot` reports drift for every agent, and every
project card in the dashboard renders with an empty description. That is
exactly what happened after the 2026-07 machine move, and it stayed broken for
days because nothing fails loudly when a file is merely missing.

Hand-maintaining it is the wrong answer — it drifts from agents.conf the moment
an agent is added. Everything except `mission` is already recorded somewhere
authoritative, so derive it:

    repo        <- the filesystem
    agents      <- agents/registry/*.md, via `sk-registry-gen generate`
                   (the same generated conf `sk check ssot` diffs against)
    description <- the repo's own README H1
    mission     <- NOT derivable. Preserved across runs if already written,
                   left empty otherwise. That is a human's to fill in.

Per-agent prose belongs in .claude/agents.json (which IS versioned) — the
dashboard reads descriptions from there, not from this file.

Usage:
    sk-projects-sync [--dry-run] [--print]
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OUT = Path.home() / ".claude" / "projects.json"
SIBLINGS = REPO.parent


def readme_h1(path: Path) -> str:
    readme = path / "README.md"
    if not readme.exists():
        return ""
    for line in readme.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#"):
            return line.lstrip("# ").strip()
    return ""


def agents_conf_text() -> str:
    """Return a FRESH agents.conf.

    agents.conf is a generated build artifact (SoT = agents/registry/*.md) and
    is gitignored, so on a fresh clone it is simply absent and on an old one it
    is stale. Either way, reading it off disk would hand back an empty or wrong
    agent list — and this script's whole reason for existing is that a missing
    file fails quietly. Generate, and only fall back to the on-disk cache if
    generation itself breaks. This mirrors `_ensure_agents_conf` in bin/sk.
    """
    gen = REPO / "bin" / "sk-registry-gen"
    if gen.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(gen), "generate"],
                capture_output=True, text=True, check=True,
            )
            return result.stdout
        except (subprocess.CalledProcessError, OSError) as exc:
            print(f"warning: sk-registry-gen failed ({exc}); "
                  f"falling back to the on-disk agents.conf", file=sys.stderr)
    conf = REPO / "agents" / "agents.conf"
    if not conf.exists():
        print("warning: no agents.conf and no generator — "
              "every project will report 0 agents", file=sys.stderr)
        return ""
    return conf.read_text(encoding="utf-8")


def agents_by_project() -> dict[str, list[str]]:
    """Parse agents.conf. Service labels (com.sk.dashboard.*) are not agents."""
    out: dict[str, list[str]] = {}
    for line in agents_conf_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        match = re.match(r"^com\.sk\.agent\.[^.]+\.(.+)$", parts[0])
        if not match:
            continue
        out.setdefault(parts[1], []).append(match.group(1))
    return out


def build() -> dict:
    # Preserve anything a human wrote; only regenerate the derivable fields.
    existing: dict = {}
    if OUT.exists():
        try:
            existing = json.loads(OUT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}

    by_project = agents_by_project()
    projects: dict = {}

    candidates = [REPO]
    if SIBLINGS.exists():
        candidates += [SIBLINGS / n for n in sorted(os.listdir(SIBLINGS))]
    # Sibling layout differs per machine; also look where agents.conf points.
    alt = Path.home() / "Company" / "engineering" / "repos"
    if alt.exists() and alt != SIBLINGS:
        candidates += [alt / n for n in sorted(os.listdir(alt))]

    seen: set[str] = set()
    for path in candidates:
        if not path.is_dir() or not (path / ".git").exists():
            continue
        name = path.name
        if name in seen:
            continue
        seen.add(name)
        prior = existing.get(name, {})
        projects[name] = {
            "repo": str(path),
            "description": readme_h1(path) or prior.get("description", ""),
            "agents": sorted(by_project.get(name, [])),
            # mission is authored by hand and never generated — carry it over.
            "mission": prior.get("mission", {}) or {},
        }

    # Keep entries for repos not present on this machine rather than dropping
    # them: a checkout missing locally is not the same as a project retired.
    for name, entry in existing.items():
        if name not in projects:
            entry.setdefault("agents", [])
            entry["_absent_on_this_machine"] = True
            projects[name] = entry

    # The registry defines agents for projects that may not be cloned here at
    # all. Without a stub entry `sk check ssot` reports those agents as missing
    # metadata on every run, forever — drift that no action can ever clear,
    # which trains everyone to ignore the whole report.
    for name, agents in by_project.items():
        if name not in projects:
            projects[name] = {
                "repo": "",
                "description": "",
                "agents": sorted(agents),
                "mission": {},
                "_absent_on_this_machine": True,
            }
        elif projects[name].get("_absent_on_this_machine"):
            projects[name]["agents"] = sorted(agents)
    return projects


def main() -> int:
    dry = "--dry-run" in sys.argv
    projects = build()
    blob = json.dumps(projects, ensure_ascii=False, indent=2) + "\n"

    if "--print" in sys.argv:
        print(blob)
        return 0

    if dry:
        print(f"--dry-run — would write {OUT}")
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(blob, encoding="utf-8")
        print(f"wrote {OUT}")

    for name, p in projects.items():
        flag = " (absent here)" if p.get("_absent_on_this_machine") else ""
        missing = "" if p.get("description") else "  [no description]"
        print(f"  {name:<24} agents={len(p.get('agents', [])):<3}{missing}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
