# Findings — dashboard-next redesign

This file is intentionally thin. Authoritative knowledge lives in:

- `dashboard-next/DESIGN.md` — design tokens, brand assets, component patterns, decision log
- `docs/requirements/dashboard-redesign.md` — scope, user stories, acceptance criteria
- `dashboard-next/mockups/workflow-map-v4.html` — visual target
- `.learnings/LEARNINGS.md` (project root) — cross-session lessons (e.g. "logo-first beats full aesthetic redesign")

Use this file only for findings that emerge **during implementation** that don't yet belong in DESIGN.md / requirement / learnings — e.g. "tailwind ↔ CSS variables strategy choice", "React Flow gotcha", "next.js 16 migration friction".

---

## Implementation findings (added during Stage 1/2)

### Tailwind + CSS variables integration

_To fill during Task B2._ Two strategies on the table:
- **Strategy A** — Tailwind colors map to `var(--accent)` etc. via `'rgb(var(--accent-rgb) / <alpha-value>)'` pattern. Requires storing tokens as RGB triplets (not hex) for opacity to work.
- **Strategy B** — Tailwind colors map to `var(--accent)` directly as a string. Simpler but loses Tailwind's `bg-accent/50` opacity modifier.
- Decision: TBD when implementing B2. Default to A unless it adds friction.

### React Flow + Bezier connectors

_To fill during Task F3._ React Flow edges have a `type` prop with built-in `bezier`, `smoothstep`, `step`. The mockup uses custom-control-point Bezier curves. Decide whether to use built-in `bezier` (less control but zero code) or custom edge component (matches mockup exactly).

### workflow.json schema decisions

_To fill during Task E1._ The current `src/app/workflow/page.tsx` defines `CoreTrack`, `CoreStep`, `DomainStep`, `DomainFlow`, `Maintenance`, `Situational`, `Orphan` interfaces. The JSON schema should mirror these. Open question: are `mandatory` / `optional` skill arrays (under each step) the right shape, or does each skill need its own object with `{ name, role: 'mandatory' | 'optional', notes? }`?

### Self-host font checksums

_To fill during Tasks A1/A2._ Record SHA256 of downloaded woff2 files for verifiability. Useful for future colleague-onboarding to detect tampered downloads.

---

## Anti-discoveries (things that look like discoveries but aren't worth tracking)

- "Geist supports tabular-nums via `font-feature-settings: 'tnum' 1`" — already in DESIGN.md
- "Forest green is the only accent" — already in DESIGN.md, no need to re-discover
- "Self-host fonts" — already in DESIGN.md Portability section
