#!/usr/bin/env python3
"""Compare Claude weekly quota readings with local session usage."""

import argparse
import importlib.util
import json
import math
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[4] / "platform/monitoring/usage/quota_attribution.py"
SPEC = importlib.util.spec_from_file_location("quota_attribution", MODULE_PATH)
attribution = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(attribution)

WEEK = 7 * 86400
WEIGHTS = (1, 1.25, 0.1, 5)
TOKEN_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
WEEKDAYS = "一二三四五六日"


def local_time(epoch):
    date = datetime.fromtimestamp(epoch).astimezone()
    return f"{date:%m/%d}（{WEEKDAYS[date.weekday()]}）{date:%H:%M}"


def millions(value):
    return f"{value / 1_000_000:.1f}M"


def load_readings(path):
    """Return valid weekly readings in file order."""
    readings = []
    raw_rows = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            try:
                row = json.loads(line)
                weekly = row["limits"]["seven_day"]
                reading = {
                    "ts": float(row["ts"]), "account_id": str(row["account_id"]),
                    "label": str(row.get("label") or row["account_id"]),
                    "reset": float(weekly["resets_at"]),
                    "used": float(weekly["used_percentage"]),
                }
                if all(math.isfinite(reading[key]) for key in ("ts", "reset", "used")):
                    raw_rows.append(row)
            except (ValueError, TypeError, KeyError, AttributeError):
                continue
    for row in attribution.attribute_rows(raw_rows):
        weekly = row["limits"]["seven_day"]
        readings.append({"ts": float(row["ts"]), "account_id": str(row["account_id"]),
                         "label": str(row.get("label") or row["account_id"]),
                         "reset": float(weekly["resets_at"]),
                         "used": float(weekly["used_percentage"]),
                         "relabeled": row.get("relabeled", False),
                         "ambiguous": row.get("ambiguous", False)})
    return readings


def load_map(path):
    try:
        with path.open(encoding="utf-8") as source:
            data = json.load(source)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def build_windows(readings, account, weeks, now):
    """Group readings by reset, retaining off-cycle overlaps.

    Keep each window that started in the last `weeks` weeks. An off-cycle window does
    not push a regular window out of the report. An account resets at one fixed time of
    the week; a window with another reset time that overlaps a window is off-cycle and
    gets the overlap mark.
    """
    grouped = defaultdict(list)
    for row in readings:
        if row["account_id"] == account and row["reset"] - WEEK <= now:
            grouped[row["reset"]].append(row)
    windows = []
    for reset, rows in grouped.items():
        start = reset - WEEK
        rows = sorted((row for row in rows if start <= row["ts"] <= min(reset, now)),
                      key=lambda row: row["ts"])
        if not rows:
            continue
        high = 0.0
        hit = None
        for row in rows:
            high = max(high, row["used"])
            if hit is None and high >= 100:
                hit = row["ts"]
        windows.append({"start": start, "reset": reset, "rows": rows,
                        "high": high, "hit": hit, "overlap": False})
    windows.sort(key=lambda window: window["start"])
    usual = usual_phase(window_row for window in windows for window_row in window["rows"])
    for window in windows:
        window["overlap"] = window["reset"] % WEEK != usual and any(
            other is not window and other["start"] < window["reset"] and window["start"] < other["reset"]
            for other in windows)
    recent = [window for window in windows if window["start"] >= now - weeks * WEEK]
    return list(reversed(recent or windows[-1:]))


def usual_phase(rows):
    """Return the most common reset time of the week (seconds into the week)."""
    phases = Counter(int(row["reset"]) % WEEK for row in rows)
    return phases.most_common(1)[0][0] if phases else None


def weighted(usage):
    try:
        return sum(float(usage.get(key, 0) or 0) * weight
                   for key, weight in zip(TOKEN_KEYS, WEIGHTS))
    except (ValueError, TypeError, AttributeError):
        return 0.0


def parse_timestamp(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError, AttributeError):
        return None


def project_name(name):
    return re.sub(r"^-Users-[^-]+-", "", name)


def load_usage(root, readings, account, first_start):
    """Load main and subagent records under their parent session."""
    events, sessions, seen = [], {}, set()
    if not root.is_dir():
        return events, sessions
    active_at = attribution.active_account_index(readings)
    for project in root.iterdir():
        if not project.is_dir():
            continue
        files = list(project.glob("*.jsonl")) + list(project.glob("*/subagents/*.jsonl"))
        for path in files:
            try:
                if path.stat().st_mtime < first_start:
                    continue
            except OSError:
                continue
            session = path.stem if path.parent == project else path.parent.parent.name
            meta = sessions.setdefault(session, {"project": project_name(project.name),
                                                 "title": None, "unmapped": False})
            try:
                with path.open(encoding="utf-8") as source:
                    for line in source:
                        if '"custom-title"' in line:
                            try:
                                row = json.loads(line)
                                if row.get("type") == "custom-title":
                                    meta["title"] = row.get("customTitle") or meta["title"]
                            except (ValueError, AttributeError):
                                pass
                        if '"usage"' not in line:
                            continue
                        try:
                            row = json.loads(line)
                            message = row["message"]
                            usage = message["usage"]
                            stamp = parse_timestamp(row.get("timestamp"))
                            key = (message["id"], row["requestId"])
                            if stamp is None or stamp < first_start or key in seen:
                                continue
                            active = active_at(stamp)
                            if active != account:
                                continue
                            amount = weighted(usage)
                            if amount <= 0:
                                continue
                            seen.add(key)
                            events.append({"ts": stamp, "session": session,
                                           "model": str(message.get("model") or "未知"),
                                           "tokens": amount, "unmapped": meta["unmapped"]})
                        except (ValueError, TypeError, KeyError, AttributeError):
                            continue
            except OSError:
                continue
    return events, sessions


def quota_at(rows, at):
    return max((row["used"] for row in rows if row["ts"] <= at), default=0.0)


def build_slots(window, events, slot_hours, now):
    slots = []
    width = slot_hours * 3600
    end = min(window["reset"], now)
    at = window["start"]
    while at < end:
        stop = min(at + width, end)
        local = sum(event["tokens"] for event in events if at <= event["ts"] < stop)
        slots.append({"start": at, "end": stop,
                      "delta": max(0.0, quota_at(window["rows"], stop) - quota_at(window["rows"], at)),
                      "local": local})
        at = stop
    return slots


def tokens_per_percent(windows):
    samples = [slot["local"] / slot["delta"] for window in windows for slot in window["slots"]
               if slot["local"] >= 10_000_000 and slot["delta"] >= 2]
    return (statistics.median(samples) if len(samples) >= 3 else None, len(samples))


def assess_slots(slots, ratio):
    for slot in slots:
        slot["explained"] = min(slot["delta"], slot["local"] / ratio) if ratio else None
        slot["flagged"] = ratio is not None and slot["delta"] >= 3 and slot["explained"] < slot["delta"] / 2


def session_totals(events, start, end):
    totals = defaultdict(float)
    models = defaultdict(lambda: defaultdict(float))
    for event in events:
        if start <= event["ts"] < end:
            totals[event["session"]] += event["tokens"]
            models[event["session"]][event["model"]] += event["tokens"]
    return totals, models


def burst_period(window, now):
    end = min(window["reset"], now)
    starts = [slot["start"] for slot in window["slots"]]
    if not starts:
        return window["start"], end, 0.0
    candidates = [(start, min(start + 12 * 3600, end)) for start in starts]
    start, stop = max(candidates, key=lambda pair: quota_at(window["rows"], pair[1])
                      - quota_at(window["rows"], pair[0]))
    return start, stop, max(0.0, quota_at(window["rows"], stop) - quota_at(window["rows"], start))


def session_lines(events, sessions, start, end, limit):
    totals, models = session_totals(events, start, end)
    overall = sum(totals.values())
    lines = []
    for session, amount in sorted(totals.items(), key=lambda item: -item[1])[:limit]:
        meta = sessions[session]
        name = str(meta["title"] or session[:8]).replace("|", "\\|").replace("\n", " ")
        model = max(models[session], key=models[session].get)
        lines.append(f"| {meta['project']} | {name} | {millions(amount)} | "
                     f"{amount / overall:.0%} | {model} |")
    return lines or ["| — | — | 0.0M | — | — |"]


def render(readings, windows, events, sessions, label, ratio, sample_count, now):
    out = [f"# Claude 額度診斷 — {label}",
           f"- 資料來源：這台的額度紀錄 {len(readings)} 筆、這台的對話紀錄。另一台電腦和網頁版的用量看不到，只能從額度的變化推。",
           "- 用量單位是加權 token（輸入 1、寫快取 1.25、讀快取 0.1、輸出 5，照 API 價格比估計）。"]
    if ratio:
        out.append(f"- 每 1% 額度約等於這台 {millions(ratio)} 加權 token（從 {sample_count} 個時段估計）。")
    else:
        out.append(f"- 每 1% 額度：未判讀；符合這台用量至少 10M 且額度增加至少 2% 的時段只有 {sample_count} 個，少於 3 個。")
    out.extend(["", "## 各週一覽", "| 週期 | 最高 | 到 100% 的時間 | 撐了幾天 | 這台用量 | 這台解釋得了 | 其他來源（推估） |",
                "| --- | ---: | --- | ---: | ---: | ---: | ---: |"])
    details = []
    for window in windows:
        start, reset = window["start"], window["reset"]
        local = sum(slot["local"] for slot in window["slots"])
        explained = sum(slot["explained"] for slot in window["slots"]) if ratio else None
        other = sum(slot["delta"] - slot["explained"] for slot in window["slots"] if slot["flagged"]) if ratio else None
        hit = window["hit"]
        days = (hit if hit is not None else min(reset, now)) - start
        name = f"{local_time(start)}–{local_time(reset)}"
        if reset > now:
            name += "（進行中）"
        if window["overlap"]:
            name += "（和另一個週期重疊）"
        explained_text = f"{explained:.1f}%" if ratio else "未判讀"
        other_text = f"{other:.1f}%" if ratio else "未判讀"
        out.append(f"| {name} | {window['high']:.1f}% | {local_time(hit) if hit else '未達 100%'} | "
                   f"{days / 86400:.1f} | {millions(local)} | {explained_text} | {other_text} |")
        period_events = [event for event in events if start <= event["ts"] < min(reset, now)]
        unmapped = sum(event["tokens"] for event in period_events if event["unmapped"])
        burst_start, burst_end, burst_rise = burst_period(window, now)
        if hit:
            sentences = [f"第 {days / 86400:.1f} 天就用完。"]
        elif reset <= now:
            sentences = [f"整週最高 {window['high']:.1f}%，到重置都沒用完。"]
        else:
            sentences = [f"目前最高使用 {window['high']:.1f}%，已經過 {days / 86400:.1f} 天。"]

        if ratio and other >= 5:
            sentences.append(f"約 {other:.1f}% 的額度是在這台用量不足以解釋的時段扣掉，可能來自另一台電腦或網頁版。")
        elif ratio:
            sentences.append("額度的增加大致對得上這台的用量。")
        else:
            sentences.append("可用時段不足，其他來源占比未判讀。")
        sentences.append(f"額度增加最快的 12 小時用掉 {burst_rise:.1f}%。")
        sentences.append(f"未對應帳號的 session 佔這台用量的 {unmapped / local:.0%}。" if local else "這台在此週期沒有可用的 session 紀錄。")
        attribution_lines = []
        relabeled = sum(bool(row["relabeled"]) for row in window["rows"])
        if relabeled:
            attribution_lines.append(f"有 {relabeled} 筆原本記在別的帳號，依週期改算到這個帳號")
        if any(row["ambiguous"] for row in window["rows"]):
            attribution_lines.append("這個週期有兩個帳號同一個重置時間，無法分開")
        details.extend(["", f"## {name}", *attribution_lines, "### 判讀", "".join(sentences), "", "### 額度跳最快的時段（前 5）",
                    "| 時段 | 額度 +% | 這台用量 | 這台解釋得了 | 標記 |",
                    "| --- | ---: | ---: | ---: | --- |"])
        for slot in sorted(window["slots"], key=lambda item: -item["delta"])[:5]:
            explained_text = f"{slot['explained']:.1f}%" if ratio else "未判讀"
            marker = "其他來源可能" if slot["flagged"] else "—"
            details.append(f"| {local_time(slot['start'])}–{local_time(slot['end'])} | {slot['delta']:.1f}% | "
                       f"{millions(slot['local'])} | {explained_text} | {marker} |")
        details.extend(["", "### 這台用最多的 session（前 8）", "| 專案 | session | 用量 | 佔比 | 主要模型 |",
                    "| --- | --- | ---: | ---: | --- |"])
        details.extend(session_lines(events, sessions, start, min(reset, now), 8))
        details.extend(["", f"### 12 小時內用最多（{local_time(burst_start)}–{local_time(burst_end)}，額度 +{burst_rise:.1f}%）",
                    "| 專案 | session | 用量 | 佔比 | 主要模型 |", "| --- | --- | ---: | ---: | --- |"])
        details.extend(session_lines(events, sessions, burst_start, burst_end, 5))
        models = defaultdict(float)
        for event in period_events:
            models[event["model"]] += event["tokens"]
        details.extend(["", "### 模型比例", "| 模型 | 這台用量 | 佔比 |", "| --- | ---: | ---: |"])
        for model, amount in sorted(models.items(), key=lambda item: -item[1]):
            details.append(f"| {model} | {millions(amount)} | {amount / local:.0%} |")
        if not models:
            details.append("| — | 0.0M | — |")
    return "\n".join(out + details) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Diagnose Claude weekly quota usage")
    parser.add_argument("--account")
    parser.add_argument("--weeks", type=int, default=3)
    parser.add_argument("--slot-hours", type=float, default=6)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--quota-log", type=Path, default=Path("~/.claude/usage-quota/claude-rate-limits.jsonl"))
    parser.add_argument("--sessions-map", type=Path, default=Path("~/.claude/usage-quota/.sessions-claude.json"),
                        help="保留舊指令相容性，已不再使用")
    parser.add_argument("--projects-root", type=Path, default=Path("~/.claude/projects"))
    parser.add_argument("--now", type=float, default=None)
    args = parser.parse_args(argv)
    if args.weeks < 1 or args.slot_hours <= 0:
        parser.error("--weeks 與 --slot-hours 必須大於 0")
    now = args.now if args.now is not None else time.time()
    try:
        readings = load_readings(args.quota_log.expanduser())
    except OSError:
        print("找不到額度紀錄檔。", file=sys.stderr)
        return 1
    if not readings:
        print("額度紀錄沒有可用的 seven_day 資料。", file=sys.stderr)
        return 1
    newest = max(readings, key=lambda row: row["ts"])
    account = next((row["account_id"] for row in sorted(readings, key=lambda row: row["ts"], reverse=True)
                    if args.account in (row["account_id"], row["label"])), None) if args.account else newest["account_id"]
    selected = [row for row in readings if row["account_id"] == account]
    windows = build_windows(selected, account, args.weeks, now)
    if not windows:
        print("此帳號沒有可用的 seven_day 週期。", file=sys.stderr)
        return 1
    events, sessions = load_usage(args.projects_root.expanduser(), readings,
                                  account, min(window["start"] for window in windows))
    for window in windows:
        window["slots"] = build_slots(window, events, args.slot_hours, now)
    ratio, count = tokens_per_percent(windows)
    for window in windows:
        assess_slots(window["slots"], ratio)
    label = max(selected, key=lambda row: row["ts"])["label"]
    report = render(selected, windows, events, sessions, label, ratio, count, now)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
