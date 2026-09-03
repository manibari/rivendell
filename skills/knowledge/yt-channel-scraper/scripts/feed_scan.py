#!/usr/bin/env python3
"""Find what's NEW across subscribed channels — the discovery half of yt-channel-scraper.

This script does everything that must be deterministic (who am I following, what
did they publish, have I already archived it) and nothing that needs judgement.
It hands back a work queue; the skill's agent loop does the reading and writing.

Three source kinds, three very different fetch paths — that asymmetry is the
whole reason this file exists:

  youtube   Atom feed at youtube.com/feeds/videos.xml?channel_id=UC…  — a plain
            XML GET. No API key, no quota, and crucially no yt-dlp, so polling
            15 channels daily does not spend any of the rate-limit budget that
            media_fetch.sh needs later for the actual subtitle download.
  podcast   the show's RSS. Same parser; items carry an audio enclosure.
  bilibili  no official feed exists. Falls back to `yt-dlp --flat-playlist`,
            which returns ids but NOT titles or dates, so unseen items get one
            cheap metadata call each (see enrich_bilibili). That cost is paid
            only for genuinely new videos — typically zero or one per run.

Dedupe is ground-truth-first: the seen-set is the union of (a) every url already
in the notes vault frontmatter and (b) a state file recording items deliberately
skipped or failed. Deriving (a) from the vault means a note archived by hand, or
by another machine pulling the same git repo, is never re-processed — the state
file alone would drift.

First contact with a subscription NEVER backfills. A newly added channel is
seeded: everything currently in its feed is marked seen and nothing is queued.
Without that guard, adding one active channel would dump 15 videos into the
auto-archive loop. Pass --backfill N to deliberately take the newest N.

Usage:
    feed_scan.py scan     [--json] [--sub NAME] [--backfill N] [--limit N]
                          # --limit overrides each subscription's own cap (per sub, not total)
    feed_scan.py subs                              # list subscriptions + state
    feed_scan.py baseline [--sub NAME]             # mark everything visible as seen
    feed_scan.py mark <url> [--why archived|skipped|failed] [--title T]
    feed_scan.py add <youtube|podcast|bilibili> <source> [name]

Env:
    VIDEO_NOTES_DIR   notes vault (default <repo>/knowledge/videos)
    SUBS_CONF         subscriptions file (default <vault>/subscriptions.conf)

Stdlib only.
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import os

SCRIPT_DIR = Path(__file__).resolve().parent
# scripts → yt-yt-channel-scraper → knowledge → skills → repo
REPO = SCRIPT_DIR.parents[3]
SHARED = (SCRIPT_DIR.parents[1] / "_shared" / "scripts").resolve()
sys.path.insert(0, str(SHARED))
import feed_items  # noqa: E402  (sibling shared engine: RSS/Atom → items)

VAULT = Path(os.environ.get("VIDEO_NOTES_DIR", REPO / "knowledge" / "videos"))
CONF = Path(os.environ.get("SUBS_CONF", VAULT / "subscriptions.conf"))
STATE = VAULT / "subscriptions-state.json"

KINDS = ("youtube", "podcast", "bilibili")
DEFAULT_LIMIT = 5          # max new items queued per subscription per run
FEED_WINDOW = 20           # how far back to look in a feed before giving up
CHANNEL_ID_RE = re.compile(r"^UC[\w-]{22}$")

CONF_HEADER = """\
# 訂閱清單 — yt-channel-scraper 讀這份檔
# 格式: NAME | KIND | SOURCE | LIMIT
#   KIND   youtube | podcast | bilibili
#   SOURCE youtube  → UCxxxx… 頻道 ID、@handle 或頻道網址
#          podcast  → RSS/Atom feed 網址
#          bilibili → UP 主 uid（數字）或 space.bilibili.com 網址
#   LIMIT  單次最多排入幾支新片（可省略，預設 5）
# 井字號開頭是註解。新訂閱第一次掃描只會「建基準線」不回補舊片。
"""


# ── config ───────────────────────────────────────────────────────────────────
def load_subs() -> list[dict]:
    if not CONF.exists():
        return []
    subs = []
    for lineno, raw in enumerate(CONF.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            print(f"warn: {CONF.name}:{lineno} needs at least NAME | KIND | SOURCE — skipped",
                  file=sys.stderr)
            continue
        name, kind, source = parts[0], parts[1].lower(), parts[2]
        if kind not in KINDS:
            print(f"warn: {CONF.name}:{lineno} unknown kind '{kind}' — skipped", file=sys.stderr)
            continue
        limit = DEFAULT_LIMIT
        if len(parts) > 3 and parts[3].isdigit():
            limit = int(parts[3])
        subs.append({"name": name, "kind": kind, "source": source, "limit": limit})
    return subs


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"error: {STATE} is not valid JSON ({e}). Fix or delete it.")
    return {"subs": {}, "seen": {}}


def save_state(state: dict) -> None:
    VAULT.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")


# ── identity ─────────────────────────────────────────────────────────────────
def canon(url: str) -> str:
    """One stable id per item, so the same video found via feed, vault, or a
    hand-typed link collapses to the same key. YouTube alone has four url
    shapes (watch?v=, youtu.be/, /shorts/, /embed/) for one video."""
    if not url:
        return ""
    u = url.strip()
    m = (re.search(r"[?&]v=([\w-]{11})", u)
         or re.search(r"youtu\.be/([\w-]{11})", u)
         or re.search(r"youtube\.com/(?:shorts|embed|live)/([\w-]{11})", u))
    if m:
        return f"yt:{m.group(1)}"
    m = re.search(r"(BV[\w]{10})", u)
    if m:
        return f"bili:{m.group(1)}"
    return f"url:{u.split('#')[0].rstrip('/')}"


def vault_seen() -> dict[str, str]:
    """Canonical ids already archived, read from note frontmatter — the vault is
    the source of truth, not the state file."""
    seen = {}
    if not VAULT.exists():
        return seen
    for note in VAULT.glob("*/note.md"):
        lines = note.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines or lines[0].strip() != "---":
            continue
        for line in lines[1:30]:
            if line.strip() == "---":
                break
            if line.startswith("url:"):
                key = canon(line[4:].strip())
                if key:
                    seen[key] = note.parent.name
                break
    return seen


# ── fetching ─────────────────────────────────────────────────────────────────
def ytdlp_json(url: str, *args: str, timeout: int = 90) -> dict:
    cmd = ["yt-dlp", "-J", "--flat-playlist", "--ignore-no-formats-error", *args, url]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise RuntimeError("yt-dlp not installed (brew install yt-dlp)")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"yt-dlp timed out after {timeout}s on {url}")
    if out.returncode != 0:
        tail = (out.stderr or "").strip().splitlines()[-1:] or ["(no stderr)"]
        raise RuntimeError(f"yt-dlp failed: {tail[0]}")
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"yt-dlp returned no JSON for {url}")


def resolve_youtube(source: str, cached: str | None) -> str:
    """Atom needs a channel_id. Handles and vanity urls need one yt-dlp lookup,
    which we cache in the state file — the id never changes."""
    if CHANNEL_ID_RE.match(source):
        return source
    if cached and CHANNEL_ID_RE.match(cached):
        return cached
    url = source
    if source.startswith("@"):
        url = f"https://www.youtube.com/{source}"
    elif not source.startswith("http"):
        url = f"https://www.youtube.com/@{source}"
    data = ytdlp_json(url, "--playlist-end", "1")
    cid = data.get("channel_id") or data.get("uploader_id") or ""
    if not CHANNEL_ID_RE.match(cid):
        raise RuntimeError(f"could not resolve a channel_id from {source} (got '{cid}')")
    return cid


def fetch_youtube(sub: dict, state: dict) -> tuple[list[dict], str | None]:
    entry = state["subs"].get(sub["name"], {})
    cid = resolve_youtube(sub["source"], entry.get("resolved"))
    feed = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
    _show, items = feed_items.parse(feed_items.fetch(feed), feed)
    out = [{"title": i["title"], "date": i["date"], "url": i["page_url"]}
           for i in items if i.get("page_url")]
    return out[:FEED_WINDOW], cid


def fetch_podcast(sub: dict) -> list[dict]:
    _show, items = feed_items.parse(feed_items.fetch(sub["source"]), sub["source"])
    out = []
    for i in items:
        url = i.get("audio_url") or i.get("page_url")
        if url:
            out.append({"title": i["title"], "date": i["date"], "url": url,
                        "duration_sec": i.get("duration_sec")})
    return out[:FEED_WINDOW]


def fetch_bilibili(sub: dict) -> list[dict]:
    src = sub["source"]
    url = src if src.startswith("http") else f"https://space.bilibili.com/{src}/video"
    data = ytdlp_json(url, "--playlist-end", str(FEED_WINDOW))
    out = []
    for e in data.get("entries") or []:
        vid = e.get("id") or ""
        if not vid:
            continue
        out.append({"title": (e.get("title") or "").strip(),
                    "date": "",
                    "url": e.get("url") or f"https://www.bilibili.com/video/{vid}"})
    return out


def enrich_bilibili(items: list[dict]) -> None:
    """--flat-playlist gives ids only. Fill title/date for the few unseen items
    with one metadata call each — cheap because it runs post-dedupe."""
    for it in items:
        if it["title"] and it["date"]:
            continue
        try:
            out = subprocess.run(
                ["yt-dlp", "--no-download", "--print", "%(title)s\t%(upload_date)s", it["url"]],
                capture_output=True, text=True, timeout=90)
            if out.returncode == 0 and out.stdout.strip():
                title, _, ud = out.stdout.strip().splitlines()[-1].partition("\t")
                it["title"] = it["title"] or title.strip()
                if len(ud.strip()) == 8:
                    it["date"] = f"{ud[:4]}-{ud[4:6]}-{ud[6:8]}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # a missing title is cosmetic; the url is what the queue needs


FETCHERS = {"podcast": fetch_podcast, "bilibili": fetch_bilibili}


# ── commands ─────────────────────────────────────────────────────────────────
def do_scan(argv: list[str]) -> int:
    as_json = "--json" in argv
    only = _opt(argv, "--sub")
    backfill = int(_opt(argv, "--backfill") or 0)
    hard_limit = int(_opt(argv, "--limit") or 0)

    subs = load_subs()
    if only:
        subs = [s for s in subs if s["name"] == only]
        if not subs:
            sys.exit(f"error: no subscription named '{only}' in {CONF}")
    if not subs:
        print(f"no subscriptions yet — add one:\n"
              f"  feed_scan.py add youtube @handle '頻道名'\n  (config: {CONF})",
              file=sys.stderr)
        return 0

    state = load_state()
    seen = dict(state.get("seen", {}))
    seen.update({k: {"why": "archived"} for k in vault_seen()})

    queue, errors, seeded, dirty = [], [], [], False

    for sub in subs:
        try:
            if sub["kind"] == "youtube":
                items, cid = fetch_youtube(sub, state)
                entry = state["subs"].setdefault(sub["name"], {})
                if entry.get("resolved") != cid:
                    entry.update({"kind": "youtube", "source": sub["source"], "resolved": cid})
                    dirty = True
            else:
                items = FETCHERS[sub["kind"]](sub)
                state["subs"].setdefault(sub["name"],
                                         {"kind": sub["kind"], "source": sub["source"]})
        except (RuntimeError, SystemExit) as e:
            errors.append({"sub": sub["name"], "error": str(e)})
            continue

        entry = state["subs"].setdefault(sub["name"], {})
        fresh = [i for i in items if canon(i["url"]) not in seen]

        if not entry.get("seeded"):
            take = fresh[:backfill] if backfill else []
            for i in fresh[len(take):]:
                state["seen"][canon(i["url"])] = {"why": "baseline", "date": str(date.today()),
                                                  "title": i["title"]}
            entry["seeded"] = str(date.today())
            dirty = True
            seeded.append({"sub": sub["name"], "marked": len(fresh) - len(take),
                           "queued": len(take)})
            fresh = take

        cap = hard_limit or sub["limit"]
        fresh = fresh[:cap]
        if sub["kind"] == "bilibili" and fresh:
            enrich_bilibili(fresh)
        for i in fresh:
            queue.append({"sub": sub["name"], "kind": sub["kind"], "title": i["title"],
                          "url": i["url"], "date": i["date"], "id": canon(i["url"]),
                          "duration_sec": i.get("duration_sec")})

    if dirty:
        save_state(state)

    if as_json:
        print(json.dumps({"queue": queue, "seeded": seeded, "errors": errors},
                         ensure_ascii=False, indent=2))
        return 1 if errors else 0

    for s in seeded:
        print(f"🌱 {s['sub']}：首次訂閱，{s['marked']} 支既有影片設為基準線（不回補）"
              f"{'，排入最新 %d 支' % s['queued'] if s['queued'] else ''}")
    if not queue:
        print("✅ 沒有新影片" if not errors else "（沒有新影片）")
    else:
        print(f"\n{len(queue)} 支待處理：\n")
        for n, q in enumerate(queue, 1):
            print(f"{n:>3}. [{q['sub']}] {q['date'] or '—'}  {q['title'] or q['id']}")
            print(f"     {q['url']}")
    for e in errors:
        print(f"\n⚠️  {e['sub']}：{e['error']}", file=sys.stderr)
    return 1 if errors else 0


def do_subs(_argv: list[str]) -> int:
    subs, state = load_subs(), load_state()
    if not subs:
        print(f"no subscriptions in {CONF}")
        return 0
    print(f"{len(subs)} subscriptions  ({CONF})\n")
    for s in subs:
        e = state["subs"].get(s["name"], {})
        flag = f"seeded {e['seeded']}" if e.get("seeded") else "NEW (will seed on next scan)"
        resolved = f" → {e['resolved']}" if e.get("resolved") else ""
        print(f"  {s['name']:<24} {s['kind']:<9} {s['source']}{resolved}  [max {s['limit']}]  {flag}")
    print(f"\nseen: {len(state.get('seen', {}))} in state + {len(vault_seen())} in vault")
    return 0


def do_baseline(argv: list[str]) -> int:
    only = _opt(argv, "--sub")
    state = load_state()
    for sub in load_subs():
        if only and sub["name"] != only:
            continue
        try:
            items = (fetch_youtube(sub, state)[0] if sub["kind"] == "youtube"
                     else FETCHERS[sub["kind"]](sub))
        except (RuntimeError, SystemExit) as e:
            print(f"⚠️  {sub['name']}: {e}", file=sys.stderr)
            continue
        for i in items:
            state["seen"].setdefault(canon(i["url"]),
                                     {"why": "baseline", "date": str(date.today()),
                                      "title": i["title"]})
        state["subs"].setdefault(sub["name"], {})["seeded"] = str(date.today())
        print(f"🌱 {sub['name']}: {len(items)} items marked seen")
    save_state(state)
    return 0


def do_mark(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        sys.exit("usage: feed_scan.py mark <url> [--why archived|skipped|failed] [--title T]")
    key = canon(argv[0])
    why = _opt(argv, "--why") or "archived"
    state = load_state()
    state["seen"][key] = {"why": why, "date": str(date.today()),
                          "title": _opt(argv, "--title") or ""}
    save_state(state)
    print(f"{key} → {why}")
    return 0


def do_add(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.exit("usage: feed_scan.py add <youtube|podcast|bilibili> <source> [name]")
    kind, source = argv[0].lower(), argv[1]
    if kind not in KINDS:
        sys.exit(f"error: kind must be one of {'|'.join(KINDS)}")
    name = argv[2] if len(argv) > 2 else source.lstrip("@")
    if any(s["name"] == name for s in load_subs()):
        sys.exit(f"error: '{name}' is already subscribed")
    CONF.parent.mkdir(parents=True, exist_ok=True)
    if not CONF.exists():
        CONF.write_text(CONF_HEADER, encoding="utf-8")
    with CONF.open("a", encoding="utf-8") as fh:
        fh.write(f"{name} | {kind} | {source} | {DEFAULT_LIMIT}\n")
    print(f"added: {name} | {kind} | {source}\n"
          f"next scan will seed it (no backfill) — use `scan --sub '{name}' --backfill 3` to take the newest 3")
    return 0


def _opt(argv: list[str], flag: str) -> str | None:
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            return argv[i + 1]
    return None


COMMANDS = {"scan": do_scan, "subs": do_subs, "baseline": do_baseline,
            "mark": do_mark, "add": do_add}


def main() -> int:
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "scan"
    if cmd in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if cmd not in COMMANDS:
        sys.exit(f"error: unknown command '{cmd}' (expected {'|'.join(COMMANDS)})")
    return COMMANDS[cmd](argv[1:])


if __name__ == "__main__":
    sys.exit(main())
