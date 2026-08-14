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

## 2026-06-24 — 真實 repo harvest（ChimesFlow/tukey-automl/PTI-ARES/IC-YMS 一週開發）

daily harvest 盲區（只收排程噪音）→ 直接挖 4 個主力 repo。候選（嚴格 triage，
domain-reference 容許 n=1 codebase；design-rubric 需第 2 架構驗證）：

### 🟢 建議優先建（grounded domain reference，清楚可重用、零覆蓋）
- **`odb-dfm-reference`**（PTI-ARES，n≥2）— ODB++ 解析 + DFM domain：matrix/profile/feature 解析、UNITS inch→mm per-layer、.Z gzip-aware 讀層、bbox 旋轉/鏡像。**這就是 session 早期想建未建的 DFM/CAM 知識 skill,現在有真實 code grounding。** src/pti_ares/parser.py, enricher.py。
- **`ic-lot-normalization`**（IC-YMS,n=3 routers）— 半導體 lot/batch 正規化:wafer/pkg lot、product code、program variant;subcon(SG/GS/JCET/Carsem)+ TE 平台碼(SG9000/STS8200)。backend/normalize.py(257 行,test 驗證)。

### 🟡 tukey-automl ML-platform 群（richest vein,但全 n=1 codebase → 當 reference 待第 2 ML 專案驗證,值得一次專門 pass）
- DQ monitoring(missing_rate+drift,無 label,n=3)｜CV robustness gate(LOOCV/stratified/Q²,小資料,n=3)｜model registry+lineage(SIT→UAT→PROD,n=4)｜DOE/RSM 參數最佳化(desirability/PSO/factor-rank,n=4,與 tukey-or 連動)｜task-aware metric dispatch(n=2)。

### 🟡 ChimesFlow（偏 design-rubric → 需第 2 架構驗證,先 pending）
- config-layering-resolver(DB>env per-field fallback,n=3)｜data-consistency-guard(authority 欄位 coercion,n=2)｜temporal-aggregation-view(CRM 週視圖,n=3,domain 偏窄)。
- temporal-boundary-validation(排除未來日期,n=2)→ 太薄,記成 learning 不抽 skill。

### ⚪ 不抽
- PPTX 週報(n=1)｜IC SPC/yield(9% 資料覆蓋,太早,2 sprint 後再看)｜DFM rule framework(eng-review locked,未穩)｜前端 viz(UI 迭代無 domain)。

**Trigger to revisit**：ML 群等第 2 個 ML 專案;ChimesFlow rubric 群等第 2 架構;IC-SPC/DFM-framework 等資料/設計穩定。

## 2026-07-06 — session-harvest（9 sessions：新北案 demo / 演講備料 / SOW / 新專案）

本輪無 Strong 候選；多數 session 為正確觸發既有 skill（sow-writer、requirement、
subsidy-scraper、context-recovery、office-pptx）。兩個 Moderate 候選 hold 待第 2 實例：

- **`demo-walkthrough-pages`**（提案用互動 demo 頁管線）— 情境腳本 → 多畫面
  walkthrough HTML（假資料、build script 產版）→ headless Chrome 截圖鏈自檢 →
  PNG 餵 office-pptx。新北案兩輪（YouBike 動線、訴願填寫/預評估）形狀一致，但
  **n=1 客戶專案**。與 mockup / gstack-design-html 重疊大，delta 只有「情境
  walkthrough + 截圖鏈 + 餵 deck」黏合層。→ 第 2 個客戶/專案出現同需求時再抽，
  屆時優先評估併入 mockup 當一個 mode。
- **`gdrive-deck-miner`**（舊 deck 內容開採）— Google Drive 歷史簡報當素材庫：
  getGoogleSlidesContent 抽每頁文字/講者備註 → 主題歸併 → 新演講 outline +
  可重用頁清單。與 gdrive-to-skills（轉知識）、slide-template-extractor（抽樣式）
  角度不同，零覆蓋；但 **n=1 session**（數位孿生演講）。→ 再出現一次「舊 deck
  開採」即升 Strong。

**Trigger to revisit**：demo 頁遇第 2 個客戶；deck 開採遇第 2 場演講。
詳見 reports/harvest-2026-07-06.md。

## 2026-07-07 — session-harvest（11 sessions：9 個為排程 headless）

本輪無 Strong 候選；9/11 sessions 是排程自動化在跑（台股新聞情緒 ×7、token 日報、
crm-projection），可收割的人工模式極少。一個 Moderate hold：

- **`personal-info-vault`**（個人資訊 SoT → 官方表單自動填寫）— 使用者主動提議
  「放一個資料夾收集我的個人資訊」，本輪走 office-docx 填提名表（fill_form.py +
  掃描頁對照）。設計方向：個人資料 markdown SoT（基本資料/學經歷/證照/公司資訊）
  → 表單欄位對映 → 路由 office-docx/office-pdf，缺欄回問並回寫 SoT。
  **n=1 表單** → 等第 2 份不同官方表單出現、確認 SoT schema 可重用再抽
  （薄 orchestrator + data files 原則）。

**Trigger to revisit**：第 2 份表單填寫需求。詳見 reports/harvest-2026-07-07.md。

## 2026-07-23 — slide-office-hours: channel-enablement 缺 profile cell

**Context**: 詠鋐通用 channel enablement deck（給通路 SI 業務的動能+產品地圖簡報）跑
/slide-office-hours 壓測，frontmatter 的 `profile` 四值（傳產中小/大型科技廠/公部門/新創）
全是「終端客戶」畫像，通路夥伴聽眾無格可對；`stage` 亦然（audience 是 channel sales，
非客戶決策者）。本次 review 以 Layer 1 全跑 + Layer 2/3 就近類比（operator_guesses ≈
認客戶 checklist；differentiation_target ≈ 「channel 為何帶我們而非其他供應商」）。

**Request**: 新增 profile: `通路SI`（或獨立 checklist）：必查 (a) 認客戶 checklist ≥3/端
且 operator-level；(b) differentiation vs channel 自家 AI 團隊/其他被代理供應商；
(c) channel mix 敏感性（案例來源集中於單一 channel 時，通用版如何呈現）。
**n=1** — 等第 2 份 channel/partner deck 需求出現再抽。
**Refinement (同日壓測討論)**：通路 deck 要先分兩型——recruitment（招親，differentiation
必查）vs enablement（打法/playbook，合作已存在，differentiation 降級為「業務省力濾鏡」：
每頁檢查是否讓 channel 業務更容易推）。上面 (b) 的 differentiation 必查僅適用 recruitment 型。

## 2026-08-06 — session-harvest（7 sessions：ChimesFlow / PTI-ARES 家族拆 repo）

一個 Moderate hold：

- **`repo-contract-brief`**（sibling repo 契約優先 + 直接查證取代假設）— PTI-ARES 功能
  拆到 3 個 sibling repo（Transcribe=寫入 PG／Translate=讀取渲染／Main=顯示），3 個獨立
  session（Converter/Transcribe、Main、Translate）各自都先用直接查證（`psql`/`docker exec`/
  重新解析原始檔）確認上游真實現狀，才寫 `api-contract.md`（消費者視角、先於 requirement），
  再進 `requirement.md`/`schema.md`。順序一致、被同一條架構決策（PG 必須自足、不依賴外部檔）
  逼出來。**但 3 次集中在同一天、同一個 fleet、同一功能的拆解**，比較像一個計畫分派到 3 個
  repo 各跑一次，而非不相關情境各自獨立重新發現——只到 Moderate。
  → 等下一個不同 fleet 產品（如 tukey-* 或 ic-yms）出現「功能跨 sibling repo 拆分、需要
  契約優先」的情境再抽，可参考 spine-* 系列「先驗證多產品收斂、再定 canonical + divergent
  兩層」的寫法。

**Trigger to revisit**：第 2 個不同 fleet 產品出現同款 repo 拆分。詳見 reports/harvest-2026-08-06.md。

## 2026-08-14 — 8 月 harvest 候選盤點（補追蹤斷鏈）

8 月出了三個 🟢 Strong 候選，全都停在 `reports/` 沒有進到這裡——報告寫得勤，但
「報告 → 追蹤檔 → 動手」這條鏈是斷的。補記如下，並定一條規矩：**harvest 報告出現
Strong 候選時，同一輪就在這裡開一條**，否則下一份報告蓋過去就沒人記得。

| 候選 | 來源 | 狀態 |
|---|---|---|
| `skill-apply` | harvest 08-03 🟡 → 08-05 🟢 | ✅ 已建（`skills/meta/skill-apply`, 2026-08-13） |
| `subsidy-review-deck` | harvest 08-07 🟢 | ✅ 已併入 `subsidy-writer` Phase 8 + `references/review-rebuttal.md`（2026-08-14），未獨立成 skill |
| `site-survey-transcription` | harvest 08-01 🟢 | ⬜ **未動，仍開放** |

### ⬜ `site-survey-transcription`（唯一還沒處理的）

harvest 08-01 標 Strong。尚未回頭核對原始 session 的產物與形狀——動手前先做一次，
比照 `skill-apply` 的做法（去磁碟上找當時的實際交付物，別只信報告的描述；08-07 那次
報告寫的 `architecture-review-chimesflow.html` 就已經不存在了）。
詳見 `reports/harvest-2026-08-01.md`。

### 為什麼 subsidy-review-deck 選擇併入而非獨立

08-07 報告已建議優先評估併入，實際看過產物後確認：那次的交付物**包含一份修正版計畫書
docx**，而那正是 subsidy-writer 的核心產物。拆成獨立 skill 等於要重抄一整套 docx build、
figures 規格、紅字▲、writing-rules HARD GATE。入口狀態不同（手上有意見表而非申請須知），
但機器完全共用，且是同一個案子資料夾的下一站——按 sequence 而非按 invocation 切。

### 仍在 hold 的 Moderate（沿用既有條目，未變動）

`demo-walkthrough-pages`（07-06）、`gdrive-deck-miner`（07-06）、`personal-info-vault`
（07-07）、`repo-contract-brief`（08-06）、光泉配給預測（05-18 條目，08-05 有進展）。
另 08-11 兩個 Weak 觀察等第 2 實例：多來源 ETL 合併、跨專案 port registry。
