# Zero-hit classes

A rule that produced 0 hits on the reference inputs can mean four different things.
Classify every zero-hit rule before any page says "passed" or "clean".

| Class | Condition | What the report may say |
|---|---|---|
| A skipped | Engine reports the rule skipped (missing layer / object) | "未執行：<skip reason>" |
| B ran, no ground truth | Executed, 0 findings, reference tool never reported this rule | "有跑、這批輸入上未觸發" — never "驗證通過"; there is no external evidence 0 is correct |
| C ground truth > 0 | Reference tool reported N, we reported 0 | A real miss unless a documented decision or scope difference explains it; list the reason per rule |
| D coverage unknown | Engine did not report executed / skipped for this rule | "判不出來" — and flag it as a product gap: the check plan cannot show why a rule did not run |

How to classify: read the engine's per-rule coverage output (in PTI-ARES:
`out/diagnostics.json` → `rule_coverage` with `executed` / `skipped` / `skip_reason`),
cross it with the reference ground truth, and put the counts in a table with the
denominator (all enabled rules), not only the zero-hit ones.

Also check the reverse: rules that DID hit but have no coverage record belong to the
same gap (PTI-ARES 2026-09-23: 21 of 59 enabled rules had no coverage record; 8 of them
had hits).

Worked example: PTI-ARES `docs/reports/weekly-2026-09-23/rules-status-2026-09-23.md`.
