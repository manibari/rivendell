#!/usr/bin/env python3
"""Pick the single best subtitle track from `yt-dlp -J` metadata.

Why this exists: asking yt-dlp to download every matching subtitle language at
once makes it fire one HTTP request per language, and YouTube 429s the later
ones — which (under `set -e`) killed the fetch even though a usable track had
already landed. So instead we inspect what's available first, choose ONE track,
and download only that. This file does the choosing.

Manual subtitles are preferred over auto-captions (accurate, punctuated). Within
each kind we honor the caller's language preference order, matching a preference
like "zh-Hant" against real keys such as "zh-Hant", "zh-HK", "en-US" by exact
match first, then family prefix.

Input:  path to a JSON file from `yt-dlp -J --skip-download` (or "-" for stdin)
Args:   [meta.json] [comma-separated language preference]
Output: one tab-separated line to stdout:  <lang>\t<manual|auto>\t<title>
        exit 3 if no subtitle track exists at all.
"""
import json
import sys

DEFAULT_PREFS = ["zh-Hant", "zh-TW", "zh-Hans", "zh", "en", "ja"]


def _match(pref: str, keys: list[str]) -> str | None:
    """Return the real subtitle key best matching a preference, or None."""
    # exact match wins
    for k in keys:
        if k.lower() == pref.lower():
            return k
    # family prefix: pref "zh-Hant" matches "zh-Hant-...", pref "en" matches "en-US"
    fam = pref.lower()
    for k in keys:
        kl = k.lower()
        if kl.startswith(fam + "-") or kl.split("-")[0] == fam:
            return k
    return None


def pick(meta: dict, prefs: list[str]) -> tuple[str, str] | None:
    manual = meta.get("subtitles") or {}
    auto = meta.get("automatic_captions") or {}
    # drop yt-dlp's synthetic "live_chat" pseudo-track
    manual_keys = [k for k in manual if k != "live_chat"]
    auto_keys = [k for k in auto if k != "live_chat"]

    for pref in prefs:                       # manual first, across all prefs
        hit = _match(pref, manual_keys)
        if hit:
            return hit, "manual"
    for pref in prefs:                       # then auto-captions
        hit = _match(pref, auto_keys)
        if hit:
            return hit, "auto"
    # nothing in preference order — fall back to any manual, then any auto
    if manual_keys:
        return manual_keys[0], "manual"
    if auto_keys:
        return auto_keys[0], "auto"
    return None


def main() -> int:
    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    prefs = (sys.argv[2].split(",") if len(sys.argv) > 2 else DEFAULT_PREFS)
    prefs = [p.strip() for p in prefs if p.strip()]

    raw = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    meta = json.loads(raw)
    title = (meta.get("title") or meta.get("id") or "").replace("\t", " ").replace("\n", " ")

    chosen = pick(meta, prefs)
    if chosen is None:
        print("no subtitle tracks available", file=sys.stderr)
        return 3
    lang, kind = chosen
    sys.stdout.write(f"{lang}\t{kind}\t{title}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
