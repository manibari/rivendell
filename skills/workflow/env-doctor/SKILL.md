---
name: env-doctor
loop: dev
pdca: check
description: >
  Generate a project `doctor.sh` (or `doctor.py`) that checks Python/Node
  versions, dependency lockfile hashes, model/data download state, key env vars,
  and external-service connectivity, then prints a colored PASS/FAIL report for
  one-command cross-machine diagnosis.
  TRIGGER: 「為什麼我在另一台機器跑出來不一樣」「環境排錯」「reproducibility」
  「寫一個 doctor 腳本」「跨機器 setup 驗證」.
  SKIP: a one-off "is the port up" check (use lsof directly); CI pipeline setup
  (ci-pipeline); a deterministic numeric reproduction test (repro-exam).
tags: [workflow, environment, reproducibility, diagnostics]
version: 1.1.0
source: manual
---

# env-doctor

Produce a single `doctor.sh` a teammate runs on their machine to find *why* "it
works here but not there" — before debugging the app itself.

## Workflow

1. **Enumerate the environment contract** for this project:
   - Runtimes: Python / Node versions (exact, from `.python-version` / `.nvmrc` /
     `package.json` engines).
   - Dependency integrity: lockfile present + hash matches.
   - Data/model assets: required downloads present + correct size/hash.
   - Key env vars: present (and, where safe, non-empty / well-formed).
   - External services: reachable (DB, API, queue) with a fast timeout.
2. **Emit `doctor.sh`** that runs each check and prints colored `PASS`/`FAIL` with
   the actual observed value vs expected.
3. **Exit non-zero on any FAIL** so it's CI / pre-flight usable.

## Gotchas

- **Compare per-key, not aggregate**: "is the env healthy?" hides the one missing
  var/asset. Check and report each item individually — a single missing row is
  the common silent root cause of cross-machine divergence.
- **Lockfile picks the package manager**: `pnpm-lock.yaml` → pnpm,
  `package-lock.json` → npm, `yarn.lock` → yarn. Wrong choice silently installs to
  the wrong place; assert the *expected* manager.
- **Build-time env is baked**: a value correct locally (e.g. `NEXT_PUBLIC_*`) can
  be wrong in a build others use. Check build-time vars distinctly from runtime.
- **Trust ground truth**: read actual versions/hashes, not a cached "setup ok"
  marker file — stale markers are a classic false PASS.
