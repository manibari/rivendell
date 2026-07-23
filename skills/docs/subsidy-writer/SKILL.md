---
name: subsidy-writer
description: >
  Write Taiwan government subsidy proposals (政府補助計畫書) end-to-end — official
  目錄 framing, A/B/C/D 分項架構 with 經費占比, 逐題拍板 decision loop, 委員白話
  writing rules, quantified benefit models with explicit assumptions, 紅字▲
  pending-item tracking, and md-SoT → docx build pipeline. Use this whenever the
  user is applying for a government grant/subsidy and needs the proposal document
  written — "投補助案", "寫計畫書", "補助申請書", "SBIR", "數產署補助", "AI 創新補助",
  even if they only paste the 申請須知 and say "我要投這個".
  SKIP: finding subsidies to apply for (subsidy-scraper); RFQ/tender responses
  (rfq-writer); consulting contracts (sow-writer).
tags: [docs, business, government]
version: 1.0.0
source: manual
user_invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep, WebSearch"
---

# Subsidy Writer — 政府補助計畫書

Write a submission-ready government subsidy proposal. Distilled from a real case
(2026-07 數產署 AI 創新服務研發補助, 500 萬上限, 2-day sprint to deadline) where
every rule below was earned through reviewer-style feedback.

**Step 0 (HARD GATE): Read `references/writing-rules.md` before writing any prose.**
Those rules override your default writing style. They exist because a proposal is
read by 審查委員 — non-specialist reviewers who punish jargon, and who must never
see your internal strategy on the page.

## Why this workflow

A subsidy proposal is not a technical document; it is a **structured argument to a
review committee** with hard formal constraints (official 目錄, 經費占比 rules,
eligibility red lines). The failure modes are always the same: self-invented
structure, jargon the committee can't parse, unquantified benefits, fabricated
facts, and internal calculus leaking into the body text. Each phase below closes
one of those holes.

## Phase 1 — 官方文件先行 (never invent structure)

1. Locate the official 申請須知 / 計畫書格式附件. If the user hasn't provided it,
   ask for it or find it in the project's `intel/` folder — a sibling case for the
   same program often already has it.
2. Use the official 章節目錄 as the document skeleton verbatim (typically:
   計畫摘要 → 壹、公司概況 → 貳、計畫內容與實施方法 → 時程/團隊/經費 → 附件).
   Do not rename, reorder, or merge sections.
3. Extract the **hard constraints** into the project STATE.md as a checklist:
   - 資格條件 (行業別代碼、憑證、財報、淨值)
   - 經費上限、自籌比例、經費科目限制 (e.g. 資安經費 ≥7%)
   - 紅線 (e.g. 不得為已開發技術、非中國來源模型、同期政府計畫件數上限)
   - 結案硬要求 (e.g. 付費用戶數、意向書)
4. **紅線 framing**: if existing technology underlies the proposal, frame the split
   explicitly — what exists (prior PoC, single-client custom work) vs. what is
   genuinely new R&D in this proposal. Never hide the prior art; position it as
   執行優勢 while the 新研發 carries the innovation claim.

## Phase 2 — 分項架構 (before any prose)

1. Decompose into 3–5 分項 (A/B/C/D…). 分項比重＝經費占比 is usually an official
   rule — assign percentages at the same time.
2. Decide **where the innovation claim lives**: exactly one 分項 is the
   創新性主戰場 (highest %, the genuinely new R&D). Others play support roles:
   productizing prior assets (可行性), delivery/UI (完整性), pilot + paid
   conversion (落地證據 — check the program's 結案 requirements).
3. 分項/工作項目 names must pass the 委員 test: no internal jargon
   (多租戶/DSL/pipeline → say what it does in plain words).
4. Work-item names must be **identical** across 內文, 架構圖, and 甘特圖 —
   reviewers cross-check.

## Phase 3 — 逐題拍板 (batch decisions, no guessing)

Facts you cannot derive → collect into **one numbered question list** for the user
(LLM/model choice, pilot count, pricing, KPI targets, market-size numbers,
company registration data). Never fabricate; never drip questions one at a time.

Write every answer back into STATE.md as 定案 so later sessions don't re-ask.
Anything still unanswered becomes a 紅字▲ item (Phase 6), not a guess.

Company facts: use 公開資料 (商工登記, official site) with source + retrieval date
noted; mark anything third-party-aggregated as ⚠️ 待確認.

## Phase 4 — 內文撰寫

Write into a single markdown file — the **content SoT** (e.g.
`cache/YYYYMMDD-計畫書內文/計畫書內文_v1.md`). All edits happen here first; docx
is always regenerated, never hand-edited.

Apply `references/writing-rules.md` throughout. The two highest-yield rules:

- Every work item = **one bold plain-language sentence** (the claim) + an indented
  natural paragraph (the detail). No 「細節：」 labels, no meta-notes to the reader.
- Body text must read as a **neutral report**. Strategy words (佐證/命門/加分/
  紅線/審查委員視角) and English shop-talk (recall-first, human-in-the-loop) never
  appear in the body — see Phase 6 for the scan.

## Phase 5 — 效益量化 (build the assumption model yourself)

Reviewers reject "大幅提升效率". Build an explicit calculation and show your work:

```
單廠年效益 = 月處理量 × 單件人工工時 × 工程師時薪 × 工時下降率 × 12
          + 避免損失 (事故次數/年 × 單次成本 × 下降率)
回收期    = 年度服務費 ÷ 單廠年效益
```

Rules: every assumption listed in a table, each marked 「規劃值，將於試點校正」;
KPI targets stated as numbers (處理時間 ≤X、正確率 ≥Y%、導入 ≤Z 天); market size
from a citable industry statistic (source + year), target-customer count as an
estimate with a stated calibration method — never a fake-precise number.

## Phase 6 — 紅字▲歸零 + 文體掃描

1. Every pending fact = red ▲ marker in the docx (`color C00000`). The user can
   flip pages scanning for red. Before submission, drive 貳章 (the substantive
   chapters) to **zero red marks** — company-profile blanks may stay longer since
   only the user can fill them.
2. Run the **審查文體掃描** from the de-slopify skill (審查文體模式 section):
   sweep the full text for internal-calculus traces, English shop-talk, and
   reviewer-facing asides. In the real case this pass found 12 instances after the
   author thought the text was clean — do not skip it.

## Phase 7 — 輸出

1. Generate docx from the md SoT via a build script — copy
   `assets/build-template.js` (docx npm package; includes the ▲red-marker helper,
   numbered-list, claim+detail, and table helpers). Run with
   `NODE_PATH=$(npm root -g) node build.js`.
2. Figures are **document illustrations, not slides**: height 620–740px at
   1600px width, tight padding, inserted at ~16.5cm width. Slide-ratio
   (1600×900) figures leave huge whitespace in A4 — regenerate, don't scale.
3. Figure content rules (from the diagram defaults): official 章節代碼 as
   top-level framing, work-item names matching the text, 委員-facing wording
   (no ports/tech brands).
4. Deliver: open the docx for the user, report page count, and list remaining
   ▲ items grouped by who can resolve them.

## Project conventions

- Presales-style folder: `STATE.md` (decisions, rules, risk list) +
  `cache/YYYYMMDD-<artifact>/` per deliverable. Update STATE.md every session —
  it is the cross-session memory.
- User feedback on wording/format is **cumulative law**: append it to a
  「寫作規則」 list in STATE.md and apply to all later output. The same feedback
  arriving twice means your direction is wrong — redo structurally, don't tweak.
