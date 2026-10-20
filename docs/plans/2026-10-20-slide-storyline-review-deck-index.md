# Slide pipeline: storyline genre, slide review, deck index

Date: 2026-10-20. Owner: Peter. Planner and reviewer: Claude. Executor: Codex.

Source: GitHub issues #1, #2, #3 (2026-06). Peter decided on 2026-10-20:
#1 re-evaluate, #2 still needed, #3 needed with a location for each machine.
The issues close after this plan records them (spine-roadmap, rule 3).

## Findings (2026-10-20)

- 4 storyline.md files exist on this machine. None is signed-off. 3 are for
  internal decks.
- `slide-office-hours` reviews B2B presales storylines only. An internal deck
  has no path to sign-off.
- `storyline-gate-hook.sh` checks only `status: signed-off`. Thus a draft
  storyline for an internal deck blocks .pptx output. The only exit is the
  escape hatch.
- The rules that issue #2 cites ("Diagram & Slide Output Defaults" in the
  global CLAUDE.md) are gone since the 2026-07-27 rebuild.
- `chart-design/references/check-html-figure.mjs` already checks one page:
  overflow, text wrap, small font, text overlap, canvas fill, empty band. It
  also makes an annotated screenshot.
- Real decks are folders of one HTML file per slide (html2pptx style). The
  body is `720pt x 405pt` (960 x 540 CSS px). Issue #2 assumed 1600 x 900.
- Real slides use 8-9pt text widely. The old rule "12px minimum on a 1600px
  canvas" is 0.75% of the canvas width. That ratio passes these slides.
- The work folder moved to `~/Work/ChimesAI` on 2026-10-08. `~/Vault` does not
  exist on this machine. The work folder already defines where finished decks
  go: drafts in `cache/`, finished files in `1-presales/presentations/`.
- 23 .pptx and 14 .pdf files are in `presentations/` folders now.
- rivendell `node_modules` was not installed on this machine. Thus
  `check-html-figure.mjs` failed. Claude ran `npm install` on 2026-10-20.

## Tickets

### SLIDE-STORYLINE-GENRE (from issue #1)

Goal: an internal deck can get a signed-off storyline without the presales
review. A presales deck still needs `/slide-office-hours`.

- Add a `genre` field to the storyline frontmatter:
  `presales | internal | talk | report | other`. No value means `presales`.
- New script `skills/docs/slide-workflow/scripts/storyline-selfcheck.sh`.
  It checks a non-presales storyline: `audience` and `expected_action` have a
  value, the body has at least one `## ` section, and no placeholder remains.
  With `--sign` it sets `status: signed-off`, `signed_by: self-check` and
  `signed_at`.
- The gate hook blocks a storyline that is `signed_by: self-check` when the
  genre is `presales` or empty.
- New template `skills/docs/slide-workflow/storyline-template-general.md`.
- Claude updates `slide-workflow` Gate 0 and the `slide-office-hours` intro.

Not done: the five-genre scaffolder skill from issue #1. Copying a template
is one command, and `slide-office-hours` already prints it.

### SLIDE-REVIEW (from issue #2)

Goal: before export, each slide gets a mechanical check and a visual check.
A failure gets a fix loop with a stop rule.

- New skill `skills/docs/slide-review/`. Claude writes `SKILL.md`. It holds the
  rules, because the old CLAUDE.md section is gone.
- New script `scripts/review-deck.mjs` (Codex). Input: a folder of slide HTML
  files, or one file. For each slide it measures the canvas from the body box,
  sets the minimum font to 0.75% of the canvas width, and runs
  `check-html-figure.mjs` with an annotated screenshot. It writes
  `review/iter-<n>/report.json` and prints a summary.
- With `--iter n` (n > 1) the script marks each check code that fails again on
  the same slide as `repeat`. The skill uses this mark for rule R6.
- Claude reads each screenshot for the rules that a script cannot check:
  separate colour boxes for separate concepts, one main label for each card.
- Fix loop: iteration 1 fixes small defects. A `repeat` defect in iteration 2
  needs a structural change, and the user approves it first. A failure in
  iteration 3 stops the loop and goes to the user.
- The skill writes `review.md` with `status: passed | failed-needs-user`.
- `slide-workflow` Gate 6.5 uses this skill for the visual check.

### DECK-INDEX (from issue #3)

Goal: each machine knows where the work folder is. A list of finished decks is
generated from that folder. A deck moves to its final place only after the
storyline and the review pass.

- New registry `platform/deployment/work-roots.conf` (symlink
  `data/work-roots.conf`): `HOST | KEY | PATH | NOTES`. First row: this machine,
  `chimes-work`, `~/Work/ChimesAI`.
- New script `scripts/work_roots.py`: `get <key>` and `check`. A host with no
  row gives an error. The script does not guess a path.
- New script `scripts/deck_index.py`: lists deck files (.pptx, .pdf, .key) in
  every `presentations/` folder. It skips `cache/`, `workspace/`, `archive/`,
  `封存/`, `素材/`, `範本/`. `--write` writes `<work root>/簡報索引.md`.
- New script `scripts/deck_preflight.py <deck dir>`: storyline signed-off and
  review passed. A missing file is "not read", not a pass.
- `bin/sk`: `sk work-root`, `sk deck-index`, `sk deck-preflight`, and a
  `[Work roots]` section in `sk check`.
- Internal and product decks also go into a `presentations/` folder when they
  are final. Claude adds this to `slide-workflow` Gate 7.

Not done: a separate archive folder (the old `~/Vault/Peter/decks/`). Decks in
`~/Downloads` are not indexed.

## Order

1. Codex runs the three tickets at the same time. They change different files.
2. Claude reviews each result with the six checks of `agent-code-dispatch`.
   Claude runs the browser checks outside the sandbox.
3. Claude writes the skill text: the `slide-review` SKILL.md and the changes
   to `slide-workflow` and `slide-office-hours`.
4. Claude updates the catalog files: README, skills-by-role, summaries, routing
   tests.
5. Claude asks Peter, then closes issues #1-#3 with a link to this plan.

## Open after this plan

- The work folder `CLAUDE.md` (`~/Work/ChimesAI/CLAUDE.md`) has its own
  promotion steps. A line that runs `sk deck-preflight` there is a decision for
  Peter. It is outside rivendell.
- The previous machine has no row in `work-roots.conf`. Add it when that
  machine runs `sk check`.
