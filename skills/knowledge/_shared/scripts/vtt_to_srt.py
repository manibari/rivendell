#!/usr/bin/env python3
"""Convert a .vtt subtitle file into a clean .srt, PRESERVING cue timing.

This is the timestamp-keeping sibling of vtt_to_text.py. Where that one throws
timing away to make readable prose, this one keeps it — because the point of a
subtitle file is to sit in sync with the video (for re-upload, translation, or
burning in). It strips inline karaoke tags (<00:00:01.200><c>…</c>), merges
consecutive cues that carry identical text (the rolling-caption artifact) into a
single block spanning their combined time, and renumbers as SRT.

Good input is human-authored subtitles (one clean cue per line). Auto-captions
convert too, but their rolling nature means cue boundaries are approximate —
fine for a rough translation pass, not for frame-accurate work.

Usage:
    python3 vtt_to_srt.py input.vtt            # -> stdout
    python3 vtt_to_srt.py input.vtt out.srt    # -> file
"""
import re
import sys

TAG = re.compile(r"<[^>]+>")
CUE_SETTING = re.compile(r"\s+(align|position|size|line|region):\S+")
TIMING = re.compile(
    r"(\d{2}:\d{2}:\d{2})[.,](\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2})[.,](\d{3})"
)
ENTITIES = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&#39;": "'"}


def _decode(s: str) -> str:
    for k, v in ENTITIES.items():
        s = s.replace(k, v)
    return s


def parse_cues(raw: str):
    """Yield (start, end, text) tuples. Times as 'HH:MM:SS,mmm' (SRT style)."""
    lines = raw.splitlines()
    i, n = 0, len(lines)
    cur = None
    buf: list[str] = []
    while i < n:
        line = lines[i]
        m = TIMING.search(line)
        if m:
            if cur is not None:
                yield cur[0], cur[1], " ".join(buf).strip()
            start = f"{m.group(1)},{m.group(2)}"
            end = f"{m.group(3)},{m.group(4)}"
            cur = (start, end)
            buf = []
        elif cur is not None:
            stripped = line.strip()
            if stripped and not stripped.isdigit() and not stripped.startswith(
                ("WEBVTT", "Kind:", "Language:", "NOTE")
            ):
                text = CUE_SETTING.sub("", line)
                text = TAG.sub("", text)
                text = _decode(text).strip()
                if text:
                    buf.append(text)
        i += 1
    if cur is not None:
        yield cur[0], cur[1], " ".join(buf).strip()


def to_srt(raw: str) -> str:
    cues = [(s, e, t) for s, e, t in parse_cues(raw) if t]
    # merge consecutive identical-text cues into one spanning block
    merged: list[list[str]] = []
    for start, end, text in cues:
        if merged and merged[-1][2] == text:
            merged[-1][1] = end          # extend end time
        else:
            merged.append([start, end, text])
    out = []
    for idx, (start, end, text) in enumerate(merged, 1):
        out.append(str(idx))
        out.append(f"{start} --> {end}")
        out.append(text)
        out.append("")
    return "\n".join(out).strip() + "\n"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    with open(sys.argv[1], encoding="utf-8", errors="replace") as fh:
        srt = to_srt(fh.read())
    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w", encoding="utf-8") as out:
            out.write(srt)
        print(f"wrote {sys.argv[2]} ({srt.count(chr(10) + chr(10)) + 1} cues)", file=sys.stderr)
    else:
        sys.stdout.write(srt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
