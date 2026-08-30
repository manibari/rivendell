#!/usr/bin/env python3
"""dispatch-lib.py — state machine + validation + the ONLY execution gate
for `sk dispatch`.

Layout: dispatch/<id>/{request.txt, proposal.json, proposal.md,
decisions.json, results/}

Contract for new event channels: call
    sk dispatch new --source <channel> --context <event.json> [--auto-internal] "描述"
Everything downstream (confirmation levels, decisions.json, actuators) is
shared — never fork the confirmation machinery per channel.

Enforcement is structural, by task TYPE (the model's `risk` label has no
execution power):
    email, calendar_event  -> per-item, confirm must be typed-yes
    mail_trash             -> batch list shown, confirm must be batch-yes
    crm                    -> simple approve (handoff; CRM side owns detail)
    todo, mail_label       -> simple/auto
    agent_task             -> simple/auto (readonly profile) — run by bin/sk

Exit codes: 0 ok; 1 error; 3 validation failed; 5 caller must run sk_exec
(stdout carries the instruction JSON; afterwards call `mark`).
"""

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

REPO_DIR = Path(os.environ.get("SK_REPO_DIR", Path(__file__).resolve().parent.parent))
DISPATCH_ROOT = Path(os.environ.get("DISPATCH_ROOT", REPO_DIR / "dispatch"))
SCRIPTS = REPO_DIR / "scripts"

TYPES = ("todo", "agent_task", "email", "calendar_event",
         "mail_label", "mail_trash", "crm")
RISKS = ("internal", "draft", "external")
MAX_TASKS = 8

# type -> confirm level required for execution
REQUIRED_CONFIRM = {
    "email": {"typed-yes"},
    "calendar_event": {"typed-yes"},
    "mail_trash": {"batch-yes"},
    "crm": {"simple"},
    "todo": {"simple", "auto"},
    "mail_label": {"simple", "auto"},
    "agent_task": {"simple", "auto"},
}

PAYLOAD_REQUIRED = {
    "todo": ["text"],
    "agent_task": ["prompt", "tools_profile"],
    "email": ["to", "subject", "body"],
    "calendar_event": ["summary", "start", "end"],
    "mail_label": ["label", "uids"],
    "mail_trash": ["uids", "messages"],
    "crm": ["brief"],
}

TERMINAL = {"executed", "rejected"}


def die(msg, code=1):
    print(f"dispatch: {msg}", file=sys.stderr)
    sys.exit(code)


def payload_hash(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def ddir(dispatch_id: str) -> Path:
    d = DISPATCH_ROOT / dispatch_id
    if not d.is_dir():
        die(f"dispatch {dispatch_id} not found under {DISPATCH_ROOT}")
    return d


def load(dispatch_id: str):
    d = ddir(dispatch_id)
    proposal = json.loads((d / "proposal.json").read_text())
    dec_path = d / "decisions.json"
    decisions = json.loads(dec_path.read_text()) if dec_path.exists() else None
    return d, proposal, decisions


def write_decisions(d: Path, decisions: dict):
    lock = d / ".lock"
    with lock.open("w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        tmp = d / ".decisions.tmp"
        tmp.write_text(json.dumps(decisions, ensure_ascii=False, indent=1))
        os.replace(tmp, d / "decisions.json")


def notify(text: str):
    try:
        subprocess.run(["bash", str(SCRIPTS / "tg-notify.sh"), text],
                       timeout=15, check=False)
    except Exception:
        pass


def persona_name() -> str:
    """Active persona display name from data/persona.conf (flat dotted keys)."""
    conf = REPO_DIR / "data" / "persona.conf"
    try:
        text = conf.read_text()
        active = next(l.split("=", 1)[1].strip() for l in text.splitlines()
                      if l.replace(" ", "").startswith("active="))
        return next(l.split("=", 1)[1].strip() for l in text.splitlines()
                    if l.replace(" ", "").startswith(f"{active}.display_name="))
    except (OSError, StopIteration):
        return "助理"


# ── new-id ──────────────────────────────────────────────────────────────

def cmd_new_id(_a) -> int:
    DISPATCH_ROOT.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    n = 1 + sum(1 for p in DISPATCH_ROOT.iterdir()
                if p.is_dir() and p.name.startswith(today))
    print(f"{today}-{n:03d}")
    return 0


# ── validate ────────────────────────────────────────────────────────────

def strip_fence(raw: str) -> str:
    m = re.search(r"```(?:json)?\s*\n(.*?)```", raw, re.S)
    text = m.group(1) if m else raw
    # last resort: outermost braces
    if not text.strip().startswith("{"):
        i, j = text.find("{"), text.rfind("}")
        if i >= 0 and j > i:
            text = text[i:j + 1]
    return text.strip()


def validate_proposal(obj) -> list:
    errs = []
    for field in ("dispatch_id", "request", "summary", "tasks"):
        if field not in obj:
            errs.append(f"missing top-level '{field}'")
    tasks = obj.get("tasks", [])
    if len(tasks) > MAX_TASKS:
        errs.append(f"{len(tasks)} tasks > MAX_TASKS={MAX_TASKS} (extraction ran wild)")
    seen = set()
    for t in tasks:
        tid = t.get("id", "?")
        if tid in seen:
            errs.append(f"duplicate task id {tid}")
        seen.add(tid)
        if t.get("type") not in TYPES:
            errs.append(f"{tid}: bad type '{t.get('type')}'")
            continue
        if t.get("risk") not in RISKS:
            errs.append(f"{tid}: bad risk '{t.get('risk')}'")
        payload = t.get("payload")
        if not isinstance(payload, dict):
            errs.append(f"{tid}: payload must be an object")
            continue
        for req in PAYLOAD_REQUIRED[t["type"]]:
            if not payload.get(req):
                errs.append(f"{tid}: payload missing '{req}'")
        if t["type"] in ("email", "calendar_event", "mail_trash") \
                and t.get("risk") != "external":
            t["risk"] = "external"  # normalize: these are external no matter what
    for c in obj.get("conflicts", []):
        for req in ("index", "fact_id", "entity_type", "entity_slug",
                    "old_fact", "new_direction", "replacement_fact"):
            if req not in c:
                errs.append(f"conflict: missing '{req}'")
    return errs


def cmd_validate(a) -> int:
    raw = sys.stdin.read()
    try:
        obj = json.loads(strip_fence(raw))
    except json.JSONDecodeError as e:
        print(f"invalid JSON: {e}", file=sys.stderr)
        return 3
    errs = validate_proposal(obj)
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 3
    if a.out:
        Path(a.out).write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    print("ok")
    return 0


# ── init-decisions / render ─────────────────────────────────────────────

def cmd_init_decisions(a) -> int:
    d, proposal, _ = load(a.id)
    decisions = {"schema": 1, "tasks": {}, "conflicts": {}}
    blocked = {t.get("blocked_by_conflict") for t in proposal["tasks"]}
    for t in proposal["tasks"]:
        decisions["tasks"][t["id"]] = {
            "status": "pending", "confirm": None, "payload_sha256": None,
            "decided_at": None, "executed_at": None, "result": None,
            "error": None, "blocked_reason": None,
        }
    for c in proposal.get("conflicts", []):
        decisions["conflicts"][str(c["index"])] = {
            "resolution": "pending", "resolved_at": None, "new_fact_id": None}
    write_decisions(d, decisions)
    (d / "results").mkdir(exist_ok=True)
    print("ok")
    return 0


CONFIRM_LABEL = {
    "email": "逐件確認（typed-yes）", "calendar_event": "逐件確認（typed-yes）",
    "mail_trash": "批次確認（清單 + yes）", "crm": "simple approve（交接 CRM）",
    "todo": "自動", "mail_label": "自動", "agent_task": "自動/simple",
}


def cmd_render(a) -> int:
    d, p, dec = load(a.id)
    L = [f"# Dispatch {p['dispatch_id']}", "",
         f"**指令/事件**：{p['request']}", "",
         f"**理解**：{p.get('summary', '')}", ""]
    src = p.get("source", {})
    if isinstance(src, dict) and src.get("channel") not in (None, "user"):
        L += [f"**來源**：{src.get('channel')} — "
              f"{json.dumps(src.get('context', {}), ensure_ascii=False)}", ""]
    if p.get("conflicts"):
        L += ["## ⚠️ 方向衝突（需先 resolve）", ""]
        for c in p["conflicts"]:
            L += [f"- **#{c['index']}** [{c['entity_type']}/{c['entity_slug']} "
                  f"{c['fact_id']}] 舊：{c['old_fact']}",
                  f"  新方向：{c['new_direction']}",
                  f"  說明：{c.get('explanation', '')}",
                  f"  → keep-new 將寫入：{c['replacement_fact']}", ""]
    if p.get("clarifications"):
        L += ["## ❓ 待釐清（sk dispatch answer）", ""]
        L += [f"- {q}" for q in p["clarifications"]] + [""]
    L += ["## 任務", ""]
    for t in p["tasks"]:
        st = (dec or {}).get("tasks", {}).get(t["id"], {}).get("status", "pending")
        L += [f"### {t['id']} — {t['title']}  `{t['type']}` `{t['risk']}` `{st}`",
              f"- 依據：{t.get('rationale', '')}",
              f"- 確認等級：{CONFIRM_LABEL[t['type']]}"]
        if t.get("blocked_by_conflict"):
            L += [f"- ⛔ blocked by conflict #{t['blocked_by_conflict']}"]
        if t["type"] in ("email", "calendar_event", "mail_trash", "crm"):
            L += ["", "```json",
                  json.dumps(t["payload"], ensure_ascii=False, indent=1), "```"]
        L += [""]
    (d / "proposal.md").write_text("\n".join(L))
    print(str(d / "proposal.md"))
    return 0


# ── status / list ───────────────────────────────────────────────────────

def derive_status(p, dec) -> str:
    if dec is None:
        return "new"
    tstat = [v["status"] for v in dec["tasks"].values()]
    conflicts_pending = any(v["resolution"] == "pending"
                            for v in dec.get("conflicts", {}).values())
    if p.get("clarifications") or conflicts_pending:
        return "needs-input"
    if any(s == "pending" for s in tstat):
        return "awaiting"
    if any(s == "approved" for s in tstat):
        return "in-progress"
    if any(s == "failed" for s in tstat):
        return "failed"
    return "done"


def cmd_status(a) -> int:
    _, p, dec = load(a.id)
    print(derive_status(p, dec))
    return 0


def cmd_list(_a) -> int:
    if not DISPATCH_ROOT.is_dir():
        return 0
    for d in sorted(DISPATCH_ROOT.iterdir()):
        if not d.is_dir() or d.name == "archive":
            continue
        try:
            p = json.loads((d / "proposal.json").read_text())
            dec_p = d / "decisions.json"
            dec = json.loads(dec_p.read_text()) if dec_p.exists() else None
        except (OSError, json.JSONDecodeError):
            continue
        print(f"{d.name} | {derive_status(p, dec):>11} | {p.get('summary', '')[:60]}")
    return 0


# ── decide ──────────────────────────────────────────────────────────────

def cmd_decide(a) -> int:
    d, p, dec = load(a.id)
    if dec is None:
        die("decisions.json missing — run init-decisions")
    task = next((t for t in p["tasks"] if t["id"] == a.task), None)
    if task is None:
        die(f"task {a.task} not in proposal")
    rec = dec["tasks"][a.task]
    if a.action == "approve":
        # "approved" allowed again: re-approve after an interrupted execute
        # refreshes the hash under an explicit user act
        if rec["status"] not in ("pending", "failed", "approved"):
            die(f"task {a.task} is {rec['status']}, cannot approve")
        if task.get("blocked_by_conflict"):
            cidx = str(task["blocked_by_conflict"])
            if dec["conflicts"].get(cidx, {}).get("resolution") == "pending":
                die(f"task {a.task} blocked by unresolved conflict #{cidx} — "
                    "run resolve first")
        need = REQUIRED_CONFIRM[task["type"]]
        if a.confirm not in need:
            die(f"type {task['type']} requires confirm in {sorted(need)}, "
                f"got '{a.confirm}'")
        rec.update(status="approved", confirm=a.confirm,
                   payload_sha256=payload_hash(task["payload"]),
                   decided_at=datetime.now().isoformat(timespec="seconds"),
                   error=None)
    elif a.action == "reject":
        if rec["status"] in TERMINAL:
            die(f"task {a.task} already {rec['status']}")
        rec.update(status="rejected",
                   decided_at=datetime.now().isoformat(timespec="seconds"))
    write_decisions(d, dec)
    print(f"{a.task}: {rec['status']}")
    return 0


# ── junk-guard ──────────────────────────────────────────────────────────

EMAIL_RE = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)", re.I)
GENERIC_DOMAINS = {"gmail.com", "outlook.com", "hotmail.com", "yahoo.com",
                   "googlemail.com", "icloud.com", "msn.com", "qq.com"}


def kg_known_keys(kg_dump: str):
    addrs, domains, slugs = set(), set(), set()
    for m in EMAIL_RE.finditer(kg_dump):
        addrs.add(m.group(0).lower())
        domains.add(m.group(1).lower())
    for line in kg_dump.splitlines():
        parts = line.split("|", 1)
        if parts and "/" in parts[0]:
            slug = parts[0].split("/", 1)[1].strip().lower().replace("-", "")
            if len(slug) >= 4:
                slugs.add(slug)
    return addrs, domains, slugs


def guard_reason(sender: str, addrs, domains, slugs):
    m = EMAIL_RE.search(sender)
    if not m:
        return None
    addr, domain = m.group(0).lower(), m.group(1).lower()
    if addr in addrs:
        return f"address {addr} appears in knowledge base"
    if domain in domains:
        return f"domain {domain} appears in knowledge base"
    if domain not in GENERIC_DOMAINS:
        stem = domain.split(".", 1)[0].lower().replace("-", "")
        for slug in slugs:
            if len(stem) >= 4 and (stem in slug or slug in stem):
                return f"domain {domain} matches known entity slug"
    return None


def cmd_junk_guard(a) -> int:
    """Candidates on stdin; kg dump from a file (stdin is taken)."""
    if a.kg_dump == "-":
        die("junk-guard: --kg-dump must be a file (stdin carries the candidates)")
    candidates = json.loads(sys.stdin.read() or "[]")
    kg_dump = Path(a.kg_dump).read_text() if Path(a.kg_dump).exists() else ""
    addrs, domains, slugs = kg_known_keys(kg_dump)
    kept, excluded = [], []
    for c in candidates:
        reason = guard_reason(c.get("from", ""), addrs, domains, slugs)
        if reason:
            excluded.append({**c, "excluded_reason": reason})
        else:
            kept.append(c)
    print(json.dumps({"candidates": kept, "excluded": excluded},
                     ensure_ascii=False, indent=1))
    return 0


# ── execute / mark ──────────────────────────────────────────────────────

def run_actuator(cmd: list, payload: dict, timeout=120):
    return subprocess.run(cmd, input=json.dumps(payload, ensure_ascii=False),
                          capture_output=True, text=True, timeout=timeout)


def cmd_execute(a) -> int:
    d, p, dec = load(a.id)
    if dec is None:
        die("decisions.json missing")
    task = next((t for t in p["tasks"] if t["id"] == a.task), None)
    if task is None:
        die(f"task {a.task} not in proposal")
    rec = dec["tasks"][a.task]

    # gate — second line of defense, independent of the CLI
    if rec["status"] != "approved":
        die(f"task {a.task} is {rec['status']}, not approved — refusing")
    if rec["confirm"] not in REQUIRED_CONFIRM[task["type"]]:
        die(f"confirm '{rec['confirm']}' insufficient for type {task['type']} — refusing")
    if rec["payload_sha256"] != payload_hash(task["payload"]):
        die(f"payload hash mismatch for {a.task} — proposal changed after approve, refusing")

    ttype = task["type"]
    payload = task["payload"]
    results = d / "results"
    results.mkdir(exist_ok=True)
    result_file = results / f"{a.task}.json"
    ok, output, error = False, "", None

    if ttype == "todo":
        todos = DISPATCH_ROOT / "todos.md"
        due = f"（{payload['due']}）" if payload.get("due") else ""
        with todos.open("a", encoding="utf-8") as f:
            f.write(f"- [ ] {payload['text']}{due} <!-- {p['dispatch_id']}/{a.task} -->\n")
        ok, output = True, "appended to dispatch/todos.md"

    elif ttype == "email":
        if task.get("risk") == "draft":
            draft = results / f"{a.task}-draft.eml"
            r = run_actuator(["python3", str(SCRIPTS / "send-mail.py"),
                              "--payload", "-", "--dry-run"], payload)
            draft.write_text(r.stdout)
            ok, output = r.returncode == 0, f"draft written: {draft.name} (NOT sent)"
        else:
            r = run_actuator(["python3", str(SCRIPTS / "send-mail.py"),
                              "--payload", "-", "--dispatch-id", p["dispatch_id"]],
                             payload)
            ok, output, error = r.returncode == 0, r.stdout.strip(), \
                (r.stderr.strip() or None if r.returncode else None)

    elif ttype == "calendar_event":
        r = run_actuator(["python3", str(SCRIPTS / "gcal.py"), "create-event",
                          "--payload", "-"], payload)
        ok, output, error = r.returncode == 0, r.stdout.strip(), \
            (r.stderr.strip() or None if r.returncode else None)

    elif ttype in ("mail_label", "mail_trash"):
        if ttype == "mail_trash":
            # depth: re-run junk-guard against the CURRENT kg dump
            kg = subprocess.run(["python3", str(SCRIPTS / "kg.py"),
                                 "dump", "--active-only"],
                                capture_output=True, text=True).stdout
            addrs, domains, slugs = kg_known_keys(kg)
            msgs = payload.get("messages", [])
            keep = [m for m in msgs
                    if not guard_reason(m.get("from", ""), addrs, domains, slugs)]
            dropped = len(msgs) - len(keep)
            payload = {**payload,
                       "uids": [m["uid"] for m in keep], "messages": keep}
            if dropped:
                output += f"junk-guard dropped {dropped} known sender(s); "
            if not payload["uids"]:
                ok, output = True, output + "nothing left to trash"
        if ttype == "mail_label" or payload.get("uids"):
            sub = ["label", "--label", payload.get("label", "sk-junk")] \
                if ttype == "mail_label" else ["trash"]
            r = run_actuator(["python3", str(SCRIPTS / "mail-actions.py"),
                              *sub, "--payload", "-"], payload)
            ok = r.returncode == 0
            output += r.stdout.strip()
            error = r.stderr.strip() or None if r.returncode else None

    elif ttype in ("agent_task", "crm"):
        # sk_exec lives in bash — hand the instruction to bin/sk (exit 5),
        # which runs it and reports back via `mark`.
        print(json.dumps({"action": "sk_exec", "dispatch_id": p["dispatch_id"],
                          "task": a.task, "type": ttype, "payload": payload},
                         ensure_ascii=False))
        return 5

    result_file.write_text(json.dumps(
        {"ok": ok, "output": output, "error": error,
         "at": datetime.now().isoformat(timespec="seconds")},
        ensure_ascii=False, indent=1))
    rec.update(status="executed" if ok else "failed",
               executed_at=datetime.now().isoformat(timespec="seconds"),
               result=f"results/{result_file.name}", error=error)
    write_decisions(d, dec)
    notify(f"{persona_name()}：「{task['title']}」"
           f"{'辦好了 ✅ ' + output if ok else '沒成 ❌ ' + (error or '')}"
           f"（{p['dispatch_id']}/{a.task}）")
    print(output if ok else f"FAILED: {error}")
    return 0 if ok else 1


def cmd_mark(a) -> int:
    d, p, dec = load(a.id)
    rec = dec["tasks"][a.task]
    rec.update(status=a.status,
               executed_at=datetime.now().isoformat(timespec="seconds"),
               result=a.result, error=a.error or None)
    write_decisions(d, dec)
    title = next((t["title"] for t in p["tasks"] if t["id"] == a.task), a.task)
    notify(f"{persona_name()}：「{title}」"
           f"{'辦好了 ✅' if a.status == 'executed' else '沒成 ❌ ' + (a.error or '')}"
           f"（{p['dispatch_id']}/{a.task}）")
    print("ok")
    return 0


# ── resolve-conflict ────────────────────────────────────────────────────

def cmd_resolve_conflict(a) -> int:
    d, p, dec = load(a.id)
    conflict = next((c for c in p.get("conflicts", [])
                     if str(c["index"]) == str(a.conflict)), None)
    if conflict is None:
        die(f"conflict #{a.conflict} not in proposal")
    crec = dec["conflicts"][str(a.conflict)]
    if crec["resolution"] != "pending":
        die(f"conflict #{a.conflict} already {crec['resolution']}")
    if a.keep == "new":
        r = subprocess.run(
            ["python3", str(SCRIPTS / "kg.py"), "add",
             conflict["entity_type"], conflict["entity_slug"],
             "--fact", conflict["replacement_fact"],
             "--category", conflict.get("category", "decision"),
             "--supersedes", conflict["fact_id"]],
            capture_output=True, text=True)
        if r.returncode != 0:
            die(f"kg.py add failed: {r.stderr.strip()}")
        crec["new_fact_id"] = r.stdout.strip()
        crec["resolution"] = "keep-new"
    else:
        crec["resolution"] = "keep-old"
    crec["resolved_at"] = datetime.now().isoformat(timespec="seconds")
    # unblock dependent tasks
    for t in p["tasks"]:
        if str(t.get("blocked_by_conflict")) == str(a.conflict):
            t["blocked_by_conflict"] = None
    (d / "proposal.json").write_text(json.dumps(p, ensure_ascii=False, indent=1))
    write_decisions(d, dec)
    print(json.dumps({"resolution": crec["resolution"],
                      "new_fact_id": crec["new_fact_id"],
                      "entity_type": conflict["entity_type"],
                      "entity_slug": conflict["entity_slug"]}, ensure_ascii=False))
    return 0


# ── main ────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("new-id")
    v = sub.add_parser("validate")
    v.add_argument("--out", help="write normalized proposal.json here on success")
    for name in ("init-decisions", "render", "status"):
        s = sub.add_parser(name)
        s.add_argument("id")
    sub.add_parser("list")
    dcd = sub.add_parser("decide")
    dcd.add_argument("id")
    dcd.add_argument("--task", required=True)
    dcd.add_argument("--action", required=True, choices=["approve", "reject"])
    dcd.add_argument("--confirm", default="simple",
                     choices=["typed-yes", "batch-yes", "simple", "auto"])
    ex = sub.add_parser("execute")
    ex.add_argument("id")
    ex.add_argument("--task", required=True)
    mk = sub.add_parser("mark")
    mk.add_argument("id")
    mk.add_argument("--task", required=True)
    mk.add_argument("--status", required=True, choices=["executed", "failed"])
    mk.add_argument("--result")
    mk.add_argument("--error")
    jg = sub.add_parser("junk-guard")
    jg.add_argument("--kg-dump", required=True)
    rc = sub.add_parser("resolve-conflict")
    rc.add_argument("id")
    rc.add_argument("--conflict", required=True)
    rc.add_argument("--keep", required=True, choices=["new", "old"])
    a = p.parse_args()
    return {"new-id": cmd_new_id, "validate": cmd_validate,
            "init-decisions": cmd_init_decisions, "render": cmd_render,
            "status": cmd_status, "list": cmd_list, "decide": cmd_decide,
            "execute": cmd_execute, "mark": cmd_mark,
            "junk-guard": cmd_junk_guard,
            "resolve-conflict": cmd_resolve_conflict}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
