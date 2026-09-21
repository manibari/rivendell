"""Repository Git health read model."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter()

@router.get("/api/health/git", tags=["Health"])
def api_git_health() -> dict[str, Any]:
    """Git hygiene across all repos under the code root (parent of this repo).

    Per repo: branch, uncommitted file count, ahead/behind vs upstream. Surfaces
    work that's sitting uncommitted or unpushed. Scans ~17 repos in ~0.5s.
    """
    code_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent

    def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )

    repos: list[dict[str, Any]] = []
    if code_root.is_dir():
        for d in sorted(code_root.iterdir()):
            if not (d / ".git").exists():
                continue
            try:
                branch = git(d, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "?"
                dirty = sum(
                    1 for ln in git(d, "status", "--porcelain").stdout.splitlines() if ln.strip()
                )
                ahead = behind = 0
                has_upstream = git(d, "rev-parse", "--abbrev-ref", "@{u}").returncode == 0
                if has_upstream:
                    parts = git(d, "rev-list", "--left-right", "--count", "@{u}...HEAD").stdout.split()
                    if len(parts) == 2:
                        behind, ahead = int(parts[0]), int(parts[1])
            except (subprocess.SubprocessError, ValueError, OSError):
                continue
            repos.append({
                "name": d.name,
                "branch": branch,
                "dirty": dirty,
                "ahead": ahead,
                "behind": behind,
                "has_upstream": has_upstream,
            })

    repos.sort(key=lambda r: (r["dirty"] + r["ahead"] + r["behind"]), reverse=True)
    return {
        "root": str(code_root),
        "total": len(repos),
        "dirty": sum(1 for r in repos if r["dirty"] > 0),
        "unpushed": sum(1 for r in repos if r["ahead"] > 0),
        "repos": repos,
    }
