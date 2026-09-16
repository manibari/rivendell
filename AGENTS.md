# Rivendell Agent Rules

Codex should treat this repo as the same operational system described in
`.claude/CLAUDE.md`.

Before changing skills, agents, schedules, dashboard behavior, or maintenance
tooling, read `.claude/CLAUDE.md` and follow those rules. In particular:

- Rivendell skills own internal automation, harvest, retro, and `sk-*` tooling.
- Gstack-prefixed skills live in the gstack repo and own external-facing dev workflow.
- Do not manually edit generated `reports/*` in interactive sessions.
- After any skill change, update `README.md` so the Skills Catalog stays in sync.

The canonical skill source is `skills/*/*/SKILL.md`. `./bin/sk deploy` links the
same source skills into both Claude Code (`~/.claude/skills`) and Codex
(`${CODEX_HOME:-~/.codex}/skills`).

Gstack skills are intentionally not copied into this repo. They come from the
separate `gstack` checkout, whose location is machine-dependent — this file used
to name `/Users/manibari/code/gstack`, which is the previous machine's path and
resolves to nothing after the move. Same rule as `.claude/CLAUDE.md` line 15:
derive the path, don't hardcode it. Find the checkout with
`git -C "$(dirname "$PWD")/gstack" rev-parse --show-toplevel` or wherever
`external_skill_pack` in `sk bootstrap` put it; Codex-specific generated skills
live under that repo's `.agents/skills/gstack-*`, linked into
`${CODEX_HOME:-~/.codex}/skills`.

On a host with no gstack checkout, the deployed `~/.claude/skills/gstack-*`
directories are plain copies with no live source — they still work, but editing
them edits nothing upstream.

Use gstack skills for external-facing product, planning, review, QA, ship, and
design workflows; use Rivendell skills for this repo's internal automation system.
