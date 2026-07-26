# Codex Visual Assets For PPTX

Use this reference when `pitch-deck` or `slide-workflow` hands `office-pptx`
slides with `hybrid` or `image-heavy` visual modes.

## Principle

Generated images provide visual presence; PowerPoint remains the source of
editable truth. Keep titles, labels, metrics, legends, logos, charts, diagrams,
and callouts as native PPT/HTML elements.

## Runtime Rule

- In Codex with image generation available, generate the raster image before
  building the PPTX.
- In Claude Code without image generation, stop at `visual_briefs.md` and
  `visual_assets.json`, then hand those files to Codex. Do not replace the image
  with a CSS gradient, decorative abstraction, fake stock photo, or text rendered
  inside an image.

## Asset Manifest

Prefer a machine-readable manifest beside `visual_briefs.md`:

```json
{
  "deck_id": "client-deck",
  "assets": [
    {
      "slide_id": "slide-01",
      "slide_number": 1,
      "mode": "image-heavy",
      "role": "hero",
      "brief_path": "visual_briefs.md#slide-01-cover-hero",
      "image_path": "assets/generated/slide-01-cover-hero.png",
      "prompt_path": "assets/generated/slide-01-cover-hero.prompt.md",
      "status": "approved",
      "safe_area": "left 42% clear for title",
      "placement": {
        "fit": "cover",
        "focal_point": "right center",
        "overlay": "dark 35%"
      }
    }
  ]
}
```

Allowed `status` values:
- `briefed`: prompt exists, image not generated yet
- `generated`: image exists but has not been visually approved
- `approved`: usable in final export
- `draft-placeholder`: allowed only for explicitly draft/internal output

## Placement Rules

- Use `cover` for full-bleed hero/background images; use `contain` only when the
  entire generated visual must be visible.
- Preserve the safe area from the brief. Place title/subtitle/callouts there.
- Add an overlay when text contrast is weak.
- Never stretch raster images.
- Save the prompt/brief beside the image so the asset can be regenerated.

## Red Flags That Require Regeneration

- Visible text, watermark, fake logo, or accidental UI copy inside the image
- Distorted or stretched image placement
- Subject hidden by title safe area or overlays
- Fake product screen presented as a real screenshot
- Visual style clashes with the locked template palette
- Generated image used for financial charts, KPI numbers, architecture labels,
  legal text, real logos, or dense small text

## Final Export Gate

For external or client-facing PPTX, do not export with `briefed`, `generated`, or
`draft-placeholder` assets unless the user explicitly accepts draft quality.
Run thumbnail QA after export and inspect image crop, contrast, style consistency,
and whether native text remains readable.
