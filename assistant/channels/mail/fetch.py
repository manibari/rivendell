#!/usr/bin/env python3
"""fetch-mail.py — READ-ONLY inbox reader for mail triage.

Read-only is guaranteed twice: select(readonly=True) and BODY.PEEK — this
script can never change read/unread state, move, or flag anything.

Output: JSON array [{uid, from, subject, date, snippet, self_dispatch}]
    self_dispatch = true when the mail carries X-Rivendell-Dispatch
    (sent by our own send-mail.py — caller should skip these).

Credentials: same ~/.config/rivendell/secrets.env as send-mail.py.
Exit codes: 0 ok (possibly empty array); 1 error; 4 not configured.
"""

import argparse
import email
import email.header
import imaplib
import json
import sys
from datetime import date, datetime
from pathlib import Path

SECRETS = Path.home() / ".config" / "rivendell" / "secrets.env"
SNIPPET_LEN = 300


def load_secrets() -> dict:
    env = {}
    if SECRETS.exists():
        for line in SECRETS.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def decode_header(value: str) -> str:
    if not value:
        return ""
    parts = []
    for chunk, enc in email.header.decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts)


def snippet_of(msg) -> str:
    part = msg
    if msg.is_multipart():
        part = next((p for p in msg.walk()
                     if p.get_content_type() == "text/plain"), None)
        if part is None:
            return ""
    try:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ""
        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    except Exception:
        return ""
    return " ".join(text.split())[:SNIPPET_LEN]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--since", default=date.today().isoformat(),
                   help="YYYY-MM-DD (default: today)")
    p.add_argument("--max", type=int, default=50)
    args = p.parse_args()

    env = load_secrets()
    user = env.get("RIVENDELL_GMAIL_USER", "")
    password = env.get("RIVENDELL_GMAIL_APP_PASSWORD", "")
    if not user or not password:
        print(f"fetch-mail: not configured ({SECRETS})", file=sys.stderr)
        return 4

    since_imap = datetime.strptime(args.since, "%Y-%m-%d").strftime("%d-%b-%Y")

    conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    try:
        conn.login(user, password)
        conn.select("INBOX", readonly=True)
        status, data = conn.uid("search", None, f"(SINCE {since_imap})")
        if status != "OK":
            print(f"fetch-mail: search failed: {status}", file=sys.stderr)
            return 1
        uids = data[0].split()[-args.max:]
        out = []
        for uid in uids:
            status, msg_data = conn.uid("fetch", uid, "(BODY.PEEK[])")
            if status != "OK" or not msg_data or msg_data[0] is None:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            out.append({
                "uid": uid.decode(),
                "from": decode_header(msg.get("From", "")),
                "subject": decode_header(msg.get("Subject", "")),
                "date": msg.get("Date", ""),
                "snippet": snippet_of(msg),
                "self_dispatch": bool(msg.get("X-Rivendell-Dispatch")),
            })
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    finally:
        try:
            conn.logout()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
