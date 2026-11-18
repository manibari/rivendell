"""New E2E path overrides preserve production defaults."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "module_name,helper,env_name,default",
    [
        ("routes.harvest", "_skill_repo_dir", "HARVEST_SKILLS_ROOT",
         lambda m: m.REPO_DIR),
        ("routes.monitoring.disk", "_snapshot_file", "DISK_TREE_FILE",
         lambda m: Path("/fixture/repo/dashboard/data/disk-tree.json")),
        ("routes.monitoring.disk", "_snapshot_command", "DISK_SNAPSHOT_COMMAND",
         lambda m: Path("/fixture/repo/bin/sk-disk-snapshot")),
        ("routes.monitoring.overview", "_sk_command", "SK_CHECK_COMMAND",
         lambda m: Path("/fixture/repo/bin/sk")),
        ("routes.monitoring.git", "_code_root", "GIT_HEALTH_ROOT",
         lambda m: Path(m.__file__).resolve().parents[5]),
        ("routes.monitoring.issues", "_projects_dir", "ISSUES_PROJECTS_DIR",
         lambda m: m.REPO_DIR.parent),
        ("routes.monitoring.errors", "_reports_dir", "REPORTS_DIR",
         lambda m: Path("/fixture/repo/reports")),
    ],
)
def test_route_override(monkeypatch, module_name, helper, env_name, default):
    module = importlib.import_module(module_name)
    monkeypatch.delenv(env_name, raising=False)
    get_path = getattr(module, helper)
    args = (Path("/fixture/repo"),) if helper in {
        "_snapshot_file", "_snapshot_command", "_sk_command", "_reports_dir"
    } else ()
    assert get_path(*args) == default(module)
    monkeypatch.setenv(env_name, "/fixture/override")
    assert get_path(*args) == Path("/fixture/override")


def test_legacy_database_override(monkeypatch):
    import lib.db as db

    monkeypatch.delenv("RIVENDELL_LEGACY_DB_PATH", raising=False)
    importlib.reload(db)
    assert db.DB_PATH == Path(db.__file__).parent.parent / "data" / "rivendell.db"
    monkeypatch.setenv("RIVENDELL_LEGACY_DB_PATH", "/fixture/override.db")
    importlib.reload(db)
    assert db.DB_PATH == Path("/fixture/override.db")
    monkeypatch.delenv("RIVENDELL_LEGACY_DB_PATH")
    importlib.reload(db)
