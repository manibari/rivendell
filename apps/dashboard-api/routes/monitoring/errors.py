"""Recent agent error log read model."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter()

@router.get("/api/health/errors", tags=["Health"])
def api_recent_errors() -> dict[str, Any]:
    """Recent non-empty agent error logs (reports/*-error.log).

    Complements /api/issues (which only shows exit codes) by surfacing the
    actual captured stderr text. "Noisy when broken, silent when fine" — an
    empty list means every recent agent run wrote nothing to stderr.
    """
    import time as _time

    repo_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    reports = repo_dir / "reports"
    recent_days = 14
    cutoff = _time.time() - recent_days * 86400
    errors: list[dict[str, Any]] = []
    if reports.is_dir():
        for f in reports.glob("*-error.log"):
            try:
                st = f.stat()
            except OSError:
                continue
            if st.st_size == 0 or st.st_mtime < cutoff:
                continue
            try:
                text = f.read_text(errors="replace")
            except OSError:
                text = ""
            tail = "\n".join(text.splitlines()[-12:])
            errors.append({
                "name": f.name,
                "size": st.st_size,
                "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                "tail": tail[:2000],
            })
    errors.sort(key=lambda e: e["mtime"], reverse=True)
    return {"recent_days": recent_days, "total": len(errors), "errors": errors}
