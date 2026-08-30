#!/usr/bin/env python3
"""kg.py — knowledge graph 唯一寫入 API（skills/meta/knowledge-graph 的資料層）。

儲存根目錄由 KG_ROOT 覆寫（預設 ~/.claude/knowledge），結構：
    <KG_ROOT>/{people,companies,projects}/<slug>/facts.jsonl + summary.md

headless agent 與互動 session 都只准經此腳本寫入 —— append-only、id 遞增、
supersede 的單行修改、summary 落地與結構驗證全部封裝在這裡。

Subcommands:
    init                                  建目錄 + git init（冪等）
    add <type> <slug> --fact T --category C [--supersedes ID] [--source S]
    dump [--active-only]                  全庫 facts 緊湊輸出（餵 prompt 用）
    summary <type> <slug>                 stdin 讀 markdown body，寫 summary.md
    verify                                全庫結構檢查，exit 0/1

Exit codes: 0 成功；1 錯誤；3 重複 fact（未寫入）。
"""

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from datetime import date
from pathlib import Path

TYPES = ("people", "companies", "projects")
CATEGORIES = ("relationship", "milestone", "status", "preference", "context", "decision")
SOURCES = ("conversation", "manual", "inference")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MAX_FACT_LEN = 300


def kg_root() -> Path:
    return Path(os.environ.get("KG_ROOT", str(Path.home() / ".claude" / "knowledge")))


def die(msg: str, code: int = 1):
    print(f"kg.py: {msg}", file=sys.stderr)
    sys.exit(code)


def normalize(text: str) -> str:
    """去重比對用：NFKC、lowercase、去標點、壓空白。"""
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def read_facts(path: Path) -> list:
    """讀 facts.jsonl → [(line_no, raw_line, obj_or_None)]。"""
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            stripped = line.rstrip("\n")
            if not stripped.strip():
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                obj = None
            rows.append((i, stripped, obj))
    return rows


def _git_identity() -> tuple:
    """從環境（cwd 的 local/global config）推導 identity；KG_ROOT 是獨立 repo 讀不到。"""

    def cfg(key, fallback):
        r = subprocess.run(["git", "config", "--get", key], capture_output=True, text=True)
        return r.stdout.strip() or fallback

    return cfg("user.name", "knowledge-graph"), cfg("user.email", "kg@localhost")


def cmd_init(_args) -> int:
    root = kg_root()
    for t in TYPES:
        (root / t).mkdir(parents=True, exist_ok=True)
    if not (root / ".git").exists():
        readme = root / "README.md"
        if not readme.exists():
            readme.write_text(
                "# Knowledge Graph\n\n"
                "Entity memory for the rivendell personal-assistant stack.\n"
                "Written ONLY via `rivendell/scripts/kg.py` (add/summary). Do not hand-edit facts.jsonl.\n"
                "Schema: skills/meta/knowledge-graph/SKILL.md in the rivendell repo.\n",
                encoding="utf-8",
            )
        name, email = _git_identity()
        subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", name], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", email], check=True)
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "init knowledge graph"],
            check=True,
        )
    print(f"ok: {root}")
    return 0


def cmd_add(args) -> int:
    if args.type not in TYPES:
        die(f"type must be one of {TYPES}")
    if not SLUG_RE.match(args.slug):
        die("slug must match ^[a-z0-9][a-z0-9-]*$")
    if args.category not in CATEGORIES:
        die(f"category must be one of {CATEGORIES}")
    if args.source not in SOURCES:
        die(f"source must be one of {SOURCES}")
    fact = args.fact.strip()
    if not fact:
        die("fact is empty")
    if len(fact) > MAX_FACT_LEN:
        die(f"fact exceeds {MAX_FACT_LEN} chars ({len(fact)})")
    if "\n" in fact:
        die("fact must be a single line")

    entity_dir = kg_root() / args.type / args.slug
    entity_dir.mkdir(parents=True, exist_ok=True)
    facts_path = entity_dir / "facts.jsonl"
    lock_path = entity_dir / ".lock"

    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        rows = read_facts(facts_path)
        for _, raw, obj in rows:
            if obj is None:
                die(f"corrupt line in {facts_path}; run verify / fix before adding")

        # id 由腳本指派：掃既有 max NNN
        max_n = 0
        prefix = f"{args.slug}-"
        for _, _, obj in rows:
            fid = obj.get("id", "")
            if fid.startswith(prefix):
                try:
                    max_n = max(max_n, int(fid[len(prefix):]))
                except ValueError:
                    pass

        # 去重 backstop：正規化全文比對 active facts
        norm_new = normalize(fact)
        for _, _, obj in rows:
            if obj.get("status") == "active" and normalize(obj.get("fact", "")) == norm_new:
                print(f"DUPLICATE of {obj['id']}")
                return 3

        # supersede：驗證目標，外科手術式改該行 status
        if args.supersedes:
            target = next((o for _, _, o in rows if o.get("id") == args.supersedes), None)
            if target is None:
                die(f"supersedes target {args.supersedes} not found in {args.slug}")
            if target.get("status") != "active":
                die(f"supersedes target {args.supersedes} is not active")
            new_lines = []
            for _, raw, obj in rows:
                if obj.get("id") == args.supersedes:
                    obj["status"] = "superseded"
                    new_lines.append(json.dumps(obj, ensure_ascii=False))
                else:
                    new_lines.append(raw)  # 其他行 byte-level 原樣保留
            fd, tmp = tempfile.mkstemp(dir=str(entity_dir), prefix=".facts-")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")
            os.replace(tmp, facts_path)

        new_id = f"{args.slug}-{max_n + 1:03d}"
        entry = {
            "id": new_id,
            "fact": fact,
            "category": args.category,
            "ts": date.today().isoformat(),
            "source": args.source,
            "status": "active",
        }
        if args.supersedes:
            entry["supersedes"] = args.supersedes
        with facts_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(new_id)
    return 0


def iter_entities():
    root = kg_root()
    for t in TYPES:
        tdir = root / t
        if not tdir.is_dir():
            continue
        for entity_dir in sorted(tdir.iterdir()):
            if entity_dir.is_dir() and (entity_dir / "facts.jsonl").exists():
                yield t, entity_dir.name, entity_dir / "facts.jsonl"


def cmd_dump(args) -> int:
    for t, slug, path in iter_entities():
        for _, _, obj in read_facts(path):
            if obj is None:
                continue
            if args.active_only and obj.get("status") != "active":
                continue
            print(f"{t}/{slug} | {obj.get('id')} | {obj.get('category')} | "
                  f"{obj.get('ts')} | {obj.get('fact')}")
    return 0


def cmd_summary(args) -> int:
    if args.type not in TYPES:
        die(f"type must be one of {TYPES}")
    if not SLUG_RE.match(args.slug):
        die("slug must match ^[a-z0-9][a-z0-9-]*$")
    entity_dir = kg_root() / args.type / args.slug
    if not entity_dir.is_dir():
        die(f"entity {args.type}/{args.slug} does not exist (add a fact first)")
    body = sys.stdin.read().strip()
    lines = [ln for ln in body.splitlines() if ln.strip()]
    # 去掉模型自帶的 last-updated 行，統一由腳本補
    lines = [ln for ln in lines if not re.match(r"_?last updated", ln.strip(), re.I)]
    if not 3 <= len(lines) <= 10:
        die(f"summary must be 3-10 non-empty lines (got {len(lines)})")
    content = "\n".join(lines) + f"\n\n_Last updated: {date.today().isoformat()}_\n"
    fd, tmp = tempfile.mkstemp(dir=str(entity_dir), prefix=".summary-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, entity_dir / "summary.md")
    print(f"ok: {args.type}/{args.slug}/summary.md")
    return 0


def cmd_verify(_args) -> int:
    errors = []
    for t, slug, path in iter_entities():
        rows = read_facts(path)
        ids = {}
        by_id = {}
        for line_no, _, obj in rows:
            where = f"{t}/{slug}:{line_no}"
            if obj is None:
                errors.append(f"{where}: invalid JSON")
                continue
            for field in ("id", "fact", "category", "ts", "source", "status"):
                if field not in obj:
                    errors.append(f"{where}: missing field '{field}'")
            fid = obj.get("id", "")
            if not fid.startswith(f"{slug}-"):
                errors.append(f"{where}: id '{fid}' prefix != slug '{slug}'")
            if fid in ids:
                errors.append(f"{where}: duplicate id '{fid}' (also line {ids[fid]})")
            ids[fid] = line_no
            by_id[fid] = obj
            if obj.get("category") not in CATEGORIES:
                errors.append(f"{where}: bad category '{obj.get('category')}'")
            if obj.get("source") not in SOURCES:
                errors.append(f"{where}: bad source '{obj.get('source')}'")
            if obj.get("status") not in ("active", "superseded"):
                errors.append(f"{where}: bad status '{obj.get('status')}'")
        for fid, obj in by_id.items():
            sup = obj.get("supersedes")
            if sup:
                if sup not in by_id:
                    errors.append(f"{t}/{slug}: {fid} supersedes missing id '{sup}'")
                elif by_id[sup].get("status") != "superseded":
                    errors.append(f"{t}/{slug}: {fid} supersedes '{sup}' but its status is "
                                  f"'{by_id[sup].get('status')}'")
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        print(f"FAIL: {len(errors)} error(s)")
        return 1
    print("ok")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    pa = sub.add_parser("add")
    pa.add_argument("type")
    pa.add_argument("slug")
    pa.add_argument("--fact", required=True)
    pa.add_argument("--category", required=True)
    pa.add_argument("--supersedes")
    pa.add_argument("--source", default="conversation")

    pd = sub.add_parser("dump")
    pd.add_argument("--active-only", action="store_true")

    ps = sub.add_parser("summary")
    ps.add_argument("type")
    ps.add_argument("slug")

    sub.add_parser("verify")

    args = p.parse_args()
    return {"init": cmd_init, "add": cmd_add, "dump": cmd_dump,
            "summary": cmd_summary, "verify": cmd_verify}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
