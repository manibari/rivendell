#!/usr/bin/env python3
"""Regenerate INDEX.md for the video knowledge base — a browsable table built
from each note's frontmatter, so you can scan/grep everything at a glance.

Mirrors the tender/subsidy scrapers' "regenerate INDEX from the .md files"
pattern: the notes are the source of truth; this is a derived view. Safe to
re-run any time (idempotent).

Scans  <videos_dir>/*/note.md  (default: <repo>/knowledge/videos, resolved from
this script's location) and writes <videos_dir>/INDEX.md.

Usage:  python3 build_index.py [videos_dir]
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DIR = SCRIPT_DIR.parents[3] / "knowledge" / "videos"  # skills/media/_shared/scripts → repo


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip("'\"")
    return fm


def one_liner(body: str) -> str:
    """Pull the BLUF — the '一句話' line if present, else first prose line."""
    for line in body.splitlines():
        s = line.strip()
        if "一句話" in s:
            # keep text after the colon
            for sep in ("：", ":"):
                if sep in s:
                    return s.split(sep, 1)[1].strip().lstrip("*").strip()
            return s.lstrip("#* ").strip()
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith(("#", "---", ">", "|")):
            return s.lstrip("*").strip()
    return ""


RELIABILITY_ICON = {
    "manual subs": "✅",
    "auto-caption (rough)": "⚠️",
    "asr": "🤖",
    "asr (machine transcription)": "🤖",
}


def main() -> int:
    videos_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIR
    if not videos_dir.exists():
        print(f"no videos dir: {videos_dir}", file=sys.stderr)
        return 1

    rows = []
    for note in sorted(videos_dir.glob("*/note.md")):
        text = note.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        body = text.split("\n---", 2)[-1] if text.startswith("---") else text
        rel = fm.get("reliability", "")
        icon = RELIABILITY_ICON.get(rel, "🤖" if "asr" in rel else "")
        rows.append({
            "date": fm.get("date", ""),
            "title": fm.get("title", note.parent.name),
            "source": fm.get("source", ""),
            "rel": f"{icon} {rel}".strip(),
            "url": fm.get("url", ""),
            "rel_path": f"{note.parent.name}/note.md",
            "blurb": one_liner(body),
        })

    rows.sort(key=lambda r: r["date"], reverse=True)

    lines = [
        "# 影片知識庫索引",
        "",
        f"{len(rows)} 篇筆記。可信度：✅ 人工字幕 · ⚠️ 自動字幕（粗略）· 🤖 whisper ASR（術語以原片為準）。",
        "",
        "| 日期 | 標題 | 來源 | 可信度 | 一句話 |",
        "|------|------|------|--------|--------|",
    ]
    for r in rows:
        # link the title to the local note; keep a source link too. Escape any
        # literal '|' in cell text — it would otherwise split the markdown column.
        safe_title = r["title"].replace("|", "／")
        title_cell = f"[{safe_title}]({_esc(r['rel_path'])})"
        src = f"[{r['source']}]({r['url']})" if r["url"] else r["source"]
        blurb = r["blurb"].replace("|", "／").replace("\n", " ")
        lines.append(f"| {r['date']} | {title_cell} | {src} | {r['rel']} | {blurb} |")
    lines.append("")

    out = videos_dir / "INDEX.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} ({len(rows)} entries)")
    return 0


def _esc(p: str) -> str:
    return p.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


if __name__ == "__main__":
    raise SystemExit(main())
