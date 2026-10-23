---
name: agent-code-dispatch
loop: dev
pdca: do
description: >
  Give one scoped coding ticket to an executor (Qwen, Codex, or a Claude subagent)
  in its own git worktree, then review the work before it reaches the user. Claude
  plans and reviews; the executor writes the code. The default executor is a rule in
  the global CLAUDE.md (開發分工); the user can name another executor for one ticket.
  Owns `scripts/code-run` (the launcher; `sk code` on the owner's machine) and the GMI
  proxy that lets codex drive Qwen (127.0.0.1:8004).
  TRIGGER when: a ticket or planned change is ready to implement and the next step is
  writing code; or the user says "派給 Qwen", "給 Codex 寫", "這張 Claude 寫", "用 Qwen 做",
  "qwen 開發", "dispatch to qwen", "run this on codex", "換人寫", or asks to compare
  executors on a ticket.
  DO NOT TRIGGER when: Codex is wanted as a second-opinion review or consult
  (gstack-codex); 3+ independent investigations in parallel (agent-dispatch); an LLM
  provider inside a product app (that is the app's own provider code).
tags: [workflow, agents]
version: 2.1.0
languages: all
---

# agent-code-dispatch

Claude is the planner and the reviewer. An executor writes the code. The user
receives the work only after Claude reviewed it. The procedure is the same for
every executor; only step 3 changes.

## Pick the executor

1. The user named an executor for this ticket ("這張給 Codex 寫"): use it for this ticket only.
2. The user said to change the default ("之後都用 Codex"): edit the default line in
   `~/.claude/CLAUDE.md` (section 開發分工; add the section if it is missing), then use it.
3. Else: use the default from that line. If there is no such line (a new machine or
   another user), ask the user once which executor to use, and offer to add the line.

| Executor | How it runs | Account / cost |
|---|---|---|
| `qwen` | `code-run exec --executor qwen` (codex CLI + GMI proxy) | GMI per-token, price not recorded |
| `codex` | `code-run exec --executor codex` (codex CLI) | ChatGPT login in `~/.codex`, weekly quota |
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
  Check: `python3 "${CLAUDE_SKILL_DIR}/scripts/code-run" key-check` prints `key found`.
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
- Do not change the expected values of existing tests. If an existing test fails
  because of your new code, fix your code; do not stop for it. Stop and report the
  test and the old and new values only when the fix needs a change to the test
  (an expected value, a guard) or to a file outside "Scope".
  Exception: the brief says that the behavior changes on purpose.
- If a test cannot run (no database, no network, missing tool), stop.
  Report the command and the exact error. Do not make the test pass another way.
  A test path that you typed wrong is not this case: find the right file and continue.
- Do not commit. Do not add dependencies.
- Do not start a browser, Playwright, whisper, or a GPU model. Claude runs them
  outside the sandbox.

# Goal
<one paragraph: what the user gets>

# Scope
<files or directories the executor may change>

# Acceptance
<observable results, one per line>

# Test command
<the exact command; say if it needs a service>

# Claude runs after review
<commands that cannot run in the sandbox (see "Sandbox limits"); omit if none>

# Report
End with: files changed, test command output (last 20 lines), anything you could not do.
```

#### Sandbox limits (qwen, codex)

The codex sandbox blocks access to the macOS window server and to the GPU.
These commands fail at start inside it. Do not put them in "Test command" or
"Acceptance". Put them under "Claude runs after review", and run them in step 5.

- Playwright, or any other browser launch. Chrome stops in `_RegisterApplication`
  with exit 134, and macOS writes a crash report for each launch.
- Programs that use the GPU: PyTorch on MPS (`torch.backends.mps.is_available()`
  is False in the sandbox), whisper-cli (stopped at start 8 times on 2026-10-09),
  local image or video models.
- `uv run`: the sandbox cannot write `~/.cache/uv`. Run `uv sync` in the worktree
  before dispatch, and give `.venv/bin/python ...` commands.

(2026-10-11: a brief told Codex to run Playwright "and stop if the browser cannot
start". Codex ran 128 tests anyway. All failed, and Chrome crashed 16 times.)

### 3. Run in the background

qwen or codex:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/code-run" exec --executor <qwen|codex> -C <worktree> --brief-file <brief> [--network]
```

Run it with `run_in_background`. Do not poll. The command prints the run
directory first and a JSON summary last (exit, seconds, usage, error, changed
files). Run files are in `~/.local/state/sk/code-runs/<stamp>-<executor>-<dir>/`.
`--network` lets the sandbox reach a local database or dev server.
A watchdog samples the run every 10 s. The run is alive while, in the last
minute (`--idle-min 1`), codex wrote an event, its process tree used CPU (a
command runs, or the model streams; long thinking counts), or it received bytes.
All three still for a minute is a stall: the watchdog stops codex and every
command it started, then continues once in the same worktree (`--retries 1`,
the brief plus a "read git diff first" note). The summary lists `attempts` and
`stalls`; `error` starts with `stalled:` or `timeout:` (90 min, `--timeout-min`)
only when the last attempt failed. The owner (2026-10-12): 15 min was too long,
time is money. Note: when codex waits on a long command it posts status lines,
which count as movement; the total limit still applies.

On a laptop, prefix the command with `caffeinate -i` so idle sleep cannot stop
the run. A closed lid on battery still sleeps the machine; tell the user to keep
it open. (2026-10-14: the Mac slept from 11:53 to 13:04 during a run; the
watchdog then reported a 2239 s stall and the round ended with no report.
`pmset -g log | grep -E 'Sleep|Wake'` shows such gaps.)

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
4. Tests: run the test command and the "Claude runs after review" commands
   yourself, outside the sandbox. Do not trust the executor report for this.
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
CR="${CLAUDE_SKILL_DIR}/scripts/code-run"
python3 "$CR" exec --executor <qwen|codex> -C <dir> --brief-file <file> [-m <model>] [--network]
                  [--idle-min 1] [--retries 1] [--timeout-min 90]
python3 "$CR" proxy start|stop|status     # GMI proxy for qwen
python3 "$CR" key-check                   # GMI key for qwen
```

Where rivendell's `sk` is installed, `sk code <args>` runs the same script.
`--executor` has no default: the default lives only in the CLAUDE.md rule. The
proxy starts on the first qwen run and keeps running; stop it with `proxy stop`. A qwen run uses
`CODEX_HOME=~/.codex-qwen`, so `/tokens` counts it under the Qwen source.

## Files

- `scripts/code-run`: launcher (executor choice, proxy lifecycle, run directory).
- `scripts/qwen_codex_proxy.py`: Responses-stream shim for GMI. Tests:
  `python3 -m unittest qwen_codex_proxy_test` in `scripts/`.
- `scripts/code_run_liveness.py`: the watchdog's signals (events, process-tree CPU,
  bytes received). Tests: `python3 -m unittest code_run_liveness_test` in `scripts/`.
- `scripts/set-gmi-key.command`: stores the GMI key in the Keychain.
