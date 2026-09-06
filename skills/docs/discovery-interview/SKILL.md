---
name: discovery-interview
loop: sales
pdca: plan
description: >
  Run a structured Discovery interview with a potential consulting client to find their
  most painful manual workflow — the basis for an AI agent proposal and SOW.
  Produces a discovery-summary.md that feeds directly into sow-writer.
  TRIGGER when: user says "客戶 discovery", "需求訪談", "discovery interview", "客戶痛點挖掘",
  "找客戶第一個 agent", "客戶第一次會議準備", "30 分鐘訪談", "問客戶什麼問題".
  DO NOT TRIGGER when: user has already done discovery and wants to write the SOW directly
  (use sow-writer instead).
tags: [docs, workflow, business]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash"
---

# Discovery Interview

Structured first-meeting discovery to find the client's most painful workflow — the wedge for an AI agent engagement.

## Goal

In 30–60 minutes, find:
1. **One specific repetitive workflow** that costs real human hours
2. **The systems/data** that workflow touches
3. **The decision-maker** and their AI/budget context
4. **Enough detail** to write a credible RFQ + SOW

## Pre-Meeting Checklist

Before the meeting, confirm:

- [ ] **參與者**: 誰是決策者？誰是業務使用者？IT 是否在場？
- [ ] **產業/規模**: 員工數、主要產品/服務
- [ ] **底層系統**: ERP 品牌、有無 OSIsoft PI、主要資料庫
- [ ] **公開資料**: 公司網站、新聞、最近募資/採購訊息

## Interview Script

Walk through these sections in order. Adjust pacing — if the client is engaged on B (痛點), spend more time there.

### A. 開場：現況理解（10 分鐘）

| # | 問題 | 預期答案 / 用途 |
|---|------|---------------|
| A1 | 公司目前如何使用 AI 或自動化？ | 「ChatGPT 手動用」或「完全沒有」。如果已有，追問哪種工具、誰在用 |
| A2 | 老闆/董事會對 AI 導入有什麼期待或壓力？ | 「被要求要有 AI」或「想降低人力成本」— 預算授權的線索 |
| A3 | 目前 IT 資源的能力？有沒有內部工程師？ | 沒工程師 → 需要包辦更多；有 → 評估後續誰維護 |

### B. 核心痛點：找出那個流程（15 分鐘）—— 最重要的一段

| # | 問題 | 引導方向 |
|---|------|---------|
| B1 | 你們目前哪個業務流程最重複、最耗人力？ | 日報/週報、資料彙整、例行審查、客戶通知。目標：找一個「每天/每週都要做、不做會出問題」的流程 |
| B2 | 這個流程現在是誰在做？多少人？花多少時間？ | 計算公式：人數 × 時間 × 工作天 = 月人力成本。範例：3 人 × 2h/天 × 22 天 = 132 人時/月 |
| B3 | 做這個流程需要從哪些系統拿資料？ | 廠務：OSIsoft PI、SCADA、MES、自建 DB。ERP/業務：SAP、Oracle、自建、Excel。追問：API 還是 DB？ |
| B4 | 做完這個流程的輸出是什麼？給誰看？ | 日報 PDF 給廠長、異常通知 email、進度報表給客戶 — 決定 agent 的輸出格式 |
| B5 | 這個流程出錯過嗎？出錯的代價是什麼？ | 量化痛點 — 罰款、客戶投訴、production downtime |

### C. 預算與決策（10 分鐘）

| # | 問題 | 用途 |
|---|------|-----|
| C1 | 這類專案通常的預算範圍？ | 校準後續報價區間 |
| C2 | 採購/簽約流程通常多久？ | 規劃時程 — 政府/上市公司常需 2-3 個月 |
| C3 | 你的決策權限到哪？需要誰簽核？ | 找出真正決策者 |
| C4 | 有沒有比較過其他廠商或方案？ | 了解競爭、客戶教育程度 |

### D. 結束：下一步（5 分鐘）

| # | 問題 / 行動 |
|---|-----------|
| D1 | 確認下次會議：「我們會在 {N} 個工作日內準備 RFQ 草稿，下次會議目標是 {goal}」 |
| D2 | 索取資料：API 文件、欄位定義、現有報表範例 |
| D3 | 確認 NDA 是否需要先簽 |

---

## Output: discovery-summary.md

After the meeting, save to `docs/discovery/{client-shortname}-{date}.md`:

```markdown
# Discovery Summary — {Client Name}

- **日期**: {YYYY-MM-DD}
- **出席**: 甲方 [names + titles] | 乙方 [names]
- **下次會議**: {date} — {goal}

## 公司背景
- 產業 / 規模 / 主要產品
- 現有 IT 能力與系統

## 找到的核心痛點
**流程名稱**: {一句話描述}

| 項目 | 內容 |
|------|------|
| 誰在做 | {N} 人 |
| 頻率 | {每日/每週} |
| 每次耗時 | {N 小時} |
| 月人時成本 | {N} 人時/月 ≈ NTD {N,NNN} |
| 涉及系統 | {system 1, system 2, ...} |
| 輸出格式 | {報表/email/通知} |
| 出錯代價 | {quantified pain} |

## 預算與決策
- 預算範圍: NTD {min}-{max}
- 採購時程: {N} 個月
- 真正決策者: {role/name}
- 競爭情境: {none / vendor X / built-in solution}

## 下一步
- [ ] 取得 {data/document/access}
- [ ] 草擬 RFQ → 預計 {date}
- [ ] 草擬 SOW → 預計 {date}
- [ ] 簽 NDA: {needed / done / not needed}

## 提案方向（內部評估）
- 建議第一個 agent: {agent name + 1-line description}
- 預估人天: {N} 人天
- 預估報價: NTD {amount:,}
- 主要風險: {risk}
```

---

## Hand-off to Next Skill

After saving discovery-summary.md, suggest the next step:

> Discovery 完成。建議下一步：
> - **如果客戶願意進入提案階段** → 用 `sow-writer` 草擬 SOW
> - **如果還在評估階段** → 先寫 RFQ（簡單版報價）
> - **如果需要技術 workshop** → 排 Metadata Workshop（參考 lorien/docs/templates/metadata-workshop-checklist.md）

---

## Common Mistakes to Avoid

- ❌ 問太多開放問題，讓客戶滔滔不絕但抓不到痛點
- ❌ 在 A 段（現況理解）花太多時間，沒有進到 B 段
- ❌ 沒有量化痛點（人時成本）— 後續報價無法說服客戶
- ❌ 沒有確認決策者 — 提案做了但給錯人
- ❌ 沒有設定明確的下次會議目標

## Reference Templates

Original templates this skill is based on:
- `~/Documents/Projects/lorien/docs/templates/discovery-checklist.md`
- `~/Documents/Projects/lorien/docs/templates/discovery-summary.md`
- `~/Documents/Projects/lorien/docs/templates/metadata-workshop-checklist.md` (for follow-up workshops)
