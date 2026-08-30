#!/usr/bin/env python3
"""send-mail.py — deterministic outbound email actuator for sk dispatch.

Sends EXACTLY the approved payload — this script is only ever invoked by
dispatch-lib.py execute after the confirmation gate. The model never calls it.

Payload JSON: {"to": [...], "cc": [...], "subject": "...", "body": "..."}

Credentials: ~/.config/rivendell/secrets.env
    RIVENDELL_GMAIL_USER=you@gmail.com
    RIVENDELL_GMAIL_APP_PASSWORD=xxxx

Exit codes: 0 sent; 1 error; 4 not configured.
Every sent mail carries "X-Rivendell-Dispatch: <id>" so mail-triage can
filter our own output (anti-loop).
"""

import argparse
import json
import smtplib
import sys
from email.message import EmailMessage
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--payload", required=True, help="JSON file path, or - for stdin")
    p.add_argument("--dispatch-id", default="manual")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    raw = sys.stdin.read() if args.payload == "-" else Path(args.payload).read_text()
    payload = json.loads(raw)
    to = payload.get("to") or []
    cc = payload.get("cc") or []
    subject = payload.get("subject", "")
    body = payload.get("body", "")
    if not to or not subject:
        print("send-mail: payload needs non-empty 'to' and 'subject'", file=sys.stderr)
        return 1

    env = load_secrets()
    user = env.get("RIVENDELL_GMAIL_USER", "")
    password = env.get("RIVENDELL_GMAIL_APP_PASSWORD", "")
    if not args.dry_run and (not user or not password):
        print(f"send-mail: not configured ({SECRETS} missing RIVENDELL_GMAIL_USER/"
              "RIVENDELL_GMAIL_APP_PASSWORD)", file=sys.stderr)
        return 4

    msg = EmailMessage()
    msg["From"] = user or "unconfigured@localhost"
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg["X-Rivendell-Dispatch"] = args.dispatch_id
    msg.set_content(body)

    if args.dry_run:
        print(msg.as_string())
        return 0

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.starttls()
        s.login(user, password)
        s.send_message(msg)
    print(f"sent: to={','.join(to)} subject={subject!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
