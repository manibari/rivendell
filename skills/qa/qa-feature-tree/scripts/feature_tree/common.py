"""Shared tree helpers."""

import json
from pathlib import Path


def read_json(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def row(code, place, detail, severity="red"):
    return {"code": code, "place": str(place), "detail": detail, "severity": severity}


def modules(tree):
    return tree.get("modules", []) if isinstance(tree.get("modules", []), list) else []


def screens(tree):
    for module in modules(tree):
        for screen in module.get("screens", []):
            yield module, screen


def controls(tree):
    for module, screen in screens(tree):
        for control in screen.get("controls", []):
            yield module, screen, control


def leaves(tree):
    for module, screen, control in controls(tree):
        for case in control.get("cases", []):
            yield ".".join((module["id"], screen["id"], control["id"], case["id"])), case
