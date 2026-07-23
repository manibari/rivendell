---
name: mockup
description: >
  Create UI mockups at three fidelity levels (ASCII → static HTML → interactive HTML),
  reading the project's design system for tokens and constraints, with Figma export.
  TRIGGER when: user says /mockup, asks to create wireframe, mockup, or UI prototype,
  or dev-process-gate identifies missing wireframe/mockup stage.
  DO NOT TRIGGER when: user is already coding components, doing backend work,
  or asking about design system creation (not mockup creation).
tags: [workflow, design, mockup]
version: 1
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

## Step 1: Clarify Scope

Ask or confirm:

1. **What screens/flows?** — Reference the user-flow output if available
2. **Target platform?** — Mobile (375×812), Desktop (1440×900), or both
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
- Show mobile and desktop variants if both targeted

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
<body class="bg-slate-950 text-slate-50">

  <!-- Phone Frame -->
  <div class="mx-auto my-8" style="width:375px;">
    <div class="rounded-[2.5rem] border-[3px] border-slate-700 overflow-hidden"
         style="height:812px;">

      <!-- Status Bar -->
      <div class="h-12 flex items-end justify-between px-6 pb-1 text-xs">
        <span>9:41</span>
        <div class="flex gap-1">
          <span>📶</span><span>🔋</span>
        </div>
      </div>

      <!-- Content Area (scrollable) -->
      <div class="h-[700px] overflow-y-auto px-4 pt-2 pb-24">
        <!-- SCREEN CONTENT HERE -->
      </div>

      <!-- Bottom Nav -->
      <div class="h-[52px] border-t border-slate-800 flex items-center justify-around px-4">
        <!-- Nav items -->
      </div>

      <!-- Home Indicator -->
      <div class="h-2 flex justify-center pt-1">
        <div class="w-32 h-1 bg-slate-600 rounded-full"></div>
      </div>
    </div>
  </div>

</body>
</html>
```

**Rules:**
- Inject design system tokens into `tailwind.config.theme.extend`
- Use semantic color names from design system, not raw hex
- All text in the target app's language (default: 繁體中文)
- Use Lucide SVG icons inline (no icon fonts, no emoji as UI icons)
- Phone frame: 375×812px with rounded corners and status bar

## Level 3: Interactive HTML

Extends L2 with vanilla JavaScript for UX validation.

**Required interactions:**

| Feature | Implementation |
|---------|---------------|
| Dark/Light toggle | `classList.toggle('dark')` on `<html>`, persist to `localStorage` |
| State switching | Buttons/tabs that show/hide sections via `data-*` attributes |
| Scroll behavior | Native overflow-y-auto, snap points where appropriate |
| Input simulation | Realistic placeholder text, focus ring styles |
| Navigation | Tab highlighting on click, screen section switching |
| Transition | `transition-all duration-200` on interactive elements |

**Multi-screen journeys:**
- Horizontal scroll layout with snap: each phone frame is one screen
- Arrow indicators between screens showing the flow direction
- Screen titles above each frame (Step 1, Step 2, ...)

```html
<!-- Multi-screen container -->
<div class="flex gap-8 overflow-x-auto snap-x snap-mandatory px-8 py-8">

  <!-- Screen 1 -->
  <div class="snap-center shrink-0">
    <p class="text-center text-sm text-slate-400 mb-2">Step 1 — Home</p>
    <div class="phone-frame"><!-- ... --></div>
  </div>

  <!-- Arrow -->
  <div class="flex items-center shrink-0">
    <svg class="w-8 h-8 text-slate-500" ...><!-- arrow-right --></svg>
  </div>

  <!-- Screen 2 -->
  <div class="snap-center shrink-0">
    <p class="text-center text-sm text-slate-400 mb-2">Step 2 — Input</p>
    <div class="phone-frame"><!-- ... --></div>
  </div>

</div>
```

**JavaScript rules:**
- Vanilla JS only — no frameworks, no build tools
- All state in `data-*` attributes or simple variables
- Event delegation where possible
- `localStorage` only for theme preference

## Quality Checklist

Before delivering any L2/L3 mockup, verify:

- [ ] All colors come from design system tokens (no hardcoded hex)
- [ ] Dark and light mode both work correctly
- [ ] Touch targets minimum 44×44px with 8px gaps
- [ ] Text contrast minimum 4.5:1 (WCAG AA)
- [ ] Input font size >= 16px (prevents iOS auto-zoom)
- [ ] No horizontal scroll at target viewport width
- [ ] Content not hidden behind bottom nav (sufficient bottom padding)
- [ ] Phone frame status bar and home indicator present
- [ ] All icons are Lucide SVG (no emoji as UI icons)
- [ ] File opens correctly in browser with no external dependencies except CDN

## Anti-Patterns

Never do these in mockups:

- **No emoji as UI icons** — use Lucide SVG
- **No purple/pink AI gradient backgrounds** — follow design system palette
- **No hamburger menu on mobile** — use bottom navigation
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

If html-to-figma is not available or produces unsatisfactory results:

```python
# Using Playwright to screenshot each phone frame
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(f"file://{mockup_path}")

    # Screenshot each phone frame
    frames = page.query_selector_all(".phone-frame")
    for i, frame in enumerate(frames):
        frame.screenshot(path=f"mockups/screens/screen-{i+1}.png")

    browser.close()
```

Then upload screenshots to Figma via REST API or manually drag-and-drop.

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
- `mockups/<feature-name>.html` — the approved mockup file
- `mockups/screens/` — exported screenshots (if Figma export used)
- Component inventory list — extracted from the mockup for implementation planning
