"""Read token waste reports written by the scheduled watch."""
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()
REPO_DIR = Path(__file__).resolve().parents[4]
REPORT_NAME = re.compile(r"^token-watch-(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$")
WINDOW = re.compile(r"^- 資料區間：(.+?) 到 (.+?)\s*$", re.MULTILINE)
FAILED = re.compile(r"^## 判讀失敗\s*$", re.MULTILINE)


def _reports_dir() -> Path:
    return Path(os.environ.get("REPORTS_DIR", REPO_DIR / "reports"))


def _updated_at(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="minutes")


@router.get("/api/tokens/waste-reports", tags=["Tokens"])
def api_token_waste_reports() -> dict[str, list[dict[str, Any]]]:
    reports = []
    for path in _reports_dir().glob("token-watch-*.md"):
        match = REPORT_NAME.fullmatch(path.name)
        if not match or not path.is_file() or path.is_symlink():
            continue
        content = path.read_text(encoding="utf-8")
        window = WINDOW.search(content)
        reports.append({
            "name": path.name,
            "day": match.group(1),
            "host": match.group(2),
            "updated_at": _updated_at(path),
            "window": list(window.groups()) if window else None,
            "failed": bool(FAILED.search(content)),
        })
    reports.sort(key=lambda report: (report["day"], report["updated_at"]), reverse=True)
    return {"reports": reports}


@router.get("/api/tokens/waste-reports/{name:path}", tags=["Tokens"])
def api_token_waste_report(name: str) -> dict[str, str]:
    if not REPORT_NAME.fullmatch(name):
        raise HTTPException(status_code=404, detail="找不到報告。")
    path = _reports_dir() / name
    if not path.is_file() or path.is_symlink():
        raise HTTPException(status_code=404, detail="找不到報告。")
    return {"name": name, "updated_at": _updated_at(path),
            "markdown": path.read_text(encoding="utf-8")}
