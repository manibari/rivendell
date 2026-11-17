---
name: token-waste-watch
loop: platform
pdca: check
description: >
  Watch the token use of every AI work session on this machine for a time window
  (default: tonight) and get a report that marks suspected waste with numbers. A local
  script counts per-session facts from the session logs (Claude Code, Codex, code-run
  dispatches). Gemini on the Chimes GPT Gateway judges them, so the watch spends no
  Claude or Codex quota. It marks: a long context with no compact, a cache rebuild after
  one hour idle, a repeated command or polling, tool error retries, a failed or retried
  dispatch, a subagent with a large context. The report is updated every hour.
  TRIGGER when: "監控 token", "token 浪費報告", "疑似浪費", "哪個 session 在燒 token",
  "今晚各 session 的 token", "叫 google 監控", "叫 gemini 看 token", "token waste report",
  "watch token usage tonight".
  DO NOT TRIGGER when: quota percent or reset time (token-quota-log); one day's cost by
  project (dashboard /tokens, sk-token-analysis-cron); cutting this session's own
  context (context-journal).
tags: [meta, monitoring, tokens]
version: 1.0.0
---

# token-waste-watch

Many sessions spend tokens at the same time: interactive Claude sessions, Codex
dispatches, subagents. The dashboard shows how much each project spent. This skill
shows where the spend was probably wasted, with the numbers that show it.

Owner request 2026-11-18: 「叫 google 監控今天晚上各個 session 的 token 應用狀況」,
「要是有疑似浪費，標記起來變成報告」, then 「把這個功能變成一個 skills」.

## Procedure

1. **Check the gateway.** Run `python3 "${CLAUDE_SKILL_DIR}/scripts/gateway.py"`. It makes
   one small call and prints `'Ok.'`. If it fails, stop and tell the user the error. Do
   not use another model: the watch must not spend Claude or Codex quota, and a silent
   switch hides that cost. The key setup is in agent-code-dispatch ("Setup", gemini).
2. **Pick the window.** Default: 18:00 to 09:00 the next day. After midnight, "tonight"
   means yesterday 18:00 to today 09:00. Times that the user gives win.
3. **Start the watch in the background** (Bash `run_in_background`, not `&` or `nohup`):

   ```bash
   caffeinate -i "${CLAUDE_SKILL_DIR}/scripts/watch.sh" 2026-11-17T18:00 2026-11-18T09:00 [every_min]
   ```

   Each round counts from the window start to now, asks Gemini, and overwrites the report
   `<repo>/reports/token-watch-<end day>-<host>.md`. The default is one round each 60
   minutes. The last round runs at the end time. An end time in the past gives one report
   and stops.
4. **Wait for the first report** with a background `until [ -f <report> ]` loop (Gemini
   needs about 30 s). Read its 結論 and 疑似浪費 table. Tell the user the top items, the
   report path, and that the waste numbers are estimates (upper bounds).
5. **When the background task ends**, read the final report and tell the user.

## What Gemini marks

Long context with no compact, cache rebuild after idle, repeated command or polling, tool
error retries, failed or retried dispatch, subagent with a large context, and other
anomalies with a stated reason. Each mark needs numbers. The criteria, the estimate
formulas and the report format are in `INSTRUCTIONS` in `scripts/analyze.py`. Change
them there, so that this file and the prompt cannot disagree.

The report ends with an appendix table that the script makes from the numbers, without
Gemini. Use it to check a claim in the Gemini part.

## What leaves this machine

Only the Chimes GPT Gateway gets data. It gets numbers, tool names, the first 100
characters of each repeated shell command, and the first 90 characters of up to four
user messages for each session. Keys, JWTs, long tokens, `password=` values and emails
are masked first (`collect.mask`). All other session content stays on this machine.

## Gotchas

- The watch runs under the Claude session that started it. If that session closes, the
  watch stops. `caffeinate -i` blocks idle sleep only; keep the lid open.
- The waste numbers are upper bounds from formulas, for example
  (avg_context − 150k) × calls. A dispatch that finished after a retry counts its whole
  run. Say 「疑似」 and 「上限」 when you report them.
- A code-run dispatch also writes a Codex session. `analyze.py` marks that overlap
  (`also_code_run`) so that Gemini does not count it twice.
- A cache rebuild is a call that comes more than 60 minutes after the previous call and
  writes more than 50k tokens to the cache. The prompt cache TTL is one hour.
- If the Gemini call fails, the report says 「判讀失敗」 and still has the appendix. Do
  not run the judgment again with Claude.
- Two watches with the same end day write the same report file. Run one at a time.

First run (2026-11-18, 18:00 to 02:54): one session sent an average context of 631k on
71 calls with no compact (about 34M over the formula), and four Codex dispatches retried
or failed on "workspace routing discovery failed".

## Files

- `scripts/watch.sh` runs the rounds. Snapshots go to `~/.local/state/sk/token-watch/<day>/`.
- `scripts/collect.py` counts per-session facts for one window (JSON to stdout).
- `scripts/analyze.py` sends one snapshot to Gemini and writes the report.
- `scripts/gateway.py` calls the gateway (Responses API). Model: `TOKEN_WATCH_MODEL`,
  default `gemini-4-argon`.
- Tests: `python3 -m unittest collect_test analyze_test` in `scripts/`.

Related: token-quota-log (quota history), dashboard /tokens (cost per project),
`bin/sk-token-analysis-cron` (nightly "what the tokens were spent on"), context-journal
(compact and handoff for one session).
