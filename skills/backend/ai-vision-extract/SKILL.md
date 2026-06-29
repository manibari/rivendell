---
name: ai-vision-extract
description: >
  The pattern for "photo → AI does the OCR/extraction → structured data", learned
  from iihi (孕 app) prod: a cost-aware identify→normalize→cache→generate→persist
  pipeline against a SEPARATE AI microservice, with timeout + graceful-degrade
  resilience. The clever part is NOT "send image to a vision model" — it's the cache
  layer: identify cheaply from the image once, normalize to a key, reuse from DB on
  hit, only generate (from TEXT, not the image again) + persist on miss. Language-
  agnostic pattern (iihi is Next.js); n=1 source (one product) — validate on the 2nd.
  TRIGGER when: photo/image → structured fields; 拍照辨識 / 拍照分析; food / receipt /
  label / document / gear extraction via an AI or vision model; using an LLM as OCR;
  "用 AI 看圖抽資料"; calling a separate AI service for extraction.
  SKIP when: a true OCR product needing raw text only (tesseract/textract, no semantic
  structure); a pure text LLM call with no image + no caching need; a one-shot script
  where cost/resilience don't matter.
tags: [backend, ai, vision, ocr, llm, caching, resilience, reference]
version: 1.0.0
source: manual
---

# ai-vision-extract

Turn a photo into structured data with an AI model, **without paying the vision cost
every time and without 500-ing when the model is slow/down**. Learned from
`~/code/iihi/web/app/food/actions.ts` (+ `gear`, `supplements`) — proven prod, but
**n=1 (one product)**: capture now, converge the canonical shape on the 2nd product
that needs it.

## The pipeline (the actual value)

```
photo ──①identify──▶ AI:/identify  (image → just the NAME, the cheap call)
        normalize(name) → cache key   (番↔蕃, strip space/punctuation)
        ──②lookup──▶ DB cache by key
              hit  → REUSE, no AI     (free + instant)
              miss → ③generate ──▶ AI:/analyze  (TEXT name → structured fields)
                     → persist (INSERT ... ON CONFLICT DO NOTHING)
```

1. **Two calls, not one**: identify from the image (cheap), then analyze from the
   **text name** — never re-send the image for the second step. Halves vision cost.
2. **Normalize before caching**: `normFood` collapses variants (番↔蕃, whitespace,
   punctuation) to one key. Without this the cache barely hits — "蕃茄" and "番茄 "
   miss each other and you re-pay the AI every time.
3. **DB-backed cache + persist**: a `food_item` table keyed on the normalized name;
   `ON CONFLICT DO NOTHING` so concurrent writers + a fresh-vs-warm DB converge. Every
   unique item costs the AI once, ever, across all users.
4. **Separate AI service** (`AI_URL`, its own port :8400, distinct from `BACKEND_URL`
   :8300): keeps heavy model deps / GPU / long timeouts isolated from the web app, and
   makes the model swappable behind a stable HTTP contract (`/identify`, `/analyze`).
   Web↔services share an `INTERNAL_SECRET` header.

## Resilience — every AI call (non-negotiable)

The model being slow or down is NORMAL, not exceptional. Each call:
- has a **timeout** (`AbortSignal.timeout(150000)` / equivalent),
- is wrapped in try/catch,
- on failure writes a **structured error onto the record** (`photo.meta = {error: reason}`)
  + `logOp(..., "error")` + revalidates the page,
- degrades to a user-actionable message ("AI 服務沒回應", "辨識不出食物,再拍清楚一點") —
  **never a 500, never a thrown stack to the user**.

## Gotchas

- **Don't re-send the image for the analysis step**: identify from the image once, then
  analyze from the cheap text name. Sending the image twice doubles the expensive call.
- **Normalize the cache key or the cache is theatre**: variant spellings/whitespace mean
  near-zero hit rate without a `normFood`-style normalizer.
- **AI-down is a normal branch, not an exception**: timeout + write the error to the
  record + show an actionable message. A vision feature with no timeout hangs the request.
- **Persist with `ON CONFLICT DO NOTHING`**: makes repeat items free and lets a fresh DB
  and a warm DB converge; without persistence every user re-pays for the same食物.
- **Keep the AI service separate + behind a stable contract**: `/identify`, `/analyze`
  HTTP endpoints, own process/port. Swapping GPT↔Claude↔a local model then never touches
  the web app. Don't import the model SDK into the web tier.

## Sources (SoT)

- `~/code/iihi/web/app/food/actions.ts` (the full pipeline), `app/gear/actions.ts`,
  `app/supplements/actions.ts` (same pattern, 3 features) — AI service endpoints
  `${AI_URL}/identify-food` + `/analyze-food`, cache table `food_item`, `normFood`.
- **n=1**: iihi (孕) only so far. Registry `rivendell/docs/spine-modules.md` (#19, AI-feature
  family). Converge the canonical shape when a 2nd product (receipts? documents?) needs it.
