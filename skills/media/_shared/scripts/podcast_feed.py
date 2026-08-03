#!/usr/bin/env python3
"""Parse a podcast RSS/Atom feed into a list of episodes with direct audio URLs.

Why this exists: a podcast feed already publishes a direct link to the audio file
(the <enclosure>). Capturing the audio by playing the episode is bound by playback
duration — a 60-minute show costs at least 60 minutes of wall clock, and speeding
playback up does not escape it. Reading the enclosure URL instead turns the same
episode into a download, which ffmpeg does in seconds. Every paid podcast-to-text
tool works this way; there is no cleverness here, only the right input.

Usage:
    podcast_feed.py list <feed-url> [--json] [--limit N]
    podcast_feed.py get  <feed-url> <index>      # 1-based, prints the audio URL

Stdlib only — no new dependency for the media family.
"""
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) podcast-transcript/1.0"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
}
AUDIO_EXT = (".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".mp4", ".m4b")


def fetch(url: str) -> bytes:
    """GET the feed. Redirects ARE followed — podcast enclosures and feed hosts
    redirect as a matter of course (feedburner, podtrac, chartable prefixes), so
    the usual 'disable redirects' scraper rule does not apply. What that rule is
    really protecting against is a redirect landing on a homepage and being
    mistaken for data, so parse() validates the root element instead."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"error: feed returned HTTP {e.code} — {url}")
    except urllib.error.URLError as e:
        sys.exit(f"error: could not reach feed ({e.reason}) — {url}")


def _duration_seconds(raw: str | None) -> int | None:
    """itunes:duration is any of 3600, 60:00, or 01:00:00."""
    if not raw:
        return None
    raw = raw.strip()
    if raw.isdigit():
        return int(raw)
    parts = raw.split(":")
    if not all(p.isdigit() for p in parts):
        return None
    secs = 0
    for p in parts:
        secs = secs * 60 + int(p)
    return secs


def _date_iso(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        pass
    try:  # Atom uses RFC 3339
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return raw[:10]


def _looks_like_audio(url: str, mime: str | None) -> bool:
    if mime and mime.startswith("audio"):
        return True
    if mime in ("video/mp4", "application/octet-stream"):
        return True
    path = url.split("?", 1)[0].lower()
    return path.endswith(AUDIO_EXT)


def parse(raw: bytes, feed_url: str) -> tuple[str, list[dict]]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        sys.exit(f"error: not valid XML — {e}\n       (a redirect to an HTML page? open {feed_url} in a browser)")

    tag = root.tag.split("}")[-1]
    if tag not in ("rss", "feed"):
        sys.exit(f"error: root element is <{tag}>, not <rss> or <feed> — this is not a podcast feed")

    episodes: list[dict] = []

    if tag == "rss":  # RSS 2.0
        channel = root.find("channel")
        if channel is None:
            sys.exit("error: <rss> without <channel>")
        show = (channel.findtext("title") or "").strip()
        for item in channel.findall("item"):
            enc = item.find("enclosure")
            if enc is None:
                continue
            url = (enc.get("url") or "").strip()
            if not url or not _looks_like_audio(url, enc.get("type")):
                continue
            episodes.append({
                "title": (item.findtext("title") or "(untitled)").strip(),
                "date": _date_iso(item.findtext("pubDate")),
                "duration_sec": _duration_seconds(item.findtext("itunes:duration", namespaces=NS)),
                "audio_url": url,
            })
    else:  # Atom
        show = (root.findtext("atom:title", namespaces=NS) or "").strip()
        for entry in root.findall("atom:entry", NS):
            url = None
            mime = None
            for link in entry.findall("atom:link", NS):
                if link.get("rel") == "enclosure":
                    url, mime = (link.get("href") or "").strip(), link.get("type")
                    break
            if not url or not _looks_like_audio(url, mime):
                continue
            episodes.append({
                "title": (entry.findtext("atom:title", namespaces=NS) or "(untitled)").strip(),
                "date": _date_iso(entry.findtext("atom:published", namespaces=NS)
                                  or entry.findtext("atom:updated", namespaces=NS)),
                "duration_sec": _duration_seconds(entry.findtext("itunes:duration", namespaces=NS)),
                "audio_url": url,
            })

    if not episodes:
        sys.exit("error: feed parsed, but no episode carried an audio enclosure")
    return show, episodes


def _hms(secs: int | None) -> str:
    if not secs:
        return "?"
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def main() -> None:
    argv = sys.argv[1:]
    if len(argv) < 2:
        sys.exit(__doc__)
    cmd, feed_url = argv[0], argv[1]
    rest = argv[2:]

    show, episodes = parse(fetch(feed_url), feed_url)

    if cmd == "get":
        if not rest or not rest[0].isdigit():
            sys.exit("usage: podcast_feed.py get <feed-url> <index>   # 1-based")
        idx = int(rest[0])
        if not 1 <= idx <= len(episodes):
            sys.exit(f"error: index {idx} out of range (1..{len(episodes)})")
        ep = episodes[idx - 1]
        print(ep["audio_url"])
        print(f"# {ep['date']}  {ep['title']}  ({_hms(ep['duration_sec'])})", file=sys.stderr)
        return

    if cmd != "list":
        sys.exit(f"error: unknown command '{cmd}' (expected list|get)")

    limit = len(episodes)
    if "--limit" in rest:
        i = rest.index("--limit")
        if i + 1 < len(rest) and rest[i + 1].isdigit():
            limit = int(rest[i + 1])
    episodes = episodes[:limit]

    if "--json" in rest:
        print(json.dumps({"show": show, "episodes": episodes}, ensure_ascii=False, indent=2))
        return

    print(f"{show}  ({len(episodes)} episodes)\n")
    for n, ep in enumerate(episodes, 1):
        print(f"{n:>3}. {ep['date']}  {_hms(ep['duration_sec']):>8}  {ep['title']}")


if __name__ == "__main__":
    main()
