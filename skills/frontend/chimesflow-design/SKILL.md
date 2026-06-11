---
name: chimesflow-design
description: >
  HARD GATE loader that anchors all new frontend / UI work to ChimesFlow's design
  system as the default starting point. Step 0 force-reads ChimesFlow's canonical
  design-system.md (the SoT), embeds its tokens/conventions into the working prompt,
  then hands off to the actual generator (mockup / frontend-design / gstack-design-html).
  Does NOT generate UI itself — it is the gate, not the painter.
  TRIGGER: building a new page/component/dashboard/web UI, "新前端", "做個畫面",
  "建一頁", "new frontend", or any UI work where no project-specific design system
  is already loaded.
  SKIP: backend/CLI/pure-logic work with no UI; a project that already has its own
  loaded design system and the user explicitly wants that instead.
tags: [frontend, design, hard-gate]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Bash, Grep, Glob, Skill"
---

# ChimesFlow Design (HARD GATE)

Every new frontend surface starts from one source of truth: **ChimesFlow's design
system**. This skill does not draw UI — it guarantees the design SoT is on the
execution path *before* any generator runs, then delegates.

Pattern mirrors `slide-office-hours` (storyline gate): the rule lives in a canonical
markdown SoT, the skill is the loader that forces it into the prompt. See
`~/.claude/CLAUDE.md` → "Cross-Repo Strategy".

## Hard Rules

1. **Never skip Step 0.** No mockup, component, or page may be generated until the
   ChimesFlow SoT has been Read in *this* session and its tokens embedded below.
   If the SoT file cannot be found → STOP and tell the user, do not improvise tokens.
2. **SoT is the default, not a cage** *(mode b)*. ChimesFlow's system is the starting
   point. A project MAY override the aesthetic — but only **explicitly**: state which
   tokens are kept (usually layout/spacing/component conventions) and which are
   replaced (usually brand color/typography), and why. Silent drift is not allowed.
3. **This skill never generates UI.** After loading + embedding, hand off via the
   `Skill` tool to `mockup`, `frontend-design`, or `gstack-design-html`. If you catch
   yourself writing JSX/HTML here → stop, delegate.
4. **Read live, never copy.** Always Read the SoT file fresh each run so it reflects
   the current ChimesFlow system. Do not cache a stale copy into the consumer repo.

---

## Workflow

### Step 0 — Load the SoT (mandatory)

```bash
# Canonical location, overridable via env. Web vs mobile picks the variant.
CF_DIR="${CHIMESFLOW_DIR:-$HOME/code/ChimesFlow}"
WEB_SOT="$CF_DIR/docs/design-system.md"
MOBILE_SOT="$CF_DIR/docs/design-system-mobile.md"

ls -la "$WEB_SOT" "$MOBILE_SOT" 2>/dev/null
# Fallback if ChimesFlow moved:
[ -f "$WEB_SOT" ] || find "$HOME/code" "$HOME/Documents" -maxdepth 4 \
  -path "*ChimesFlow*/docs/design-system.md" -not -path "*/node_modules/*" 2>/dev/null | head
```

Then **Read** the relevant file(s):
- Target is **web / desktop** → Read `design-system.md`.
- Target is **mobile / responsive-first** → Read `design-system-mobile.md` as well.

If neither resolves → STOP:
> 找不到 ChimesFlow design-system.md（預設 `~/code/ChimesFlow/docs/`）。
> 設 `CHIMESFLOW_DIR` 或確認 repo 位置，再呼叫一次 — 我不會憑空編 token。

### Step 1 — Embed the contract

Echo a short embedded summary back into the working context so it stays on the
execution path (not just "I read it"):

- **Stack**: e.g. Next.js + antd v6, zh-TW default (per SoT header)
- **Color tokens**: `colorPrimary`, success/warning/error, text greys (verbatim from SoT)
- **Brand assets**: logo paths, sidebar treatment
- **Domain palettes**: stage/status colors if the surface shows them
- **Any project override (mode b)**: list kept vs replaced tokens + reason, or write
  "無 override — full ChimesFlow defaults".

### Step 2 — Delegate generation

Hand off via the `Skill` tool, passing the embedded contract as context:

| Target | Delegate to |
|--------|-------------|
| Wireframe / quick layout | `mockup` |
| Production component / page / distinctive UI | `frontend-design` |
| Static HTML deliverable | `gstack-design-html` |
| Token/palette/typography exploration | `ui-ux-pro-max` |

Tell the downstream skill: "Design tokens are fixed by the ChimesFlow contract above —
apply them, do not invent a new palette" (unless mode-b override was declared).

---

## Notes

- ChimesFlow's current SoT is **antd v6-coupled** (`colorPrimary #1677ff`). For a
  non-antd / different-brand project, mode-b override is expected — keep ChimesFlow's
  **layout & component conventions**, swap the **brand color/type**, and record it.
- This is intentionally NOT a hook (would over-fire on every file touch). It is
  prompt-routed: `~/.claude/CLAUDE.md` UI flow should call it at Step 0 of new UI work.
