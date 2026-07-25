---
name: autoresearch
description: >
  Autonomous iteration loop — define goal + metric + verify command, agent loops
  modify→verify→keep/discard. Integrates with agent-headless + dashboard.
  TRIGGER: "autoresearch", "自動迭代", "improve overnight", measurable-metric optimization.
  SKIP: one-time optimization; subjective quality work.
version: 1.0.0
tags: [workflow, automation, optimization, agent-headless]
languages: [bash, python, yaml]
user_invocable: true
---

# autoresearch — Autonomous Iteration Loop

## Core Principle

Karpathy's insight: **Constraint + Mechanical Metric + Autonomous Iteration = Compounding Gains**.

The idea is deliberately narrow:

- **One scope** — the file(s) the agent is allowed to modify
- **One number** — a metric extracted from a command's output
- **One direction** — higher is better, or lower is better
- **Infinite loop** — modify → verify → keep/discard → repeat

By constraining the agent to a single measurable goal and giving it a
mechanical feedback signal, you get compounding improvements overnight
without human babysitting. Each iteration is a small, safe bet: if the
metric improves, keep it; if not, revert instantly via git.

---

## Config Format (`autoresearch.yml`)

Place this file in the project root or pass it via `--config`.

```yaml
goals:
  - name: keyword-coverage
    description: Improve tender scraper keyword match rate
    scope: materials/tenders/keywords.yml
    metric_cmd: "python3 scripts/tender_scraper.py --analyze | grep 'match_rate' | awk '{print $2}'"
    direction: higher  # or "lower"
    verify_cmd: "python3 scripts/tender_scraper.py --dry-run"
    max_iterations: 20
    cooldown_secs: 60  # between iterations
    prompt: |
      Review the keyword match rate and unmatched tender titles.
      Add or refine keywords in keywords.yml to improve coverage.
      Avoid false positives — prefer compound Chinese terms over short English abbreviations.
```

### Field Reference

| Field            | Required | Description                                         |
|------------------|----------|-----------------------------------------------------|
| `name`           | yes      | Unique identifier, used in branch names and logs    |
| `description`    | no       | Human-readable purpose                              |
| `scope`          | yes      | File(s) the agent may modify (glob ok)              |
| `metric_cmd`     | yes      | Shell command that prints a single number to stdout  |
| `direction`      | yes      | `higher` or `lower`                                 |
| `verify_cmd`     | yes      | Sanity-check command; must exit 0 for iteration to count |
| `max_iterations` | no       | Default: 50                                         |
| `cooldown_secs`  | no       | Default: 30                                         |
| `prompt`         | yes      | Instructions fed to the agent each iteration        |

---

## Runner (`sk-autoresearch`)

The bash runner implements the core loop:

1. **Read config** — parse `autoresearch.yml`, extract the target goal.
2. **Create branch** — `git checkout -b autoresearch/{goal-name}/{date}`.
3. **Baseline** — run `verify_cmd` then `metric_cmd`, capture the starting number.
4. **Loop** (up to `max_iterations`):
   - a. Call `claude -p` with the goal prompt, current metric, and recent
        iteration history appended for context.
   - b. Run `verify_cmd` — if exit code != 0, treat as discard.
   - c. Run `metric_cmd` — capture new metric.
   - d. **Compare**:
     - Improved (or equal)? → `git add -A && git commit -m "autoresearch: {goal} {old} → {new}"`
     - Worse? → `git checkout -- .` (revert all unstaged changes)
   - e. Log iteration to dashboard DB via `_sk_exec_record_run`.
   - f. Sleep `cooldown_secs`, check iteration count.
5. **Summary** — print best metric achieved, total iterations, keep/discard ratio.
6. **Optionally merge** — if `--merge` flag, fast-forward merge back to the source branch.

### Pseudocode

```bash
baseline=$(_run_metric "$metric_cmd")
best=$baseline
for i in $(seq 1 "$max_iterations"); do
    claude -p "$prompt\n\nCurrent metric: $baseline\nHistory: $history"
    if ! _run_verify "$verify_cmd"; then
        git checkout -- .
        _log "iter $i: verify failed, discarded"
        continue
    fi
    new_metric=$(_run_metric "$metric_cmd")
    if _is_improved "$new_metric" "$baseline" "$direction"; then
        git add -A && git commit -m "autoresearch: $goal_name $baseline → $new_metric"
        baseline=$new_metric
        [[ $(_compare "$new_metric" "$best") ]] && best=$new_metric
        _log "iter $i: KEEP ($baseline → $new_metric)"
    else
        git checkout -- .
        _log "iter $i: discard ($new_metric not better than $baseline)"
    fi
    sleep "$cooldown_secs"
done
```

---

## Keep/Discard via Git

Git is the safety net. Every iteration is either committed or reverted —
there is no middle ground.

- **Before loop**: `git checkout -b autoresearch/{goal-name}/{YYYY-MM-DD}`
- **Keep**: `git add -A && git commit -m "autoresearch: {goal} improved {old} → {new}"`
- **Discard**: `git checkout -- .` (revert all unstaged changes)
- **After loop**: optionally `git checkout main && git merge --ff-only autoresearch/...`

This means you can always inspect the full improvement history via
`git log --oneline autoresearch/keyword-coverage/2026-03-24` and cherry-pick
individual iterations if needed.

---

## Integration Points

### launchd

Schedule via `agents.conf` like any other headless agent:

```
autoresearch  keyword-coverage  02:00  daily  sk-autoresearch --goal keyword-coverage
```

The `sk-launchd-gen` skill picks this up and generates the plist automatically.

### dashboard

Each iteration writes to the dashboard DB. The metric trend is visible in
run history — you can watch the number climb (or drop) over time. The
iteration log includes: timestamp, iteration number, metric before/after,
keep/discard decision, and token cost.

### exec-lib

Uses `_sk_exec_record_run` to log each iteration. The `metric_value` can
be stored in the existing `cost_usd` field (repurposed) or in a dedicated
`metric` column if the schema has been extended.

### doctor

`sk-agent-doctor` recognizes autoresearch failures:
- Too many consecutive discards (stuck) → flag for human review
- Verify command consistently failing → likely broken metric
- Branch diverged from main → merge conflict risk

---

## When to Use vs Not

| Use autoresearch                              | Don't use                            |
|-----------------------------------------------|--------------------------------------|
| Keyword match rate optimization               | One-time keyword update              |
| Test coverage improvement                     | Writing a specific test              |
| Prompt quality iteration (with eval scores)   | Subjective prompt tuning             |
| Performance benchmark optimization            | General refactoring                  |
| Regex/pattern recall improvement              | Exploratory research                 |
| Config tuning with measurable output          | Tasks requiring human judgment calls |

**Rule of thumb**: if you can't write a command that prints a single number
representing success, autoresearch is not the right tool.

---

## Example: Tender Keyword Discovery

The existing keyword-discovery flow maps directly to autoresearch:

```yaml
goals:
  - name: tender-keywords
    description: Maximize tender keyword match rate without false positives
    scope: materials/tenders/keywords.yml
    metric_cmd: >
      python3 scripts/tender_scraper.py --analyze
      | grep 'match_rate'
      | awk '{print $2}'
    direction: higher
    verify_cmd: "python3 scripts/tender_scraper.py --dry-run"
    max_iterations: 30
    cooldown_secs: 45
    prompt: |
      You are optimizing tender keyword coverage.

      Current file: materials/tenders/keywords.yml
      Goal: increase match_rate (% of relevant tenders matched by keywords).

      Steps:
      1. Run the analyzer to see unmatched tender titles.
      2. Identify patterns in unmatched titles.
      3. Add compound Chinese keywords that capture those patterns.
      4. Avoid short or ambiguous terms that would cause false positives.

      Only modify keywords.yml. Do not touch any other files.
```

A typical overnight run: 30 iterations, ~18 kept, match rate from 62% → 84%.

---

## Writing Good Metrics

A good metric for autoresearch must satisfy four properties:

1. **Single number** — the `metric_cmd` must print exactly one number to
   stdout (integer or float). If your tool outputs more, pipe through
   `grep`/`awk`/`jq` to extract it.

2. **Deterministic** — same input files → same output number. Avoid metrics
   that depend on network calls, timestamps, or random seeds (or pin the
   seed).

3. **Fast** — under 60 seconds. The agent will run this every iteration;
   a slow metric means fewer iterations per night. If the full test suite
   takes 10 minutes, write a focused subset.

4. **Meaningful** — not trivially gameable. "Number of lines in file" is a
   bad metric because the agent will just add blank lines. "Percentage of
   test cases passing" is better. "F1 score on a held-out eval set" is best.

### Metric Anti-patterns

| Anti-pattern                | Problem                              | Fix                                  |
|-----------------------------|--------------------------------------|--------------------------------------|
| Lines of code               | Gameable by adding whitespace        | Use a functional metric              |
| Binary pass/fail            | No gradient for the agent to follow  | Use a continuous score               |
| Network-dependent           | Flaky, non-deterministic             | Mock or cache external calls         |
| Multi-minute runtime        | Too few iterations per session       | Subset the test data                 |
| Composite score without log | Hard to debug regressions            | Log sub-metrics alongside main score |
