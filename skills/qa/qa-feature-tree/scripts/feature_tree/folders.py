"""Compare module ownership with source files."""

import re
from pathlib import Path

from .common import row

EXCLUDED = {"node_modules", ".next", "__pycache__", ".venv"}


def glob_match(pattern, path):
    """Match paths with globstar folders and single-segment stars."""
    pattern = pattern.replace("\\", "/").strip("/")
    path = path.replace("\\", "/").strip("/")
    parts = pattern.split("/")
    expression = "^"
    for index, part in enumerate(parts):
        if part == "**":
            expression += "(?:[^/]+/)*" if index < len(parts) - 1 else "(?:.*)?"
        else:
            expression += re.escape(part).replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
            if index < len(parts) - 1:
                expression += "/"
    return re.fullmatch(expression + "$", path) is not None


def source_files(tree, repo):
    config = tree.get("config", {})
    roots = config.get("source_roots", [])
    e2e = config.get("e2e_dirs", [])
    ignores = config.get("ignore", [])
    found = set()
    for root in roots:
        base = Path(repo, root)
        if not base.exists():
            continue
        for file in base.rglob("*"):
            if not file.is_file():
                continue
            relative = file.relative_to(repo).as_posix()
            parts = file.relative_to(repo).parts
            if any(part in EXCLUDED or part.startswith(".") for part in parts[:-1]):
                continue
            if any(relative == directory.rstrip("/") or relative.startswith(directory.rstrip("/") + "/") for directory in e2e):
                continue
            if any(glob_match(pattern, relative) for pattern in ignores):
                continue
            found.add(relative)
    return sorted(found)


def check(tree, repo):
    files = source_files(tree, repo)
    rows = []
    by_folder = {}
    for file in files:
        owners = [module["id"] for module in tree.get("modules", [])
                  if any(glob_match(pattern, file) for pattern in module.get("paths", []))]
        if not owners:
            rows.append(row("UNOWNED", file, "來源檔案沒有模組擁有者"))
        if len(owners) > 1:
            rows.append(row("OVERLAP", file, "多個模組擁有：" + "、".join(owners)))
        if len(owners) == 1:
            by_folder.setdefault(str(Path(file).parent), set()).update(owners)
    for module in tree.get("modules", []):
        for pattern in module.get("paths", []):
            if module.get("status") != "planned" and not any(glob_match(pattern, file) for file in files):
                rows.append(row("EMPTY_GLOB", pattern, f"模組 {module['id']} 的路徑沒有來源檔案"))
    for folder, owners in sorted(by_folder.items()):
        if len(owners) > 1:
            rows.append(row("MIXED_FOLDER", folder, "同層檔案屬於模組：" + "、".join(sorted(owners)), "yellow"))
    return rows
