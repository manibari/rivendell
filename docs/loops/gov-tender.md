# gov 循環細化：政府標案（tender）

> 2026-09-07 依 `skills/gov/*` 與 `materials/tenders/` 實查。這是**一條循環的展開**，不是新分類；
> 對應角色頁第 4 節（顧問／報告與標案撰寫），loop = `gov`。補助（subsidy）是同循環的另一條線，另開文件。

## 一句話

現在只有「找到標案」和「寫文件」兩段有 skill；**要不要投、投得對不對、投完發生什麼事，全部沒有落地**。
README 的 Loop × PDCA 表 gov 那列 check／act 是「—」，不是漏標，是真的沒有。

## 現況：跑一次會發生什麼

```
[Plan]  gov-tender-scraper（排程）
        g0v API → 關鍵字過濾（keywords.yml）→ 去重 → 寫 cases/{job}.md → 過期歸檔 → 重生 INDEX
        → Step 7 未命中標題分析 → keywords.yml candidates
[Do]    gov-rfq-writer（報價單）、sow-writer（工作說明書）、gov-subsidy-writer（補助計畫書，不是標案）
[Check] —
[Act]   —
```

證據：

- case 檔的 `status` 只有 `active` / `archived`，而且**由截止日決定**，不是由人的決定決定（`gov-tender-scraper/SKILL.md:180-184`）。
- `materials/tenders/` 除了爬蟲自己，沒有任何 skill 讀它（grep `skills/`、`dashboard/`、`bin/`、`scripts/`：只有三處把它當路徑範例）。
- 標案要交的是「服務建議書／投標文件」，不是 RFQ；`~/.claude/CLAUDE.md` Text Report 段已標 `RFP ★ 暫無 skill → doc-coauthoring`。
- 沒有任何地方記「投了沒、得標沒、為什麼沒得標」，所以 Step 7 的關鍵字回饋是**唯一**的學習迴路，而且它學的是「標題像不像」，不是「我們投得上投不上」。

## 細化後的 PDCA

| 階段 | 步驟 | 現在用誰 | 狀態 | 缺什麼 |
|---|---|---|---|---|
| **Plan** | P1 抓標案、過濾、歸檔、重生 INDEX | `gov-tender-scraper` | ✅ | — |
| | P2 **評估要不要投**：機關、預算、資格門檻、截止日、跟我們能力的吻合度，給一個 go / no-go 和理由 | ★ 無 | 缺 | `gov-tender-triage`：讀 case 檔 + 招標文件，出 fit 評分與資格檢核，寫回 `status: evaluating → bidding | no-bid` 與 `decision_reason` |
| | P3 查機關與競爭對手（過去誰得標、決標價） | `tw-company-lookup`（部分） | 半 | g0v 有決標資料端點；P3 可併進 triage |
| **Do** | D1 報價 | `gov-rfq-writer` | ✅ | 但 RFQ 是議價前的報價單，不是投標價格單 |
| | D2 工作說明書 | `sow-writer` | ✅ | — |
| | D3 **服務建議書／投標文件**（依招標文件章節、評選項目配分寫） | ★ 無（fallback `doc-coauthoring`） | 缺 | `gov-tender-proposal-writer`：跟 `gov-subsidy-writer` 同型——官方章節代碼當框架、逐題拍板、紅字歸零；差別是框架來自招標文件與評選表 |
| | D4 圖表、Word 輸出 | `chart-design` → `office-docx` | ✅ | — |
| **Check** | C1 投標前檢核：資格文件齊不齊、押標金、印章、份數、截止時間、格式（頁數、字級） | ★ 無 | 缺 | 一張 checklist 就夠，放在 D3 的收尾；漏一項就廢標，這是整條循環最貴的失敗 |
| | C2 審查文體：去內部代號、去自評、委員白話 | `de-slopify` 審查文體模式、`say-it-plain` | ✅ | — |
| | C3 評選簡報與答詢 | `gov-subsidy-writer` Phase 8 的形狀 | 半 | 補助的「審查意見回覆」和標案的「評選簡報」流程相近，可抽共用 |
| **Act** | A1 **開標結果回填**：won / lost / no-bid，決標價、得標者、我們的價、落差原因 | ★ 無 | 缺 | 爬蟲加一步：對 `status: bidding` 的案子查 g0v 決標端點，自動回填 `result`、`awarded_to`、`awarded_amount`；人補 `lost_reason` |
| | A2 關鍵字回饋 | `gov-tender-scraper` Step 7 | ✅ | 只回饋「標題命中」，應再吃 A1：得標的關鍵字加權、no-bid 多次的降權 |
| | A3 案例沉澱：得標案變成下一次的素材與實績 | ★ 無 | 缺 | won 的案子推進 `sales-material` 素材庫（案例）與 `knowledge-graph`（機關、承辦、競爭者事實） |
| | A4 循環回顧：命中率、投標率、得標率、平均落差 | ★ 無 | 缺 | 一張表從 case frontmatter 算出來，掛進 `workflow-retro` 或 dashboard gov 頁 |

## 狀態機（要先定，其他都掛在它上面）

現在 `status` 是截止日的函數。改成人的決定加上事實回填：

```
active ──(P2 triage)──▶ evaluating ──▶ bidding ──(截止)──▶ submitted ──(A1 決標)──▶ won | lost
   │                        │
   └── deadline 過 ──▶ expired    └──▶ no-bid（含 decision_reason）
```

frontmatter 新增欄位（全部可選，爬蟲不填不會壞）：

```yaml
status: active | evaluating | bidding | submitted | won | lost | no-bid | expired
fit_score: 0-5            # P2
qualification_ok: true    # P2 資格門檻
decision_reason: ""       # P2 / no-bid
our_bid_amount: ""        # D1
awarded_to: ""            # A1
awarded_amount: ""        # A1
lost_reason: ""           # A1（人填）
```

`archived/` 目錄保留給 expired 與已結案（won/lost/no-bid）的案子；狀態以 frontmatter 為準，跟 `presales-pipeline` 同一條規矩。

## 優先順序（照「哪一步不做最貴」排）

1. **C1 投標前檢核**：一張 checklist，一小時。漏一項就廢標，投入全部歸零。
2. **P2 triage + 狀態機**：沒有 go / no-go 紀錄，後面的 A1、A4 都沒有分母。
3. **A1 決標回填**：爬蟲多一步，資料 g0v 本來就有；這是讓循環真的閉合的那一步。
4. **D3 投標文件 writer**：接到第一個真的要投的案子再抽，形狀照 `gov-subsidy-writer`（用真案子抽 skill，不憑空寫）。
5. A3、A4 等前面有資料再說。

## 跟其他循環的接縫

- 得標 → `sales` 循環的 `presales-pipeline`／`sales-client-kickoff-docs`（案子從標案變成客戶）。
- 機關、承辦人、競爭者 → `knowledge-graph`。
- 爬蟲存活 → `platform` 循環（`agent-launchd`、排程健康），不在這條循環裡。

## 登錄

- 角色頁：`docs/skills-by-role.md` 第 4 節連到本文件。
- 缺的四支能力登記在 `.learnings/FEATURE_REQUESTS.md`（2026-09-07）。
- 補助線（subsidy）的細化另開 `docs/loops/gov-subsidy.md`，它的 Check／Act 已有 Phase 6–8，缺口不同。
