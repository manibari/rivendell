---
name: agent-code-dispatch
loop: dev
pdca: do
description: >
  Give one scoped coding ticket to an executor (Qwen, Codex, or a Claude subagent)
  in its own git worktree, then review the work before it reaches the user. Claude
  plans and reviews; the executor writes the code. The default executor is a rule in
  the global CLAUDE.md (開發分工); the user can name another executor for one ticket.
  Owns `sk code` (launcher) and the GMI proxy that lets codex drive Qwen (127.0.0.1:8004).
  TRIGGER when: a ticket or planned change is ready to implement and the next step is
  writing code; or the user says "派給 Qwen", "給 Codex 寫", "這張 Claude 寫", "用 Qwen 做",
  "qwen 開發", "dispatch to qwen", "run this on codex", "換人寫", or asks to compare
  executors on a ticket.
  DO NOT TRIGGER when: Codex is wanted as a second-opinion review or consult
  (gstack-codex); 3+ independent investigations in parallel (agent-dispatch); an LLM
  provider inside a product app (that is the app's own provider code).
tags: [workflow, agents]
version: 2.0.0
languages: all
---

# agent-code-dispatch

Claude is the planner and the reviewer. An executor writes the code. The user
receives the work only after Claude reviewed it. The procedure is the same for
every executor; only step 3 changes.

## Pick the executor

1. The user named an executor for this ticket ("這張給 Codex 寫"): use it for this ticket only.
2. The user said to change the default ("之後都用 Codex"): edit the default line in
   `~/.claude/CLAUDE.md` (section 開發分工), then use it.
3. Else: use the default from that line.

| Executor | How it runs | Account / cost |
|---|---|---|
| `qwen` | `sk code exec --executor qwen` (codex CLI + GMI proxy) | GMI per-token, price not recorded |
| `codex` | `sk code exec --executor codex` (codex CLI) | ChatGPT login in `~/.codex`, weekly quota |
| `claude` | Agent tool, `isolation: "worktree"`, brief as the prompt | Claude session quota |

Do not switch the executor by yourself. If the executor cannot run (no key,
proxy down, quota used up), stop and tell the user the error and the
alternatives. The user picks.

Claude writes code directly, without a brief, only for: a small fix found in
the review gate, and rivendell configuration and operations. State it in the report.

## Executor notes

The first comparison (2026-10-06, Yellow-Chick, one ticket):

| | Codex gpt-6-sol | Qwen3.8-27B |
|---|---|---|
| Time | about 5 min | about 27 min |
| Tokens (incl. cache) | about 1.3 M | about 4.2 M |
| Tests | 24, all pass | 33, all pass |
| Defects | 0 | 2 |

The two Qwen defects:

1. It wrote user-facing strings in English. The UI language is Traditional Chinese.
2. Its sandbox could not reach the database. It did not report this. It replaced a
   project-wide guard with a stub in its test file, so the tests passed.

One sample is not a benchmark. But defect 2 is the kind that passes every test.
Thus the review gate in step 5 is mandatory for every executor, Claude included.

Do not give any executor these tickets without a design from Claude first:
schema migrations, auth, permissions, secrets, deploy scripts, design across modules.

## Setup (one time)

- qwen: the user stores the GMI key in the Keychain. Ask the user to open
  `scripts/set-gmi-key.command` in Finder. It needs a TTY, so the `!` prefix
  does not work. Never type or paste the key for the user.
  Check: `sk code key-check` prints `key found`.
- codex: `codex login` done in `~/.codex`. Quota per account shows on `/tokens`.
- claude: nothing.

Port 8004 belongs to the GMI proxy (`platform/deployment/ports.conf`).

## Procedure

### 1. Make a worktree

```bash
git -C <repo> worktree add .claude/worktrees/<executor>-<slug> -b <executor>/<slug>
```

The executor never works in the main tree or in a tree that another session
uses. For `claude`, the Agent tool makes the worktree.

### 2. Write the brief

Write the brief to the scratchpad as `brief-<slug>.md`. Use this order:

```markdown
# Rules (read first)
- UI strings, error messages that users see, and README text: Traditional Chinese.
  Code, comments, commit-style text: English.
- Change only the files in "Scope". If you must change another file, stop and say why.
- Do not change shared test infrastructure: conftest, fixtures, guards, CI config,
  skip markers. Do not replace a guard with a stub.
- Do not change the expected values of existing tests. If your change makes an
  existing test fail, stop and report the test and the old and new values.
  Exception: the brief says that the behavior changes on purpose.
- If a test cannot run (no database, no network, missing tool), stop.
  Report the command and the exact error. Do not make the test pass another way.
- Do not commit. Do not add dependencies.

# Goal
<one paragraph: what the user gets>

# Scope
<files or directories the executor may change>

# Acceptance
<observable results, one per line>

# Test command
<the exact command; say if it needs a service>

# Report
End with: files changed, test command output (last 20 lines), anything you could not do.
```

### 3. Run in the background

qwen or codex:

```bash
sk code exec --executor <qwen|codex> -C <worktree> --brief-file <brief> [--network]
```

Run it with `run_in_background`. Do not poll. The command prints the run
directory first and a JSON summary last (exit, seconds, usage, error, changed
files). Run files are in `~/.local/state/sk/code-runs/<stamp>-<executor>-<dir>/`.
`--network` lets the sandbox reach a local database or dev server.
A watchdog stops codex after 15 min with no event (`--idle-min`) or 90 min in
total (`--timeout-min`); the summary `error` then starts with `stalled:` or
`timeout:`. Report it; do not re-run more than once without telling the user.

claude: call the Agent tool with `isolation: "worktree"`,
`run_in_background: true`, and the brief as the prompt. Do not do the work in
this session.

### 4. Read the result

Read the report (`last.md`, or the subagent result) and `summary.json`. Then
read the full diff: `git -C <worktree> diff` and `git -C <worktree> status --short`.
If `error` is set, report it to the user and stop.

### 5. Review gate (mandatory, every executor)

Check each item. Write the result of each item in your report.

1. Scope: every changed file is in "Scope".
2. Guards: no change to conftest, fixtures, guards, skip markers, CI config, or
   mocks of a shared check. Search the diff for `skip`, `xfail`, `monkeypatch`,
   `mock`, and `return True`.
3. Language: user-facing strings are Traditional Chinese.
4. Tests: run the test command yourself, outside the sandbox. Do not trust the
   executor report for this.
5. Claim versus fact: each claim in the report agrees with the diff and your test run.
6. Changed expectations: list each `-` line in an existing test that holds an
   expected value (`assertEqual`, `assert ==`, `expect(...)`). For each one, the
   brief must say that this behavior changes. If not, the executor made the test
   agree with a defect. Fix the code, not the test.
   (2026-10-08: Qwen changed an expected 5M to 4M. The code counted "no model"
   as a model. All tests passed.)

### 6. Decide

- All items pass: tell the user the result. Commit only if the user asks.
- A small defect: fix it yourself and say what you fixed.
- A larger defect: give the same executor one fix round with a new brief that
  lists the findings. If the second round fails too, stop and ask the user
  which executor to use next.

### 7. Report to the user (Traditional Chinese)

Result first. Then the executor, the six review items, time, tokens, and the
defects found.

## Commands

```bash
sk code exec --executor <qwen|codex> -C <dir> --brief-file <file> [-m <model>] [--network]
             [--idle-min 15] [--timeout-min 90]
sk code proxy start|stop|status     # GMI proxy for qwen
sk code key-check                   # GMI key for qwen
```

`sk code` runs `scripts/code-run`. `--executor` has no default: the default
lives only in the CLAUDE.md rule. The proxy starts on the first qwen run and
keeps running; stop it with `sk code proxy stop`. A qwen run uses
`CODEX_HOME=~/.codex-qwen`, so `/tokens` counts it under the Qwen source.

## Files

- `scripts/code-run`: launcher (executor choice, proxy lifecycle, run directory).
- `scripts/qwen_codex_proxy.py`: Responses-stream shim for GMI. Tests:
  `python3 -m unittest qwen_codex_proxy_test` in `scripts/`.
- `scripts/set-gmi-key.command`: stores the GMI key in the Keychain.
