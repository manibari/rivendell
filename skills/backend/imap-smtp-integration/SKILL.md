---
name: imap-smtp-integration
loop: dev
pdca: do
description: IMAP/SMTP Integration - Integrate email reading and sending via IMAP/SMTP into a FastAPI project. TRIGGER when integrating email into FastAPI without OAuth, setting up Gmail IMAP fallback, or building email compose/read features with IMAP/SMTP. DO NOT TRIGGER when using OAuth-based email APIs (Microsoft Graph, Gmail API).
tags: [backend, email, imap, smtp, fastapi]
version: 1.0.0
---

# IMAP/SMTP Integration

Integrate email reading and sending via IMAP/SMTP into a FastAPI project. Serves as a fallback when OAuth (Microsoft Graph, Gmail API) is unavailable. Works with Gmail App Password, corporate mail servers, and any standard mail server.

**TRIGGER when**: integrating email into FastAPI without OAuth, setting up Gmail IMAP fallback, or building email compose/read features with IMAP/SMTP.

## Gmail App Password Setup

Gmail requires a specific App Password (not your account password):

1. Enable 2-Step Verification on the Google account
2. Go to: Google Account → Security → 2-Step Verification → App passwords
3. Create an app password (select "Mail" + "Other")
4. Copy the 16-character password — **format: `xxxx xxxx xxxx xxxx` (with spaces)**

**Critical**: Use the password WITH spaces in the config. Strip spaces in code:

```python
password = config["password"].replace(" ", "")  # "rzae flyt vxlo zfky" → "rzaeflytxvlozfky"
```

Gmail IMAP/SMTP settings:
- IMAP: `imap.gmail.com`, port `993`, SSL: `true`
- SMTP: `smtp.gmail.com`, port `587`, TLS (STARTTLS): `true`

## Service Implementation

Create `services/nexus/imap_smtp.py`:

```python
"""IMAP/SMTP email service — fallback when OAuth is unavailable."""
import asyncio
import email
import imaplib
import smtplib
import logging
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


def _decode_str(raw) -> str:
    """Decode email header value (handles UTF-8, Base64, etc.)."""
    if not raw:
        return ""
    parts = decode_header(str(raw))
    result = []
    for b, enc in parts:
        if isinstance(b, bytes):
            result.append(b.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(str(b))
    return " ".join(result)


def test_imap_connection(host: str, port: int, username: str, password: str, use_ssl: bool = True) -> dict:
    """Test IMAP connection. Returns {success: bool, error: str}."""
    try:
        password = password.replace(" ", "")  # strip spaces from App Password
        if use_ssl:
            conn = imaplib.IMAP4_SSL(host, port)
        else:
            conn = imaplib.IMAP4(host, port)
        conn.login(username, password)
        status, data = conn.select("INBOX")
        count = int(data[0]) if status == "OK" else 0
        conn.logout()
        return {"success": True, "inbox_count": count}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_smtp_connection(host: str, port: int, username: str, password: str, use_tls: bool = True) -> dict:
    """Test SMTP connection. Returns {success: bool, error: str}."""
    try:
        password = password.replace(" ", "")
        if use_tls:
            conn = smtplib.SMTP(host, port)
            conn.starttls()
        else:
            conn = smtplib.SMTP_SSL(host, port)
        conn.login(username, password)
        conn.quit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_imap_emails(config: dict, limit: int = 20) -> list[dict]:
    """
    Fetch recent emails from IMAP inbox.
    config: {host, port, username, password, use_ssl}
    """
    password = config["password"].replace(" ", "")

    if config.get("use_ssl", True):
        conn = imaplib.IMAP4_SSL(config["host"], config["port"])
    else:
        conn = imaplib.IMAP4(config["host"], config["port"])

    conn.login(config["username"], password)
    conn.select("INBOX")

    _, data = conn.search(None, "ALL")
    all_ids = data[0].split()
    recent_ids = all_ids[-limit:][::-1]  # most recent first

    emails = []
    for eid in recent_ids:
        _, msg_data = conn.fetch(eid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        break
                    except Exception:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
            except Exception:
                body = ""

        emails.append({
            "message_id": msg.get("Message-ID", ""),
            "subject": _decode_str(msg.get("Subject", "")),
            "from_addr": _decode_str(msg.get("From", "")),
            "to_addrs": _decode_str(msg.get("To", "")),
            "date": msg.get("Date", ""),
            "body_preview": body[:500],
            "has_attachments": any(
                part.get_content_disposition() == "attachment"
                for part in msg.walk()
            ),
        })

    conn.logout()
    return emails


def send_smtp_email(config: dict, to: str, subject: str, body: str, html: bool = False) -> dict:
    """
    Send email via SMTP.
    config: {host, port, username, password, use_tls}
    """
    password = config["password"].replace(" ", "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config["username"]
    msg["To"] = to

    content_type = "html" if html else "plain"
    msg.attach(MIMEText(body, content_type, "utf-8"))

    if config.get("use_tls", True):
        conn = smtplib.SMTP(config["host"], config["port"])
        conn.starttls()
    else:
        conn = smtplib.SMTP_SSL(config["host"], config["port"])

    conn.login(config["username"], password)
    conn.sendmail(config["username"], to, msg.as_string())
    conn.quit()

    return {"success": True, "to": to, "subject": subject}


# Async wrappers for FastAPI (imaplib is synchronous)
async def async_test_imap(host, port, username, password, use_ssl=True):
    return await asyncio.to_thread(test_imap_connection, host, port, username, password, use_ssl)

async def async_fetch_emails(config: dict, limit: int = 20):
    return await asyncio.to_thread(fetch_imap_emails, config, limit)

async def async_send_email(config: dict, to: str, subject: str, body: str):
    return await asyncio.to_thread(send_smtp_email, config, to, subject, body)
```

## FastAPI Endpoints

```python
@router.post("/imap/test")
async def test_imap(body: ImapTestRequest):
    result = await async_test_imap(
        body.imap_host, body.imap_port, body.username, body.password, body.use_ssl
    )
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result

@router.post("/smtp/test")
async def test_smtp(body: SmtpTestRequest):
    result = await asyncio.to_thread(
        test_smtp_connection, body.smtp_host, body.smtp_port, body.username, body.password, body.use_tls
    )
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result

@router.get("/emails")
async def list_emails():
    config = get_imap_config_from_db()  # load from settings
    emails = await async_fetch_emails(config)
    return {"emails": emails}
```

## Frontend Settings Component

```typescript
// SecretInput — password field with show/hide toggle
function SecretInput({ value, onChange, placeholder }: SecretInputProps) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        type={show ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-sm pr-10"
      />
      <button
        type="button"
        onClick={() => setShow(!show)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
      >
        {show ? <EyeOff size={14} /> : <Eye size={14} />}
      </button>
    </div>
  );
}
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Authentication failed` | Wrong password or App Password not created | Re-generate App Password |
| `b'' LOGIN failed` | Spaces in App Password | `password.replace(" ", "")` |
| `[ALERT] Please log in via your web browser` | Less secure app access disabled | Use App Password (2FA required) |
| `Connection refused` | Wrong port or SSL setting | Gmail IMAP=993/SSL, SMTP=587/TLS |
| `asyncio.to_thread` not found | Python < 3.9 | Use `loop.run_in_executor(None, fn)` |

## AI Email Analysis

After fetching emails, pass to AI provider for spam/category analysis:

```python
from services.ai_provider import call_ai

async def analyze_emails_for_spam(emails: list[dict]) -> list[dict]:
    summary = "\n".join([
        f"- From: {e['from_addr']} | Subject: {e['subject']} | Preview: {e['body_preview'][:100]}"
        for e in emails[:10]
    ])

    result = await call_ai(
        system="You are an email analyst. Identify spam, newsletters, and important business emails.",
        user=f"Analyze these emails and classify each as spam/newsletter/business/other:\n\n{summary}"
    )
    return result
```
