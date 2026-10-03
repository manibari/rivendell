#!/usr/bin/env python3
"""守衛：大小只是訊號，意義才是拆的理由（Yellow-Chick D37 / PTI-ARES PTI-492 的可攜版）。

    python scripts/checks/check_size.py [--quiet]
    python scripts/checks/check_size.py --init      # 第一次導入：把現有超標項目寫成清單

兩條機械規則，加一張只准變短的清單。

規則一：檔案長度。line_scopes 底下的程式檔（副檔名見 suffixes）超過 line_red 行就紅；
超過 line_yellow 行是黃燈，只列出來、不擋。產生檔可豁免，但每一項豁免都要在清單寫理由——
沒寫理由的豁免會紅。

規則二：資料夾寬度。一個資料夾直接放的檔案超過 folder_limit 個，要嘛按意義分成子資料夾，
要嘛放一份 README.md，裡面有 `## 為什麼平鋪` 標題、底下至少一行說明為什麼平鋪才對。

清單（ratchet，預設 scripts/checks/size_ratchet.json）記規則上線時已經超標的項目與當時的數字：
  - 比數字大：紅（清單只准變短）
  - 變小但仍超標：過，提示把數字調低
  - 回到線下、不存在、或資料夾放了平鋪 README：紅，直到從清單移除
不在清單上的超標項目一律紅。

算的是 git 索引裡的檔案（已追蹤＋已 stage），不算未追蹤的檔：工作區常有多個 session 並行，
別的 session 還沒 commit 的檔不該讓這裡紅。

這支檔案原樣複製進專案；專案差異（範圍、副檔名、門檻）寫在清單的 config，不改程式。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG = {
    "line_red": 800,
    "line_yellow": 400,
    "folder_limit": 20,
    # 空字串＝整個 repo。專案導入時改成實際的程式目錄，例如 ["app/", "frontend/src/", "tests/"]
    "line_scopes": [""],
    "suffixes": [".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".css", ".sh",
                 ".go", ".rs", ".swift", ".kt", ".java", ".vue", ".svelte"],
}

RATCHET_NOTE = (
    "檔案大小與資料夾寬度守衛（rivendell skills/quality/dev-size-gate）的清單，由 check_size.py 讀。"
    "files 與 folders 是規則上線時已經超標的項目與當時的數字：只准變小或移除，變大會紅；"
    "修好（回到線下、不存在、或資料夾放了平鋪 README）也會紅，直到從清單移除。"
    "exempt 是不算行數的產生檔，每一項都要寫理由。config 是本專案的範圍與門檻。"
    "改這份檔用文字插入或刪行，不要整檔重新序列化。"
)

FLAT_HEADING = re.compile(r"^##\s*為什麼平鋪\s*$")
ROOT_FOLDER = "."


@dataclass
class Report:
    red: list[str] = field(default_factory=list)
    yellow: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def git_root(start: Path) -> Path:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start,
                         capture_output=True, text=True, check=True).stdout.strip()
    return Path(out)


def repo_files(root: Path) -> list[str]:
    """git 索引裡的檔案（已追蹤＋已 stage），以 posix 路徑回傳，只留實際存在的。"""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "-z"],
        cwd=root, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    seen = sorted({p for p in out.split("\0") if p})
    return [p for p in seen if (root / p).is_file() or (root / p).is_symlink()]


def load_ratchet(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    config = {**DEFAULT_CONFIG, **data.get("config", {})}
    return {
        "config": config,
        "exempt": dict(data.get("exempt", {})),
        "files": dict(data.get("files", {})),
        "folders": dict(data.get("folders", {})),
    }


def exemption(rel: str, exempt: dict[str, str]) -> str | None:
    """涵蓋 `rel` 的豁免鍵（完全相同的檔，或以 `/` 結尾的資料夾前綴）。"""
    for key in exempt:
        if rel == key or (key.endswith("/") and rel.startswith(key)):
            return key
    return None


def line_counts(root: Path, files: list[str], config: dict, exempt: dict[str, str]) -> dict[str, int]:
    scopes = tuple(config["line_scopes"])
    suffixes = frozenset(config["suffixes"])
    counts = {}
    for rel in files:
        path = root / rel
        if (not rel.startswith(scopes) or path.suffix not in suffixes
                or path.is_symlink() or exemption(rel, exempt)):
            continue
        with path.open("rb") as fh:
            counts[rel] = sum(1 for _ in fh)
    return counts


def folder_counts(files: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rel in files:
        parent = rel.rsplit("/", 1)[0] if "/" in rel else ROOT_FOLDER
        counts[parent] = counts.get(parent, 0) + 1
    return counts


def has_flat_readme(root: Path, folder: str) -> bool:
    """`folder` 裡的 README.md 有 `## 為什麼平鋪` 標題、底下有文字。"""
    readme = (root if folder == ROOT_FOLDER else root / folder) / "README.md"
    if not readme.is_file():
        return False
    lines = readme.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if FLAT_HEADING.match(line):
            for body in lines[i + 1:]:
                if body.startswith("#"):
                    return False
                if body.strip():
                    return True
            return False
    return False


def evaluate(root: Path, files: list[str], ratchet: dict) -> Report:
    report = Report()
    config = ratchet["config"]
    line_red, line_yellow, limit = config["line_red"], config["line_yellow"], config["folder_limit"]
    exempt, listed_files, listed_folders = ratchet["exempt"], ratchet["files"], ratchet["folders"]

    for key, reason in sorted(exempt.items()):
        if not str(reason).strip():
            report.red.append(f"  {key}  [豁免沒寫理由]")

    lines = line_counts(root, files, config, exempt)
    for rel, n in sorted(lines.items()):
        if n > line_red:
            if rel not in listed_files:
                report.red.append(f"  {rel}  {n} 行 > {line_red}  [新的過長檔]")
            elif n > listed_files[rel]:
                report.red.append(f"  {rel}  {n} 行，清單記 {listed_files[rel]}  [變長了]")
            elif n < listed_files[rel]:
                report.notes.append(f"  {rel}  {n} 行：清單的數字可以調低到 {n}")
        elif n > line_yellow:
            report.yellow.append(f"  {rel}  {n}")
    for rel in sorted(listed_files):
        if lines.get(rel, 0) <= line_red:
            report.red.append(f"  {rel}  {lines.get(rel, '不存在')}  [已修好或已刪：從清單移除]")

    folders = folder_counts(files)
    for folder, n in sorted(folders.items()):
        flat = has_flat_readme(root, folder)
        if folder in listed_folders:
            if flat:
                report.red.append(f"  {folder}/  已有平鋪 README  [從清單移除]")
            elif n > listed_folders[folder]:
                report.red.append(f"  {folder}/  {n} 個檔，清單記 {listed_folders[folder]}  [變多了]")
            elif limit < n < listed_folders[folder]:
                report.notes.append(f"  {folder}/  {n} 個檔：清單的數字可以調低到 {n}")
        elif n > limit and not flat:
            report.red.append(
                f"  {folder}/  {n} 個檔 > {limit}，沒有含 `## 為什麼平鋪` 的 README  [新的過寬資料夾]")
    for folder in sorted(listed_folders):
        if folders.get(folder, 0) <= limit:
            report.red.append(f"  {folder}/  {folders.get(folder, '不存在')}  [已修好或已刪：從清單移除]")
    return report


def init_ratchet(root: Path, files: list[str], path: Path) -> int:
    """把目前所有超標項目寫成清單。只在清單還不存在時用。"""
    if path.exists():
        print(f"{path} 已存在；清單只准手動變短，不重新產生。", file=sys.stderr)
        return 1
    ratchet = load_ratchet(path)
    config = ratchet["config"]
    lines = line_counts(root, files, config, {})
    over_files = {k: v for k, v in sorted(lines.items()) if v > config["line_red"]}
    over_folders = {k: v for k, v in sorted(folder_counts(files).items())
                    if v > config["folder_limit"] and not has_flat_readme(root, k)}
    data = {"_說明": RATCHET_NOTE, "config": config, "exempt": {},
            "files": over_files, "folders": over_folders}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"寫入 {path}：{len(over_files)} 個檔 > {config['line_red']} 行、"
          f"{len(over_folders)} 個資料夾 > {config['folder_limit']} 個檔。"
          "先檢查 config 的 line_scopes，再把產生檔移到 exempt 並寫理由。")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quiet", action="store_true", help="不列黃燈")
    parser.add_argument("--init", action="store_true", help="第一次導入：產生清單")
    parser.add_argument("--root", type=Path, default=None, help="repo 根目錄（預設：git 根目錄）")
    parser.add_argument("--ratchet", type=Path, default=None,
                        help="清單路徑（預設：<root>/scripts/checks/size_ratchet.json）")
    args = parser.parse_args(argv)

    root = (args.root or git_root(Path.cwd())).resolve()
    ratchet_path = args.ratchet or root / "scripts" / "checks" / "size_ratchet.json"
    files = repo_files(root)
    if args.init:
        return init_ratchet(root, files, ratchet_path)

    ratchet = load_ratchet(ratchet_path)
    config = ratchet["config"]
    report = evaluate(root, files, ratchet)
    if report.yellow and not args.quiet:
        print(f"黃燈 {len(report.yellow)} 個檔超過 {config['line_yellow']} 行（不擋；看看哪些東西屬於一起）：")
        print("\n".join(report.yellow))
    if report.notes:
        print("提示：清單可以收緊：")
        print("\n".join(report.notes))
    if report.red:
        print(
            f"擋下：有檔超過 {config['line_red']} 行、資料夾超過 {config['folder_limit']} 個檔又沒寫平鋪理由，"
            f"或 {ratchet_path.name} 過期：",
            file=sys.stderr,
        )
        print("\n".join(report.red), file=sys.stderr)
        return 1
    print(f"通過：沒有新的檔超過 {config['line_red']} 行、"
          f"沒有新的資料夾超過 {config['folder_limit']} 個檔、清單沒有變長")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
