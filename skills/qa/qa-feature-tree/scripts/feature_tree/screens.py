"""Compare accessibility scan entries with tree controls."""

import re
from urllib.parse import quote, urlsplit

from .common import row, screens


def matches(control, scanned):
    if control.get("role") != scanned.get("role"):
        return False
    name = control.get("name", "")
    actual = scanned.get("name", "")
    if isinstance(name, str) and len(name) >= 2 and name.startswith("/") and name.endswith("/"):
        try:
            return re.fullmatch(name[1:-1], actual) is not None
        except re.error:
            return False
    return name == actual


def resolved_path(path, sample):
    def substitute(match):
        name = match.group(1) or match.group(2) or match.group(3)
        value = sample.get(name)
        if value is None:
            return match.group(0)
        return "/".join(quote(segment, safe="~!*'()") for segment in str(value).split("/"))

    return re.sub(r"\[\[\.\.\.([^\]]+)\]\]|\[\.\.\.([^\]]+)\]|\[([^\]]+)\]", substitute, path)


def normalized_path(path):
    return path.rstrip("/") or "/"


def check(tree, scan):
    rows = []
    if scan.get("schema") != 1:
        return [row("SCAN_SCHEMA", "$scan.schema", "掃描版本必須是 1")]
    entries = {(entry.get("module"), entry.get("screen"), entry.get("state", "default")): entry
               for entry in scan.get("screens", [])}
    layout = [(module, screen, control) for module, screen in screens(tree) if screen.get("layout")
              for control in screen.get("controls", [])]
    normal = [(module, screen) for module, screen in screens(tree) if not screen.get("layout")]
    redirect_keys = {(module["id"], screen["id"]) for module, screen in normal if "redirect" in screen}
    reached_defaults = [entry for key, entry in entries.items() if key[2] == "default" and entry.get("reached")
                        and key[:2] not in redirect_keys]
    unlabeled_layout = {}
    for module, screen, control in layout:
        if not any(matches(control, scanned) for entry in reached_defaults for scanned in entry.get("controls", [])):
            rows.append(row("MISSING", f"{module['id']}.{screen['id']}.{control['id']}",
                            "共用控制項未出現在任何已到達的預設畫面"))
    for module, screen in normal:
        if "redirect" in screen:
            key = (module["id"], screen["id"], "default")
            entry = entries.get(key)
            place = ".".join(key[:2])
            if not entry or not entry.get("reached") or not entry.get("final_url"):
                rows.append(row("REDIRECT_UNCHECKED", place, "掃描沒有到達或沒有最終網址", "yellow"))
            else:
                expected = normalized_path(urlsplit(resolved_path(screen["redirect"], screen.get("sample", {}))).path)
                actual = normalized_path(urlsplit(entry["final_url"]).path)
                if actual != expected:
                    rows.append(row("REDIRECT_BROKEN", place, f"預期 {expected}；實際 {actual}"))
            continue
        states = ["default"] + [state.get("id") for state in screen.get("states", [])]
        for state in states:
            key = (module["id"], screen["id"], state)
            entry = entries.get(key)
            own = [control for control in screen.get("controls", []) if control.get("state", "default") == state]
            if not entry or not entry.get("reached"):
                for control in own:
                    rows.append(row("NOT_REACHED", ".".join((*key, control["id"])),
                                    "畫面或狀態未到達", "yellow"))
                continue
            defaults = [control for control in screen.get("controls", []) if control.get("state", "default") == "default"]
            matchers = own + ([] if state == "default" else defaults) + [control for _, _, control in layout]
            for index, scanned in enumerate(entry.get("controls", [])):
                place = ".".join(key) + f".controls[{index}]"
                if not scanned.get("name"):
                    layout_matches = [(layout_module, layout_screen, control)
                                      for layout_module, layout_screen, control in layout
                                      if control.get("name") == "" and matches(control, scanned)]
                    for layout_module, layout_screen, control in layout_matches:
                        layout_place = f"{layout_module['id']}.{layout_screen['id']}.{control['id']}"
                        unlabeled_layout.setdefault(layout_place, set()).add(key[:2])
                    if not layout_matches:
                        rows.append(row("UNLABELED", place, "控制項沒有可存取名稱"))
                if not any(matches(control, scanned) for control in matchers):
                    rows.append(row("ORPHAN", place, f"樹上找不到 {scanned.get('role', '')}：{scanned.get('name', '')}"))
            for control in own:
                if not any(matches(control, scanned) for scanned in entry.get("controls", [])):
                    rows.append(row("MISSING", ".".join((*key, control["id"])), "樹上的控制項未出現在畫面"))
    for place, seen_screens in unlabeled_layout.items():
        rows.append(row("UNLABELED", place, f"控制項沒有可存取名稱，出現在 {len(seen_screens)} 個畫面"))
    return rows


def adopt(tree, scan):
    rows = check(tree, scan)
    orphan_places = {item["place"] for item in rows if item["code"] == "ORPHAN"}
    lookup = {(module["id"], screen["id"]): screen for module, screen in screens(tree)}
    count = 0
    for entry in scan.get("screens", []):
        key = (entry.get("module"), entry.get("screen"))
        screen = lookup.get(key)
        if not screen:
            continue
        state = entry.get("state", "default")
        for index, scanned in enumerate(entry.get("controls", [])):
            place = ".".join((*key, state)) + f".controls[{index}]"
            if place not in orphan_places:
                continue
            role = re.sub(r"[^a-z0-9-]+", "-", scanned.get("role", "control").lower()).strip("-") or "control"
            existing = {control.get("id") for control in screen.get("controls", [])}
            number = 1
            while f"{role}-{number}" in existing:
                number += 1
            control = {"id": f"{role}-{number}", "role": scanned.get("role", ""),
                       "name": scanned.get("name", ""), "does": "unknown", "evidence": "",
                       "success": "", "failure": "", "cases": []}
            if state != "default":
                control["state"] = state
            screen.setdefault("controls", []).append(control)
            count += 1
    return count
