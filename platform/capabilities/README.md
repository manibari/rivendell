# Capabilities

`skills/*/*/SKILL.md` owns each ability package. This module owns the platform's
index and the workflows that reference those packages.

| Path | Owner | Edit here for |
|---|---|---|
| `catalog/` | Skill catalog | Skill metadata, routing tests, hook manifest, and playbook chip explanations |
| `workflows/definitions/roles.json` | Workflow model | Role identity, authority, and ordered job IDs |
| `workflows/definitions/jobs/*.json` | Workflow model | PDCA steps, gaps, conditions, and skill references |
| `workflows/playbooks/*.json` | Workflow model | The four detailed Rivendell dashboard playbooks |
| `workflows/workflow-map.json` | Legacy API | `/api/workflow` compatibility only; it does not feed the canonical workflow model |

The Dashboard API projects these definitions into the existing role response
and serves the playbooks. `docs/skills-by-role.md` keeps the human explanation
and diagrams; `./bin/sk check workflows` compares its structured content with
the definitions and checks every local skill reference. Gstack skills stay in
the external gstack checkout and appear as `source: gstack` references.
Each job step has an action, an ordered PDCA stage, skill references, and
nullable `condition` and `gate` fields for decisions that can be modeled
explicitly later. Existing prose remains in `text` and `note`.

`platform/skill_catalog` and `platform/workflows` are compatibility symlinks.
