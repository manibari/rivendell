# Port Checklist — External Skill → rivendell

Step-by-step recipe for porting a skill from `anthropic/skills`,
`jdrhyne/agent-skills`, `Dicklesworthstone/agent_flywheel`, or any other
external source into `rivendell/skills/`. Read this when running Phase 3
of the skill-scout workflow.

## 1. Pick the target category

rivendell organizes by purpose, not by source:

| Category | Use for |
|----------|---------|
| `meta/` | rivendell self-management (skill creation, harvest, retro) |
| `workflow/` | cross-domain workflows (planning, agents, customer intel) |
| `quality/` | testing, code review, documentation hygiene |
| `git/` | version control workflows |
| `frontend/` | UI design, iOS, mockups |
| `backend/` | server-side, databases, integrations |
| `docs/` | document creation/processing (offices files, MCP, comms) |

Pick the one that matches what the skill *does for users*, not what
its implementation uses.

## 2. Frontmatter mapping (anthropic format → rivendell format)

External skills typically have a minimal frontmatter:

```yaml
# Anthropic format (source)
---
name: doc-coauthoring
description: Guide users through a structured workflow for co-authoring documentation. Use when user wants to write proposals, technical specs, etc. Trigger when user mentions writing docs, drafting specs.
license: Complete terms in LICENSE.txt
---
```

rivendell expects more structure for proper triggering:

```yaml
# rivendell format (target)
---
name: doc-coauthoring
description: >
  <Original description, expanded to 2-3 lines>
  TRIGGER when user says: "<phrases>", "<more phrases>",
  "<繁中 phrases too>", or otherwise indicates <intent>.
  DO NOT TRIGGER for: <existing skill> (use <name>),
  <existing skill> (use <name>). This skill is for <generic case>.
when_to_use: >
  <One-sentence summary of the situation>
version: 1.0.0
tags: [<category>, <topic-tags>]
languages: all
user_invocable: true
---
```

**The four extra fields that matter:**

- **`description` with TRIGGER + DO NOT TRIGGER lists.** The most important
  delta. rivendell has 89+ skills; ambiguity about which one fires is the
  #1 routing problem. Always enumerate adjacent rivendell skills the
  imported one should defer to. Example: `doc-coauthoring` defers to
  `sow-writer`, `gov-rfq-writer`, `jd-writer`, `sales-customer-intel`,
  `discovery-interview`, `pitch-deck` because all of those handle specific
  document genres.

- **`when_to_use`**: short prose, often shown in skill catalogs. Keep it
  to one sentence — the description carries the weight.

- **`version`**: start at `1.0.0`. External sources often omit this; we
  use it to track local divergence from upstream.

- **`tags`**: array of 3-5 short tokens. First tag should match the
  category directory (e.g. `docs` for skills under `docs/`).

## 3. Strip platform references from the body

External skills mention their origin platform. Read every paragraph and
rewrite — don't `sed`-replace, because context matters.

| Pattern in source | Action |
|-------------------|--------|
| "Anthropic's brand", "my company" | Either rewrite generically OR add a tone-adaptation note for zh-tw/non-Anthropic context |
| `create_file`, `str_replace` (claude.ai artifact tools) | Replace with `Write` / `Edit` (Claude Code tools) |
| References to claude.ai web interface | Either rewrite for Claude Code OR drop entirely |
| OpenClaw / Clawdbot / ClawHub / Codex platform mentions | Drop or rewrite — rivendell uses Claude Code |
| `cron` schedules baked into the skill | Move scheduling out: rivendell schedules via `agents.conf` + launchd |
| `memory_search` (OpenClaw-specific) | Replace with `grep` in `~/.claude/` or filesystem reads |

**Verification grep before commit:**
```bash
grep -iE "anthropic|openclaw|clawdbot|clawhub|codex|claude\.ai" \
    skills/<cat>/<skill>/SKILL.md \
  | grep -v "Ported from"   # source-attribution comment is OK
```
Empty output = clean port.

## 4. Bundled assets — copy with `cp`, then `git add` manually

If the source skill has `examples/`, `scripts/`, `references/`, copy them
recursively:

```bash
cp -r /tmp/skill-scout/<source>/skills/<skill>/examples \
      skills/<cat>/<skill>/examples
```

**Trap:** `cp` does NOT trigger rivendell's auto-stage hook (which fires
on Edit/Write tool calls). The copied files will appear as `??` (untracked)
in `git status`. You must `git add` them explicitly. The SKILL.md you
edited via the Write tool *will* be auto-staged — only the bundled
artifacts need manual staging.

```bash
git status --short skills/<cat>/<skill>/   # check what got staged vs not
git add skills/<cat>/<skill>/examples/     # stage the unstaged
```

If bundled scripts are present:
```bash
chmod +x skills/<cat>/<skill>/scripts/*.sh
chmod +x skills/<cat>/<skill>/scripts/*.py
```

## 5. Source attribution

Every ported skill ends with an HTML comment recording origin and date:

```markdown
<!-- Ported from: https://github.com/anthropics/skills/tree/main/skills/<name> (YYYY-MM-DD) by skill-scout -->
```

This makes it possible to:
- Re-pull updates from upstream later
- Detect divergence (`diff` against the source)
- Give credit in the skill catalog

## 6. Deploy and verify

```bash
./bin/sk deploy
# Look for: "link  <skill-name> → ~/.claude/skills/<skill-name>"

ls -l ~/.claude/skills/<skill-name>
# Expected: lrwxr-xr-x ... -> /Users/.../rivendell/skills/<cat>/<skill>
```

## 7. Commit-message template

```
feat(skills): port <name1> + <name2> from <source-repo>

<2-3 lines on what gap each fills, referencing the existing rivendell
skills they complement or defer to>

<Notable adaptations: TRIGGER/DO NOT TRIGGER lists added, platform refs
stripped, tone notes for zh-tw if applicable, examples/ bundled.>

Both have source-attribution HTML comments, deployed via sk deploy,
and verified for leftover platform references.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

## 8. After-port sanity check

Run through this list before declaring done:

- [ ] Frontmatter has `description`, `when_to_use`, `version`, `tags`
- [ ] `description` includes both `TRIGGER` and `DO NOT TRIGGER` lines
- [ ] DO NOT TRIGGER lists adjacent rivendell skills the new one should defer to
- [ ] No leftover platform references (grep check above)
- [ ] Bundled `examples/` / `scripts/` / `references/` are `git add`ed
- [ ] Source attribution comment at end of SKILL.md
- [ ] `./bin/sk deploy` ran clean and symlink exists
- [ ] README catalog updated by `sync-readme` hook (visible in `git status` as `M README.md`)
- [ ] Skill count increased correctly in README header

If any unchecked, the port isn't ready to commit.
