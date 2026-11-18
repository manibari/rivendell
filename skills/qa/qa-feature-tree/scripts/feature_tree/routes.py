"""Map Next App Router files to tree screens."""

from pathlib import Path

from .common import row, screens
from .folders import glob_match


def route_for(file):
    parts = Path(file).as_posix().split("/")
    try:
        start = parts.index("app") + 1
    except ValueError:
        return None
    if not parts[-1].startswith("page."):
        return None
    segments = [part for part in parts[start:-1] if not (part.startswith("(") and part.endswith(")"))]
    return "/" + "/".join(segments)


def route_files(tree, repo):
    found = set()
    for pattern in tree.get("config", {}).get("route_files", []):
        for file in Path(repo).rglob("*"):
            if file.is_file():
                relative = file.relative_to(repo).as_posix()
                if glob_match(pattern, relative):
                    found.add(relative)
    return sorted(found)


def check(tree, repo):
    files = route_files(tree, repo)
    routes = {file: route_for(file) for file in files}
    mapped = {screen.get("route") for _, screen in screens(tree) if not screen.get("layout")}
    rows = [row("UNMAPPED_ROUTE", file, f"路由 {route} 沒有對應畫面")
            for file, route in routes.items() if route not in mapped]
    available = set(routes.values())
    for module, screen in screens(tree):
        if not screen.get("layout") and screen.get("route") not in available:
            rows.append(row("MISSING_ROUTE", f"{module['id']}.{screen['id']}",
                            f"找不到路由 {screen.get('route', '')} 的檔案"))
    return rows


def initialize(tree, repo):
    if tree.get("modules"):
        raise ValueError("樹已有模組，無法初始化")
    groups = {}
    for file in route_files(tree, repo):
        route = route_for(file)
        if route is None:
            continue
        segments = route.strip("/").split("/") if route != "/" else []
        module_id = segments[0] if segments else "home"
        if module_id.startswith("["):
            module_id = "dynamic"
        group = groups.setdefault(module_id, {"id": module_id, "name_zh": module_id,
                                              "status": "planned", "paths": [], "screens": []})
        parent = str(Path(file).parent)
        pattern = file if route == "/" else parent + "/**"
        if pattern not in group["paths"]:
            group["paths"].append(pattern)
        screen_id = "main" if len(segments) <= 1 else "-".join(
            segment.strip("[]").replace("...", "") for segment in segments[1:])
        existing = {screen["id"] for screen in group["screens"]}
        candidate = screen_id
        counter = 2
        while candidate in existing:
            candidate = f"{screen_id}-{counter}"
            counter += 1
        group["screens"].append({"id": candidate, "route": route, "controls": []})
    tree["modules"] = list(groups.values())
    from .folders import source_files
    unclaimed = [file for file in source_files(tree, repo) if not any(
        glob_match(pattern, file) for module in tree["modules"] for pattern in module["paths"])]
    return unclaimed
