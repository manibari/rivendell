# Skills public release: remove the coupling, keep one source

Date: 2026-10-22. Owner: Peter. Planner and reviewer: Claude. Executor: see each ticket.
Status: superseded on 2026-10-23 by `2026-10-23-rivendell-product.md`. The owner
dropped the company / team / private split. The inventory in the appendix
stays valid as evidence.

Source: Peter, 2026-10-22: 「我是覺得可以公開啦，只是要解決耦合問題」
「畢竟誰家的公司流程不是都差不多」. On the same day `manibari/rivendell`
changed from public to private (`gh repo edit --visibility private`).

## Goal

One public GitHub repo of skills that another person can install and run.
Teammates install the same skills as a Claude Code plugin.
rivendell stays the only source and stays private.

Not in scope:

- Make rivendell public again. Its git history holds the material in
  "Never public" below. A cleanup of the current files does not remove it.
- Publish the rivendell platform (`sk`, dashboard, scheduled agents).
- Translate skills. The language of each skill stays as it is.

## Findings (2026-10-22)

Method: a scan of every text file in the 134 skill folders, then a read of
each hit. The scan was a one-time script; ticket SKILL-LEAK-CHECK makes it a
repeatable check.

| Coupling | Skills | Meaning |
|---|---|---|
| No hit | 58 | Nothing found by the scan |
| `rivendell` in the text | 35 | Cites the repo by name |
| Repo paths (`reports/`, `.learnings/`, `data/`, `knowledge/videos`, repo-root `scripts/`) | 26 | Works only inside rivendell |
| Home folders (`~/Documents`, `~/Work`, `~/Library`, `~/Vault`) | 19 | Works only on this machine |
| Other local repos (`~/Code/<repo>`) | 18 | Points to code that others cannot read |
| `~/.claude/skills/<name>/` paths | 13 | 8 cite their own folder, 6 cite another skill |
| `sk` commands | 12 | Needs the rivendell CLI |
| launchd / Keychain | 6 / 1 | macOS services of this machine |
| Company and product names | 38 | Chimes, Yellow-Chick, PTI-ARES, Verdandi, and others |
| Client names | 13 | 中華電, 光泉, 力成, Sabre, and others |
| People | 7 | Mostly "Peter 2026-xx-xx" attributions |
| Prices | 5 | Day rates, a price list, one deal size |
| Security gaps | 1 | spine-rbac (2 more hits were false) |

Other findings:

- 17 skills are copies of third-party skills. 4 are Anthropic document skills
  (`office-*`) under a source-available licence: do not republish them. 2
  sources have no licence (excalidraw-diagram, mermaid-diagram): do not
  republish them. `task-brief` is adapted from a repo with no licence.
- 5 global hooks and 2 project hooks come from skill scripts. A plugin can
  ship hooks in `hooks/hooks.json`, so `sk hooks install` is not needed there.
- 93 skills name other skills in their text. 16 of the public candidates
  name gstack skills. gstack is public, so these names can stay.
- `sk check portability` exists. It checks hardcoded home paths for a move to
  another machine of the same owner. It does not check names, prices, `sk`
  use, or licences. SKILL-LEAK-CHECK extends it. It does not add a second tool.
- 2 public forks of the old rivendell exist. They keep the content of the day
  they were made. The private switch does not change them.

## Never public

These items stay out of every public build, whatever the owner decides about
names in general:

- `spine-rbac`: the line on security gaps of the products (MFA, operator
  login audit).
- `sow-writer`: the Sabre deal size and the day rates.
- `gov-rfq-writer`: the price list.
- `gov-subsidy-writer`: the decision on a related case that was not disclosed.
- `slide-office-hours`, `slide-workflow`: facts about named clients.
- `sales-customer-intel`: the name of a client's IT manager in an example.
- `chart-design/styles/`: the per-project and per-client style files.

## Verdicts

| Verdict | Skills | Meaning |
|---|---|---|
| `public` | 48 | Publish. The export script does the path rewrites |
| `public-edit` | 15 | Publish after small hand edits (names, attributions, optional `sk` steps) |
| `public-split` | 26 | Publish after company material moves to `internal/` |
| `upstream` | 17 | Third-party copy. Do not republish. The README points to the source |
| `team` | 3 | Company product rules. Team build only |
| `private` | 25 | Personal or rivendell-only. Stays in rivendell |

Thus 89 skills can go public. The per-skill table is in the appendix.

## Design

1. **One source.** Skills stay in rivendell. Each SKILL.md gets a frontmatter
   field `share: public | team | private`. A skill with no field is private.
2. **`internal/` for company material.** Product references, client cases,
   prices and run records move into `internal/` in the skill folder. The
   SKILL.md procedure stays generic and says: "If `internal/` exists, read it
   for company reference implementations." The public build drops
   `internal/`. The team build keeps it.
3. **Export command.** It copies the skills of one share level into a plugin
   layout (`skills/<name>/`, no category folders). It rewrites
   `~/.claude/skills/<x>/` to `${CLAUDE_PLUGIN_ROOT}/skills/<x>/`. It writes
   `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and
   `hooks/hooks.json` from the hook manifest entries of exported skills.
   It writes a README that lists the upstream skills and where to install them.
4. **Leak check.** `sk check portability --public <dir>` fails on:
   names from a private denylist (`data/public-denylist.txt`: products,
   clients, people, domains), machine patterns (`sk <cmd>`, `~/Code/`,
   `~/Work/`, `/Users/`, `rivendell`, `reports/`, `.learnings/`), prices,
   references to skills that are not in the build, and third-party copies.
   The export runs the check and stops on a hit.
5. **`sk` steps.** A public skill must work without `sk`. Each `sk` step
   becomes optional ("if `sk` is installed") or moves into the skill's own
   `scripts/`.
6. **New repo, new history.** The public repo is made from the export
   output. Nothing is pushed from rivendell to it.

The scan finds only the names it knows. Thus each skill also gets a human
read before its first publish.

## Tickets

### SKILL-SHARE-FIELD

Goal: every skill states its share level.
Executor: Claude (rivendell configuration).

Acceptance:

- 134 SKILL.md files have `share:` with the value from the appendix table.
- `sk check` reports a skill without `share:`.
- README catalog and `routing-tests.json` stay unchanged.

### SKILL-LEAK-CHECK

Goal: a repeatable check that a build folder holds no coupling.
Executor: Codex.

Acceptance:

- `sk check portability --public <dir>` exits 1 and prints file:line for
  each hit of the 5 rules in Design item 4.
- `data/public-denylist.txt` is read from rivendell only. It is never copied
  into a build.
- Tests: one fixture folder for each rule, plus one clean folder.

### SKILL-EXPORT

Goal: one command makes a plugin folder for a share level.
Executor: Codex. Depends on SKILL-SHARE-FIELD and SKILL-LEAK-CHECK.

Acceptance:

- `sk skills-export --share public --out <dir>` makes the layout in Design
  item 3. `--share team` also includes `team` skills and `internal/` folders.
- The command runs the leak check on a public build and stops on a hit.
- `claude --plugin-dir <dir>` loads the skills, as `/<plugin>:<skill>`.
- The output has no symlinks and no files from outside the skill folders.

### SKILL-PUBLIC-PILOT

Goal: the first public release with the 48 `public` skills.
Executor: Claude (review). The owner creates the repo and pushes.

Acceptance:

- Export passes the leak check.
- Claude read each of the 48 skills and found no company material.
- One install test on a clean `~/.claude` (another user account or machine):
  `/plugin marketplace add`, `/plugin install`, then one skill runs.

### SKILL-EDIT-BATCH

Goal: the 15 `public-edit` skills pass the leak check.
Executor: Claude (text edits). Script changes go to Codex.

### SKILL-SPLIT-1, SKILL-SPLIT-2, SKILL-SPLIT-3

Goal: the 26 `public-split` skills pass the leak check, and the team build
keeps every reference they had.
Executor: Claude (text edits). Script changes go to Codex.

- SPLIT-1: the 6 `spine-*` skills, `app-ops-baseline`, `dev-size-gate`.
- SPLIT-2: the slide and sales family: `slide-workflow`, `slide-office-hours`,
  `slide-template-extractor`, `chart-design`, `sow-writer`,
  `discovery-interview`, `metadata-workshop`, `sales-customer-intel`,
  `gov-rfq-writer`, `gov-subsidy-writer`.
- SPLIT-3: the rest (backend, ML, QA, `rule-status-report`).

Acceptance for each batch: leak check passes on a public build; a team build
holds every removed reference in `internal/`; routing check passes.

### SKILL-TEAM-BUILD (later)

Goal: teammates install public and team skills from a private marketplace.
Start when the first teammate needs it.

## Decisions (Peter, 2026-10-23)

1. Product names (Yellow-Chick, PTI-ARES, ChimesERP, ...) do not go into
   public text. They go to `internal/`.
2. Prices and day rates go to `internal/` only.
3. Licence of the public repo: MIT.
4. The public repo is under the personal account `manibari`. The repo name
   and the plugin name are set in SKILL-PUBLIC-PILOT.
5. `task-brief`: Claude rewrites it without the skill-lab text. It stays
   `public-edit`.
6. `timeleft-style`, `artcraft-conventions`: private.
7. The 2 public forks of the old rivendell: open. The owner was told what
   they are on 2026-10-23.

## Risks

- The denylist is incomplete. Mitigation: the human read in each publish
  ticket, and the default share level is private.
- `internal/` and the public text drift. Mitigation: the procedure lives only
  in SKILL.md; `internal/` holds references, not steps.
- A teammate build and a public build differ. Mitigation: one export command
  makes both.

## Appendix: per-skill table (scan of 2026-10-22)

"Refs to non-public skills": other skills that a public skill names in its
text. Each one becomes optional text, or the other skill joins the build.

### public (48)

| Skill | Loop | Coupling found | Work | Refs to non-public skills |
|---|---|---|---|---|
| `agent-dispatch` | platform | - | - | - |
| `agent-persona` | platform | - | - | agent-headless, agent-launchd |
| `audio-transcription-flow` | dev | - | - | - |
| `db-migration` | dev | - | - | - |
| `doc-to-structured-data` | shared | - | - | office-docx, office-pdf, office-xlsx |
| `docker-compose-setup` | dev | - | - | - |
| `firebase-backend` | dev | - | Emails are placeholders | - |
| `imap-smtp-integration` | dev | - | - | - |
| `markdown-file-ssot` | dev | - | - | - |
| `oauth-token-vault` | dev | - | - | - |
| `rbac-permissions` | dev | - | - | - |
| `sqlite-to-postgres` | dev | - | - | - |
| `telegram-bot` | dev | - | - | - |
| `tunnel-proxy-deploy` | dev | - | Ports are examples | - |
| `vector-search-setup` | dev | - | - | knowledge-graph |
| `gdoc-report-builder` | shared | - | - | office-docx, office-pptx |
| `iot-factory-report` | shared | - | Check that examples hold no client data | office-pptx, office-xlsx |
| `ios-integration` | dev | - | - | - |
| `swiftui-patterns` | dev | - | - | - |
| `concurrent-session-git` | dev | - | - | auto-stage |
| `gov-subsidy-scraper` | gov | prices x1 | The price hit is a public programme cap | - |
| `gov-tender-scraper` | gov | - | - | - |
| `hr-candidate-analysis` | hr | - | Check that examples hold no candidate data | invest-research, knowledge-graph, office-pdf |
| `hr-jd-writer` | hr | - | - | office-docx |
| `mops-financial-scraper` | invest | - | - | invest-research, office-xlsx |
| `subtitle-file` | knowledge | - | - | - |
| `video-clip-extract` | knowledge | - | - | - |
| `requirement` | dev | - | - | planning-with-files |
| `user-flow` | dev | - | - | excalidraw-diagram, frontend-design, mermaid-diagram, ui-ux-pro-max |
| `qa-auto` | dev | - | - | - |
| `qa-planner` | dev | - | - | executing-plans, writing-plans |
| `qa-testing` | dev | - | - | - |
| `github-repo-audit` | dev | - | - | - |
| `protect-secrets` | platform | own deploy path | Hook into plugin hooks.json | - |
| `presales-pipeline` | sales | - | - | sales-crm-projection |
| `sales-client-kickoff-docs` | sales | - | - | - |
| `sales-keyword-discovery` | sales | - | - | - |
| `sales-material-health` | sales | - | - | - |
| `tw-company-lookup` | shared | clients: 奇美 | 奇美食品 is a public listed-company example | invest-research |
| `ci-pipeline` | dev | - | - | - |
| `deploy` | dev | - | - | - |
| `dev-process-gate` | dev | - | - | planning-with-files |
| `env-doctor` | dev | - | - | - |
| `init-project` | dev | - | - | - |
| `plan-check-style` | dev | - | - | - |
| `repro-exam` | dev | - | - | - |
| `settings-audit` | platform | - | - | - |
| `setup-permissions` | dev | - | - | - |

### public-edit (15)

| Skill | Loop | Coupling found | Work | Refs to non-public skills |
|---|---|---|---|---|
| `pitch-deck` | shared | names: Chimes; clients: cht-corporate | Template examples chimes-ai / cht-corporate to neutral names | office-pptx |
| `slide-review` | sales | sk deck-preflight; own deploy path; rivendell x2 | `sk deck-preflight` becomes optional | - |
| `local-media-transcribe` | knowledge | repo paths knowledge/videos | knowledge/videos vault path becomes a setting | - |
| `video-transcript` | knowledge | rivendell x1; repo paths knowledge/videos | knowledge/videos vault path becomes a setting | - |
| `yt-channel-scraper` | knowledge | rivendell x3; repo paths knowledge/videos, reports | reports/ and vault paths become settings | - |
| `mockup` | dev | path to chart-design; rivendell x2; people: Peter | Peter attribution out; chart-design path via export rewrite | - |
| `system-design` | dev | sk check; rivendell x1; names: PTI-ARES/Verdandi/Norns | `sk check` optional; PTI-ARES / Verdandi example refs to internal/ | planning-with-files, writing-plans |
| `qa-journey` | dev | rivendell x1; repo paths reports | reports/ path becomes a setting | - |
| `de-slopify` | shared | - | Derived from blader/humanizer (MIT): keep its notice | - |
| `say-it-plain` | shared | names: PTI-ARES | PTI-ARES origin line to neutral | - |
| `sales-material` | sales | path to office-pptx; repo paths reports; names: Chimes; clients: 奇美/cht-corporate | Template names to neutral; depends on office-pptx (upstream) | office-pptx |
| `claude-to-telegram` | platform | path to claude-to-im | Third-party install guide; fix the claude-to-im path | - |
| `context-journal` | platform | sk hooks/deploy; own deploy path; rivendell x3; repo paths data/global-hooks.json; names: Yellow-Chick/PTI-ARES | Hooks into plugin hooks.json; `sk hooks` text optional | auto-stage, session-wrap, sync-readme |
| `context-recovery` | platform | repo paths .learnings | .learnings/ becomes optional | self-improving-agent |
| `task-brief` | dev | sk run; rivendell x1 | Adapted from Jacktsai2785/skill-lab (no licence): rewrite without its text (decision 5); `sk run` optional | planning-with-files |

### public-split (26)

| Skill | Loop | Coupling found | Work | Refs to non-public skills |
|---|---|---|---|---|
| `ai-vision-extract` | dev | rivendell x1; ~/Code: iihi; names: other-own-repo | iihi source refs to internal/; pattern has n=1 | - |
| `backend-async-jobs` | dev | names: Chimes/Verdandi/Norns | ChimesFlow / Verdandi precedents to internal/ | - |
| `cloudflare-tunnel-ops` | dev | names: Chimes | ChimesFlow GCP-VM case to internal/ | - |
| `cloudflare-tunnel-provision` | dev | names: Chimes | Family-Fiscal / ChimesFlow cases to internal/ | - |
| `ml-eval-quality` | dev | ~/Code: Verdandi-AutoML; names: Verdandi/Norns | Verdandi-AutoML source refs to internal/ | - |
| `ml-model-registry` | dev | ~/Code: Verdandi-AutoML; names: Verdandi/Norns | Verdandi-AutoML source refs to internal/ | - |
| `spine-assistant` | dev | rivendell x1; ~/Code: Yellow-Chick/PTI-ARES/Skuld; names: Chimes/Yellow-Chick/PTI-ARES/Verdandi/Norns/CoBuild | Whole reference table and ChimesERP section to internal/ | agent-code-dispatch, agent-headless, mcp-builder |
| `spine-auth` | dev | rivendell x2; repo paths docs/spine-modules.md; ~/Code: ChimesFlow/Family-Fiscal; names: Chimes/Verdandi/Norns/Tukey/ic-yms/lorien | Product table to internal/ | - |
| `spine-rbac` | dev | rivendell x1; ~/Code: Family-Fiscal/ChimesFlow; names: Chimes/Yellow-Chick/PTI-ARES; security gaps | Admin-surface audit to internal/; the security-gap line never public | - |
| `spine-roadmap` | dev | rivendell x2; ~/Code: Yellow-Chick/ChimesFlow/PTI-ARES; names: Chimes/Yellow-Chick/PTI-ARES; people: Peter | YC / PTI-ARES / ChimesFlow refs to internal/; Peter quotes out | doc-drift-sync |
| `spine-schema-sync` | dev | rivendell x1; ~/Code: ChimesFlow/mops_dbs/Family-Fiscal; names: Chimes/other-own-repo | Product refs to internal/ | - |
| `spine-versioning` | dev | rivendell x1; repo paths reports; ~/Code: ChimesFlow/Family-Fiscal/Yellow-Chick; names: Chimes/Yellow-Chick | Product refs to internal/ | - |
| `chart-design` | shared | path to archify; rivendell x6; repo paths .learnings; ~/Code: ChimesERP; names: Chimes/other-own-repo/kuangchuan; clients: 力成/詠鋐/中華電/光泉; people: manibari | styles/ per project to internal/; client names out | excalidraw-diagram, mermaid-diagram, office-pptx |
| `discovery-interview` | sales | ~/Documents; names: lorien; clients: 力成 | lorien template paths: inline the templates or internal/ | - |
| `metadata-workshop` | sales | ~/Documents; names: lorien; clients: Sabre | lorien paths and the Sabre example to internal/ | - |
| `rule-status-report` | shared | names: PTI-ARES | PTI-ARES worked example to internal/ | internal-comms, session-wrap |
| `slide-office-hours` | sales | path to slide-workflow; own deploy path; clients: 光泉/中華電/力成; people: Peter | Client matrix (光泉, 力成, 中華電) to internal/; Peter quotes out | - |
| `slide-template-extractor` | sales | names: Chimes/Tukey; clients: 中華電/Sabre/CHT/cht-corporate | Chimes / CHT template refs to internal/ | office-pptx |
| `slide-workflow` | sales | sk work-root; rivendell x1; names: Chimes/PTI-ARES; clients: 中華電/詠鋐/光泉/CHT/cht-corporate; people: Peter | Brand templates, 光泉 anecdotes, Gate 7 work-folder rules to internal/; hook into plugin | autoresearch, office-pptx, sales-crm-projection, ui-ux-pro-max |
| `sow-writer` | shared | ~/Documents; names: lorien/PTI-ARES; clients: Sabre; prices x13 | Day rates and the Sabre deal (150 人天, NTD 1.5M) to internal/ | office-docx, writing-plans |
| `gov-rfq-writer` | gov | clients: 力成; prices x7 | Price list (NTD 30-50 萬 ...) to internal/ | - |
| `gov-subsidy-writer` | gov | people: Peter | Remove the related-case non-disclosure line; case details to internal/ | - |
| `app-ops-baseline` | dev | ~/Code: Yellow-Chick; names: Chimes/Yellow-Chick | ChimesFlow code is the reference: inline the pattern, refs to internal/ | chimesflow-design |
| `qa-dataflow` | dev | ~/Code: PTI-ARES/Verdandi-AutoML; ~/Library; launchd; names: PTI-ARES/Verdandi/Norns | PTI-ARES / Verdandi examples to internal/; hook into plugin | mermaid-diagram |
| `dev-size-gate` | dev | rivendell x3; names: Yellow-Chick/PTI-ARES/other-own-repo | YC D37 / PTI-ARES tests refs to internal/ | - |
| `sales-customer-intel` | sales | repo paths reports; ~/Documents; names: other-own-repo; clients: 奇美; prices x2 | sales-assistant paths and a person's name in an example out | invest-research |

### upstream (17)

| Skill | Loop | Coupling found | Work | Refs to non-public skills |
|---|---|---|---|---|
| `mcp-builder` | dev | - | anthropics/skills, Apache-2.0 | - |
| `doc-coauthoring` | shared | - | anthropics/skills (per-skill licence) | - |
| `excalidraw-diagram` | shared | - | coleam00 repo has no licence: do not republish | - |
| `internal-comms` | shared | - | anthropics/skills (per-skill licence) | - |
| `mermaid-diagram` | shared | - | mgranberry repo has no licence: do not republish | - |
| `office-docx` | shared | clients: Sabre; prices x4 | Anthropic document skill, source-available licence; also holds Sabre figures | - |
| `office-pdf` | shared | - | Anthropic document skill, source-available licence | - |
| `office-pptx` | shared | ~/Library | Anthropic document skill, source-available licence | - |
| `office-xlsx` | shared | ~/Library | Anthropic document skill, source-available licence | - |
| `frontend-design` | dev | - | anthropics/skills, Apache-2.0 | - |
| `ui-ux-pro-max` | dev | own deploy path | nextlevelbuilder, MIT | - |
| `resolving-merge-conflicts` | dev | rivendell x2 | mattpocock/skills, MIT | - |
| `executing-plans` | dev | - | obra/superpowers, MIT | - |
| `planning-with-files` | dev | - | OthmanAdi/planning-with-files, MIT | - |
| `writing-plans` | dev | - | obra/superpowers, MIT | - |
| `skill-creator` | platform | ~/Downloads | anthropics/skills, Apache-2.0; already installed as anthropic-skills:skill-creator | - |
| `writing-great-skills` | platform | rivendell x1 | mattpocock/skills, MIT | - |

### team (3)

| Skill | Loop | Coupling found | Work | Refs to non-public skills |
|---|---|---|---|---|
| `ic-lot-normalization` | dev | ~/Code: IC-YMS | IC-YMS domain rules | - |
| `odb-dfm-reference` | dev | ~/Code: PTI-ARES; ~/Vault; names: PTI-ARES; people: Peter | PTI-ARES domain; cites ~/Vault/Peter | - |
| `chimesflow-design` | dev | ~/Code: ChimesFlow; names: Chimes | ChimesFlow design system | - |

### private (25)

| Skill | Loop | Coupling found | Work | Refs to non-public skills |
|---|---|---|---|---|
| `agent-code-dispatch` | dev | sk code/check; rivendell x2; repo paths platform/deployment; Keychain; names: Yellow-Chick | Built on `sk code`, the GMI proxy and Keychain | - |
| `agent-headless` | platform | sk agent; rivendell x5; repo paths reports, scripts/parse-agent-log.py; ~/Library/Documents; launchd; names: other-own-repo | rivendell agent runner (`sk agent`, launchd, reports/) | - |
| `agent-launchd` | platform | rivendell x1; repo paths reports; ~/Library/Documents/Desktop/Downloads; launchd | rivendell launchd agents | - |
| `agent-observability` | platform | rivendell x3; repo paths reports; ~/Library; launchd | Reads rivendell reports/ | - |
| `timeleft-style` | dev | names: Artcraft | Artcraft PhotoCraft theme (decision 6) | - |
| `auto-stage` | platform | own deploy path | rivendell project hook | - |
| `repo-rename` | platform | rivendell x3; ~/Documents/Library; launchd | rivendell launchd and repo moves | - |
| `invest-research` | invest | ~/Documents; names: other-own-repo | Personal investing | - |
| `knowledge-graph` | knowledge | rivendell x9; repo paths scripts/kg.py | Adapted from jdrhyne (MIT) but wired to rivendell kg.py | - |
| `audit-fix` | platform | sk audit; repo paths reports; ~/Documents | rivendell `sk audit` | - |
| `doc-drift-sync` | platform | sk check; rivendell x2; repo paths reports | rivendell reports/ | - |
| `learnings-promotion-sprint` | platform | rivendell x8; repo paths .learnings, reports; ~/Documents | rivendell .learnings/ | - |
| `self-improving-agent` | platform | own deploy path; rivendell x4; repo paths .learnings, reports; ~/Documents | rivendell .learnings/ and global hook | - |
| `session-harvest` | platform | repo paths .learnings, reports | rivendell reports/ | - |
| `session-wrap` | platform | repo paths .learnings | rivendell .learnings/ | - |
| `skill-apply` | platform | rivendell x4; ~/Code: matt-skills; names: Chimes/PTI-ARES | Run records from own repos | - |
| `skill-scout` | platform | sk deploy; path to skill-a/skill-b; rivendell x16 | Ports skills into rivendell (`sk deploy`) | - |
| `sync-readme` | platform | sk readme; own deploy path; rivendell x11; repo paths scripts/generate-readme-catalog.py | rivendell README hook | - |
| `token-quota-log` | platform | sk deploy/hooks; rivendell x1; repo paths data/global-hooks.json, platform/monitoring | rivendell token monitoring | - |
| `workflow-retro` | platform | rivendell x3; repo paths .learnings, reports; launchd | rivendell reports/ | - |
| `sales-crm-projection` | sales | repo paths reports; ~/Documents; names: other-own-repo | Own sales-assistant repo | - |
| `app-installer` | dev | rivendell x3; ~/Code: Artcraft/Norns-Verdandi-AutoML; ~/Library; names: Verdandi/Norns/Artcraft | Artcraft / Verdandi installers, launchd | - |
| `artcraft-conventions` | dev | ~/Code: Artcraft; names: Artcraft | Artcraft conventions (decision 6) | - |
| `autoresearch` | dev | - | Wired to agent-headless and the dashboard | - |
| `gdrive-to-skills` | knowledge | - | Writes into the rivendell skills library | - |
