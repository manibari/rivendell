"""Inspect macOS JetsamEvent reports for process and memory growth."""

import argparse
from collections import Counter, defaultdict
import ctypes
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import subprocess
import sys


REPORT_DIR = Path("/Library/Logs/DiagnosticReports")
GB = 1024 ** 3
FALLBACK_TIMEBASE = (125, 3)


def mach_timebase():
    """Return the mach absolute time numerator and denominator."""
    try:
        class TimebaseInfo(ctypes.Structure):
            _fields_ = [("numer", ctypes.c_uint32), ("denom", ctypes.c_uint32)]

        info = TimebaseInfo()
        system = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
        if system.mach_timebase_info(ctypes.byref(info)) == 0 and info.denom:
            return info.numer, info.denom
    except (AttributeError, OSError):
        pass
    return FALLBACK_TIMEBASE


def age_seconds(ticks, timebase):
    numer, denom = timebase
    return int(ticks) * numer / denom / 1_000_000_000


def parse_report(path):
    with Path(path).open(encoding="utf-8") as stream:
        header = json.loads(stream.readline())
        body = json.load(stream)
    report_time = datetime.strptime(header["timestamp"], "%Y-%m-%d %H:%M:%S.%f %z")
    if not isinstance(body["processes"], list):
        raise ValueError("processes must be a list")
    return {"path": str(path), "time": report_time, "header": header, "body": body}


def boot_time():
    try:
        output = subprocess.check_output(
            ["sysctl", "-n", "kern.boottime"], text=True, stderr=subprocess.DEVNULL
        )
        match = re.search(r"sec\s*=\s*(\d+),\s*usec\s*=\s*(\d+)", output)
        if match:
            return datetime.fromtimestamp(
                int(match.group(1)) + int(match.group(2)) / 1_000_000
            ).astimezone()
    except (OSError, subprocess.CalledProcessError):
        pass
    return None


def report_paths(roots):
    paths = set()
    for root in roots:
        paths.update(Path(root).glob("JetsamEvent-*.ips"))
    return sorted(paths)


def load_reports(paths):
    reports = []
    for path in paths:
        try:
            reports.append(parse_report(path))
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
            print(f"無法讀取報告 {path}：{error}", file=sys.stderr)
    return sorted(reports, key=lambda report: (report["time"], report["path"]))


def compressed_pages(process):
    internal = process.get("physicalPages", {}).get("internal", [])
    return internal[1] if len(internal) > 1 else 0


def groups(processes, page_size):
    by_name = defaultdict(lambda: {"count": 0, "resident_gb": 0.0, "compressed_gb": 0.0})
    for process in processes:
        group = by_name[process.get("name", "未知")]
        group["count"] += 1
        group["resident_gb"] += process.get("rpages", 0) * page_size / GB
        group["compressed_gb"] += compressed_pages(process) * page_size / GB
    return [
        {"name": name, **values}
        for name, values in sorted(by_name.items(), key=lambda item: (-item[1]["count"], item[0]))
    ]


def killed_counts(processes):
    return dict(sorted(Counter(p["reason"] for p in processes if p.get("reason")).items()))


def growth(processes, previous):
    if previous is None:
        return None
    current_counts = Counter(p.get("name", "未知") for p in processes)
    old_counts = Counter(p.get("name", "未知") for p in previous["body"]["processes"])
    return [
        {"name": name, "old": old_counts[name], "new": count, "increase": count - old_counts[name]}
        for name, count in sorted(
            current_counts.items(), key=lambda item: (-(item[1] - old_counts[item[0]]), item[0])
        )
        if count > old_counts[name]
    ]


def burst(starts):
    """Return the run of consecutive minutes around the busiest minute.

    A name can have a few old processes (days or weeks old) next to a fast
    spawn loop. The overall first start and average rate then hide the loop.
    The run grows while each next minute has at least a tenth of the peak.
    """
    per_minute = Counter(start.replace(second=0, microsecond=0) for start in starts)
    if not per_minute:
        return None
    peak_minute, peak = max(per_minute.items(), key=lambda item: (item[1], item[0]))
    if peak < 3:
        return None
    floor = max(2, peak // 10)
    step = timedelta(minutes=1)
    first = last = peak_minute
    while per_minute.get(first - step, 0) >= floor:
        first -= step
    while per_minute.get(last + step, 0) >= floor:
        last += step
    inside = [s for s in starts if first <= s.replace(second=0, microsecond=0) <= last]
    span = (inside[-1] - inside[0]).total_seconds()
    return {
        "first_start": inside[0].isoformat(),
        "last_start": inside[-1].isoformat(),
        "count": len(inside),
        "per_second": len(inside) / span if span else 0.0,
    }


def start_profile(name, processes, report_time, timebase):
    selected = [p for p in processes if p.get("name", "未知") == name]
    starts = sorted(
        report_time - timedelta(seconds=age_seconds(p.get("age", 0), timebase))
        for p in selected
    )
    minutes = Counter(start.strftime("%Y-%m-%d %H:%M") for start in starts)
    duration = (starts[-1] - starts[0]).total_seconds() if len(starts) > 1 else 0
    coalitions = []
    for coalition, count in sorted(Counter(p.get("coalition") for p in selected).items(),
                                   key=lambda item: (-item[1], str(item[0]))):
        neighbours = Counter(
            p.get("name", "未知") for p in processes
            if p.get("coalition") == coalition and p.get("name", "未知") != name
        )
        coalitions.append({
            "coalition": coalition,
            "count": count,
            "other_names": [
                {"name": other, "count": total}
                for other, total in sorted(neighbours.items(), key=lambda item: (-item[1], item[0]))[:5]
            ],
        })
    return {
        "name": name,
        "first_start": starts[0].isoformat(),
        "last_start": starts[-1].isoformat(),
        "starts_per_minute": dict(sorted(minutes.items())),
        "average_per_second": len(starts) / duration if duration else 0.0,
        "count": len(starts),
        "burst": burst(starts),
        "coalitions": coalitions,
    }


def boot_mark(report_time, current_boot):
    if current_boot is None:
        return None
    gap = (current_boot - report_time).total_seconds()
    return int((gap + 30) // 60) if 0 <= gap < 1800 else None


def summarize(report, current_boot):
    processes = report["body"]["processes"]
    memory = report["body"].get("memoryStatus", {})
    page_size = memory.get("pageSize", 16384)
    counts = Counter(p.get("name", "未知") for p in processes)
    most_name, most_count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0] if counts else (None, 0)
    return {
        "path": report["path"],
        "time": report["time"].isoformat(),
        "process_count": len(processes),
        "most_frequent": {"name": most_name, "count": most_count},
        "compressor_holds_gb": memory.get("uncompressed", 0) * page_size / GB,
        "wired_gb": memory.get("memoryPages", {}).get("wired", 0) * page_size / GB,
        "killed_count": sum(killed_counts(processes).values()),
        "minutes_before_boot": boot_mark(report["time"], current_boot),
    }


def detail(report, previous, timebase):
    body = report["body"]
    processes = body["processes"]
    memory = body.get("memoryStatus", {})
    pages = memory.get("memoryPages", {})
    page_size = memory.get("pageSize", 16384)
    increases = growth(processes, previous)
    return {
        "path": report["path"],
        "time": report["time"].isoformat(),
        "largest_process": body.get("largestProcess"),
        "memory_gb": {
            "wired": pages.get("wired", 0) * page_size / GB,
            "free": pages.get("free", 0) * page_size / GB,
            "compressor_size": memory.get("compressorSize", 0) * page_size / GB,
            "compressor_holds": memory.get("uncompressed", 0) * page_size / GB,
        },
        "top_names": groups(processes, page_size)[:10],
        "growth": increases,
        "multiplied": start_profile(increases[0]["name"], processes, report["time"], timebase)
        if increases else None,
        "killed_by_reason": killed_counts(processes),
    }


def inspect(paths, selected_path=None, limit=10, current_boot=None, timebase=None):
    reports = load_reports(paths)
    if not reports:
        return None
    marked = [r for r in reports if boot_mark(r["time"], current_boot) is not None]
    marked_report = marked[-1] if marked else None
    overview = [
        summarize(report, current_boot if report is marked_report else None)
        for report in reports[-limit:]
    ]
    chosen = next((r for r in reports if Path(r["path"]) == Path(selected_path)), None) if selected_path else None
    if chosen is None:
        chosen = marked_report or reports[-1]
    position = reports.index(chosen)
    previous = reports[position - 1] if position else None
    return {"overview": overview, "detail": detail(chosen, previous, timebase or mach_timebase())}


def render(data):
    lines = ["JetsamEvent 記憶體報告", "時間                 行程數  最多的行程（數量）  壓縮區裝了 GB  wired GB  被終止數"]
    for item in data["overview"]:
        mark = f"  開機前 {item['minutes_before_boot']} 分鐘" if item["minutes_before_boot"] is not None else ""
        frequent = item["most_frequent"]
        lines.append(
            f"{item['time'][:19]}  {item['process_count']}  {frequent['name']} ({frequent['count']})"
            f"  {item['compressor_holds_gb']:.1f}  {item['wired_gb']:.1f}  {item['killed_count']}{mark}"
        )
    item = data["detail"]
    mem = item["memory_gb"]
    lines.extend([
        f"\n詳細報告：{item['path']}",
        f"時間：{item['time']}",
        f"記憶體 GB：wired {mem['wired']:.1f}、可用 {mem['free']:.1f}、"
        f"壓縮區大小 {mem['compressor_size']:.1f}、壓縮區裝了 {mem['compressor_holds']:.1f}",
        "前 10 種行程：名稱、數量、常駐 GB、壓縮 GB",
    ])
    for group in item["top_names"]:
        lines.append(f"  {group['name']}：{group['count']}、{group['resident_gb']:.1f}、{group['compressed_gb']:.1f}")
    lines.append("和前一份報告相比增加的行程：")
    if item["growth"] is None:
        lines.append("  沒有更早的報告可供比較")
    elif not item["growth"]:
        lines.append("  沒有增加的行程名稱")
    else:
        for entry in item["growth"][:10]:
            lines.append(f"  {entry['name']}：{entry['old']} → {entry['new']}（增加 {entry['increase']}）")
    profile = item["multiplied"]
    if profile:
        lines.append(f"增加最多：{profile['name']}")
        spike = profile["burst"]
        if spike:
            lines.append(
                f"集中啟動：{spike['first_start'][:19].replace('T', ' ')} 到 "
                f"{spike['last_start'][11:19]}，共 {spike['count']} 個，平均每秒 {spike['per_second']:.1f} 個"
            )
        else:
            lines.append("集中啟動：沒有明顯的集中啟動")
        lines.extend([
            f"這個名稱全部 {profile['count']} 個：最早 {profile['first_start'][:19].replace('T', ' ')}、"
            f"最後 {profile['last_start'][:19].replace('T', ' ')}",
            "每分鐘啟動數：",
        ])
        for minute, count in profile["starts_per_minute"].items():
            lines.append(f"  {minute}：{count}")
        lines.append("所屬 coalition（同一個母程式底下）與其中其他行程：")
        for coalition in profile["coalitions"]:
            others = "、".join(f"{p['name']} ({p['count']})" for p in coalition["other_names"])
            lines.append(f"  {coalition['coalition']}：{coalition['count']}；{others or '無'}")
    lines.append("被系統終止的行程（依原因）：")
    if item["killed_by_reason"]:
        for reason, count in item["killed_by_reason"].items():
            lines.append(f"  {reason}：{count}")
    else:
        lines.append("  無")
    return "\n".join(lines)


def main(argv=None, roots=None, current_boot=None, timebase=None):
    class ChineseParser(argparse.ArgumentParser):
        def format_help(self):
            return (
                "用法：jetsam.py [--file PATH] [--json] [--limit N] [--help]\n"
                "檢查 JetsamEvent 記憶體報告\n\n"
                "  --file PATH  指定詳細報告\n"
                "  --json       輸出 JSON\n"
                "  --limit N    總覽報告筆數（預設 10）\n"
                "  --help       顯示說明\n"
            )

        def error(self, message):
            self.exit(2, f"參數錯誤：{message}\n{self.format_help()}")

    parser = ChineseParser(description="檢查 JetsamEvent 記憶體報告")
    parser.add_argument("--file", type=Path, help="指定詳細報告")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    parser.add_argument("--limit", type=int, default=10, help="總覽報告筆數")
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit 必須大於零")
    if roots is None:
        root = args.file.parent if args.file else REPORT_DIR
        roots = [root, root / "Retired"]
        if args.file and root.name == "Retired":
            roots.append(root.parent)
    paths = report_paths(roots)
    if args.file:
        paths = sorted(set(paths) | {args.file})
    data = inspect(paths, args.file, args.limit, current_boot or boot_time(), timebase)
    if data is None:
        print("找不到 JetsamEvent 記憶體報告（未判讀）")
        return 2
    print(json.dumps(data, ensure_ascii=False) if args.json else render(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
