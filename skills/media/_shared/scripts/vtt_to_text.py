#!/usr/bin/env python3
"""Convert a YouTube .vtt subtitle file into clean, readable plain text.

YouTube auto-captions are the messy case this exists for: cues carry inline
timestamp tags (<00:00:01.200><c>word</c>), and the rolling display repeats
each line as new words stream in — so a naive strip leaves every sentence
printed 2-3 times. We strip the markup, drop exact consecutive dupes, then
drop any line that is wholly contained in the next one (the rolling-caption
artifact). What survives reads like prose, ready to feed a summariser/rewriter.

Usage:
    python3 vtt_to_text.py input.vtt            # -> stdout
    python3 vtt_to_text.py input.vtt out.txt    # -> file
"""
import re
import sys

TAG = re.compile(r"<[^>]+>")           # <00:00:01.200>, <c>, </c>, <c.colorXXXXXX>
CUE_SETTING = re.compile(r"\balign:\S+|\bposition:\S+")
ENTITIES = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&#39;": "'"}


def _decode_entities(s: str) -> str:
    for k, v in ENTITIES.items():
        s = s.replace(k, v)
    return s


def clean_vtt(raw: str) -> str:
    lines = raw.splitlines()
    cues: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if "-->" in stripped:            # timestamp / cue-timing line
            continue
        if stripped.isdigit():           # numeric cue index (SRT-style)
            continue
        text = CUE_SETTING.sub("", line)
        text = TAG.sub("", text)
        text = _decode_entities(text).strip()
        if not text:
            continue
        # drop exact consecutive duplicates
        if cues and cues[-1] == text:
            continue
        cues.append(text)

    # drop rolling-caption partials: a line fully contained in the next one
    deduped: list[str] = []
    for i, cur in enumerate(cues):
        nxt = cues[i + 1] if i + 1 < len(cues) else ""
        if nxt and cur in nxt:
            continue
        deduped.append(cur)

    return "\n".join(deduped).strip() + "\n"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    with open(sys.argv[1], encoding="utf-8", errors="replace") as fh:
        cleaned = clean_vtt(fh.read())
    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w", encoding="utf-8") as out:
            out.write(cleaned)
        print(f"wrote {sys.argv[2]} ({len(cleaned)} chars)", file=sys.stderr)
    else:
        sys.stdout.write(cleaned)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
