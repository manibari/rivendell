"""Human-readable report and tree rendering."""

from collections import Counter

from .common import leaves, row

EXPLANATIONS = {
    "ORPHAN": "畫面上有、樹上沒有，控制項用途尚未記錄。",
    "MISSING": "樹上的控制項沒有出現在畫面。",
    "UNLABELED": "控制項沒有可存取名稱。",
    "NOT_REACHED": "掃描未到達畫面或狀態。",
    "UNMAPPED_ROUTE": "路由檔案沒有對應畫面。",
    "MISSING_ROUTE": "畫面路由沒有對應檔案。",
    "UNOWNED": "來源檔案沒有模組擁有者。",
    "OVERLAP": "來源檔案由多個模組認領。",
    "EMPTY_GLOB": "模組路徑沒有來源檔案。",
    "MIXED_FOLDER": "同一資料夾有不同模組的直接檔案。",
    "STALE": "測試標籤沒有對應葉子。",
    "NO_TEST": "葉子沒有端到端測試。",
    "NOT_RUN": "葉子有測試標籤，但沒有最近的執行結果。",
    "FAILED": "葉子的端到端測試失敗。",
    "KIND_MISSING": "控制項缺少案例種類。",
    "UNKNOWN_PURPOSE": "沒人說得出這個控制項做什麼，要決定它的用途或拿掉它。",
    "NO_EVIDENCE": "控制項沒有寫處理程式的位置（file:line）。",
}


def _table(rows):
    if not rows:
        return "沒有問題\n"
    lines = ["| 代碼 | 位置 | 說明 |", "| --- | --- | --- |"]
    for item in rows:
        cells = [item["code"], item["place"], item["detail"]]
        lines.append("| " + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in cells) + " |")
    return "\n".join(lines) + "\n"


def build(tree, sections, leaf_status):
    all_rows = [item for section in sections for item in section]
    counts = Counter(leaf_status.values())
    # The owner reads this line first (design §4, "Report").
    first = (f"葉子 {len(leaf_status)} 片：通過 {counts['passed']}、失敗 {counts['failed']}、"
             f"沒有測試 {counts['no-test']}、未執行 {counts['not-run']}、不適用 {counts['na']}。"
             f"紅燈 {sum(item['severity'] == 'red' for item in all_rows)} 項，"
             f"黃燈 {sum(item['severity'] == 'yellow' for item in all_rows)} 項。")
    lines = [first, ""]
    seen = set()
    for number, (title, rows) in enumerate(zip(("樹的檢查", "樹和資料夾", "樹和路由", "樹和畫面", "樹和測試"), sections), 1):
        lines.extend((f"## {number} {title}", "", _table(rows)))
        for item in rows:
            code = item["code"]
            if code not in seen:
                lines.append(f"`{code}`：{EXPLANATIONS.get(code, item['detail'])}")
                seen.add(code)
        lines.append("")
    lines.extend(("## 6 還沒有測試的葉子（依模組）", ""))
    groups = {}
    for leaf, status in leaf_status.items():
        if status in ("no-test", "not-run"):
            groups.setdefault(leaf.split(".")[0], []).append(row(status.upper().replace("-", "_"), leaf, "尚未通過測試"))
    for module in tree.get("modules", []):
        if module["id"] in groups:
            lines.extend((f"### {module.get('name_zh', module['id'])}", "", _table(groups[module["id"]]), ""))
    if not groups:
        lines.append("沒有問題")
    return "\n".join(lines).rstrip() + "\n"


def render(tree):
    lines = [f"# {tree.get('system', '')} 功能樹", ""]
    for module in tree.get("modules", []):
        count = sum(1 for leaf, _ in leaves({"modules": [module]}) )
        lines.append(f"- {module.get('name_zh', module['id'])}（{count} 片葉子）")
        for screen in module.get("screens", []):
            lines.append(f"  - {screen['id']}")
            for control in screen.get("controls", []):
                lines.append(f"    - {control.get('name', control['id'])}（{control['id']}）")
                for case in control.get("cases", []):
                    lines.append(f"      - {case['id']}：{case.get('expect', '')}")
    return "\n".join(lines) + "\n"
