#!/usr/bin/env python3
"""gcal.py — Google Calendar actuator (requests + stdlib, no Google SDK).

    auth            one-time installed-app OAuth (opens a URL, catches the
                    localhost redirect, stores refresh token)
    create-event --payload <file|->   insert an event into the primary calendar

Files under ~/.config/rivendell/ (both chmod 600):
    gcal-credentials.json   {"client_id": "...", "client_secret": "..."}
                            (GCP > OAuth client, type "Desktop app")
    gcal-token.json         written by `auth`, refreshed automatically

Payload JSON: {"summary", "start", "end", "timezone", "attendees": [],
               "location", "description"}
start/end are ISO8601 datetimes; timezone defaults to Asia/Taipei.

Exit codes: 0 ok; 1 error; 4 not configured.
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests

CONF_DIR = Path.home() / ".config" / "rivendell"
CRED_FILE = CONF_DIR / "gcal-credentials.json"
TOKEN_FILE = CONF_DIR / "gcal-token.json"
SCOPE = "https://www.googleapis.com/auth/calendar.events"
REDIRECT_PORT = 8765


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def save_token(token: dict):
    CONF_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(token, indent=1))
    os.chmod(TOKEN_FILE, 0o600)


def cmd_auth(_args) -> int:
    creds = load_json(CRED_FILE)
    if not creds or "client_id" not in creds:
        print(f"gcal: not configured — put GCP OAuth client (Desktop app) into "
              f"{CRED_FILE} as {{\"client_id\", \"client_secret\"}}", file=sys.stderr)
        return 4

    redirect_uri = f"http://localhost:{REDIRECT_PORT}"
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    })
    print("在瀏覽器開啟以下網址完成授權（WSL 可貼到 Windows 瀏覽器）：\n")
    print(auth_url + "\n")
    print(f"等待 localhost:{REDIRECT_PORT} 回呼中…（授權後若瀏覽器打不開回呼頁，"
          "把網址列的 code= 參數貼回來也行）")

    code_holder = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            code_holder["code"] = (qs.get("code") or [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>授權完成，回到終端機。</h2>".encode())

        def log_message(self, *a):
            pass

    server = HTTPServer(("localhost", REDIRECT_PORT), Handler)
    server.timeout = 300
    server.handle_request()
    code = code_holder.get("code", "")
    if not code:
        code = input("code= ").strip()
    if not code:
        print("gcal: no auth code received", file=sys.stderr)
        return 1

    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }, timeout=30)
    if r.status_code != 200:
        print(f"gcal: token exchange failed: {r.status_code} {r.text}", file=sys.stderr)
        return 1
    token = r.json()
    token["obtained_at"] = int(time.time())
    save_token(token)
    print(f"ok: token stored at {TOKEN_FILE}")
    return 0


def access_token() -> str:
    creds = load_json(CRED_FILE)
    token = load_json(TOKEN_FILE)
    if not creds or not token:
        print(f"gcal: not configured (run `gcal.py auth` first; needs {CRED_FILE} "
              f"and {TOKEN_FILE})", file=sys.stderr)
        sys.exit(4)
    expires_at = token.get("obtained_at", 0) + token.get("expires_in", 0) - 60
    if time.time() < expires_at:
        return token["access_token"]
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": token.get("refresh_token", ""),
        "grant_type": "refresh_token",
    }, timeout=30)
    if r.status_code != 200:
        print(f"gcal: token refresh failed: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    fresh = r.json()
    token.update(fresh)
    token["obtained_at"] = int(time.time())
    save_token(token)
    return token["access_token"]


def cmd_create_event(args) -> int:
    raw = sys.stdin.read() if args.payload == "-" else Path(args.payload).read_text()
    p = json.loads(raw)
    if not p.get("summary") or not p.get("start") or not p.get("end"):
        print("gcal: payload needs summary/start/end", file=sys.stderr)
        return 1
    tz = p.get("timezone", "Asia/Taipei")
    body = {
        "summary": p["summary"],
        "start": {"dateTime": p["start"], "timeZone": tz},
        "end": {"dateTime": p["end"], "timeZone": tz},
    }
    if p.get("location"):
        body["location"] = p["location"]
    if p.get("description"):
        body["description"] = p["description"]
    if p.get("attendees"):
        body["attendees"] = [{"email": a} for a in p["attendees"]]

    token = access_token()
    r = requests.post(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        params={"sendUpdates": "all" if p.get("attendees") else "none"},
        headers={"Authorization": f"Bearer {token}"},
        json=body, timeout=30)
    if r.status_code not in (200, 201):
        print(f"gcal: insert failed: {r.status_code} {r.text}", file=sys.stderr)
        return 1
    ev = r.json()
    print(json.dumps({"id": ev.get("id"), "htmlLink": ev.get("htmlLink")},
                     ensure_ascii=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    pc = sub.add_parser("create-event")
    pc.add_argument("--payload", required=True)
    args = p.parse_args()
    return {"auth": cmd_auth, "create-event": cmd_create_event}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
