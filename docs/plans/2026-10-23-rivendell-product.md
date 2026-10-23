# rivendell as a product: the dev flow and the deck flow

Date: 2026-10-23. Owner: Peter. Planner and reviewer: Claude. Executor: see each ticket.
Status: approved 2026-10-23.
Replaces the design in `2026-10-22-skills-public-release.md`. Its per-skill
inventory (appendix) stays valid as evidence.

## Source

Peter, 2026-10-23:

- 「其實我還是想維持 rivendell 公開的狀態」
- 「而且也不用特別分公司私人」
- 「就單純我自己常用，可以整理成標準化產品的方式」
- 「如果公司常遇到 我個人會遇到 那就值得作為一個產品啊」

Done on the same day:

- `manibari/rivendell` is public again.
- 3f512df removed the lines about third parties (a person's name, a deal size,
  a non-disclosure decision, the security gaps of named products).
- ffe4a63 took the 4 Anthropic document skills (`office-*`) out of git. Their
  licence does not allow redistribution. They stay on the owner's disk.

## Goal

Another person adds the rivendell marketplace in Claude Code, installs a
plugin, and runs the flow from start to end on their own machine.

Not in scope:

- A split into company, team and private skills (dropped on 2026-10-23).
- The 94 skills with no use in the last 90 days. They stay as they are.
- The rivendell platform (`sk` scheduler, dashboard, agents).

## Evidence: what is used (2026-07-25 to 2026-10-23)

Source: Claude Code session logs, `Skill` calls and `SKILL.md` reads, one count
for each session. Not counted: Codex sessions, and skills that run as hooks.

| Skill | Sessions | Projects | Examples |
|---|---|---|---|
| agent-code-dispatch | 55 | 5+ | Yellow-Chick, PTI-ARES, Artcraft, mops-dbs |
| system-design | 22 | 5+ | Yellow-Chick, ChimesERP, TWstock-invest |
| spine-roadmap | 13 | 5+ | PTI-ARES, Verdandi-AutoML, ChimesFlow |
| mockup | 11 | 5 | Yellow-Chick, ChimesERP, mops-dbs |
| chart-design | 10 | 5 | ChimesERP, PTI-ARES, work folder |
| requirement | 8 | 5 | TWstock-invest, Yellow-Chick |
| slide-workflow | 7 | 4 | work folder, PTI-ARES |
| user-flow | 6 | 4 | TWstock-invest, Yellow-Chick |
| slide-office-hours | 5 | 4 | work folder, PTI-ARES |
| video-transcript | 5 | 4 | Yellow-Chick, PTI-ARES |

40 of 134 skills were used at least once. The ones above are used in company
projects and in personal projects. That is the product rule (Peter: a problem
that the company and the owner both meet is worth a product).

## The two products

| Plugin | Skills | Flow |
|---|---|---|
| `dev-flow` | requirement, user-flow, mockup, system-design, spine-roadmap, agent-code-dispatch, chart-design | requirement → screens → design → tickets → an executor writes the code → review |
| `deck-flow` | slide-office-hours, slide-workflow, slide-review, chart-design | storyline → slides → per-slide check |

`chart-design` is in both. `video-transcript` is the next candidate.

`deck-flow` needs Anthropic's `document-skills` plugin for `html2pptx`. The
README says how to install it.

## What stops another user today

From the 2026-10-22 inventory, for the 10 product skills:

| Blocker | Skills | Fix (ticket) |
|---|---|---|
| `~/.claude/skills/<name>/` paths. A plugin copy is not there | mockup, chart-design, slide-office-hours, slide-review | PRODUCT-PATHS |
| `sk` commands: `code exec`, `check`, `work-root`, `deck-preflight` | agent-code-dispatch, system-design, slide-workflow, slide-review | PRODUCT-NO-SK |
| Playwright from rivendell `node_modules`, no lockfile | chart-design, mockup, slide-review | PRODUCT-NODE |
| A global hook from `sk hooks install` (storyline gate) | slide-workflow | PRODUCT-HOOK |
| `html2pptx` from the local `office-pptx` copy | slide-workflow | PRODUCT-HOOK |
| Rules that read the owner's work folder (deck promotion) | slide-workflow | PRODUCT-NO-SK (optional step) |

References to the owner's other repos (for example Yellow-Chick code as an
example) stay. They do not stop a skill from running.

## Design

1. **The repo is the marketplace.** `.claude-plugin/marketplace.json` at the
   rivendell root lists the 2 plugins. Each entry uses `"source": "./"`,
   `"strict": false` and a `skills` list of paths, as
   `anthropics/skills` does. The category folders stay.
2. **A skill owns its scripts.** Each `sk` subcommand that a product skill
   calls moves into that skill's `scripts/`. `sk` keeps the subcommand as a
   thin wrapper, so the owner's commands do not change. A step that needs the
   owner's setup (work folder registry) says "if available".
3. **One path rule for both installs.** A file of another skill is found from
   the physical path of the current skill folder, so it works for the `sk
   deploy` symlink and for the plugin copy. PRODUCT-PATHS tests both.
4. **Node dependencies have a lockfile.** The setup step installs the Chromium
   that Playwright uses.
5. **Version.** Each plugin entry has a version. A release bumps it
   (spine-versioning).

## Tickets

### PRODUCT-MARKETPLACE

Goal: the 2 plugins install from GitHub.
Executor: Claude (configuration).

Acceptance:

- `/plugin marketplace add manibari/rivendell`, then
  `/plugin install dev-flow@<marketplace>` and `deck-flow@<marketplace>`.
- The skills show as `/dev-flow:<skill>` and `/deck-flow:<skill>`.
- The owner's `sk deploy` setup still works next to the plugins (no duplicate
  trigger on the same machine: the owner does not install the plugins).

### PRODUCT-PATHS

Goal: no product skill cites `~/.claude/skills/`.
Executor: Claude (text), Codex for scripts.

Acceptance: the rule in Design item 3 is in each product skill; one test runs
the chart-design checker through the mockup instructions from a plugin copy and
from the `sk deploy` symlink.

### PRODUCT-NO-SK

Goal: the product skills run with no `sk` on PATH.
Executor: Codex.

Acceptance:

- `code exec` (agent-code-dispatch), the check that system-design calls,
  `work-root` and `deck-preflight` run from the owning skill's `scripts/`.
- `sk` still runs each one with the same arguments and output.
- Existing tests pass; one test for each moved command.

### PRODUCT-NODE

Goal: a fresh install can run the figure checker and the slide review.
Executor: Codex.

Acceptance: a committed lockfile; one setup command in the README installs the
packages and Chromium; `check-html-figure.mjs` runs from a plugin copy.

### PRODUCT-HOOK

Goal: `deck-flow` brings its own storyline gate and uses the official pptx skill.
Executor: Codex for the hook, Claude for the skill text.

Acceptance: the gate runs from the plugin install with no `sk hooks install`;
`slide-workflow` finds `html2pptx` in the installed `document-skills` plugin,
and in the owner's local copy.

### PRODUCT-README

Goal: a Chinese README section: what the 2 products do, install, setup, the
flow in 5 lines each.
Executor: Claude.

### PRODUCT-INSTALL-TEST

Goal: proof on a clean setup.
Executor: the owner (another macOS user account or machine), Claude reviews.

Acceptance: install both plugins, then run one requirement → mockup →
system-design pass and one storyline → slides → review pass on a sample.

## Order

PRODUCT-MARKETPLACE first (small, shows the shape), then PRODUCT-NO-SK and
PRODUCT-PATHS, then PRODUCT-NODE and PRODUCT-HOOK, then README, then the
install test.

## Risks

- The owner's machine has the same skills twice (deploy and plugin) if the
  owner installs the plugins. Rule: the owner does not install them; the
  install test runs on another account.
- `agent-code-dispatch` needs a Codex login, and Qwen needs a GMI key. The
  README says this; the skill stops with a clear message when they are missing.
- Usage counts miss Codex and hooks. The product list may need a second look
  after one month.
