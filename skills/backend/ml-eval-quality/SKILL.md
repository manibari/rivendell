---
name: ml-eval-quality
description: >
  Domain reference for the evaluation + quality backbone of an ML/AutoML platform:
  one task-aware metric dispatcher, a small-data cross-validation gate, CV-consistent
  hyperparameter tuning, a single feature-encoding seam (train=inference parity), and
  post-deployment DATA-quality drift monitoring. The patterns that make many trainers
  comparable and many small datasets trustworthy.
  TRIGGER when: building/reviewing an ML training or AutoML pipeline; choosing/
  computing model metrics; "為什麼這個 R² 很怪", small-dataset reliability, CV /
  Q² / LOOCV, hyperparameter tuning, train/inference skew, feature encoding, model
  drift / data-quality monitoring; working in Verdandi-AutoML.
  SKIP when: the async/job-tier decision for ML work (backend-async-jobs); model
  registry / versioning / lineage (separate concern); IC lot data (ic-lot-
  normalization); a one-off pandas analysis with no model.
tags: [backend, ml, automl, evaluation, monitoring, reference]
version: 1.0.0
source: manual
---

# ml-eval-quality

The eval/quality backbone of an ML platform: make every trainer **comparable** and
every small dataset **trustworthy**, with one metric seam, one encode seam, a CV
gate, and input-only drift monitoring. Grounded in `~/code/Verdandi-AutoML/apps/api/app/`
(`metrics.py`, `validation.py`, `tuning.py`, `features.py`, `data_quality.py`).

## The four seams

1. **Task-aware metric dispatcher** (`compute_metrics(task_type, …)`): one function so
   any two trainers of a task are scored identically.
   - regression: `rmse, mae, maape, r2` — rank by rmse (lower better)
   - classification: `accuracy, precision, recall, f1(macro)` — rank by f1
   - clustering: `silhouette, davies_bouldin, n_clusters` — rank by silhouette
   - anomaly: `anomaly_rate, n_anomalies` (informational; no ground truth)
   - `RANK_METRIC = {"regression": ("rmse", False), "classification": ("f1", True), …}`
2. **Small-data CV gate** (`cross_validate`): a single split lies on small data —
   the real reliability signal is cross-validated.
   - `n ≤ LOOCV_MAX(30)` → Leave-One-Out (the holdout is meaningless this small)
   - `n < SMALL_N(50)` → gate marks `reliable=False`, warn "trust CV over the split"
   - `n > CV_MAX_N(2000)` → holdout already reliable, skip the extra CV fits
   - regression CV score = **Q²** (cross-validated R², PRESS-based)
3. **CV-consistent tuning** (`tune_config`): each trainer declares a small `cv_grid`;
   score every candidate with the **same** `compute_metrics` used for the final fit
   and comparison — tuning, CV, and ranking must share the metric or they diverge.
4. **One feature-encoding seam** (`encode_features`): training, inference, AND
   optimization call the same encoder. role(input/reject) × type(numerical/
   categorical); numeric→coerce+mean-impute; categorical→one-hot capped at
   `CARDINALITY_CAP(50)`; at inference **reindex to the trained feature_columns**
   (unseen dummies → 0, missing cols → 0).

## Post-deploy DATA-quality (≠ model-quality)

Model-quality ("is it still accurate?") needs ground-truth labels you usually don't
have yet. **Data-quality** ("does input still look like training?") is computable
from inputs alone, so it catches drift BEFORE accuracy is even measurable. Two cheap,
explainable signals vs the version's training reference (feature columns + per-numeric
[min,max]):
- `missing_rate` = NaN fraction across feature columns → `> MISSING_DEGRADED(0.20)` degraded
- `drift_rate` = avg fraction out of training [min,max] → `> DRIFT_DEGRADED(0.10)` degraded
- Per-column drill-down; emit to a gauge (Prometheus) for trend.

## Gotchas (highest-signal — each is a real trap)

- **A single train/test split lies on small data**: the SDP PVD case reported
  **R² = -2400** from one unlucky holdout. Don't trust a single split below ~50 rows
  — gate to CV/LOOCV and report Q², not the holdout R².
- **Tune, CV, compare, and monitor must use the SAME metric dispatcher**: a separate
  metric in tuning vs final scoring makes the "best" model not actually best.
- **Encode in exactly one place or you get train/serve skew**: if inference encodes
  differently from training, predictions are silently wrong. Reindex to the trained
  columns; unseen categories → all-zero dummies, not a new column.
- **DATA-quality ≠ model-quality**: drift is detectable from inputs with no labels and
  fires earlier — don't wait for accuracy to drop to notice the world changed.
- **Cap one-hot cardinality (50)**: a high-cardinality categorical one-hots into a
  dummy explosion that wrecks training; cap + warn rather than silently blow up.
- **MAAPE over MAPE for regression error**: MAPE blows up near zero targets; MAAPE
  (arctan) is bounded — the dispatcher uses it on purpose.
