"""Validate a feature tree without rejecting draft controls."""

import re

from .common import row

KINDS = ("happy", "empty", "invalid-input", "no-permission",
         "dependency-down", "repeat", "side-effect")
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DYNAMIC = re.compile(r"\[\[?\.\.\.([a-zA-Z][a-zA-Z0-9_-]*)\]\]?|\[([a-zA-Z][a-zA-Z0-9_-]*)\]")
STEPS = {"click", "fill", "press", "goto", "wait_for"}


def validate(tree):
    rows = []
    if not isinstance(tree, dict):
        return [row("SCHEMA", "$", "根節點必須是物件")]
    if tree.get("schema") != 1:
        return [row("SCHEMA_VERSION", "$.schema", "版本必須是 1")]
    for key in ("system", "config"):
        if key not in tree:
            rows.append(row("REQUIRED", f"$.{key}", "缺少必要欄位"))
    config = tree.get("config", {})
    if not isinstance(config, dict):
        rows.append(row("TYPE", "$.config", "必須是物件"))
    else:
        for key in ("source_roots", "route_files", "e2e_dirs", "e2e_report", "base_url"):
            if key not in config:
                rows.append(row("REQUIRED", f"$.config.{key}", "缺少必要欄位"))
        if config.get("route_style", "next-app") != "next-app":
            rows.append(row("ROUTE_STYLE", "$.config.route_style", "只支援 next-app"))
    if not isinstance(tree.get("modules", []), list):
        return rows + [row("TYPE", "$.modules", "模組必須是陣列")]
    for mi, module in enumerate(tree.get("modules", [])):
        mp = f"$.modules[{mi}]"
        _fields(module, ("id", "name_zh", "paths"), mp, rows)
        if not isinstance(module, dict):
            continue
        _id(module, mp, rows)
        if module.get("status") not in (None, "planned"):
            rows.append(row("STATUS", mp + ".status", "模組狀態只能是 planned"))
        _siblings(module.get("screens", []), mp + ".screens", rows)
        for si, screen in enumerate(module.get("screens", [])):
            sp = f"{mp}.screens[{si}]"
            _fields(screen, ("id",), sp, rows)
            if not isinstance(screen, dict):
                continue
            _id(screen, sp, rows)
            if screen.get("layout"):
                if "route" in screen:
                    rows.append(row("LAYOUT_ROUTE", sp + ".route", "版面畫面不可設定路由"))
                if "redirect" in screen:
                    rows.append(row("LAYOUT_REDIRECT", sp + ".redirect", "版面畫面不可設定轉址"))
            elif not screen.get("route"):
                rows.append(row("REQUIRED", sp + ".route", "一般畫面需要路由"))
            if "redirect" in screen:
                redirect = screen["redirect"]
                if not isinstance(redirect, str) or not redirect.startswith("/"):
                    rows.append(row("REDIRECT_PATH", sp + ".redirect", "轉址路徑必須以 / 開頭"))
                if screen.get("controls") or screen.get("states"):
                    rows.append(row("REDIRECT_WITH_CONTROLS", sp, "轉址頁不應該有自己的控制項或狀態"))
            route = screen.get("route", "")
            sample = screen.get("sample", {})
            for path in (route, screen.get("redirect", "")):
                if isinstance(path, str):
                    for match in DYNAMIC.finditer(path):
                        name = match.group(1) or match.group(2)
                        if not isinstance(sample, dict) or not sample.get(name):
                            rows.append(row("SAMPLE_MISSING", sp + ".sample", f"動態路由缺少 {name} 範例"))
            states = screen.get("states", [])
            _siblings(states, sp + ".states", rows)
            state_ids = {s.get("id") for s in states if isinstance(s, dict)}
            for ti, state in enumerate(states):
                tp = f"{sp}.states[{ti}]"
                _fields(state, ("id", "steps"), tp, rows)
                if not isinstance(state, dict):
                    continue
                _id(state, tp, rows)
                for xi, step in enumerate(state.get("steps", [])):
                    xp = f"{tp}.steps[{xi}]"
                    if not isinstance(step, dict) or len(step) != 1 or next(iter(step), None) not in STEPS:
                        rows.append(row("STEP", xp, "步驟必須只有一個有效動作"))
                        continue
                    action, value = next(iter(step.items()))
                    required = {"click": ("role", "name"), "fill": ("role", "name", "value"),
                                "press": ("key",), "wait_for": ("role", "name")}.get(action)
                    if required and (not isinstance(value, dict) or any(k not in value for k in required)):
                        rows.append(row("STEP", xp, "步驟缺少必要值"))
                    if action == "goto" and not isinstance(value, str):
                        rows.append(row("STEP", xp, "goto 必須是路徑"))
            _siblings(screen.get("controls", []), sp + ".controls", rows)
            for ci, control in enumerate(screen.get("controls", [])):
                cp = f"{sp}.controls[{ci}]"
                _fields(control, ("id", "role", "name", "does", "evidence", "success", "failure", "cases"), cp, rows)
                if not isinstance(control, dict):
                    continue
                _id(control, cp, rows)
                if control.get("state", "default") not in state_ids | {"default"}:
                    rows.append(row("STATE_UNKNOWN", cp + ".state", "找不到畫面狀態"))
                if control.get("does") == "unknown":
                    rows.append(row("UNKNOWN_PURPOSE", cp + ".does", "控制項用途尚未釐清"))
                if not control.get("evidence"):
                    rows.append(row("NO_EVIDENCE", cp + ".evidence", "缺少處理程式依據"))
                cases = control.get("cases", [])
                _siblings(cases, cp + ".cases", rows)
                found = set()
                for ki, case in enumerate(cases):
                    kp = f"{cp}.cases[{ki}]"
                    _fields(case, ("id", "kind", "expect"), kp, rows)
                    if not isinstance(case, dict):
                        continue
                    _id(case, kp, rows)
                    kind = case.get("kind")
                    if kind not in KINDS:
                        rows.append(row("KIND_INVALID", kp + ".kind", "無效的案例種類"))
                    else:
                        found.add(kind)
                    if case.get("status") == "na" and not case.get("na_reason"):
                        rows.append(row("NA_REASON", kp + ".na_reason", "不適用需要原因"))
                    if case.get("status") not in (None, "na"):
                        rows.append(row("STATUS", kp + ".status", "案例狀態只能是 na"))
                    if "boundary" in case and (kind != "side-effect" or case["boundary"] != "recorder"):
                        rows.append(row("BOUNDARY", kp + ".boundary", "只有 side-effect 可使用 recorder"))
                for kind in KINDS:
                    if kind not in found:
                        rows.append(row("KIND_MISSING", cp + ".cases", f"缺少 {kind} 案例"))
    _siblings(tree.get("modules", []), "$.modules", rows)
    return rows


def _fields(obj, fields, path, rows):
    if not isinstance(obj, dict):
        rows.append(row("TYPE", path, "必須是物件"))
        return
    for field in fields:
        if field not in obj:
            rows.append(row("REQUIRED", path + "." + field, "缺少必要欄位"))


def _id(obj, path, rows):
    value = obj.get("id") if isinstance(obj, dict) else None
    if value is not None and (not isinstance(value, str) or not ID.fullmatch(value)):
        rows.append(row("ID_INVALID", path + ".id", "ID 必須使用小寫 kebab-case"))


def _siblings(items, path, rows):
    seen = set()
    for index, item in enumerate(items):
        value = item.get("id") if isinstance(item, dict) else None
        if value is not None:
            if value in seen:
                rows.append(row("ID_DUPLICATE", f"{path}[{index}].id", "同層 ID 重複"))
            seen.add(value)
