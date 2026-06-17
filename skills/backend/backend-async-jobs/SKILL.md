---
name: backend-async-jobs
description: >
  Design decision + pattern for backend work that might be slow: when to keep a
  request synchronous, when to push it to a real queue/worker tier, and the
  generic one-off Job (status-row + enqueue + poll) abstraction. Kills the
  "FastAPI sync def goes to a threadpool so we're fine" misconception — a
  threadpool is not a queue.
  TRIGGER when: adding/reviewing a backend endpoint that runs a report, an ML
  predict/train, an optimizer, a file parse, an external API call, or anything
  whose worst-case latency could exceed ~1-2s; deciding sync vs async; "should
  this be a Celery task"; designing a long-running job's status/polling.
  SKIP when: fast CRUD or a single cheap predict (keep it sync); a pure frontend
  concern; choosing the queue *broker* product (that's infra, this is the
  design rule).
tags: [backend, architecture, async, queue, design]
version: 1.0.0
source: manual
---

# backend-async-jobs

A design rubric for "this backend work might be slow." Most backend bugs of this
class are not crashes — they're capacity collapse under load because slow work
sat on the request path. Decide the tier up front, by latency, not by reflex.

## The decision rule

| Work | Tier | Why |
|------|------|-----|
| Fast CRUD, single cheap predict, validation | **Sync** (normal `async def` / `def`) | Sub-second; queue overhead not worth it. |
| Worst-case latency **> ~1-2s**, OR CPU-bound, OR spawns a subprocess, OR calls a slow/flaky external API | **Queue / worker tier** (Celery task + status row + frontend polling) | Keeps the web tier free; scales the slow work independently. |

Decide on **worst-case**, not the happy path. A report that's 200ms on small data
and 30s on big data is a queue job.

## Gotcha — threadpool ≠ queue (the misconception this skill exists for)

FastAPI runs a **sync `def`** endpoint in a threadpool, so it doesn't block the
event loop. People conclude "so sync is fine." It is not, for slow work:

1. It **occupies a threadpool worker for the entire duration**.
2. Under load the threadpool is **exhausted** — new requests (even fast ones)
   queue behind the slow ones.
3. It is **not** the same as running in an independent worker tier you can scale,
   retry, rate-limit, and observe separately.

So: threadpool buys you "doesn't block the loop," not "handles slow work." Slow
work still belongs on a real queue.

## The generic one-off Job pattern

Don't make a bespoke status table per task type (ai_reports, optimize_runs,
predict_runs, …). Abstract **one** Job pattern:

- **A status row**: `id, type, status (queued|running|done|error), params,
  result_ref, error, created_at, updated_at`.
- **Enqueue**: `POST` creates the row (`queued`) + dispatches the worker task;
  returns the job id immediately.
- **Poll**: `GET /jobs/{id}` returns status; frontend polls until `done|error`,
  then fetches `result_ref`.
- **Worker**: flips `running` → does the work → writes `result_ref` / `error` →
  `done|error`. Idempotent on retry.
- **Dev/prod parity**: eager mode in dev, real broker in prod — same task code,
  same status transitions, so behavior matches.

One table + one task signature serves reports, training, optimize, predict-file.
New job type = a new `type` value + a worker function, not a new table.

> **Precedent**: ChimesFlow moved AI reports + training onto a Celery worker tier
> (an `ai_reports` status row, an enqueue `POST`, a polling `GET`,
> eager-dev/broker-prod). Generalize that one-off-job shape into the Job pattern
> above before adding optimize (PSO/GA/CP-SAT/DOE) and predict-file — so each new
> long task reuses it instead of growing its own table.

## Review checklist

- [ ] Every endpoint whose worst-case > ~1-2s is on the worker tier, not sync.
- [ ] No reliance on "it's in a threadpool" to justify slow sync work.
- [ ] Long jobs expose status + polling, not a held-open request.
- [ ] New job types reuse the generic Job pattern, not a new bespoke table.
- [ ] Worker tasks are idempotent and have an error state the UI can show.
