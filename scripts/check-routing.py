#!/usr/bin/env python3
"""check-routing.py — regression test for skill trigger phrases.

The model routes by reading each skill's description, so a phrase that sits
in two skills' TRIGGER text is a coin toss. This script makes that mechanical:
for every phrase in data/routing-tests.json, list the skills whose TRIGGER
segment contains it (substring, case-insensitive), and require exactly the
expected one. Text after "DO NOT TRIGGER" / "SKIP" is the negative segment
and does not count as a hit.

Usage: check-routing.py [--json] [--verbose]
Exit:  0 all pass; 1 any ambiguous / missing / wrong.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
TESTS = ROOT / "data" / "routing-tests.json"

_NEG = re.compile(r"(DO NOT TRIGGER|SKIP|DON'T TRIGGER)", re.I)
_TRIG = re.compile(r"TRIGGER", re.I)


def _frontmatter(text: str) -> str:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    return m.group(1) if m else ""


def _description(fm: str) -> str:
    """Flatten the description block (handles `>` folded blocks and quoted one-liners)."""
    lines = fm.splitlines()
    out: list[str] = []
    grab = False
    for line in lines:
        if grab:
            if line and not line.startswith((" ", "\t")):
                break
            out.append(line.strip())
            continue
        m = re.match(r"^description\s*:\s*(.*)$", line)
        if m:
            head = m.group(1).strip()
            if head and head not in (">", "|", ">-", "|-"):
                out.append(head.strip('"'))
                break
            grab = True
    # when_to_use also carries TRIGGER text for some skills
    for line in lines:
        m = re.match(r"^when_to_use\s*:\s*(.*)$", line)
        if m:
            out.append(m.group(1).strip().strip('"'))
    return " ".join(out)


def _positive_segment(desc: str) -> str:
    """Text from the first TRIGGER up to the first DO NOT TRIGGER / SKIP.

    If the description has no TRIGGER keyword at all, the whole description is
    the positive segment (older skills). Negative text is cut out entirely.
    """
    neg = _NEG.search(desc)
    pos_end = neg.start() if neg else len(desc)
    trig = _TRIG.search(desc[:pos_end])
    start = trig.start() if trig else 0
    return desc[start:pos_end]


def load_skills() -> dict[str, str]:
    result: dict[str, str] = {}
    for md in sorted(SKILLS.glob("*/*/SKILL.md")):
        fm = _frontmatter(md.read_text(encoding="utf-8"))
        result[md.parent.name] = _positive_segment(_description(fm))
    return result


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).lower()


def main() -> int:
    as_json = "--json" in sys.argv
    verbose = "--verbose" in sys.argv
    tests = json.loads(TESTS.read_text(encoding="utf-8"))["tests"]
    skills = {name: _norm(seg) for name, seg in load_skills().items()}
    results = []
    failures = 0
    for t in tests:
        phrase = _norm(t["phrase"])
        hits = [name for name, seg in skills.items() if phrase in seg]
        ok = hits == [t["expect"]]
        if not ok:
            failures += 1
        results.append({"phrase": t["phrase"], "expect": t["expect"], "hits": hits, "ok": ok})
    if as_json:
        print(json.dumps({"ok": failures == 0, "failures": failures, "results": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if r["ok"] and not verbose:
                continue
            mark = "ok " if r["ok"] else "FAIL"
            print(f"  [{mark}] {r['phrase']!r} → expect {r['expect']}; hits {r['hits'] or '—'}")
        print(f"  routing: {len(tests) - failures}/{len(tests)} phrases route to exactly one skill")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
