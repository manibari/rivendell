---
name: backend-async-jobs
description: >
  Tiered design rubric for backend work that might be slow: keep it sync, push it
  to a one-off job, or model it as a multi-run ML/pipeline — and the patterns for
  each. Kills the "FastAPI sync def goes to a threadpool so we're fine"
  misconception (threadpool ≠ queue), AND the opposite trap of applying a simple
  "status-row + poll once" job to an ML training pipeline (N parallel runs, partial
  success, no hard SLA).
  TRIGGER when: adding/reviewing a backend endpoint that runs a report, an ML
  train / AutoML search / HPO, an optimizer, a file parse, or any work whose
  worst-case latency could exceed ~1s; deciding sync vs async; "should this be a
  Celery task / pipeline"; designing a long job's status, progress, or polling.
  SKIP when: fast CRUD or a single cheap predict (sync); a pure frontend concern;
  choosing the broker product (infra, not this design rule).
tags: [backend, architecture, async, queue, ml, design]
version: 1.1.0
source: manual
---

# backend-async-jobs

A design rubric for "this backend work might be slow." The classic bug is capacity
collapse — slow work on the request path exhausts the web tier under load. The
*second* bug (just as real) is over-fitting a simple one-off-job pattern onto an ML
pipeline. Pick the **tier** by the shape of the work, not by reflex.

## Gotcha — threadpool ≠ queue (true at every tier)

FastAPI runs a sync `def` endpoint in a threadpool, so it doesn't block the event
loop. People conclude "so sync is fine." It is not, for slow work: it **occupies a
threadpool worker for the whole duration**, the pool **exhausts under load** (fast
requests queue behind slow ones), and it is **not** an independent worker tier you
can scale/retry/observe. Threadpool buys "doesn't block the loop," not "handles slow
work." Slow work belongs on a real queue.

## Pick the tier

| Tier | Work | Shape |
|------|------|-------|
| **0 — Sync** | fast CRUD, single cheap predict, validation (<~1s worst case) | normal request; queue overhead not worth it |
| **1 — One-off job** | one unit of slow work, bounded (~1–60s), single result | Celery task + status row (queued/running/done/error) + poll |
| **2 — Bounded job w/ progress** | 2–30s+ and the user is watching | Tier-1 + a `progress` / phase field; poll every 1–2s |
| **3 — ML / multi-run pipeline** | fan-out to N sub-jobs, nested sub-work, minutes–hours, rich artifacts | see below — a one-off-job rubric is WRONG here |

Decide on **worst-case**, not the happy path. A report that's 200ms on small data
and 30s on big data is at least Tier 1.

## Tier 1–2: the generic one-off Job pattern

Don't make a bespoke table per task type. One Job shape:

- **Status row**: `id, type, status (queued|running|done|error), params, result_ref,
  error, progress?, created_at, updated_at`.
- **Enqueue**: `POST` creates the row (`queued`) + dispatches the worker; returns the id.
- **Poll**: `GET /jobs/{id}` until `done|error`, then fetch `result_ref`.
- **Worker**: `running` → work → write `result_ref`/`error` → `done|error`; idempotent on retry.
- **Dev/prod parity**: eager in dev, real broker in prod — same task code, same transitions.

New job type = a new `type` value + a worker function, not a new table.
**Precedent**: ChimesFlow `ai_reports` (a status row, enqueue POST, polling GET,
eager-dev/broker-prod).

## Tier 3: ML training / multi-run pipeline (where a simple Job rubric BREAKS)

When one user action fans out to many heterogeneous, long, independent jobs, the
"status-row + poll once" rubric is wrong. What Tier 3 needs (evidence:
`Verdandi-AutoML/apps/api/app/training.py`):

- **N independent runs, not 1** — one enqueue creates N runs (e.g. one per
  algorithm). Track **N status rows**; the frontend subscribes to all of them.
- **Failure isolation / partial success** — one run fails, the others continue; the
  UI shows `4/5 done` + a per-run error reason. **Not all-or-nothing.**
- **Invisible sub-work needs a progress signal** — a run may do k-fold CV grid
  search (e.g. 15 fits) under a single `running`. Add a `progress`/phase field or
  expose `started_at` for elapsed, or the user stares at a spinner for minutes.
- **No hard latency SLA** — minutes to hours by data size + algorithm. Do NOT apply
  the "<1–2s or redesign" rule here; long is inherent, not a smell.
- **Cross-run coordination** — results are only comparable when runs share inputs
  (e.g. the same split snapshot); the compare step waits for all to finish.
- **Rich, immutable artifacts + lineage** — a run's result is `artifact_key` +
  metrics + tuning(best_params, cv_score) in an object store, copied to a registry
  on promotion — not a scalar `result_ref`.
- **Resource-aware scheduling** — `worker_prefetch_multiplier=1` so a long job
  doesn't starve the queue; plan CPU/GPU routing for v2.

> **The trap this skill exists to stop**: applying Tier 1 (ChimesFlow one-off job)
> to a Tier 3 workload (Verdandi-AutoML AutoML). They look similar (both "Celery +
> status") but differ on cardinality, failure model, progress, SLA, and artifacts.
> Don't conflate them.

## Tier-picking checklist

- [ ] Worst-case > ~1s, CPU-bound, or subprocess/external → not Tier 0.
- [ ] One bounded unit, single result → Tier 1 (add progress if user watches → Tier 2).
- [ ] Fans out to N jobs, or runs minutes–hours, or produces artifacts/lineage,
      or needs partial-success → **Tier 3**; don't force the one-off pattern.
- [ ] No reliance on "it's in a threadpool" to justify slow sync work.
- [ ] Worker tasks idempotent; an error state the UI can show; failure isolated
      across sibling runs at Tier 3.
