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
  ALSO covers the stage after submission (Phase 8): 收到書面審查意見表要準備審查會議
  簡報 — "審查意見回來了", "要上台報告補助案", "書面審查意見表", "照官方簡報格式做".
  SKIP: finding subsidies to apply for (subsidy-scraper); RFQ/tender responses
  (rfq-writer); consulting contracts (sow-writer); customer-facing sales decks
  (sales-deck-design — 那是對客戶提案，不是對審查委員).
tags: [docs, business, government]
version: 1.3.0
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
5. **Already have an approved similar plan?** If the company has a prior
   approved/submitted subsidy plan on a related theme, do NOT rewrite from scratch —
   mine it as a source library and write a 差異表 to clear the double-funding red
   line. This is a distinct workflow: read `references/reapply-from-approved.md`
   before Phase 2.

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

Apply `references/writing-rules.md` throughout. The three highest-yield rules:

- **Prose, not layout** (rule 9): narrative content (pain points, current-state
  analysis) is written as thesis-style paragraphs — no 破折號「——」, no tables
  for narrative, no inline labels/arrow chains, no parenthetical
  viewpoint lines. Tables only for genuinely tabular content (經費/指標/風險).
- Every work item = **three sections: 功能說明／執行項目／驗證項目** (rule 10) —
  a work item without a verification section is not a fundable 分項. Inside each,
  claims are one bold plain sentence + natural paragraphs; no 「細節：」 labels,
  no meta-notes to the reader.
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

**Three-tier benefit language** (rule 12) — never mix the tiers: 結案承諾 only
for auditable facts (付費成交 N 案、合約認列); technical/operational metrics are
目標值; assumption-derived numbers are 試算值. Writing a 試算 as a 承諾 is
exactly the 「宣稱」 reviewers strike down.

## Phase 6 — 紅字▲歸零 + 文體掃描

1. Every pending fact = red ▲ marker in the docx (`color C00000`). The user can
   flip pages scanning for red. Before submission, drive 貳章 (the substantive
   chapters) to **zero red marks** — company-profile blanks may stay longer since
   only the user can fill them. Maintain a `待補清單.md` that sorts the ▲ items by
   **who is blocked and lead time**, not by page order, so the user attacks them in
   the right sequence:
   - **A. 要對外要文件的** (longest lead time, do first): 意向書用印、顧問願任
     同意書、第三方資安檢測機構擇定、ISO 證書影本、客戶名單。
   - **B. 使用者可直接拍板**: 效益數字定版、關鍵人員名單、經費科目取捨。
   - **C. 等核定日才能定**: 預定進度表/查核點的實際年月。
   - **D. 編列體例待審查意見**: LLM 用量列無形資產 vs 雲端租賃等。
   Only A and B block submission; C and D can carry a note explaining the dependency.
2. Run the **審查文體掃描** from the de-slopify skill (審查文體模式 section):
   sweep the full text for internal-calculus traces, English shop-talk, and
   reviewer-facing asides. In the real case this pass found 12 instances after the
   author thought the text was clean — do not skip it. Also run its
   structural-tells sweep: grep the full text for 「——」 (must be zero), arrow
   chains, inline labels, and parenthetical viewpoint lines.
3. **連動網 check** (rule 11): the document is a cross-reference web — 功能規格表
   has a 對應交付 column, 分項驗證項目 point back to the spec table, pain points
   keep their numbers and later sections cite 「回應痛點 N」, and work-item names
   are identical across 內文/架構圖/甘特圖. After ANY rename, renumber, or
   deletion, grep the full text for the old reference before regenerating the
   docx — a dangling reference is the first thing a reviewer catches.

## Phase 7 — 輸出

1. Generate docx from the md SoT via a build script — copy
   `assets/build-template.js` (docx npm package; includes the ▲red-marker helper,
   numbered-list, claim+detail, and table helpers). Run with
   `NODE_PATH=$(npm root -g) node build.js`.
2. Figures — read `references/figures.md` before making any. Two distinct types:
   the **official black-and-white WBS 計畫架構圖** (reviewers use it to check
   經費占比 and cross-reference 預定進度表 — an HTML skeleton is in that file), and
   **low-saturation explanatory illustrations** (system function, deployment,
   Gantt). Both are **document illustrations, not slides**: 1600px wide × 620–740px
   tall (official WBS closer to 4:3), inserted at ~16.5cm. Slide-ratio (1600×900)
   figures leave huge whitespace in A4 — regenerate, don't scale. Every figure must
   be screenshot-verified (headless Chrome) before it counts as done.
3. Deliver: open the docx for the user, report page count, and hand over the
   `待補清單.md` (Phase 6) so the user sees what is blocked on whom.

## Phase 8 — 書面審查意見 → 審查會議簡報 (after submission)

送件不是終點。台灣補助案的標準流程是 **送件 → 書面審查意見 → 審查會議簡報**，所以
每個走完 Phase 7 的案子都會再回來一次。入口狀態不同（你手上有委員意見表、送審版
計畫書、官方簡報範本），但機器是同一套：官方格式先行、逐題拍板、紅字▲、md-SoT →
輸出。

**Read `references/review-rebuttal.md` before planning the deck.** 那裡有意見的
四類分類法（決定每條要不要佔版面、要不要動計畫書）、頁次骨架、逐頁素材盤點的
✅🟡🔴 表，以及素材露出的敏感決策清單。

三件在這個階段最容易錯的事，先知道再去讀細節：

1. **交付物是兩份，不是一份。** 指出「正文與表格對不起來」的意見沒有回答空間，只有
   修正——簡報之外還要交一份改過的計畫書 docx。只做簡報等於當場承認錯誤卻交不出改正。
2. **逐頁素材盤點要在寫內容之前做。** 標完 ✅🟡🔴 才知道哪幾頁根本沒料。那次 33 頁
   有 6 頁是硬缺料，而且全是委員問得最兇的幾條；先盤點，它們在第一小時就變成問使用者
   的題目，而不是寫到第 20 頁才卡住。
3. **官方大綱不可動。** 深答頁塞進第一章之內，不要為了回應意見新增章節——與 Phase 1
   的 目錄先行 同一條規矩。

## Project conventions

- Presales-style folder: `STATE.md` (decisions, rules, risk list) +
  `cache/YYYYMMDD-<artifact>/` per deliverable. Update STATE.md every session —
  it is the cross-session memory.
- User feedback on wording/format is **cumulative law**: append it to a
  「寫作規則」 list in STATE.md and apply to all later output. The same feedback
  arriving twice means your direction is wrong — redo structurally, don't tweak.
