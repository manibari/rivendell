"""Collect per-session token facts for one time window (Claude sessions, Codex sessions, code-run runs).

Usage: python3 -I collect.py <start ISO local> <end ISO local>  -> JSON on stdout
Only numbers, tool names, masked command prefixes and masked prompt snippets leave this script.
"""
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
CLAUDE_PROJECTS = HOME / ".claude" / "projects"
# codex executor, gemini executor (company gateway) and qwen executor homes
CODEX_DIRS = [HOME / h / d for h in (".codex", ".codex-gemini", ".codex-qwen")
              for d in ("sessions", "archived_sessions")]
CODE_RUNS = HOME / ".local" / "state" / "sk" / "code-runs"

SECRET = re.compile(r"(sk-[A-Za-z0-9_\-]{8,}|eyJ[A-Za-z0-9_\-.]{20,}|[A-Za-z0-9_\-]{32,}"
                    r"|(?i:(?:password|passwd|token|secret|api[_-]?key)\s*[=:]\s*\S+))")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
GAP_REBUILD_MIN = 60      # the prompt cache TTL is one hour
BIG_CTX = (200_000, 500_000)


def mask(s: str, n: int) -> str:
    s = " ".join(str(s).split())
    s = EMAIL.sub("<email>", SECRET.sub("***", s))
    return s[:n]


def ts(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def project_of(cwd: str) -> str:
    p = Path(cwd)
    parts = p.parts
    for root in ("Code", "Work"):
        if root in parts:
            i = parts.index(root)
            rest = parts[i + 1:]
            if root == "Code" and rest and rest[0] in ("Personal", "Chimes") and len(rest) > 1:
                return rest[1]
            return rest[0] if rest else root
    return p.name or cwd


def claude_sessions(start: datetime, end: datetime, root: Path = CLAUDE_PROJECTS) -> list[dict]:
    files = [f for f in root.rglob("*.jsonl")
             if datetime.fromtimestamp(f.stat().st_mtime, timezone.utc) >= start]
    sessions: dict[str, dict] = {}

    def slot(sid: str) -> dict:
        return sessions.setdefault(sid, {
            "session": sid[:8], "name": "", "project": "", "models": Counter(),
            "first": None, "last": None, "api_calls": 0, "user_prompts": 0,
            "tokens": Counter(), "ctx": [], "rebuilds": 0, "rebuild_tokens": 0,
            "compactions": 0, "scheduled_fires": 0, "tools": Counter(), "tool_errors": 0,
            "bash": Counter(), "prompts": [],
            "subagent": {"files": 0, "api_calls": 0, "tokens": 0, "peak_ctx": 0},
        })

    for f in files:
        is_sub = "subagents" in f.parts
        parent = f.parent.parent.name if is_sub else f.stem
        s = slot(parent)
        calls: dict[str, tuple[datetime, dict, str]] = {}
        if is_sub:
            s["subagent"]["files"] += 1
        try:
            fh = open(f, errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = e.get("type")
                if kind == "custom-title" and not is_sub:
                    s["name"] = e.get("customTitle") or e.get("title") or s["name"]
                elif kind == "agent-name" and not is_sub and not s["name"]:
                    s["name"] = e.get("agentName") or e.get("name") or ""
                t = ts(e.get("timestamp", ""))
                if not t or t < start or t > end:
                    continue
                if e.get("cwd") and not s["project"]:
                    s["project"] = project_of(e["cwd"])
                if kind == "system":
                    sub = e.get("subtype")
                    if sub == "compact_boundary":
                        s["compactions"] += 1
                    elif sub == "scheduled_task_fire":
                        s["scheduled_fires"] += 1
                    continue
                msg = e.get("message") or {}
                if kind == "user" and not is_sub:
                    content = msg.get("content")
                    if isinstance(content, str) and not content.startswith("<"):
                        s["user_prompts"] += 1
                        if len(s["prompts"]) < 4:
                            s["prompts"].append(mask(content, 90))
                    elif isinstance(content, list):
                        for part in content:
                            if part.get("type") == "tool_result" and part.get("is_error"):
                                s["tool_errors"] += 1
                            elif part.get("type") == "text" and not is_sub:
                                txt = part.get("text", "")
                                if txt and not txt.startswith("<"):
                                    s["user_prompts"] += 1
                                    if len(s["prompts"]) < 4:
                                        s["prompts"].append(mask(txt, 90))
                    continue
                if kind != "assistant":
                    continue
                for part in msg.get("content") or []:
                    if isinstance(part, dict) and part.get("type") == "tool_use":
                        name = part.get("name", "?")
                        s["tools"][name] += 1
                        if name == "Bash":
                            cmd = (part.get("input") or {}).get("command", "")
                            s["bash"][mask(cmd.splitlines()[0] if cmd else "", 100)] += 1
                usage = msg.get("usage")
                if usage:
                    key = msg.get("id") or e.get("requestId") or e.get("uuid")
                    calls[key] = (t, usage, msg.get("model", ""))
        ordered = sorted(calls.values(), key=lambda x: x[0])
        prev_t = None
        for t, u, model in ordered:
            inp = u.get("input_tokens") or 0
            cw = u.get("cache_creation_input_tokens") or 0
            cr = u.get("cache_read_input_tokens") or 0
            out = u.get("output_tokens") or 0
            ctx = inp + cw + cr
            if is_sub:
                sa = s["subagent"]
                sa["api_calls"] += 1
                sa["tokens"] += ctx + out
                sa["peak_ctx"] = max(sa["peak_ctx"], ctx)
            else:
                s["api_calls"] += 1
                s["ctx"].append(ctx)
                if model:
                    s["models"][model] += 1
                if prev_t and (t - prev_t).total_seconds() > GAP_REBUILD_MIN * 60 and cw > 50_000:
                    s["rebuilds"] += 1
                    s["rebuild_tokens"] += cw
            s["tokens"]["input"] += inp
            s["tokens"]["cache_write"] += cw
            s["tokens"]["cache_read"] += cr
            s["tokens"]["output"] += out
            s["first"] = min(filter(None, [s["first"], t]))
            s["last"] = max(filter(None, [s["last"], t]))
            prev_t = t

    result = []
    for sid, s in sessions.items():
        total = sum(s["tokens"].values())
        if total == 0:
            continue
        ctx = s["ctx"]
        cw, cr = s["tokens"]["cache_write"], s["tokens"]["cache_read"]
        result.append({
            "session": s["session"], "name": s["name"], "project": s["project"],
            "models": dict(s["models"]),
            "first": s["first"].astimezone().strftime("%m-%d %H:%M") if s["first"] else "",
            "last": s["last"].astimezone().strftime("%m-%d %H:%M") if s["last"] else "",
            "api_calls": s["api_calls"], "user_prompts": s["user_prompts"],
            "calls_per_prompt": round(s["api_calls"] / s["user_prompts"], 1) if s["user_prompts"] else None,
            "tokens": dict(s["tokens"]), "tokens_total": total,
            "peak_context": max(ctx) if ctx else 0,
            "avg_context": int(sum(ctx) / len(ctx)) if ctx else 0,
            f"calls_over_{BIG_CTX[0] // 1000}k": sum(c > BIG_CTX[0] for c in ctx),
            f"calls_over_{BIG_CTX[1] // 1000}k": sum(c > BIG_CTX[1] for c in ctx),
            "cache_write_share": round(cw / (cw + cr), 3) if cw + cr else 0,
            "cache_rebuilds_after_idle_1h": s["rebuilds"], "rebuild_tokens": s["rebuild_tokens"],
            "compactions": s["compactions"], "scheduled_fires": s["scheduled_fires"],
            "tool_errors": s["tool_errors"], "top_tools": dict(s["tools"].most_common(8)),
            "repeated_bash": [{"cmd": c, "n": n} for c, n in s["bash"].most_common(5) if n >= 5],
            "subagent": s["subagent"], "prompt_snippets": s["prompts"],
        })
    return sorted(result, key=lambda r: -r["tokens_total"])


def codex_sessions(start: datetime, end: datetime, roots: list[Path] = CODEX_DIRS) -> list[dict]:
    out = []
    for root in roots:
        if not root.is_dir():
            continue
        for f in root.rglob("*.jsonl"):
            if datetime.fromtimestamp(f.stat().st_mtime, timezone.utc) < start:
                continue
            cwd, model, prev, tools = "", "", {}, 0
            agg = Counter()
            requests = 0
            with open(f, errors="replace") as fh:
                for line in fh:
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    p = e.get("payload") or {}
                    kind = e.get("type")
                    if kind in ("session_meta", "turn_context"):
                        cwd = p.get("cwd") or cwd
                        model = p.get("model") or model
                        continue
                    t = ts(e.get("timestamp", ""))
                    if kind == "event_msg" and p.get("type") == "token_count":
                        total = (p.get("info") or {}).get("total_token_usage")
                        if not total:
                            continue
                        delta = {k: max(0, (total.get(k) or 0) - (prev.get(k) or 0)) for k in total}
                        prev = total
                        if t and start <= t <= end:
                            requests += 1
                            agg["input"] += delta.get("input_tokens", 0)
                            agg["cached"] += delta.get("cached_input_tokens", 0)
                            agg["output"] += delta.get("output_tokens", 0)
                    elif kind == "response_item" and t and start <= t <= end and \
                            p.get("type") in ("function_call", "custom_tool_call", "local_shell_call"):
                        tools += 1
            if requests:
                out.append({"file": f.stem[-12:], "home": root.parent.name, "project": project_of(cwd) if cwd else "",
                            "model": model, "requests": requests, "tool_calls": tools,
                            "input_tokens_incl_cached": agg["input"], "cached_input_tokens": agg["cached"],
                            "output_tokens": agg["output"]})
    return sorted(out, key=lambda r: -r["input_tokens_incl_cached"])


def code_runs(start: datetime, end: datetime, root: Path = CODE_RUNS) -> list[dict]:
    out = []
    if not root.is_dir():
        return out
    for d in root.iterdir():
        try:
            started = datetime.strptime(d.name[:15], "%Y%m%d-%H%M%S").astimezone()
        except ValueError:
            continue
        if not (start <= started <= end):
            continue
        sj = d / "summary.json"
        row = {"run": d.name, "started": started.strftime("%m-%d %H:%M")}
        if sj.exists():
            try:
                s = json.loads(sj.read_text())
            except json.JSONDecodeError:
                s = {}
            u = s.get("usage") or {}
            row.update(executor=s.get("executor"), exit=s.get("exit"), seconds=s.get("seconds"),
                       input_tokens_incl_cached=u.get("input_tokens"), cached_input_tokens=u.get("cached_input_tokens"),
                       output_tokens=u.get("output_tokens"), attempts=s.get("attempts"),
                       stalls=len(s.get("stalls") or []), error=mask(s.get("error") or "", 160),
                       changed_files=len(s.get("changed") or []))
        else:
            row["status"] = "running or no summary"
        out.append(row)
    return sorted(out, key=lambda r: r["run"])


def main() -> None:
    start = datetime.fromisoformat(sys.argv[1]).astimezone()
    end = datetime.fromisoformat(sys.argv[2]).astimezone()
    data = {
        "window": [start.isoformat(timespec="minutes"), end.isoformat(timespec="minutes")],
        "generated_at": datetime.now().astimezone().isoformat(timespec="minutes"),
        "claude_sessions": claude_sessions(start, end),
        "codex_sessions": codex_sessions(start, end),
        "code_runs": code_runs(start, end),
    }
    json.dump(data, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
