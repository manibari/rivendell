---
name: internal-comms
description: >
  Templates for during/after-project stakeholder comms — 3P updates, status reports,
  incident reports, FAQs, newsletters.
  TRIGGER: "weekly update", "3P update", "status report", "incident report",
  "客戶週報", "進度報告", "事故報告".
  SKIP: pre-engagement docs (sow-writer / gov-rfq-writer / jd-writer / sales-customer-intel).
version: 1.0.0
tags: [docs, communication, status-update, reports]
languages: all
user_invocable: true
---

# Internal Communications

## When to use this skill

To write organizational communications, use this skill for:
- 3P updates (Progress, Plans, Problems)
- Company / team newsletters
- FAQ responses
- Status reports
- Leadership updates
- Project updates
- Incident reports
- Other stakeholder-facing recurring comms

## How to use this skill

1. **Identify the communication type** from the request.
2. **Load the appropriate guideline file** from the `examples/` directory:
   - `examples/3p-updates.md` — Progress / Plans / Problems team updates
   - `examples/company-newsletter.md` — Company- or team-wide newsletters
   - `examples/faq-answers.md` — Answering frequently asked questions
   - `examples/general-comms.md` — Anything else that doesn't explicitly match the above
3. **Follow the specific instructions** in that file for formatting, tone, and content gathering.

If the communication type doesn't match any existing guideline, ask the user for clarification or more context about the desired format. If a useful new pattern emerges, propose adding a new file under `examples/` so the next instance can reuse it.

## Tone Adaptation

The bundled examples were originally written for a US-style internal corporate audience. When the user is writing for a Taiwan / Chinese-speaking team or for external clients, adjust:
- Formality level (繁體中文 business comms tend to be more formal than US tech-startup style)
- Section headers (translate or keep English depending on team norm)
- Greeting / sign-off conventions
- Use of bullet vs. paragraph

Always ask the user once if they have a preferred existing template before defaulting to the bundled examples.

## Keywords

3P updates, company newsletter, company comms, weekly update, faqs, common questions, updates, internal comms, status report, leadership update, project update, incident report, 進度報告, 週報, 事故報告

<!-- Ported from: https://github.com/anthropics/skills/tree/main/skills/internal-comms (2026-04-28) by skill-scout -->
