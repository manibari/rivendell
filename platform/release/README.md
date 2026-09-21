# Release ownership

This module owns version and release policy. The canonical files remain at the repository root while their readers and release checks still use those paths:

- `VERSION`: current baseline version
- `CHANGELOG.md`: released changes
- `ROADMAP.md`: planned work

Service startup and environment configuration belong to `platform/deployment/`.
