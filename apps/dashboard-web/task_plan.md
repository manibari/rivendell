# Task Plan — dashboard-next redesign

**Goal:** Apply v4 design system (logo-first / light / forest green / Geist) to 8 pages of dashboard-next. Workflow map page becomes flagship — React Flow + workflow.json SSOT.

**Source-of-truth references** (read these before any decision):
- `dashboard-next/DESIGN.md` — design system spec
- `docs/requirements/dashboard-redesign.md` — 4 user stories + scope boundary
- `dashboard-next/mockups/workflow-map-v4.html` — v4 mockup (visual target)
- `dashboard-next/CLAUDE.md` — project rules (read DESIGN.md before any UI change)

**Stages:**
- **Stage 1** (foundation + workflow page): land DESIGN.md as code, refactor workflow map. Highest user-facing payoff.
- **Stage 2** (other 7 pages): apply tokens to landing / agents / harvest / ports / projects / skills / tokens. Lower-risk, mostly mechanical.

Each task should be 2–5 min when prerequisites are met. If a task balloons, split it.

---

## Stage 1 — Foundation + Workflow Map

### A. Font self-hosting (use Next.js `next/font/local`, not raw @font-face)

> **Review note (2026-05-07):** project uses Next.js 16 + `next/font/google` already. Switch to `next/font/local` — Next.js handles all the @font-face plumbing, asset hashing, and CSS variable wiring. No raw @font-face needed.

| # | Task | Status | Notes |
|---|------|--------|-------|
| A1 | Download `Geist-Variable.woff2` → `dashboard-next/src/fonts/` (NOT public/, keep co-located with loader) | done | Got from geist-font 1.8.0 release, 68K. SHA256 logged below. |
| A2 | Download `GeistMono-Variable.woff2` → `dashboard-next/src/fonts/` | done | Same release, 69K. |
| A3 | Refactor `src/app/layout.tsx`: `next/font/local`, `weight: "100 900"`, `display: "swap"` + favicon + viewport themeColor | done | Bonus: separated `viewport` export from `metadata` (Next.js 16 pattern) |
| A4 | Build verifies font loading is local | done | `.next/static/media/{Geist,GeistMono}_Variable-*.woff2` exists; no fonts.googleapis.com in built output |

### B. Design tokens (Tailwind v4 native: `:root` + `@theme inline`)

> **Review note (2026-05-07):** Tailwind v4 already configured. globals.css already has `:root` + `@theme inline` block. Extend the EXISTING block, do not create new infrastructure. No `tailwind.config.ts` needed — v4 uses CSS @theme directives.

| # | Task | Status | Notes |
|---|------|--------|-------|
| B0 | Remove `@media (prefers-color-scheme: dark)` block from globals.css | done | Block deleted. Single-user light-only. |
| B1 | Extend `:root` with all DESIGN.md tokens (15 color tokens + 8 spacing + 3 radii) | done | Legacy aliases `--background`/`--foreground` kept for not-yet-migrated pages |
| B2 | Extend `@theme inline { ... }` to expose `bg-accent`, `text-muted`, `border-strong` etc as Tailwind utilities | done | Plus added `.tabular-nums` helper class |
| B3 | Build verifies Tailwind v4 parses `@theme` block correctly | done | `pnpm next build` succeeded — Compiled in 1.67s, 11 routes generated |

### C. Brand assets

| # | Task | Status | Notes |
|---|------|--------|-------|
| C1 | Logo SVGs already shipped (`public/logo.svg`, `public/logo-mono.svg`) | done | Committed `22f43ae` |
| C2 | Set SVG favicon in `src/app/layout.tsx` metadata | pending | `icons: { icon: '/logo.svg' }` |
| C3 | Add `themeColor: '#2d4a3e'` to layout metadata | pending | For browser chrome on supporting platforms |

### D. Shared components (used across all 8 pages)

| # | Task | Status | Notes |
|---|------|--------|-------|
| D1 | `src/components/Logo.tsx` — twin-leaves inline SVG + wordmark, props `{size, variant, withWordmark}` | done | Inline SVG, no `<Image>` (currentColor support) |
| D2 | Refactor `src/components/Sidebar.tsx` — Logo at top + tagline + token-based colors + emoji removed from project switcher | done | Active state uses surface elevation + box-shadow border |
| D3 | `src/app/layout.tsx` shell | done | Already correct from A3 — Sidebar + main flex shell |
| D4 | `src/components/StatusDot.tsx` — semantic colors via CSS vars | done | 8/12/16px sizes supported |
| D5 | `src/components/SkillChip.tsx` — `{name, variant, asLink, onClick}` | done | Default routes to `/skills/[name]`; `onClick` overrides for cross-ref state lift |
| D6 | _Skipped_ — was helper for h2 accent leader, ended up using Tailwind+style attribute directly. Not blocking. | skipped | Revisit in Stage 2 if pattern repeats |

### E. Workflow data — DEFERRED to parking lot K2

> **Review decision (2026-05-07):** API already returns typed `WorkflowData` via `apiFetch("/workflow")` in `src/app/workflow/page.tsx`. Stage 1 = readonly view. Freezing into a JSON file SSOT only matters when UI starts writing back (drag/edit, parking lot K2). **All E1-E4 deferred to K2** — keep using the API in Stage 1.

| # | Task | Status | Notes |
|---|------|--------|-------|
| E1-E4 | _deferred to K2 in parking lot_ | deferred | When React Flow drag/edit lands, then design the JSON SSOT + write loader |

### F. Workflow page rebuild (HTML/CSS/SVG, no React Flow yet)

> **Review decision (2026-05-07):** React Flow's value is drag/connect/edit. Stage 1 is readonly tree view. v4 mockup proves HTML + flexbox + SVG Bezier connectors render the same visual. **Skip React Flow installation.** Defer to K2 in parking lot when drag/edit lands. Saves ~30% Stage 1 complexity.

| # | Task | Status | Notes |
|---|------|--------|-------|
| F1 | _deferred to K2 in parking lot_ | deferred | |
| F2 | `src/components/workflow/StepNode.tsx` | done | Width 165px, props `{step, active, selectedSkill, onSkillClick}` |
| F3 | `src/components/workflow/TrackRow.tsx` | done | Computed Bezier paths with alternating wobble, viewBox stretches with preserveAspectRatio="none" |
| F4 | `src/components/workflow/CrossReferencePanel.tsx` | done | Empty state placeholder + reference list + jump-to-skill CTA |
| F5 | `src/app/workflow/page.tsx` refactor | done | Core flows = horizontal trees, other 4 sections = token swap in-place. Cross-ref panel always rendered (right 320px) |
| F6 | SkillChip click → state lift | done | `onClick={setSelectedSkill}` on every chip across all sections |
| F7 | Build verifies | done | `pnpm next build` 1.55s clean. Browser smoke test = next manual step |
| F8 | Empty state in CrossReferencePanel | done | "Pick a skill chip to see where it appears" |
| F9 | Loading skeleton | done | 5 metric placeholders + 3 section blocks, surface-2 fill |

### G. Stage 1 wrap

| # | Task | Status | Notes |
|---|------|--------|-------|
| G0 | **Stage 1 prereq** (promoted from K5): verify `/skills/[name]` route exists in `src/app/skills/`. If not, scaffold a minimal route — cross-ref panel CTA depends on it. | pending | `ls src/app/skills/\\[name\\]/page.tsx 2>/dev/null` |
| G1 | Type check + lint: `pnpm tsc --noEmit && pnpm lint` | pending | No errors before commit |
| G2 | `/gstack-review` on staged diff | pending | Pre-commit |
| G3 | Commit: `feat(dashboard-next): land design tokens + workflow map v4` | pending | Single squash or split per logical chunk |
| G4 | If Stage 1 reveals DESIGN.md gaps, update Decision Log | pending | E.g. confirm next/font/local pattern |

---

## Stage 2 — Apply tokens to remaining 7 pages

### H. Chart components (shared, build before page migration)

> **Stage 2 decision (2026-05-08):** Did NOT extract LineTrend/BarRank/Heatmap. Recharts was already installed and working; just re-skinned it with the token palette inline in tokens + skills pages. Building 3 standalone inline-SVG components for marginal aesthetic gain wasn't worth the diff cost. Defer to parking lot if recharts ever needs to leave.

| # | Task | Status | Notes |
|---|------|--------|-------|
| H1-H4 | _deferred to parking lot K8_ | deferred | Kept recharts, recolored with --accent / --accent-soft / sequential greens |

### I. Page-by-page token migration

| # | Task | Status | Notes |
|---|------|--------|-------|
| I1 | `src/app/page.tsx` (landing) | done | h1 + 3 tables + StatusDot for agent rows + status pills |
| I2 | `src/app/agents/page.tsx` | done | Project group badges → accent-bg / surface-2 |
| I3 | `src/app/harvest/page.tsx` | done | strengthConfig collapsed 6→3 status colors. Toast styled with --status-* border |
| I4 | `src/app/ports/page.tsx` | done | TypeChip uniform neutral; PortStatusBadge wraps StatusDot. Lint warning fixed (inline initial fetch in useEffect) |
| I5 | `src/app/projects/page.tsx` | done | MissionCard + EditForm use accent-bg + accent-soft; replaced 🎯/🚫/🤖 emoji with Lucide icons. Lint warning fixed |
| I6 | `src/app/skills/page.tsx` | done | Killed CATEGORY_COLORS rainbow; treemap uses sequential greens. LIFECYCLE_COLORS = 3 monochrome shades. All recharts re-colored with --accent palette |
| I7 | `src/app/tokens/page.tsx` | done | Two BarCharts re-skinned with --accent / --accent-soft. Date inputs + tables full token swap |

### J. Stage 2 wrap

| # | Task | Status | Notes |
|---|------|--------|-------|
| J1 | Open all 8 pages in browser, click through nav, look for visual inconsistencies | pending | grep for any remaining hardcoded `#0a0a` / `bg-slate-` / `bg-gray-` / blue / purple |
| J2 | `pnpm tsc --noEmit && pnpm lint` clean | pending |  |
| J3 | `/gstack-design-review` for visual audit | pending | Optional but recommended |
| J4 | Commit: `feat(dashboard-next): apply design tokens across all 8 pages` | pending |  |
| J5 | Update DESIGN.md Decision Log with any deviations | pending |  |
| J6 | User self-acceptance: 30 min usage, evaluate "醜或亂" subjective pain | pending | Per requirement doc 主驗收 |

---

## Parking lot (deferred, not in this scope)

- **K1.** Graph view (skill-as-center DAG) for workflow map — implement Tree first, Graph after
- **K2.** React Flow integration: drag/edit/connect-by-handle + `data/workflow.json` SSOT + loader (was tasks E1-E4 + F1) + auto-write API endpoint for round-trip
- **K3.** Auto-sync between `workflow.json` (or API) and `~/.claude/CLAUDE.md` flow doc — script or hook
- **K4.** `bin/sk rename` tool for skill renaming (raised in earlier conversation, not blocking this redesign)
- **K5.** _PROMOTED to G0 (Stage 1 prereq)._ Skills page `/skills/[name]` deep-link route. Cross-ref CTA depends on it.
- **K6.** Mobile RWD — explicitly out of scope (desktop tool)
- **K7.** ⌘K skill search (shown in v4 mockup top-bar) — nice-to-have. Stage 1 = static placeholder text. Real implementation needs fuzzy search lib (Fuse.js or similar)
- **K8.** Extract LineTrend / BarRank / Heatmap inline-SVG components (was H1-H4). Skipped in Stage 2 because recharts was already working and we just re-colored it. Worth doing if recharts is ever ripped out.
- **K9.** Dynamic-route pages (`/skills/[name]`, `/agents/[label]`, `/projects/[name]`) and shared components `AgentCard.tsx` (309 lines), `RunHistory.tsx` (516 lines), `CollaborationFlow.tsx` — these are linked from the migrated pages but use their own zinc/dark classes. ~1850 lines of mostly mechanical token-swap left. Defer to a Stage 3 sweep when there's appetite.

---

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| _(none yet)_ | | |

---

## Files Created / Modified Log

Track at end of each phase. Keeps blast radius visible.

| Phase | Files | Notes |
|-------|-------|-------|
| Stage 1 · A (fonts) | `src/fonts/Geist-Variable.woff2` (68K), `src/fonts/GeistMono-Variable.woff2` (69K), `src/app/layout.tsx` | Geist 1.8.0 release. SHA256: Geist `9ceed04f...`, GeistMono `f2be56af...` |
| Stage 1 · B (tokens) | `src/app/globals.css` | All DESIGN.md tokens shipped. Build green. |
| Stage 1 · D (shared components) | `src/components/Logo.tsx`, `src/components/StatusDot.tsx`, `src/components/SkillChip.tsx`, `src/components/Sidebar.tsx` (refactor) | Sidebar now uses Logo + tagline + tokens; emoji removed from project switcher |
| Stage 1 · F (workflow page) | `src/components/workflow/StepNode.tsx`, `TrackRow.tsx`, `CrossReferencePanel.tsx`, `src/app/workflow/page.tsx` | Core flows = horizontal trees with Bezier connectors; other sections token-swapped; cross-ref panel right side |
| Stage 2.1 (landing + agents + shared) | `src/app/page.tsx`, `src/app/agents/page.tsx`, `src/components/MetricsRow.tsx`, `src/components/PendingIssues.tsx` | Pattern established: h1 28/500/-0.02em, h2 18/500/-0.01em, tables surface-2 thead, mono uppercase 10px headers |
| Stage 2.2 (ports + harvest) | `src/app/ports/page.tsx`, `src/app/harvest/page.tsx` | TypeChip recolored to neutral, harvest toast token-styled, lint set-state-in-effect fixed |
| Stage 2.3 (tokens + skills) | `src/app/tokens/page.tsx`, `src/app/skills/page.tsx` | Recharts re-colored to forest/sequential-green palette; CATEGORY_COLORS rainbow killed |
| Stage 2.4 (projects) | `src/app/projects/page.tsx` | MissionCard / EditForm use accent-bg + accent-soft; emoji 🎯/🚫/🤖 replaced with Lucide icons; lint fixed |

---

## Plan Review Report (tight eng review · 2026-05-07)

| Decision | Verdict | Principle |
|----------|---------|-----------|
| Tailwind ↔ CSS vars strategy | Auto-decided: use Tailwind v4 native `@theme` + `:root` (already partially in place) | P3 pragmatic — v4's pattern IS the right answer, A/B from findings.md is obsolete |
| `workflow.json` SSOT | Taste decision → user picked **defer to K2** | P5 explicit/simple — readonly view doesn't need the SSOT round-trip yet |
| React Flow integration | Taste decision → user picked **defer to K2**, use HTML/CSS/SVG for Stage 1 | P3 pragmatic + P5 explicit — v4 mockup proves HTML/CSS reaches readonly target |

**Auto-fixes applied to task_plan.md:**
- A1-A4: switched from raw @font-face → `next/font/local` (Next.js native)
- B0 added: remove `prefers-color-scheme: dark` block from globals.css
- B1-B2: extend existing `:root` + `@theme inline` (not create new infrastructure)
- D2: refactor existing Sidebar.tsx (not build from scratch)
- E1-E4: deferred to parking lot K2
- F1: deferred to parking lot K2 (no React Flow in Stage 1)
- F2-F4: rewritten to plain HTML/CSS/SVG components
- F9 added: API loading skeleton (was missing from original plan)
- G0 added (Stage 1 prereq, promoted from K5): verify `/skills/[name]` route exists
- K7 added: ⌘K search promoted to nice-to-have parking lot item

**Net effect on Stage 1 scope**: ~25–30% smaller (drop reactflow install + 4 React Flow components + JSON SSOT setup). Stage 2 unchanged.

**Recharts conflict noted, not blocking**: DESIGN.md says "inline SVG only", but `recharts ^3.8.0` is in package.json. Decision: keep recharts installed (might be used elsewhere) but H1-H3 chart components built fresh as inline SVG. Don't uninstall, don't expand recharts usage.
