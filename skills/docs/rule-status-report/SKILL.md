---
name: rule-status-report
loop: shared
pdca: do
description: >
  Periodic client-facing status report for a rule / check engine (DFM checks, QA rules,
  compliance rules, detection models): which rules are done, what they caught versus
  ground truth, and what is due next — as a fixed-size HTML deck plus PDF the client can
  read without an engineer in the room. Fixed rhythm: build the backing status files
  first (every number traceable), confirm the frame with the user BEFORE writing pages,
  generate, screenshot every page and self-check readability, converge on feedback.
  TRIGGER when: "開發週報", "規則完成度", "規則狀態", "異常要不要寫上去",
  "這樣客戶看得懂嗎", "對帳結果寫進報告", "recall 報告", or a project with a rule list +
  ground-truth reconciliation that needs a periodic report to a client. Use it even when
  the user only says "做這期的報告" in such a project.
  SKIP: a general status update with no rule list (internal-comms); internal progress notes or HANDOFF (session-wrap); sensor time-series reports
  (iot-factory-report); a sales / pitch deck (slide-workflow); drawing a single chart
  (chart-design).
version: 1.0.0
tags: [docs, report, client, rules, weekly]
user_invocable: true
---

# Rule Status Report

A periodic report to a client about a rule engine's progress. The recurring failure is
not missing data — it is writing an engineer's changelog ("底層換了一輪，行為零變動")
when the client wants to know: what can I use now, did it catch what the reference tool
catches, and what is due next. The first PTI-ARES draft of 2026-09-23 was 14 pages of
engineering headlines and was rejected outright; the shipped version was 8 pages framed
by the product's modules. This skill makes the frame decision explicit and early, so
the rewrite happens on an outline, not on finished pages.

**Announce at start:** "I'm using rule-status-report for the <date> report."

## Step 0 — Find the previous period and the house style

1. Locate the report folder convention (e.g. `docs/reports/weekly-YYYY-MM-DD/`) and the
   **previous** period's folder. Every number this period is shown against last period.
2. Read the project's design file (`DESIGN.md` or similar) for the client-document
   style. If none exists, ask once; do not invent a brand.
3. Read the previous period's `HANDOFF.md` / "沒做到的" list — unfinished items from
   last period are the first candidates for this period's pages.

## Step 1 — Backing files first (numbers before pages)

Write the evidence as markdown in the period folder before any HTML. Every number on a
page must point to a line in one of these:

| File | Content |
|---|---|
| `rules-status-<date>.md` | One row per rule: stage/group, enabled, how many inputs it ran on, hits, ground truth, TP/FN/FP, implementation state. Then a per-group summary table. |
| `reconcile-<date>.md` | Recall per stage against the reference tool, **with last period's value and the delta**, plus the exact command used to produce it. |

Rules that govern these files (each came from a real mistake):

- **State the scope (口徑) on every table**: which inputs, which rule-library version,
  which inputs were excluded and why. If two inputs ran on different versions, say so;
  do not silently mix them.
- **"0 hits" is not "passed".** Split zero-hit rules into: A skipped (missing input),
  B ran with 0 hits but no ground truth (**unverified**, never "驗證通過"), C has ground
  truth but 0 hits (**a real miss, chase it**), D engine did not report whether it ran
  (**unknown — that is itself a product gap**). See
  [references/zero-hit-classes.md](references/zero-hit-classes.md).
- **Recall covers only the rules the reference tool reported on.** Say how many enabled
  rules sit outside the denominator. "Recall of 4 families standing in for 16 rules" must
  be visible, not implied.
- **A number that dropped needs a reason next to it**: a real regression, a scope change
  (anchor point, granularity), or a deliberate decision. Never leave a red delta
  unexplained.
- **The user's memory beats stale docs.** When the user says "我不是已經做完 48 條？",
  verify against code and current output, then fix the doc — do not argue from the doc.
- **Measure without touching production output.** Use preview / dry-run modes; if the
  only way to refresh a number is to overwrite an artifact the client relies on, keep the
  old number and label it with its date.

## Step 2 — Frame gate: confirm the outline before writing pages

Draft a one-line-per-page outline and confirm it with AskUserQuestion. Ask about the
frame, not the wording. Decisions to put to the user (only the ones that are open):

1. **Organizing axis.** Default: the product's own modules as the client knows them
   (e.g. ① 匯入 ② CAD 工作台 ③ 判規則 ④ 回答與交付), each page = "what the client can do
   now", not "what we refactored". Internal restructuring gets one line, or nothing.
2. **Cover page.** Default: the items due at the next acceptance date, each with status
   and a pointer to its page — the client reads the cover and maybe nothing else.
3. **Anomalies and misses.** Default (user decision 2026-09-23): write every rule's done /
   not-done and every detected anomaly directly, with its reason. Hiding a miss costs
   more trust than showing it.
4. **What needs the client's answer.** A closing page of open decisions, each phrased as
   a question the client can answer.
5. **Page budget.** Default 8 ± 2 pages. More pages usually means changelog creep.

Headline test for every page: could the client repeat it to their boss? "規矩從 49 條
長到 59 條，但有幾條跟驗證了幾條是兩件事" passes for an engineer, fails for a client;
"S4 抓到率 63.0% → 81.5%，門檻 80% 已達" passes.

## Step 3 — Generate

- Fixed page size (e.g. 1600×900) HTML, one `<section class="slide">` per page, page
  number and date in the footer, following the project design file.
- One real product screenshot per module page when possible. Capturing a logged-in UI
  needs credentials: give the user a command to run in their own terminal (not the
  Claude Code `!` prefix — no TTY), never type credentials for them.
- Figures go through `chart-design` (it owns canvas fill, label collision, and the
  "same axis = same metric" rule).
- Export PDF with Playwright / headless Chrome from the same HTML.
- Keep `index-draftN.html` when a draft is rejected, so the next period can see what
  did not work.

## Step 4 — Self-check every page before showing the user

Screenshot each page (headless Chrome at the fixed size) and look at every image:

- No overflow: measure each page's content box against the page size.
- No label on a line, no clipped table, nothing under 10px unless the design allows it.
- Every number on the page appears in a backing file (spot-check at least the cover
  numbers and every delta).
- Read the headlines alone, in order: do they tell the period's story?

Then show the user the screenshots, not just the file path. Mechanical checks miss what
a human sees in one glance.

## Step 5 — Converge and hand off

Apply feedback at the level it was given: frame feedback goes back to Step 2 (outline),
not into patching pages. When done, write `HANDOFF.md` in the period folder: what
shipped, what was planned but not done (and how to finish it), open questions for next
period. The next run starts from it.

## Boundaries

- Does not change rules, thresholds, or the engine. Findings that need engineering work
  become a line under "建議另開票" in the backing file.
- Does not send the report. Delivery to the client is the user's call.
