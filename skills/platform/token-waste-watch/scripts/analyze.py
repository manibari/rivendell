"""Send one snapshot to Gemini, get the suspected-waste report, write it with a raw-number appendix.

Usage: python3 -I analyze.py <snapshot.json> <report.md>
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gateway  # noqa: E402

INSTRUCTIONS = """你是 token 用量稽核員。輸入是一段時間內本機每個 AI 工作 session 的用量數字（JSON）。
你的工作：找出「疑似浪費」，標記出來，寫成繁體中文報告。只根據數字判斷，你沒有讀過對話內容。

欄位說明：
- claude_sessions：Claude Code 互動 session。tokens 是 input／cache_write／cache_read／output；
  每次 API 呼叫都會把整段對話（context）重送一次，cache_read 就是重送的部分。
  avg_context／peak_context＝每次呼叫帶的 context 大小。calls_per_prompt＝每則使用者訊息平均觸發幾次呼叫。
  cache_rebuilds_after_idle_1h＝閒置超過一小時（快取過期）後回來、整段 context 重新寫入快取的次數，rebuild_tokens 是重寫的量。
  repeated_bash＝同一個指令開頭重複 5 次以上。scheduled_fires＝排程（/loop、cron）觸發次數。subagent＝子代理的用量。
- codex_sessions：Codex CLI 的 session；home 是 .codex（ChatGPT 訂閱額度）、.codex-gemini（公司 gateway）或 .codex-qwen。
  also_code_run=true 表示它就是 code_runs 裡的某次派工，不要重複計算。
- code_runs：Claude 派給 Codex／Gemini 的工作。exit≠0、attempts>1、stalls>0、error 非空代表失敗或重試。

疑似浪費的類型（每一項都要有數字證據，沒有證據就不要標）：
A. 長 context 硬撐：avg_context > 300k 且 api_calls ≥ 30。估計浪費＝(avg_context − 150k) × api_calls。建議 /compact 或交接後開新 session。
B. 閒置後重建快取：cache_rebuilds_after_idle_1h ≥ 1。估計浪費＝rebuild_tokens。
C. 重複指令或輪詢：repeated_bash 某指令 n ≥ 10，或 scheduled_fires 多但 user_prompts 很少。估計浪費＝n × avg_context（每次重複都重送一次 context）。
D. 工具錯誤重試：tool_errors ≥ 5。估計浪費＝tool_errors × avg_context。
E. 派工失敗或重試：code_runs 的 exit≠0、attempts>1 或 stalls>0。估計浪費＝失敗那次的 tokens（沒有數字就寫「未知」）。附上 error 原因。
F. 子代理帶大 context：subagent.peak_ctx > 200k。
G. 其他你從數字看得出的異常，要寫清楚依據。
自主長跑（calls_per_prompt 高）本身不算浪費，除非同時有 A–E 的證據。

規則：
- 一律寫「疑似」，不下定論。不猜對話內容，prompt_snippets 只用來說明這個 session 在做什麼。
- 數字用 M（百萬）或 k（千）表示，保留一位小數。
- 不要列出金鑰、帳密或 email。

報告格式（Markdown）：
## 結論
最多三行：今晚疑似浪費最多的是哪幾個 session、估計共浪費多少 tokens。

## 疑似浪費
| # | session（名稱／專案） | 類型 | 證據（數字） | 估計浪費 | 建議 |
依估計浪費由大到小排。

## 派工（Codex／Gemini）
失敗、重試、卡住的派工，各一行：派工名、原因、浪費多少。沒有就寫「無」。

## 沒有疑點的 session
一行列出 session 名稱即可。

## 判讀限制
兩三行：這份只看數字、估計的算法、哪些資料沒有（例如 Codex 互動 session 沒有對話內容）。
"""


def mark_overlap(data: dict) -> None:
    runs = {r.get("input_tokens_incl_cached") for r in data.get("code_runs", []) if r.get("input_tokens_incl_cached")}
    for s in data.get("codex_sessions", []):
        s["also_code_run"] = s.get("input_tokens_incl_cached") in runs


def appendix(data: dict) -> str:
    lines = ["## 附錄：原始數字（程式算的，不經 Gemini）", "",
             "| session | 名稱 | 專案 | 呼叫 | 訊息 | 總 tokens | 平均 context | 最大 context | 閒置重建 | 工具錯誤 | 重複最多的指令 |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in data["claude_sessions"]:
        rep = s["repeated_bash"][0] if s["repeated_bash"] else None
        rep_txt = f'{rep["n"]}× `{rep["cmd"][:40]}`' if rep else ""
        lines.append(f'| {s["session"]} | {s["name"] or ""} | {s["project"]} | {s["api_calls"]} | {s["user_prompts"]} '
                     f'| {s["tokens_total"] / 1e6:.1f}M | {s["avg_context"] // 1000}k | {s["peak_context"] // 1000}k '
                     f'| {s["cache_rebuilds_after_idle_1h"]} | {s["tool_errors"]} | {rep_txt} |')
    lines += ["", "| 派工 | 結果 | 秒 | 輸入 tokens | 重試 | 錯誤 |", "|---|---|---|---|---|---|"]
    for r in data["code_runs"]:
        if r.get("status"):
            lines.append(f'| {r["run"]} | 進行中 | | | | |')
            continue
        tok = r.get("input_tokens_incl_cached")
        lines.append(f'| {r["run"]} | exit {r.get("exit")} | {r.get("seconds")} | {f"{tok / 1e6:.1f}M" if tok else "未知"} '
                     f'| {r.get("attempts")} | {r.get("error") or ""} |')
    return "\n".join(lines)


def main() -> None:
    snap, report = Path(sys.argv[1]), Path(sys.argv[2])
    data = json.loads(snap.read_text())
    mark_overlap(data)
    head = (f"# 今晚 token 使用監控：疑似浪費\n\n"
            f"- 資料區間：{data['window'][0]} 到 {data['window'][1]}\n"
            f"- 產生時間：{datetime.now().astimezone().isoformat(timespec='minutes')}\n"
            f"- 判讀：Gemini（{gateway.MODEL}，經 Chimes GPT Gateway）；數字由本機程式從 session 紀錄算出\n\n")
    try:
        text, usage = gateway.ask(INSTRUCTIONS, json.dumps(data, ensure_ascii=False))
        body = text or "（Gemini 沒有回內容）"
        foot = f"\n\n_Gemini 本次用量：輸入 {usage.get('input_tokens')}、輸出 {usage.get('output_tokens')} tokens_\n"
    except Exception as e:  # report the failure; never switch to another model
        body = f"## 判讀失敗\n\nGemini 呼叫失敗：{e}\n\n下面附錄的數字仍然有效。"
        foot = "\n"
    tmp = report.with_suffix(".tmp")
    tmp.write_text(head + body + foot + "\n" + appendix(data) + "\n")
    tmp.replace(report)
    print(f"wrote {report}")


if __name__ == "__main__":
    main()
