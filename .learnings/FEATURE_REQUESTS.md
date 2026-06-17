# Feature Requests

Pending capabilities the user has asked for but isn't ready to build yet. Each
entry: what was asked, why, agreed scope, what triggers picking it back up.

---

## 2026-05-18 — Domain skill gaps surfaced by report-taxonomy redesign

**Asked**: 整理 Text Report Generation routing 時，按 domain（商業洞察 / 製造運營 / 廠務優化 / 工安治理）拆 client work，發現除 /iot-factory-report (廠務) 外多數 domain 沒有專屬 skill。Trigger: chart-design skill 完成後，user 反饋「客戶交付類有點亂」並提出 domain-driven 分類。

**Gaps** (by priority based on user's actual work):

| Domain | Sub-area | 現況 fallback | 觸發時機 |
|--------|----------|--------------|---------|
| 商業洞察 | 市場調研 / 配給預測 | /doc-coauthoring + chart-design | 光泉 FMCG case 已 fit，下次再做時抽 |
| 商業洞察 | 庫存水位預測 | manual + chart-design | 同上 |
| 商業洞察 | 通路 / 採購分析 | manual | 客戶有實際需求時 |
| 製造運營 | 時序製程分析 | /iot-factory-report 部分覆蓋 | 半導體 / FMCG 產線分析時 |
| 製造運營 | 視覺檢測 (AOI/SPC) | 無 | 看到實際 AOI 報告需求時 |
| 製造運營 | 排程 / 產能規劃 | 無 | 接到排程顧問案時 |
| 工安治理 | EHS 全 branch | 無 | 客戶要求合規報告時 |
| 法務文件 | RFP | /doc-coauthoring | 真實 RFP 撰寫需求 |
| 法務文件 | NDA | /doc-coauthoring | 同上 |
| 法務文件 | MOU | /doc-coauthoring | 同上 |

**Proposed approach** (when picking up): 每個 domain 一個 skill；內部按 sub-area 分流（同 `/iot-factory-report` 按 equipment type 分流的模式）。Skills 都 sub-call /chart-design 做視覺化。

**Trigger to revisit**: 接到該 domain 的真實案子時，從這份 gap 表挑對應 skill 抽出來做。優先順序按 user 接案頻率：商業洞察 (光泉再續) > 製造運營 (立積電/力成) > 法務文件 > 工安治理。

---

## 2026-05-08 — Tiered skill discovery (INDEX-first, drill into SKILL.md only when needed)

**Asked**: User asked whether skills should have a layered query system, so they can read a one-line index per skill (filtered by category) before deciding whether to invoke. Quote:「我只看後端相關 skills 的 index 一句話說明，來決定要不要調用」.

**Why**: Token economics. Every Claude Code session injects the full SKILL.md descriptions for all skills (~150 in this session, ~50-100 words each ≈ 10-20K tokens of skill metadata per turn). Most are irrelevant to the current task. The user noticed this is wasteful and asked for a tiered discovery pattern — same pattern as `ToolSearch` already implements for deferred tools (one-line names indexed, full schemas loaded on demand).

**What rivendell can change**:
- Produce an `INDEX.md` at repo root: `category | name | one-sentence purpose | trigger phrase`. ~100 lines, scannable in 30 seconds, far cheaper than full SKILL.md set.
- Add `bin/sk index` command (auto-regenerated post `bin/sk audit`).
- Optional: per-category index files (`skills/CATEGORIES/backend.md`, `skills/CATEGORIES/frontend.md`) for narrower scopes.
- Audit existing SKILL.md descriptions and trim the longest (some are 200+ word paragraphs when 1-2 sentences would work).

**What rivendell can't change**: Claude Code's harness is the one injecting full skill metadata into context. Until Claude Code adds tiered loading natively (similar to `ToolSearch`), the user/agent must opt out — e.g., by reading INDEX.md instead of letting all SKILL.md fire.

**Agreed scope (proposed)**: Build `bin/sk index` + `INDEX.md` first (low cost, immediately useful for human scanning). Defer SKILL.md description trimming to a separate sweep. Defer per-category drill-down until INDEX is in active use.

**Picks back up when**: User says "build the skill index" or token cost on a session feels untenable.

---

## 2026-04-30 — `slide-office-hours` skill ✅ RESOLVED 2026-05-03

**Resolution**: Skill built at `skills/docs/slide-office-hours/SKILL.md`. Now part of the storyline-first deck workflow (`~/.claude/CLAUDE.md` Slide / Deck Building section, Gate 3). 光泉 deck experience seeded the design.

---

(original request below for history)


**Asked**: User wants a gstack-style **interactive Q&A skill** specifically
for slide / pitch deck creation. Inspired by `gstack-office-hours`'s six
forcing questions and `gstack-plan-*` review skills' adversarial
challenge-and-rate pattern.

**Why**: Existing `slide-workflow` has 7 gates and `pitch-deck` has Discovery
Interview, but both are *informational fill-in* style ("what's the audience?",
"what's the time budget?"). Neither does the *Socratic-adversarial*
"逼你想清楚 story" pass that gstack-office-hours does. User wants this
because tuning a deck (current case: 光泉 pitch on 2026-04-30) takes
multiple iteration rounds and the existing skills don't sharpen the
underlying narrative — they just structure the output.

**Proposed scope (already discussed and acknowledged)**:

- New skill at `skills/docs/slide-office-hours/SKILL.md`
- Sits **before** `slide-workflow` Gate 2 — produces a `brief.md` that
  feeds into Gate 2 as a strong starting point
- Six forcing questions:
  1. 60 秒電梯故事是什麼？
  2. 聽完之後你希望聽眾做什麼**具體的下一步**？
  3. 如果只能留下 1 張 slide 給聽眾帶走，是哪張？
  4. 為什麼是「現在」做？(why now)
  5. 競品可複製什麼、不能複製什麼？
  6. 你最不想被問的問題是什麼？怎麼答？
- Optional adversarial mode: rate each answer 0–10, flag weak spots
  ("bullet 1 跟 3 重複", "你說 SOTA 但沒比較對象", "這故事在 $audience
  的房間會被噓")
- Output: `brief.md` with story arc, key messages, predicted Q&A,
  must-have / nice-to-have / kill slide list
- Handoff: trigger `slide-workflow` Gate 2 after brief is signed off

**TRIGGER candidates**: 「做簡報前先想清楚」「pitch 練習」「office hours
for slides」「這 deck 故事不太順」「pre-pitch review」

**DO NOT TRIGGER**: 已有完整 outline、純技術或內部報告、單純求 PPTX 輸出
直接走 `slide-workflow` 或 `office-pptx`

**Open naming question**: `slide-office-hours` vs `slide-discovery` vs
`pitch-rehearsal` vs 中文「簡報 office hours」. Decide when picking up.

**Trigger to revisit**: User said "等完成後再看" — currently tuning the
光泉 (KuangChuan) pitch deck (`Peter/Work/中華電/01-Presales/202604_光泉/`).
Pick this back up after that deck ships, ideally with the 光泉 experience
fresh as a real-world test case for what questions would have been most
useful to be forced to answer up-front.

**Effort estimate**: 1 SKILL.md, ~150 lines, no bundled scripts. ~30 min
write + iterate.

**Related skills already in catalog**:
- `slide-workflow` (skills/docs/) — 7-gate creation flow, this skill feeds it
- `pitch-deck` (skills/docs/) — narrative for investor pitches
- `slide-template-extractor` (skills/docs/) — extract style from existing deck
- `gstack-office-hours` — the methodology being borrowed

---

## 2026-04-30 — `cost-aware-model-routing` skill (also pending)

**Asked**: User implicitly agreed this was high-ROI when reviewing token cost
analysis but said "等完成後再看" applied to slide-office-hours. By extension
this one's also queued.

**Why**: 14-day token spend $10,683 with Opus 4.7 at 68% of cost. Most cron
headless agents (harvest, retro, scrapers, janitor) don't need Opus reasoning
and could run on Sonnet 4.6 at ~1/5 the cost — estimated $4-5K / week
savings.

**Proposed scope**: ~200 line SKILL.md covering Opus/Sonnet/Haiku decision
matrix, headless `claude -p --model claude-sonnet-4-6` cron pattern,
cost-aware iteration (Sonnet for iteration, Opus for finalization),
prompt-cache failure modes ($18.75/M create on system-prompt change /
>5min idle).

**Trigger to revisit**: Same as slide-office-hours — after 光泉 deck.

---

## How to pick these up

When ready: read this file → pick top entry → invoke `skill-creator`
with the proposed scope as args. If user has new context (e.g. lessons
from 光泉 deck process), incorporate before writing.

## 2026-06-17 — 後端設計規範候選（暫不抽，n=1/divergent）

cross-check ChimesFlow vs tukey-automl 後,3 個候選都**不是跨專案標準**,故不 codify
成 skill（避免 n=1 enshrinement，見 ~/.claude/learnings 2026-06-17）：

- **async session/transaction ownership** — DIVERGENT：ChimesFlow async+dependency 自動 commit；tukey-automl sync+handler commit。是架構選擇,不是 style。→ 若第 3 個 FastAPI app 出現,抽成「session 交易歸屬」**分層** rubric（async-dep-owns vs sync-handler-owns），別規定單一做法。
- **RBAC scoping model** — 不同模型：ChimesFlow department-based 組織 scoping；tukey-automl project-based 多租戶。`rbac-permissions` 已涵蓋基礎;這層「組織 vs 多租戶 scoping」等第 3 例再決定要不要分層 skill。
- **response envelope + HTTP status** — ABSENT in tukey-automl（只有 ChimesFlow 有 PaginatedResponse/ErrorResponse/CRUD_RESPONSES）。n=1,不是標準。第 2 個 app 也採用時再抽。

**Trigger to revisit**：任一條在第 3 個（或第 2 個一致的）codebase 出現相同模式時，抽成**分層** rubric skill。唯一通過驗證、已 codify 的是 `backend-async-jobs`（tiered）。
