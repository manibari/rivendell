"""Canonical JSON output."""

import json

ORDER = {
    0: ("schema", "system", "config", "modules"),
    "config": ("source_roots", "route_style", "route_files", "e2e_dirs", "e2e_report", "base_url"),
    "modules": ("id", "name_zh", "status", "blueprint_id", "paths", "screens"),
    "screens": ("id", "layout", "route", "redirect", "sample", "states", "controls"),
    "states": ("id", "steps"),
    "controls": ("id", "role", "name", "state", "repeat", "does", "evidence", "success", "failure", "cases"),
    "cases": ("id", "kind", "status", "na_reason", "boundary", "expect"),
}


def ordered(value, context=0):
    if isinstance(value, list):
        return [ordered(item, context) for item in value]
    if not isinstance(value, dict):
        return value
    known = ORDER.get(context, ())
    keys = [key for key in known if key in value]
    keys += sorted(key for key in value if key not in known)
    return {key: ordered(value[key], key if key in ORDER else None) for key in keys}


def canonical(tree):
    return json.dumps(ordered(tree), ensure_ascii=False, indent=2) + "\n"
