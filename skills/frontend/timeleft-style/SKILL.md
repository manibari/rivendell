---
name: timeleft-style
loop: dev
pdca: plan
description: >
  A warm, social, consumer look modelled on timeleft.com (studied 2026-10-11): cream paper
  background, near-black ink, a tight display serif for headlines, a friendly sans for UI,
  pill buttons with a pink-to-orange gradient, big white rounded cards, soft colour blobs,
  and one playful mascot motif. Gives tokens (tokens.css), components, Traditional Chinese
  type rules, dark mode, and what not to copy. Use it as the design system source when a
  project picks this style, then hand off to mockup / gstack-design-html / frontend-design.
  TRIGGER: "Timeleft 風格", "timeleft style", "走 Timeleft", "溫暖的社交感畫面",
  a project DESIGN.md that names timeleft-style.
  SKIP: pro tools and dense dashboards (use the project's own system or chimesflow-design);
  Artcraft desktop apps with the PhotoCraft theme.
version: 1.0.0
tags: [frontend, design, design-system, style]
user_invocable: true
allowed-tools: "Read, Write, Edit, Bash, Grep, Glob, Skill"
---

# Timeleft style

**The feeling in one line:** an invitation, not a tool. Warm paper, big confident serif
headlines, one cheerful gradient, and a lot of air. The screen says "relax, we handle it".

Source: timeleft.com home page, read with a headless browser on 2026-10-11 (computed
styles and screenshots). Values marked *measured* come from that page. Values marked
*ours* are our adaptations (free fonts, Chinese text, dark mode, app screens).

## 1. Seven traits (check every screen against them)

1. **Cream paper, not white.** The page is warm off-white; pure white is only for cards and
   the floating nav. Sections change by tone (cream, darker cream, ink), never by lines.
2. **Headlines are a tight display serif**, large, weight 500, negative tracking. Body and UI
   are a rounded humanist sans, mostly weight 600 for labels.
3. **One gradient, used for action and for one highlighted word.** Pink to peach to orange.
   The primary button and one accent word per headline use it. Nothing else does.
4. **Everything is a pill or a big soft card.** Buttons and nav are fully round. Cards have
   24 to 28 px corners, white fill, a long soft shadow, no border.
5. **Soft colour fields behind content**: a large blurred ellipse (peach to yellow) or a
   mint-to-cyan card. At most one per viewport.
6. **Small saturated circles carry meaning**: category icons sit in solid circles (orange,
   pink, green). They are the only strong flat colours.
7. **One playful motif, used sparingly**: Timeleft uses googly eyes and round faces. A
   project must invent its own small motif (see §6). One appearance per screen at most.

## 2. Tokens

Copy `tokens.css` from this folder into the project (do not rewrite the values). Summary:

| Token | Light | Dark (*ours*) | Note |
| --- | --- | --- | --- |
| `--paper` | `#F7F3ED` | `#151312` | page background (*measured* light) |
| `--paper-deep` | `#EFE8DE` | `#1E1B19` | alternate section, input fill (*measured*) |
| `--card` | `#FFFFFF` | `#24201E` | cards, nav pill |
| `--ink` | `#111111` | `#F7F3ED` | text, dark buttons (*measured*) |
| `--ink-muted` | `#666362` | `#B4ACA5` | secondary text (*measured*) |
| `--ink-faint` | `#958F8C` | `#857D77` | captions, placeholders (*measured*); not for body text |
| `--line` | `#E4DCD0` | `#36302C` | the rare hairline (secondary pill border) |
| `--grad-action` | `#FDD3F1 → #FEBFDF → #F97709` (bottom to top, 360deg) | same, 90 % opacity | primary button, accent word (*measured*) |
| `--grad-mint` | `#A8EBC8 → #0AA6DF` | darker 20 % | one feature card (*measured by eye*) |
| `--grad-sun` | `#FFD3C4 → #FAD94A` | darker 25 % | background blob (*measured by eye*) |
| `--dot-orange` | `#FA7A12` | same | category circle |
| `--dot-pink` | `#F472D0` | same | category circle |
| `--dot-green` | `#14B87A` | same | category circle |
| `--danger` | `#D6452F` | `#FF7A63` | errors (*ours*; warm red, never pink) |
| `--ok` | `#1F9D63` | `#4CD495` | success (*ours*) |

Radius: pill `9999px`, card `28px`, inner card `20px`, small chip `12px`.
Shadow: card `0 18px 40px -18px rgb(60 40 20 / 0.18)`; nav `0 10px 30px -12px rgb(60 40 20 / 0.20)`.
Spacing: base 8 px; section gaps 96 to 128 px on desktop; content width 1200 px max.

## 3. Type

Timeleft uses two paid fonts (FeatureDeck, FixelText). Do not use them. Free choices:

| Role | Latin | Traditional Chinese | Size / weight / tracking |
| --- | --- | --- | --- |
| Display (h1) | Newsreader, opsz 72 | Noto Serif TC | 64 to 72 px / 500 (CJK 600) / -0.025em |
| Heading (h2) | Newsreader | Noto Serif TC | 38 to 40 px / 500 (CJK 600) / -0.015em, line 1.2 |
| Title (h3, card) | Figtree | Noto Sans TC | 24 to 26 px / 600 / line 1.5 |
| Body | Figtree | Noto Sans TC | 17 to 18 px / 500 / line 1.6 |
| Label, button | Figtree | Noto Sans TC | 16 to 18 px / 600 |
| Number, time | Figtree, `tabular-nums` | — | same as context |

All four are OFL on Google Fonts. Fixel (the free cousin of FixelText) has a regional
restriction in its license; do not ship it in a downloadable app.

Chinese rules (*ours*):
- Serif only for h1 and h2. Chinese body text in serif looks like a contract.
- Chinese headings need weight 600 and less negative tracking (-0.01em) than Latin.
- Line height for Chinese body: 1.75. Keep lines under 32 characters in cards.
- Mixed text: set `font-family: "Figtree", "Noto Sans TC", sans-serif` so Latin and digits
  use Figtree.

## 4. Components

- **Floating nav pill**: white pill, full width minus 116 px, 64 px high, shadow `nav`,
  sticks 40 px from the top. Logo left, links centre (16 px / 600), two pills right:
  secondary (white, 1 px `--line` border) and primary (gradient).
- **Primary button**: pill, `--grad-action`, ink text 18 px / 600, height 52 to 56 px,
  padding 0 32 px. Hover: brightness 1.03, no movement. One per view.
- **Secondary button**: pill, `--card` fill, `--line` border, ink text.
- **Dark round button**: 32 to 40 px ink circle with a white arrow; for "open this row".
- **Accent word**: one word or short phrase in a headline with `--grad-action` as text fill
  (`background-clip: text`). Max one per screen.
- **Big card**: `--card`, radius 28, shadow card, padding 32 to 40. Content: h3, muted
  paragraph, an illustration or photo cluster. Marketing pages may tilt cards by -4 to 4
  degrees; app screens never tilt.
- **List row card** (from the app screenshots): white, radius 20, padding 16 to 20,
  category circle left, title + date + muted time, dark round arrow right.
- **Choice buttons**: full-width white pills, 60 px high, centred label; used for a quiz or
  a single choice.
- **Stat with laurels**: big number, small muted label; for counts.
- **Input** (*ours*): `--paper-deep` fill, radius 20, 60 px high, 18 px text, no border;
  focus ring 2 px ink at 30 % plus the card shadow.
- **Chip** (*ours*): radius 12, `--paper-deep`, 14 px / 600. Status chips may use a dot of a
  category colour before the label.

## 5. Layout and motion

- Desktop first for web apps; one main column 720 to 880 px for app screens, 1200 px for
  marketing. Mobile: 16 px gutter, nav becomes a bottom pill bar.
- Left-aligned headlines on app screens; centred only for section titles on marketing pages.
- Photos are rounded (24 px) and may overlap in clusters of three.
- Motion: short (150 to 250 ms), ease-out; cards fade up 12 px on enter; no parallax, no
  bouncing buttons.

## 6. Do not copy

- The Timeleft logo, name, wordmark, googly-eye mark, face mascots, photos, or copy text.
- The paid fonts.
- Make your own motif: one small shape tied to the product (for example a map pin with a
  face, a folded note corner). Same rules: small, rare, friendly.

## 7. Checks before you show a screen

- [ ] Background is `--paper`, not white; no section borders.
- [ ] Exactly one gradient element per view (plus at most one accent word).
- [ ] All buttons are pills; all cards 20 or 28 px radius; no 4 to 8 px radius boxes.
- [ ] Serif only in h1/h2; Chinese headings weight 600.
- [ ] Body text is `--ink` or `--ink-muted`, never `--ink-faint`; contrast 4.5:1 or more.
- [ ] Inputs are 16 px text or larger.
- [ ] Accent text zoomed at 2x: no stroke of a Chinese glyph is cut at the top or bottom
  (gradient text paints only its own box; `tokens.css` widens it).
- [ ] Dark mode checked with a screenshot (the gradient stays, surfaces change).
- [ ] No Timeleft assets (§6).

## 8. How to use in a project

1. Copy `tokens.css` into the project and load the four Google Fonts.
2. Write the project `DESIGN.md` as "timeleft-style + these project choices" (motif,
   category colours, which screens use the gradient). Keep the tokens here as the source.
3. Hand off to `mockup` (L3 HTML) or `gstack-design-html`. Take screenshots in light and
   dark and read them before you report.
