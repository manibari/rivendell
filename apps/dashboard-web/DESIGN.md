# Design System — rivendell-next

Source of truth for all visual decisions in `dashboard-next/`. Read this before making any UI / styling change.

## Product Context

- **What this is:** Single-user desktop dashboard managing 90+ Claude Code skills, AI agents, and workflow gates.
- **Who it's for:** Peter (manibari) — sole user. Internal tool, never customer-facing.
- **Project type:** Personal dev tool / command center. Desktop only (no mobile RWD).
- **Brand promise:** A quiet refuge for the work — dashboard stays neutral and functional; rivendell character lives in the logo and a single accent color.

## Aesthetic Direction

- **Direction:** Logo-first / neutral light dashboard with a single forest-green accent.
- **Decision tree (recorded for future "should this be more X?" debates):** We tried full Mythic Library (parchment + Garamond + scroll cards + drop caps) — it was too costly and over-indexed on aesthetic. The user's reframe ("rivendell 是不是換個 logo 就好") was correct. Identity moved to logo + accent color; the dashboard chrome stays out of the way.
- **Decoration level:** Minimal. Typography + spacing + a single accent. One ornament (`❦`) in footer for character. Nothing else decorative.
- **Mood:** Calm, considered, library-adjacent. Nothing loud.

## Brand · Logo

**Primary mark:** Twin leaves — two opposing leaves with a central stem, symbolizing council. SVG at `dashboard-next/public/logo.svg`. Hard-coded forest green (`#2d4a3e`).

**Mono variant:** `dashboard-next/public/logo-mono.svg` — same shape but `fill="currentColor"` so it inherits color from CSS context. Use this for sidebar / header / favicon where color may need to switch.

**Wordmark:** Lowercase `rivendell` set in Geist 600, letter-spacing `-0.04em`, color `var(--accent)` (forest green). Never italic.

**Lockup rules:**
- Mark + wordmark: mark on left, vertically centered against wordmark cap height.
- Mark size : wordmark size = 1 : 1 (mark height matches wordmark cap height).
- Minimum sizes: mark 16px (favicon), wordmark 14px.

**Tagline:** `council of 90 skills · refuge of work` — Geist Mono 12px, `--text-muted`, lowercase, tracking 0.05em.

**What NOT to do:** never paint the mark in any color other than forest green or `currentColor`. Never tilt, skew, or animate it. No gradient on the mark.

## Color

Light theme only. No dark mode (single-user tool, less surface-area to maintain).

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#fafafa` | Page background |
| `--surface` | `#ffffff` | Cards, panels, table rows |
| `--surface-2` | `#f3f4f6` | Subtle elevation, hover, soft chip background |
| `--border` | `#e5e7eb` | Default borders, dividers |
| `--border-strong` | `#d1d5db` | Stronger borders (cards, buttons) |
| `--text` | `#0a0a0a` | Primary text |
| `--text-muted` | `#6b7280` | Secondary text, axis labels |
| `--text-subtle` | `#9ca3af` | Tertiary text, placeholders |
| `--accent` | `#2d4a3e` | **The single brand color.** Logo, primary buttons, highlighted nodes, link emphasis, chart line color |
| `--accent-soft` | `#5b7a6a` | Lighter accent — secondary connector lines, soft hover |
| `--accent-bg` | `#e8efea` | Accent halo / selected state background |
| `--status-ok` | `#10b981` | Healthy / success / exit 0 |
| `--status-warn` | `#f59e0b` | Warning / drift / review |
| `--status-err` | `#ef4444` | Error / exit ≠ 0 |

**Color rules:**
- Never use blue, purple, indigo, pink for chrome. Forest green is the only non-status color allowed.
- Status colors only when there is an actual status to communicate. Never as decoration.
- Charts use the forest green for primary data; sequential greens (`#d1ddd5 / #8aa399 / #2d4a3e`) for ordinal/heatmap encoding. No multi-color rainbow palettes.

## Typography

Two faces, three roles. Self-host both for portability (see Self-Hosting below).

| Role | Family | Weight | Notes |
|------|--------|--------|-------|
| Display | **Geist** | 500 / 600 | Page titles, h1–h3, chart titles, button labels. Letter-spacing `-0.02em` |
| Body | **Geist** | 400 | Paragraph copy, descriptions, list items. Line-height 1.55 |
| Mono | **Geist Mono** | 400 / 500 | Skill IDs (`/gstack-investigate`), data values, tabular numbers, timestamps. Always `font-feature-settings: 'tnum' 1` on numeric content |

**Type scale:**

| Level | Size | Use |
|-------|------|-----|
| h1 | 64px | Hero / landing page only |
| h2 | 28px | Section headings (with 1px top rule + 80px accent leader) |
| h3 | 18px | Subsection |
| body | 14px | Default |
| small | 12px | Captions, secondary |
| micro | 10–11px | Labels (uppercase, tracking 0.08–0.12em), table headers |

**No serifs anywhere.** No italic. Character lives in the logo, not the type.

## Spacing

- **Base:** 4px
- **Density:** Comfortable. Default gap 8–16px, page padding 24–48px.
- **Scale:** 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 — exposed as `--space-1` through `--space-8`.

## Layout

- **App shell:** Left sidebar nav (collapsible, ~240px) + main canvas. Top breadcrumb on each page.
- **Max content width:** 1280px. Wider on workflow / chart-heavy pages where horizontal scroll is acceptable inside cards.
- **Border radius:** `sm: 4px` for chips/inputs, `md: 6px` for cards, `lg: 8px` for large containers.
- **Workflow page exception:** main canvas is a custom flowchart (React Flow or equivalent), not a CSS grid. Scrolls horizontally as needed.

## Motion

Minimal-functional. Only:
- Hover state changes: `0.15s ease`
- Route transitions: skip (Next.js default)
- Entrance animations: none
- Scroll-driven anything: none

## Components

Reference implementations live in the v4 preview at `~/.gstack/projects/manibari-rivendell/designs/design-system-20260507/preview.html` (this is a USER artifact, not committed).

| Component | Notes |
|-----------|-------|
| Button — primary | `--accent` background, `--surface` text, hover `#1f3a30` |
| Button — secondary | Transparent, `--border-strong`, hover border + text → `--accent` |
| Button — ghost | Transparent, `--text-muted`, hover → `--text` |
| Status dot | 8px circle, semantic color, `8px` right-margin |
| Skills table | Mono font, tabular-nums, 10px uppercase header tracking 0.08em |
| Chip / Tag | Mono 10px, surface bg, 1px border, 2px radius, `optional` modifier = dashed border |
| Card / Panel | `--surface` + `--border`, `radius-md`, no shadow |
| Chart card | Same as card; chart title in display 18px |

## Charts

Three patterns to standardize:

1. **Line trend** — single forest-green stroke, soft gradient fill, mono axis labels
2. **Horizontal bar rank** — top-N with mono labels, accent bars on `--surface-2` track
3. **Heatmap matrix** — sequential greens (light → forest), red `#fecaca` for error states only

All chart axis labels use `Geist Mono` 9–10px in `--text-subtle`. All numeric content uses `font-feature-settings: 'tnum' 1`. No 3D, no pie charts (use bars), no animated transitions.

## Workflow Map (the killer page)

Specific to this dashboard's flagship page. Detailed implementation lives in `dashboard-next/src/app/workflow/page.tsx`.

- **View:** Horizontal flowchart per track, Bezier-curve connectors in `--accent-soft` (current step's connectors in `--accent`).
- **Node:** White card with `--border-strong`, padding 12/16, fixed width 165px. Active node uses 1.5px `--accent` border.
- **Skill chips:** stacked vertically inside each node, mono 10px, dashed border for `optional`.
- **Toggle:** Tree (current default — track-step hierarchy) | Graph (skill-as-center DAG, future).
- **Right panel:** Cross-reference. Click any skill chip → panel shows every track / step that references it, plus mini-stats and a jump-to-skill CTA.
- **Library:** Use [React Flow](https://reactflow.dev) for any future drag/edit/connect-by-handle interactivity. Source of truth = `dashboard-next/data/workflow.json` (canonical graph). UI edits round-trip through this JSON; Claude Code reads/writes the same file to keep CLAUDE.md flow doc in sync.

## Portability · Self-Hosting

**Why:** dashboard-next must run on multiple machines (laptop, dev box, eventual server). External CDN dependencies introduce failure modes and latency surprises.

**Fonts:** Self-host Geist + Geist Mono in `dashboard-next/public/fonts/`. Both are SIL OFL licensed.
- Source: https://vercel.com/font/sans (Geist), https://vercel.com/font/mono (Geist Mono)
- File format: `.woff2` only (modern browsers)
- Files needed: `Geist-Variable.woff2`, `GeistMono-Variable.woff2` (variable font versions cover all weights in one file)
- @font-face declarations in `globals.css`:

```css
@font-face {
  font-family: 'Geist';
  src: url('/fonts/Geist-Variable.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Geist Mono';
  src: url('/fonts/GeistMono-Variable.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
```

**Logo:** SVG files in `dashboard-next/public/`, no external dependency.

**Charts:** All charts use inline SVG, no `recharts`, `d3`, or other chart library required.

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-07 | Initial design system created | `/gstack-design-consultation` session 2026-05-07. 4 iterations: dark industrial → light + charts → Mythic Library full → logo-first neutral. User reframe at v3.1 ("rivendell 是不是換個 logo 就好") drove the move to v4 |
| 2026-05-07 | Twin leaves chosen as primary mark | Council symbolism, mythic without being on-the-nose, reads at favicon size |
| 2026-05-07 | Light theme only, no dark mode | Single-user tool — dark mode is double the maintenance for a use-case that doesn't appear |
| 2026-05-07 | Geist + Geist Mono only, no serifs | Character lives in logo + color, not in type. Simpler font stack = portable |
| 2026-05-07 | Self-host fonts, not Google Fonts CDN | Portability across machines, offline, no firewall failure modes |
| 2026-05-15 | Workflow Map redesigned as 4-tab static playbook, moved under `/projects/[name]/workflow` | The encyclopedic skill-graph view (React Flow, `workflow.json` SoT) was not what Peter actually used. The mockup at `~/Documents/Peter/workflow-map.html` proposed a focused 4-tab playbook (UI Feature / Backend / Slide / Maintenance) that mirrors the canonical workflow in `~/.claude/CLAUDE.md`. Data SoT is now `dashboard-next/src/app/projects/[name]/workflow/playbook-data.ts` (TypeScript). React Flow is NOT used here — the page is static, click-a-chip-for-detail interaction only. Workflow Map removed from top-level sidebar; entry point is the rivendell project detail page. Mockup's blue/cyan chip palette mapped to rivendell tokens (forest-green accent, surface-2 + border-strong for gstack, dashed `--status-err` for critical). Tab icons use Lucide (`Palette` / `Wrench` / `Presentation` / `RotateCw`) instead of mockup's emoji to match DESIGN.md "Decoration level: Minimal." |
| 2026-05-15 | Workflow Map: tried Azure ML-style read-only DAG (React Flow + dagre), reverted to list view | Built node-graph rendering (commit b7c54d0) with dagre auto-layout, smoothstep edges in accent-soft, custom step nodes carrying chips + branch lines inline. User reaction: "感覺效果不是很好". Reverted via 791c7d5. Hypotheses (untested — user didn't elaborate): (a) DAG adds visual noise without adding information vs the list (every step still carries the same chips); (b) sequential scan is faster in a vertical list than across a graph; (c) React Flow's grid background + zoom controls reintroduce "tool chrome" that violates calm/library mood. Keep the list view; if revisiting node-graph later, do not assume the data-shape carries — re-validate against actual UX gap, not aesthetic ambition. The graph code is recoverable from commit b7c54d0 via `git revert HEAD` of the revert commit. |
