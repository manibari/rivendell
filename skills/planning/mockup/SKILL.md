---
name: mockup
loop: dev
pdca: plan
description: >
  Create UI mockups at three fidelity levels (ASCII → static HTML → interactive HTML),
  reading the project's design system for tokens and constraints, with Figma export.
  Every mockup is responsive: one layout from phone to desktop, checked at
  375 / 768 / 1024 / 1440 px before delivery.
  TRIGGER when: user says /mockup, asks to create wireframe, mockup, or UI prototype,
  or dev-process-gate identifies missing wireframe/mockup stage.
  DO NOT TRIGGER when: user is already coding components, doing backend work,
  or asking about design system creation (not mockup creation).
tags: [workflow, design, mockup]
version: 2
source: manual
user_invocable: true
---

# Mockup

Create UI mockups that conform to the project's design system, from low-fidelity exploration to interactive prototypes ready for Figma handoff.

## Step 0: Read Design System

Before creating any mockup, locate and read the project's design system:

**Search order:**
1. `design-system/*/MASTER.md`
2. `docs/design-system.md`
3. `docs/design-system/*.md`
4. `.claude/skills/uiux-design.md`
5. `AGENTS.md` sections tagged "design" or "design system"

**Extract these tokens:**
- Color palette (background, surface, accent, semantic status colors)
- Typography (font family, size scale, weight scale)
- Spacing scale (padding/margin tokens)
- Border radius and shadow tokens
- Component patterns (cards, buttons, nav, inputs)
- Anti-patterns (explicitly forbidden patterns)
- Dark/light mode strategy

**If no design system is found, STOP and tell the user:**

> This project has no design system. Create one first — define color palette, typography, spacing, and component patterns in `design-system/MASTER.md` before proceeding with mockups.

## Responsive rules (mandatory)

Every L1, L2 and L3 mockup is one layout that works at every width, from a phone to a
large desktop. A mockup that works at one width only is not finished. Many systems are
hard to use because they were designed for one screen size. The mockup is where this is
decided, so it is decided here. (Peter 2026-10-20)

**Principles**

1. **One page, all widths.** Do not draw a phone mockup and a desktop mockup as two
   designs. Draw one page that rearranges itself.
2. **Mobile first.** Write the styles for the narrowest width first. Add `md:` and `lg:`
   styles for wider screens. Do not design for the desktop and then patch the phone.
3. **Same functions at every width.** A phone may fold, reorder or move a function. It
   may not remove it. If a task is really not usable on a phone (for example, bulk edit
   of 50 rows), mark it in the mockup and show what the phone gives instead.
4. **Fluid, not fixed.** Containers use flex or grid, `w-full`, `max-w-*` and `min-w-0`.
   No fixed pixel width on a container. Long text has a maximum width (`max-w-prose`).
   Use `min-h-dvh`, not `h-screen`.
5. **Touch at every width.** Touch targets are at least 44 x 44 px, also on tablets and
   touch laptops.

**Patterns by width**

| Element | Phone (< 768) | Tablet (768-1023) | Desktop (>= 1024) |
|---|---|---|---|
| Main navigation | Bottom navigation, at most 5 items | Bottom navigation or icon rail | Side navigation or top bar |
| Columns | 1 column | 2 columns | 2-3 columns, with a maximum content width |
| Data table | Card list with 2-3 key fields, tap for detail. Or the table scrolls inside its own box, first column fixed | Table with fewer columns | Full table |
| Form | 1 column, inputs full width | 1-2 columns | At most 2 columns, with a maximum width |
| Detail or side panel | Full-screen page or bottom sheet | Overlay panel | Panel next to the list |
| Dialog | Full screen or bottom sheet | Centered dialog | Centered dialog |
| Filters | A button opens a sheet | Collapsible bar | Visible bar or side column |

**Check widths:** 375 (phone), 768 (tablet), 1024 (small laptop), 1440 (desktop). The
page never scrolls sideways at any of them. Only a table box may scroll sideways, inside
itself. See "Responsive check".

## Step 1: Clarify Scope

Ask or confirm:

1. **What screens/flows?** — Reference the user-flow output if available
2. **Primary device?** — The device most users use. That width gets the most design care
   and the first screenshot. This is not a choice between phone and desktop: all four
   check widths must pass.
3. **Fidelity level?** — See table below

| Level | Format | When to Use | Output |
|-------|--------|-------------|--------|
| **L1: ASCII wireframe** | Markdown code block | Quick layout exploration, early feedback | `docs/wireframes/<name>.md` |
| **L2: Static HTML** | HTML + Tailwind CDN | Layout + visual confirmation, no interaction | `mockups/<name>.html` |
| **L3: Interactive HTML** | HTML + Tailwind + Lucide + JS | Full UX validation with state and transitions | `mockups/<name>.html` |

**Default to L3** unless user specifies otherwise or the scope is a quick exploration.

## Level 1: ASCII Wireframe

Use ASCII box-drawing in a Markdown code block. Purpose is rapid layout exploration.

**Format rules:**
- Use `┌─┐│└─┘` for borders
- Label every region with `[ Name ]`
- Annotate with `← 44px touch target` style comments
- Always draw two variants: phone (375) and desktop (1440). Add one line on what
  changes at tablet width

**Example:**
```
┌─────────────────────────┐
│  [ Status Bar ]         │
├─────────────────────────┤
│  [ Header / Title ]     │
├─────────────────────────┤
│                         │
│  [ Card 1 ]             │
│  ┌─────────────────┐    │
│  │ Title      Tag  │    │
│  │ Subtitle        │    │
│  │ Metric    →     │    │
│  └─────────────────┘    │
│                         │
│  [ Card 2 ]             │
│  ┌─────────────────┐    │
│  │ ...              │   │
│  └─────────────────┘    │
│                         │
├─────────────────────────┤
│ 🏠  📊  👤  ⚙️         │
│  [ Bottom Nav ]         │
└─────────────────────────┘
```

After producing the wireframe, ask: **"Proceed to L2/L3, or iterate on layout?"**

## Level 2: Static HTML

Single self-contained HTML file. No JavaScript. Pure layout and visual confirmation.

**Template structure:**

```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mockup — [Screen Name]</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          // INSERT design system tokens here
        }
      }
    }
  </script>
  <!-- Lucide Icons (SVG only, no JS needed for static) -->
</head>
<body class="min-h-dvh bg-slate-950 text-slate-50">
  <div class="md:flex md:min-h-dvh">

    <!-- Side navigation: tablet and desktop only -->
    <nav class="hidden md:flex md:w-56 md:shrink-0 md:flex-col md:border-r md:border-slate-800">
      <!-- Nav items -->
    </nav>

    <div class="min-w-0 flex-1">
      <header class="sticky top-0 border-b border-slate-800 bg-slate-950 px-4 py-3 md:px-6">
        <!-- Page title, main action -->
      </header>

      <!-- Content: 1 column on a phone, more columns on wider screens -->
      <main class="mx-auto max-w-screen-xl px-4 pb-24 pt-4 md:px-6 md:pb-8">
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          <!-- SCREEN CONTENT HERE -->
        </div>
      </main>
    </div>
  </div>

  <!-- Bottom navigation: phone only -->
  <nav class="fixed inset-x-0 bottom-0 flex h-14 items-center justify-around border-t border-slate-800 bg-slate-950 md:hidden">
    <!-- Nav items, at most 5 -->
  </nav>

</body>
</html>
```

**Rules:**
- Inject design system tokens into `tailwind.config.theme.extend`
- Use semantic color names from design system, not raw hex
- All text in the target app's language (default: 繁體中文)
- Use Lucide SVG icons inline (no icon fonts, no emoji as UI icons)
- No device frame. The page is the real page at the browser width. A fixed-width
  phone frame hides every responsive defect
- Follow "Responsive rules"; the template above is the minimum layout

## Level 3: Interactive HTML

Extends L2 with vanilla JavaScript for UX validation.

**Required interactions:**

| Feature | Implementation |
|---------|---------------|
| Dark/Light toggle | `classList.toggle('dark')` on `<html>`, persist to `localStorage` |
| State switching | Buttons/tabs that show/hide sections via `data-*` attributes. The default state is the one with the most content, so the responsive check sees the worst case |
| Scroll behavior | Native overflow-y-auto, snap points where appropriate |
| Input simulation | Realistic placeholder text, focus ring styles |
| Navigation | Tab highlighting on click, screen section switching |
| Transition | `transition-all duration-200` on interactive elements |

**Multi-screen journeys:**
- One file for each screen: `mockups/<feature>/<nn>-<screen>.html`
- `mockups/<feature>/index.html` lists the steps (Step 1, Step 2, ...) with a link to each screen
- Links and buttons inside a screen go to the next screen of the flow
- Do not put screens side by side in fixed-width phone frames. Each screen must reflow on its own

**JavaScript rules:**
- Vanilla JS only — no frameworks, no build tools
- All state in `data-*` attributes or simple variables
- Event delegation where possible
- `localStorage` only for theme preference

## Responsive check (mandatory)

Run the check on each mockup file at the four widths. It uses the chart-design figure
checker. It needs the Node packages of the repo root (see the last bullet) and
Google Chrome.

```bash
S="$(cd -P "${CLAUDE_SKILL_DIR}" && pwd)"   # real folder: Node drops ".." before it follows a symlink
C="$S/../../docs/chart-design/references/check-html-figure.mjs"
mkdir -p mockups/screens
for w in 375 768 1024 1440; do
  node "$C" mockups/<name>.html --width "$w" --height auto --min-font 12 \
    --screenshot "mockups/screens/<name>-$w.png" --annotate || echo "FAIL at $w"
done
```

- Exit 1 means an error: `figure/overflow` (the page scrolls sideways) or
  `figure/text-overlap`. Fix the layout and run again. Do not fix with
  `overflow: hidden` or a smaller font.
- Fix every `figure/small-font` warning too.
- `figure/text-wrap` on a paragraph is normal. On a button, a tab, a navigation item or a
  table header, it is a defect: shorten the label or change the layout at that width.
- Ignore `figure/canvas-fill` and `figure/empty-band`. They are for fixed-size figures,
  not for pages.
- Read all four screenshots of each screen. Show the user at least the 375 and 1440
  screenshots before you call the mockup done.
- `playwright not found`: run `npm install` once in the repo root (the folder with
  `package.json`): `cd -P "${CLAUDE_SKILL_DIR}/../../.." && npm install`.

## Quality Checklist

Before delivering any L2/L3 mockup, verify:

- [ ] All colors come from design system tokens (no hardcoded hex)
- [ ] Dark and light mode both work correctly
- [ ] Touch targets minimum 44×44px with 8px gaps
- [ ] Text contrast minimum 4.5:1 (WCAG AA)
- [ ] Input font size >= 16px (prevents iOS auto-zoom)
- [ ] Responsive check passed at 375 / 768 / 1024 / 1440 (no errors, no small font), screenshots read
- [ ] Same functions at every width (folded or moved, not removed)
- [ ] Navigation changes form with width (bottom navigation on a phone, side or top navigation on a desktop)
- [ ] Content not hidden behind bottom nav (sufficient bottom padding)
- [ ] All icons are Lucide SVG (no emoji as UI icons)
- [ ] File opens correctly in browser with no external dependencies except CDN

## Anti-Patterns

Never do these in mockups:

- **No emoji as UI icons** — use Lucide SVG
- **No purple/pink AI gradient backgrounds** — follow design system palette
- **No hamburger menu on mobile** — use bottom navigation
- **No fixed-width layout** — no phone frame, no `width: 1200px` container
- **No phone-only or desktop-only mockup** — one page for all widths
- **No sideways page scroll** — only a table box may scroll sideways
- **No functions removed on the phone** — fold or move them instead
- **No forms with 5+ fields on one screen** — use card-based progressive disclosure
- **No layout-shifting hover transforms** — subtle opacity/shadow changes only
- **No font-size < 16px on input elements** — iOS will auto-zoom
- **No hardcoded dark OR light colors** — always provide both variants
- **No framework dependencies** — mockup must be a single self-contained HTML file

## Figma Export

After the mockup is approved, offer Figma export:

### Option A: html-to-figma (preserves layers)

```bash
# Install the CLI tool
npm install -g @anthropic/html-to-figma

# Convert HTML to Figma-compatible JSON
html-to-figma mockups/<name>.html --output mockups/<name>.figma.json
```

Then import via the **html-to-figma Figma plugin**:
1. Open Figma → Plugins → html-to-figma
2. Paste the generated JSON
3. Layers, text, and colors are preserved for manual adjustment

### Option B: Screenshot upload (fallback)

If html-to-figma is not available or produces unsatisfactory results, upload the
screenshots from the responsive check (`mockups/screens/<name>-<width>.png`) to Figma
via REST API or drag-and-drop.

### Recommended workflow

```
Interactive HTML mockup
  → User approves in browser
  → html-to-figma export (preserves editable layers)
  → Designer fine-tunes in Figma
  → Export final assets for development
```

## Integration with dev-process-gate

This skill fills the wireframe/mockup stages in the development workflow:

```
requirement → user-flow → [mockup skill] → development
                            ├─ L1: ASCII wireframe (quick explore)
                            ├─ L2: Static HTML (layout confirm)
                            └─ L3: Interactive HTML (UX validate) → Figma
```

When `dev-process-gate` detects missing wireframe/mockup, it should suggest this skill.

Output artifacts for handoff to development:
- `mockups/<feature-name>.html` (or `mockups/<feature-name>/` for a multi-screen journey) — the approved mockup
- `mockups/screens/<name>-<width>.png` — the responsive check screenshots at four widths
- Component inventory list — extracted from the mockup for implementation planning
