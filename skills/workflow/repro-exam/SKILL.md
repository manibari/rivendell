---
name: repro-exam
loop: dev
pdca: check
description: >
  Generate a deterministic "exam" (input → expected output) from a project's core
  logic (e.g. backtest engine, portfolio strategy) so a collaborator runs it on
  their machine and diffs results — quickly isolating the divergence source
  (data source / package version / random seed / floating point).
  TRIGGER: 「我有沒有標準的測驗考題」「跑出來不一樣怎麼排錯」「驗證對方的計算結果」
  「reference output for comparison」.
  SKIP: environment/setup checks (env-doctor); generating the project's normal
  unit tests (qa-testing); a one-off value diff you can eyeball.
tags: [workflow, quality, reproducibility]
version: 1.1.0
source: manual
---

# repro-exam

When two machines run the same code and get different numbers, hand the other side
a fixed exam: known inputs + your reference outputs. Where their answers diverge
tells you *which layer* is non-deterministic.

## Workflow

1. **Pin the inputs** — pick representative inputs that exercise the core logic;
   freeze them (committed fixtures, not live data).
2. **Capture reference outputs** on the known-good machine, at a stated tolerance
   (exact for integers/categoricals; an explicit epsilon for floats).
3. **Emit a self-contained runner** the collaborator executes: it computes their
   outputs and diffs against the reference, printing per-case PASS/FAIL + the first
   divergent value.
4. **Localize on failure** — the runner reports the layer: data source, package
   version, random seed, or floating-point/BLAS.

## Gotchas

- **Floating point isn't a bug, it's a layer**: tiny diffs usually mean a different
  BLAS/numpy build or summation order, not wrong code. Use an explicit epsilon and
  report magnitude; don't assert bit-equality.
- **Seed everything, and record it**: an unseeded RNG anywhere makes the exam
  useless. Pin and store every seed in the fixture.
- **Freeze the data source**: "different result" is most often different *input* (a
  live feed changed). The exam must ship its inputs, not fetch them.
- **Compare per-case**: an aggregate "12/13 pass" hides which input class breaks —
  report the first divergent case + value.
