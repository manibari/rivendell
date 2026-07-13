---
name: ml-model-registry
description: >
  Domain reference for the model-registry / governance layer of an ML platform:
  turning a successful training run into a versioned, governed ModelVersion that is
  INDEPENDENT of its source dataset/run, with a denormalized lineage snapshot, a
  staging→SIT→UAT→PROD lifecycle, persisted feature_spec for inference parity, and
  artifact-availability guards.
  TRIGGER when: designing/reviewing model versioning, a model registry, promotion
  (staging/UAT/PROD), model lineage/provenance, "registered model broke after we
  deleted the dataset", serving-key provisioning, MLOps governance; working in
  Verdandi-AutoML registry.
  SKIP when: the eval/metrics/CV/encoding seams (ml-eval-quality); the async job
  tier for training (backend-async-jobs); a generic file-versioning need with no
  model lifecycle.
tags: [backend, ml, mlops, registry, governance, reference]
version: 1.0.0
source: manual
---

# ml-model-registry

The governance hinge: a successful **Run** becomes a **ModelVersion** that survives
the deletion of its source project / dataset / run. Grounded in
`~/code/Verdandi-AutoML/apps/api/app/registry_service.py` + the `ModelVersion` /
`RegisteredModel` schema.

## The pattern

1. **Register only a finished run**: guard `run.status == "done" and run.artifact_key`
   — never register a failed or artifact-less run.
2. **COPY the artifact into a registry namespace** (`registry/{model_id}/v{N}.bin`),
   independent of the dataset's artifact lifecycle. The registered model must not
   point at the run's storage — that storage gets garbage-collected.
3. **Monotonic version per RegisteredModel**: `next_version = max(existing) + 1`.
4. **Denormalized lineage snapshot** captured AT register time:
   `project → dataset → run → trainer + split params + metrics + source_run_id`.
   A snapshot, not a live FK chain — the source rows may later be deleted.
5. **Persist `feature_spec` + `artifact_meta` with the version** so inference
   re-encodes identically (ties to `ml-eval-quality`'s one-encode-seam — without the
   spec you get train/serve skew).
6. **Lifecycle state machine**: `staging → SIT → UAT → PROD`. Promotion is an
   explicit transition, not a flag flip; each environment is a gate.
7. **Per-model serving credentials**: auto-provision an API key per registered model
   so serving is scoped + revocable.

## Gotchas (highest-signal)

- **COPY, don't reference, the artifact**: if the ModelVersion points at the run's
  artifact, deleting the source dataset/run **orphans or breaks** the model. The copy
  into `registry/` is the whole point — registered models are independent assets.
- **Lineage is a snapshot, not a join**: capture provenance (dataset id, split seed,
  metrics, source_run_id) into a `lineage` blob at register time. Don't rely on live
  foreign keys to a run that may be gone — you'll lose the audit trail.
- **No feature_spec → no valid inference**: the version must carry the exact encoding
  spec it was trained with, or serving silently mis-encodes. Store it on the version.
- **Guard artifact availability before serving**: a registered model whose artifact
  file was deleted will fail predictions silently — flag missing-artifact versions
  proactively, don't discover it at inference time.
- **Version + lifecycle are different axes**: `version` is monotonic identity;
  `lifecycle_state` is where it is in promotion. v3 can be UAT while v2 is PROD —
  don't conflate "latest version" with "production model".
