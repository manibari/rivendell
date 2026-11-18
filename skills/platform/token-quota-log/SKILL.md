---
name: token-quota-log
loop: platform
pdca: check
description: >
  Record the official subscription quota (Claude 5h / weekly used %, reset time) so
  token usage can be correlated with what the quota actually charged. Ships the
  Claude Code statusLine script that logs every quota change to
  ~/.claude/usage-quota/claude-rate-limits.jsonl; Codex needs no logger (its
  rollouts already carry rate_limits). The dashboard /tokens 帳號與額度 panel reads both.
  Also explains why a weekly quota ran out fast: scripts/quota_diagnose.py compares the
  quota curve with this machine's session usage and marks quota used by another machine
  or claude.ai.
  TRIGGER when: "額度紀錄", "記錄額度", "餘量", "每週額度", "額度重置", "token 跟額度的關係",
  "statusline 額度", "額度怎麼掉這麼快", "額度為什麼用完", "額度一下就噴完", "這週額度比上週",
  "quota ran out fast", setting up quota logging on a new machine, or the 帳號與額度 panel
  shows no Claude rows.
  DO NOT TRIGGER when: reading token counts alone (dashboard /tokens), tuning which
  account is logged in (token_accounts observer), or marking waste per session for one
  night (token-waste-watch).
tags: [meta, monitoring]
version: 1
user_invocable: false
trigger_label: statusLine
---

# token-quota-log

Token counts are local and exact; the quota is the server's and is the number that
actually runs out. This skill keeps a history of the quota so the two can be compared.

## Sources

| Source | Where the quota comes from | Logger |
|---|---|---|
| Claude Code | statusLine stdin `rate_limits.five_hour` / `seven_day` (`used_percentage`, `resets_at`) | `scripts/statusline-quota.py` |
| Codex | every rollout `token_count` event: `rate_limits.primary` (`used_percent`, `window_minutes`, `resets_at`, `plan_type`) | none needed |

The Claude reading exists only while an interactive session renders its status
line, so there is no history from before the script was installed. A row is
appended only when the reading changes.

### Which account a row belongs to

The quota in the status line follows the account that is logged in on this machine now,
for every open session (they share one credential). The label in a row comes from
`~/.claude.json`, which each open session rewrites with its own remembered account. Thus
after a login switch the label can change every minute while the values are one series of
one account (2026-11-09 14:24 to 17:16: about 50 label changes, one reset time, used %
rising from 7 to 21). A session binding (added 2026-11-12, removed 2026-11-19) made this
worse: a wrong label lasted for the whole session.

Thus **readers attribute each row by its window, not by its label**
(`platform/monitoring/usage/quota_attribution.py`, used by `/api/tokens/quota` and the
diagnosis). Rows with the same `seven_day.resets_at` are one track. If two labels share a
track and their used % series are within 3 points (median of nearest pairs), the track gets
the label with the most rows. If the series differ more, or the counts tie, the track is
marked ambiguous and nothing changes. The log itself is never rewritten. Since 2026-11-19
each row also has `session_id` and `subscription_type`.

## Install

Registered through the global manifest, never by hand:

```bash
sk deploy          # creates ~/.claude/skills/token-quota-log
sk hooks install   # sets statusLine in ~/.claude/settings.json (data/global-hooks.json)
```

`sk hooks install` does not overwrite a statusLine that points elsewhere; it
reports the conflict instead.

## Reading it

`platform/monitoring/usage/token_quota.py` → `GET /api/tokens/quota`:
accounts used (first / last seen), quota reset time, used % and remaining %, and
per reset window the tokens spent and tokens per 1% of quota.

## Why the quota went fast (diagnosis)

Use this when the owner asks why a week ran out early, or why one week was worse than
another. Owner, 2026-11-18: 「上上禮拜是不是怪怪的啊 / 那時候 claude 用量一下就噴完了」.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/quota_diagnose.py" --weeks 3 [--account <label>] [--out <file>]
```

It reads the quota log and the Claude Code logs of this machine. It writes a Traditional
Chinese Markdown report:

- For each weekly window: the highest %, the time it reached 100%, the days it lasted,
  the usage of this machine, and the % that this usage explains.
- The slots (6 h) with the largest quota rise. A slot is marked 「其他來源可能」 when the
  quota rose 3% or more and this machine explains less than half of it.
- The 12 hours with the largest rise, and the sessions that used the most in them.
- The model mix.

How it estimates:

- Usage is weighted tokens: input 1, cache write 1.25, cache read 0.1, output 5 (the API
  list price ratio). It is an estimate, and the same weights apply to each model.
- Tokens per 1% = the median over the slots where this machine used 10M or more and the
  quota rose 2% or more. With fewer than 3 such slots, the report says 「未判讀」.
- Each usage event goes to the account that was active at its time: the attributed account
  of the nearest quota row within 6 hours. Before 2026-11-19 a session-to-account map
  (`.sessions-claude.json`) did this; `--sessions-map` stays for old commands but is not used.

Limits:

- The report cannot see another machine or claude.ai. It finds their use only as quota
  that this machine does not explain. Do not name the source as a fact; say 「可能」.
- An account resets at one fixed time of the week. A window with another reset time that
  overlaps a window is off-cycle. Under a window, the report says 「有 N 筆原本記在別的帳號，
  依週期改算到這個帳號」 when rows were attributed into it, and 「這個週期有兩個帳號同一個重置
  時間，無法分開」 when the track is ambiguous. (Until 2026-11-19 it said 「可能標錯帳號」, and
  a rule hid the case when two labels shared a reset time; that rule hid a real error.)

Answer the owner with the conclusion first, in plain words: which week, how many days it
lasted, how much of it this machine explains, and the slots and sessions that used the
most. Reference case, 2026-11-18: the window of 11/04 lasted 4.7 days; this machine
explained 46%; about 40% came in slots when this machine was almost idle, while the Air
daily reports showed heavy use.
