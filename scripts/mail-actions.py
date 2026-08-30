#!/usr/bin/env python3
"""mail-actions.py — the ONLY write path to the mailbox, and it can only do
two reversible things:

    label --label sk-junk --payload -   apply a Gmail label (fully reversible)
    trash --payload -                   move to \\Trash (Gmail keeps 30 days)

Permanent deletion is deliberately NOT implemented — no purge subcommand,
no deletion-flag handling anywhere in this file, so no caller (model,
script, or human) can permanently destroy mail through it.

Payload JSON: {"uids": ["123", ...]}  (label also reads --label)
Credentials: ~/.config/rivendell/secrets.env (same as send-mail.py).
Exit codes: 0 ok; 1 error; 4 not configured.
"""

import argparse
import imaplib
import json
import sys
from pathlib import Path

SECRETS = Path.home() / ".config" / "rivendell" / "secrets.env"


def load_secrets() -> dict:
    env = {}
    if SECRETS.exists():
        for line in SECRETS.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def connect():
    env = load_secrets()
    user = env.get("RIVENDELL_GMAIL_USER", "")
    password = env.get("RIVENDELL_GMAIL_APP_PASSWORD", "")
    if not user or not password:
        print(f"mail-actions: not configured ({SECRETS})", file=sys.stderr)
        sys.exit(4)
    conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    conn.login(user, password)
    conn.select("INBOX")  # writable session
    return conn


def read_uids(payload_arg: str) -> list:
    raw = sys.stdin.read() if payload_arg == "-" else Path(payload_arg).read_text()
    uids = json.loads(raw).get("uids", [])
    if not uids:
        print("mail-actions: payload has no uids", file=sys.stderr)
        sys.exit(1)
    return [str(u) for u in uids]


def find_trash(conn) -> str:
    """SPECIAL-USE lookup — never hardcode a localized [Gmail]/Trash path."""
    status, boxes = conn.list()
    for line in boxes or []:
        text = line.decode() if isinstance(line, bytes) else line
        if "\\Trash" in text:
            return text.rsplit(' "/" ', 1)[-1].strip('"')
    return "[Gmail]/Trash"


def cmd_label(args) -> int:
    uids = read_uids(args.payload)
    conn = connect()
    try:
        conn.create(args.label)  # idempotent; ALREADYEXISTS is fine
    except imaplib.IMAP4.error:
        pass
    ok = 0
    for uid in uids:
        status, _ = conn.uid("store", uid, "+X-GM-LABELS", f"({args.label})")
        ok += status == "OK"
    conn.logout()
    print(f"labeled {ok}/{len(uids)} with {args.label}")
    return 0 if ok == len(uids) else 1


def cmd_trash(args) -> int:
    uids = read_uids(args.payload)
    conn = connect()
    trash = find_trash(conn)
    ok = 0
    for uid in uids:
        status, _ = conn.uid("copy", uid, trash)  # Gmail semantics: copy to Trash = move
        ok += status == "OK"
    conn.logout()
    print(f"moved {ok}/{len(uids)} to {trash} (recoverable ~30 days)")
    return 0 if ok == len(uids) else 1


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("label")
    pl.add_argument("--label", default="sk-junk")
    pl.add_argument("--payload", required=True)
    pt = sub.add_parser("trash")
    pt.add_argument("--payload", required=True)
    args = p.parse_args()
    return {"label": cmd_label, "trash": cmd_trash}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
