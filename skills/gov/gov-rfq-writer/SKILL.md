---
name: gov-rfq-writer
loop: gov
pdca: do
description: >
  Generate Request for Quotation (RFQ / 報價單) for consulting projects.
  Lighter than SOW — used for pre-contract negotiation with cost ranges, scope options,
  and version control for iterative pricing rounds.
  TRIGGER when: user says "寫 RFQ", "報價單", "估價單", "request for quotation", "報個價",
  "報價給客戶", "客戶要報價", "提案前的報價". Always check if a discovery summary exists first.
  DO NOT TRIGGER when: user wants the formal contract (use sow-writer) or a sales pitch (use pitch-deck).
tags: [docs, business]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# RFQ Writer

Generate Request for Quotation — the negotiation document **before** SOW signing.

## RFQ vs SOW

| Item | RFQ | SOW |
|------|-----|-----|
| Purpose | 議價、給客戶比較選項 | 法律約束的合約 |
| Cost format | 範圍 (e.g. NTD 30-50 萬) | 固定金額 + 稅 |
| Scope | 高層次描述 | 完整工作項目 + 人天 |
| Version | 多版本迭代（V1, V2...） | 一次定稿，變更走 change order |
| Length | 1-2 頁 | 8-15 頁 |
| Legal terms | 簡單免責聲明 | 完整合約條款 |
| Validity | 有效期限（30/60 天） | 合約有效期 |

---

## Phase 1: Gather Inputs

If a `discovery-summary.md` exists in the project, read it first — most info is already there.

### Required inputs

- **客戶名稱**: 全名 + 簡稱
- **專案名稱**: 1 句話描述
- **痛點摘要**: 1-2 句話（從 discovery 直接帶過來）
- **建議方案**: 第一個 agent 名稱 + 預期效益
- **費用區間**: 顧問項目費 + 月費托管
- **時程估計**: 工期（週數）
- **報價有效期**: 預設 30 天

### Pricing reference (Lórien defaults, 2026)

| 項目 | 費用範圍 | 備注 |
|------|---------|------|
| 顧問項目費（一次性） | NTD 30-50 萬 | 含 discovery、metadata workshop、第一個 agent 開發、API 交付 |
| 簡單版（only 1 agent） | NTD 20-30 萬 | 用於 PoC |
| 旗艦版（多 agent + 客製整合） | NTD 60-100 萬 | 含 2-3 個 agent + Client Portal |
| 月費托管 | NTD 1-3 萬/月 | 含監控、維護、minor 更新 |
| Metadata workshop（單獨報價） | NTD 5-10 萬 | 如客戶想先做 schema 不開發 agent |

---

## Phase 2: Generate RFQ

Save to `docs/rfq/{client-shortname}-rfq-v{N}.md`. First version = `v1`, revisions increment.

```markdown
# 報價單（Request for Quotation）

| | |
|--|--|
| **報價單號** | {CLIENT}-RFQ-{YYYY}-{NNN}-v{N} |
| **報價日期** | {YYYY-MM-DD} |
| **有效期限** | {YYYY-MM-DD}（{N} 個日曆天） |
| **客戶** | {客戶全名} |
| **聯絡人** | {name} {email} |
| **報價方** | {你的公司全名} |
| **聯絡人** | {name} {email}｜{phone} |

---

## 一、專案背景

{1-2 段話描述客戶現況痛點，使用 discovery 中量化的數字}

> 範例：「貴司目前每日由 3 位廠務人員花費 2 小時人工彙整廠區設備數據產出日報，
> 每月約消耗 132 人時。本案目標為導入 AI Agent 自動產出日報初稿，
> 預計可減少 70% 人力投入。」

---

## 二、建議方案

### 方案內容

- **第一個 AI Agent**: {agent name} — {1 句話描述}
- **預期效益**:
  - 節省 {N} 人時/月
  - 等值人力成本約 NTD {NN,NNN}/月
  - ROI 預估：{N} 個月回本
- **技術範圍**:
  - 整合資料來源：{system 1, system 2}
  - 輸出形式：{PDF / Email / Web / API}

### 交付項目

| # | 交付項目 | 說明 |
|---|---------|------|
| 1 | Metadata YAML Schema | 客戶資料的業務語意梳理 |
| 2 | AI Agent v1.0 | 部署於客戶或 Lórien 環境 |
| 3 | OpenAPI 規格文件 | API 串接文件 |
| 4 | 教育訓練 1 場 | 半天，現場 |
| 5 | 維運手冊 | PDF + Markdown |

---

## 三、費用報價

### 方案 A: 標準版（建議）

| 項目 | 費用（未稅） |
|------|-------------|
| 顧問項目費（一次性） | NTD {amount:,} - {amount:,} |
| 月費托管（上線後選用） | NTD {amount:,}/月 |

**人天估算**：約 {N} 人天
**預估工期**：{N} 週

### 方案 B: 簡化版（PoC）

| 項目 | 費用（未稅） |
|------|-------------|
| PoC 顧問費（一次性） | NTD {amount:,} - {amount:,} |
| **不含**月費托管 | — |

**包含**：1 個 agent，僅 1 個資料源整合
**不包含**：API 交付、教育訓練、長期維護

### 方案 C: 旗艦版（多 Agent）

| 項目 | 費用（未稅） |
|------|-------------|
| 多 Agent 顧問費 | NTD {amount:,} - {amount:,} |
| 月費托管 | NTD {amount:,}/月 |

**包含**：2-3 個 agent + Client Portal + 客製化整合

---

## 四、付款條件（建議）

| 期別 | 比例 | 觸發 |
|------|------|------|
| 簽約款 | 30% | SOW 簽署 |
| 期中款 | 50% | 第一個 Agent 開發完成 |
| 驗收款 | 20% | 最終驗收通過 |

> 詳細付款條件、發票開立、付款時限將於 SOW 階段確定。

---

## 五、時程估計

| 階段 | 工期 | 內容 |
|------|------|------|
| 簽約 + 啟動 | 1 週 | SOW 簽署、kickoff meeting |
| Metadata Workshop | 2-3 週 | 與客戶共同梳理資料語意 |
| Agent 開發 | 4-6 週 | 第一個 agent 開發 + 內部測試 |
| API 封裝 + 教育訓練 | 1-2 週 | 交付文件 + 訓練 |
| **總計** | **約 8-12 週** | |

---

## 六、本報價單之說明

1. 本報價為初步估算，最終費用以 SOW 為準
2. 報價有效期限至 {YYYY-MM-DD}，逾期需重新報價
3. 客戶若同意進入合約階段，雙方將另行簽署 SOW（工作說明書）
4. 本報價不含：客戶端硬體成本、第三方 API 費用、額外客製化需求
5. 若需簽署 NDA 後方能進一步討論技術細節，請告知

---

## 七、下一步建議

- [ ] 確認您偏好的方案（A / B / C）
- [ ] 安排技術討論會議（約 1 小時）
- [ ] 簽署 NDA（如需要）
- [ ] 確認後進入 SOW 草擬階段

---

**版本紀錄**

| 版本 | 日期 | 變更內容 |
|------|------|---------|
| v1 | {YYYY-MM-DD} | 初版 |
| v2 | {date} | {what changed - e.g. 調整方案 A 範圍 + 費用} |
```

---

## Phase 3: Versioning Workflow

When client requests changes:

1. Copy `client-rfq-v{N}.md` → `client-rfq-v{N+1}.md`
2. Update version number, date, and the 變更內容 row
3. **Highlight changes** by adding `**[v2 變更]**` markers next to changed items, e.g.:
   - `- 顧問項目費 NTD 30 - **[v2 變更] 35** 萬`
4. Send the new version with a 1-line summary of what changed

---

## Phase 4: Hand-off to SOW

When client signals "yes to this RFQ":
> RFQ 已確認。建議下一步用 `sow-writer` 草擬正式 SOW，將以下從 RFQ 帶過去：
> - 客戶資訊、聯絡人
> - 方案範圍（轉成 SOW 第二條 服務工作內容）
> - 費用（從區間轉成固定金額 + 稅 + 人天計算）
> - 付款條件
> - 時程估計（轉成 SOW 第三條 里程碑 + Gantt）

---

## Common Mistakes

- ❌ RFQ 寫得太像 SOW（太多法律條款）— 客戶會嚇跑
- ❌ 沒有報價有效期 — 拖三個月後客戶比現在的價來議
- ❌ 只給一個方案 — 客戶沒得比較會還價
- ❌ 沒有量化效益 — 客戶覺得貴
- ❌ 改版本沒有 highlight 變更 — 客戶看不出差異
