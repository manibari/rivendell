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
  TRIGGER when: "額度紀錄", "記錄額度", "餘量", "每週額度", "額度重置", "token 跟額度的關係",
  "statusline 額度", setting up quota logging on a new machine, or the 帳號與額度 panel
  shows no Claude rows.
  DO NOT TRIGGER when: reading token counts alone (dashboard /tokens), or tuning which
  account is logged in (token_accounts observer).
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
