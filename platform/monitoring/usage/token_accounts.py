"""Which account was logged in when — so token usage can be split by account.

Claude Code usage rows carry no account, and only the CURRENT login is visible
on disk. So the API samples the current login every OBSERVE_SEC and keeps the
intervals; a usage row is attributed to the account whose interval covers its
timestamp. A row outside every interval stays unattributed (未判讀) — it is
never assigned to whoever happens to be logged in now.

Codex rollouts already name their account id per session; the log here only
supplies a readable label (email) for an id.

Only identity fields are read (account id, email). Tokens are never read into
a variable that is stored, logged or returned.
"""

from __future__ import annotations

import base64
import json
import sqlite3
import threading
import time
from pathlib import Path

from lib.tokens import _history_db_path
from lib.tokens_codex import CODEX_HOME

CLAUDE_CONFIG = Path.home() / ".claude.json"
CODEX_AUTH = CODEX_HOME / "auth.json"
OBSERVE_SEC = 30
# A row this long after the last sighting still belongs to that account; beyond
# it nobody was watching (API down), so the row is left unattributed.
GRACE_SEC = OBSERVE_SEC * 2

_started = False
_start_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    path = _history_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS token_account_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            account_id TEXT NOT NULL,
            label TEXT NOT NULL,
            observed_from REAL NOT NULL,
            observed_to REAL NOT NULL
        )
    """)
    return conn


def _current_claude() -> tuple[str, str] | None:
    try:
        account = json.loads(CLAUDE_CONFIG.read_text()).get("oauthAccount") or {}
    except (OSError, json.JSONDecodeError):
        return None
    account_id = account.get("accountUuid")
    if not account_id:
        return None
    return account_id, account.get("emailAddress") or account_id[:8]


def _current_codex() -> tuple[str, str] | None:
    try:
        tokens = json.loads(CODEX_AUTH.read_text()).get("tokens") or {}
    except (OSError, json.JSONDecodeError):
        return None
    account_id = tokens.get("account_id")
    if not account_id:
        return None
    label = account_id[:8]
    parts = str(tokens.get("id_token") or "").split(".")
    if len(parts) == 3:
        try:
            body = parts[1] + "=" * (-len(parts[1]) % 4)
            label = json.loads(base64.urlsafe_b64decode(body)).get("email") or label
        except (ValueError, json.JSONDecodeError):
            pass
    return account_id, label


def observe(now: float | None = None) -> None:
    """Record who is logged in right now; extend the interval or open a new one."""
    now = time.time() if now is None else now
    seen = {"claude": _current_claude(), "codex": _current_codex()}
    with _connect() as conn:
        for source, current in seen.items():
            if current is None:
                continue
            account_id, label = current
            last = conn.execute(
                "SELECT id, account_id, observed_to FROM token_account_log "
                "WHERE source = ? ORDER BY id DESC LIMIT 1", (source,)).fetchone()
            if last and last[1] == account_id and now - last[2] <= GRACE_SEC:
                conn.execute(
                    "UPDATE token_account_log SET observed_to = ?, label = ? WHERE id = ?",
                    (now, label, last[0]))
            else:
                conn.execute(
                    "INSERT INTO token_account_log(source, account_id, label, observed_from, observed_to) "
                    "VALUES (?, ?, ?, ?, ?)", (source, account_id, label, now, now))


def intervals(source: str, since: float) -> list[tuple[float, float, str]]:
    """(from, to + grace, account_id) sightings overlapping the window, oldest first."""
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT observed_from, observed_to, account_id FROM token_account_log "
                "WHERE source = ? AND observed_to >= ? ORDER BY observed_from",
                (source, since - GRACE_SEC)).fetchall()
    except sqlite3.Error:
        return []
    out = []
    for i, (start, end, account_id) in enumerate(rows):
        limit = end + GRACE_SEC
        if i + 1 < len(rows):
            limit = min(limit, rows[i + 1][0])
        out.append((start, limit, account_id))
    return out


def account_at(spans: list[tuple[float, float, str]], at: float) -> str | None:
    for start, end, account_id in spans:
        if start <= at < end:
            return account_id
    return None


def labels() -> dict[tuple[str, str], str]:
    """(source, account_id) -> latest readable label."""
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT source, account_id, label FROM token_account_log ORDER BY id").fetchall()
    except sqlite3.Error:
        return {}
    return {(source, account_id): label for source, account_id, label in rows}


def start_observer() -> None:
    """Sample the current login in a daemon thread for the life of the API."""
    global _started
    with _start_lock:
        if _started:
            return
        _started = True

    def loop() -> None:
        while True:
            try:
                observe()
            except Exception:
                pass  # a locked DB or a half-written config must not kill the sampler
            time.sleep(OBSERVE_SEC)

    threading.Thread(target=loop, name="token-account-observer", daemon=True).start()
