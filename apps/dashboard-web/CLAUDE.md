# dashboard-next — Claude Code rules

## Design System

Always read `dashboard-next/DESIGN.md` before making any visual / UI / styling change.
All color, typography, spacing, layout, and component decisions are defined there.
Do not deviate from DESIGN.md without explicit user approval, and update the
"Decisions Log" section at the bottom of DESIGN.md when a deviation is approved.

In QA mode, flag any code that doesn't follow DESIGN.md (hardcoded colors, raw
font-family strings outside `globals.css`, blue/purple/indigo accent usage, etc.)

## Brand assets

- `public/logo.svg` — primary mark (twin leaves, hard-coded forest green `#2d4a3e`)
- `public/logo-mono.svg` — monochrome variant using `currentColor` for context-aware tinting
- Wordmark "rivendell" set in Geist 600, color `var(--accent)`, never italic

## Fonts

Self-hosted in `public/fonts/` (Geist Variable + Geist Mono Variable, .woff2).
@font-face declarations in `globals.css`. Do not switch to Google Fonts CDN —
portability across machines is a design constraint.

## Workflow page

Lives at `src/app/projects/[name]/workflow/[flow]/page.tsx` (currently only
`name=rivendell` has a playbook). Old `src/app/workflow/page.tsx` is a
permanent redirect for legacy bookmarks. Sub-routes per flow:
`/projects/rivendell/workflow/{ui,backend,slide,maintenance}`.

Source of truth is `src/app/projects/[name]/workflow/playbook-data.ts` —
a TypeScript module, not a JSON file. Edit it directly; the page re-renders
on next build. Mirrors `~/.claude/CLAUDE.md`'s "Development Workflow"
section. When that doc changes substantively, update playbook-data.ts to
match.

`FlowView.tsx` renders one flow as a vertical step list with `↳` branch
lines for `optionals`. `[flow]/page.tsx` wires the breadcrumb, title, and
the active flow. Slide branch tabs (A/B/C/D) are in-page state inside
FlowView.

Skill detail (trigger / SKIP) shows in a modal via `skillDetails` in the
same module. Click any chip to open.

**Reverted experiments** (see DESIGN.md Decisions Log for context):
- Read-only React Flow + dagre DAG view (commit b7c54d0, reverted 791c7d5).
  User found the graph noisier than the list without adding information.
  The data converter / nodes API was forward-compat for editing; if
  revisiting, recover via `git revert HEAD` of the revert.

Sidebar groups Workflow Map under 技能庫 (Skills section), not 專案管理 —
it's a view of how skills compose into usage, not a per-project runtime
concern.
