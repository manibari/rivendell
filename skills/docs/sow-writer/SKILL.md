---
name: sow-writer
loop: shared
pdca: do
description: >
  Generate Taiwan-format Statement of Work (工作說明書) for consulting projects —
  12+ sections including 服務工作內容, 時程 (Mermaid Gantt), 驗收, 費用 (人天), 變更管理.
  TRIGGER: "寫 SOW", "工作說明書", "顧問合約", "AI 導入合約", "consulting agreement".
  SKIP: sales pitch (pitch-deck); internal plan (writing-plans); simple quote (markdown).
tags: [docs, workflow, business]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# SOW Writer

Generate full Taiwan-format Statement of Work (工作說明書) for consulting/services engagements.

## Phase 1: Gather SOW Inputs

Before writing the SOW, gather these inputs. Skip questions already answered in conversation/files.

### Parties
- **甲方**: Client company name, 統一編號 (optional), 負責人 (optional)
- **乙方**: Your company name, 統一編號, 負責人

### Project
- **專案名稱**: e.g. "Sabre AI 方案 — 第一階段"
- **合約編號**: Auto-generate format `<CLIENT>-<PROJECT>-SOW-<YYYY>-<NNN>` (e.g. `SABRE-AI-SOW-2026-001`)
- **前置協議**: NDA / MSA reference if any
- **客戶背景**: 1-2 sentences about client's business and why this engagement
- **專案目標**: 3-5 numbered bullets

### Scope (Work Items)
For each major work item, gather:
- 名稱 (e.g. "AI Agent 需求工作坊")
- 預估人天 (e.g. 20 人天)
- 工作內容（3-6 bullets）
- 產出物（具體文件/系統）

> Standard 5-item structure for AI consulting:
> 1. 需求工作坊 (15-25 人天)
> 2. Metadata 盤點工作坊 (20-40 人天)
> 3. 開發 (60-100 人天)
> 4. API/系統交付 (5-15 人天)
> 5. 教育訓練與交接 (5-15 人天)

### Schedule
- **合約起算日**: ISO date
- **專案完成日**: ISO date
- **里程碑**: M1 簽約 → M2 工作坊完成 → M3 系統交付 → M4 最終驗收
- 任務時程表: T1...Tn with start/end dates

### Pricing
- **人天費率**: NTD per person-day (default 10,000)
- **總人天**: sum from work items
- **未稅金額** = 總人天 × 人天費率
- **營業稅** = 未稅 × 5%
- **合計** = 未稅 + 營業稅

### Payment Terms
- **付款期別**: typically 簽約款 30% / 期中款 35% / 期末款 35%
- **付款條件**: 各期觸發里程碑 + 付款時限（30 日曆天）

### Contacts
- **甲方主窗口/副窗口**: 姓名 + email
- **乙方主窗口/副窗口**: 姓名 + email + 電話

### Other
- **保固期間**: default 1 year from final acceptance
- **NDA 引用**: 是否使用前置 NDA 之保密條款

---

## Phase 2: Generate SOW

Save to `docs/sow/{client-shortname}-{year}.md`. Use this exact 12-section structure:

```markdown
# 工作說明書（Statement of Work）
## {專案名稱}

---

- **合約編號**：{contract_number}
- **合約日期**：中華民國 {ROC_year} 年 {MM} 月 {DD} 日
- **前置協議**：{NDA_reference}

---

## 一、專案標的

立合約書人：

- **甲方**：{客戶全名}
- **乙方**：{乙方全名}（統一編號：{tax_id}，負責人：{representative}）

{客戶背景描述 1-2 句。為什麼需要此專案。}

本專案目標：

1. {目標 1}
2. {目標 2}
3. {目標 3}
4. {目標 4}

---

## 二、服務工作內容

### 2.1 {工作項目 1 名稱}（約 {N} 人天）

- {工作內容 bullet 1}
- {工作內容 bullet 2}
- 產出「{產出物名稱}」，內容包含：
  - {子項 1}
  - {子項 2}

### 2.2 {工作項目 2 名稱}（約 {N} 人天）

[...]

**服務人天合計：{總人天} 人天**

---

## 三、專案時程與里程碑

- **合約起算日**：{YYYY-MM-DD}
- **專案完成日**：{YYYY-MM-DD}（總計約 {N} 週）

### 3.1 里程碑

| 里程碑 | 內容 | 預計完成日 |
|--------|------|----------|
| **M1** | 合約簽署生效 | {date} |
| **M2** | {milestone 2 deliverable} | {date} |
| **M3** | {milestone 3 deliverable} | {date} |
| **M4** | {milestone 4 deliverable} | {date} |

### 3.2 任務時程表

| # | 任務 | 起始日 | 結束日 | 工期 | 對應里程碑 |
|---|------|--------|--------|------|----------|
| T1 | {task} | {MM-DD} | {MM-DD} | {N} 天 | M1 |
| ... | | | | | |

> {任務之間是否有重疊以壓縮時程的說明}

### 3.3 甘特圖

\`\`\`mermaid
gantt
    title {專案名稱}時程
    dateFormat YYYY-MM-DD
    axisFormat %m/%d

    section 里程碑
    M1 {label}        :milestone, m1, {date}, 0d
    M2 {label}        :milestone, m2, {date}, 0d
    M3 {label}        :milestone, m3, {date}, 0d
    M4 {label}        :milestone, m4, {date}, 0d

    section {section name}
    {task name} (T1)  :active, t1, {date}, {N}d
    [...]
\`\`\`

如因甲方原因（如未能提供 API 存取、窗口無法配合）導致延誤，時程得順延相同天數，並以書面通知對方。

---

## 四、交付項目

| # | 交付項目 | 格式 | 對應里程碑 |
|---|---------|------|----------|
| 1 | {deliverable 1} | {format} | M{N} |
| 2 | {deliverable 2} | {format} | M{N} |

> 如有附件（如技術規格書），註明「將於 M{X} 完成後 {N} 個工作日內由雙方另行簽署」。

---

## 五、驗收程序與標準

1. 乙方完成各里程碑交付後，以書面（含電子郵件）通知甲方驗收
2. 甲方應於收到驗收通知後 **5 個工作日內**完成檢視，並以書面回覆驗收結果
3. 甲方逾期未回覆者，視同驗收通過
4. 如甲方提出修正意見，乙方應於 10 個工作日內完成修正並重新提交驗收
5. 第 4 項修正後仍未通過者，雙方應召開協調會議釐清爭議
6. {特定交付物之具體驗收項目} 詳見**附件 A**

---

## 六、專案費用

| 項目 | 金額 |
|------|------|
| 服務費（未稅） | NTD {amount:,} |
| 營業稅（5%） | NTD {tax:,} |
| **合計應付金額** | **NTD {total:,}** |

計費基準：{總人天} 人天 × NTD {rate:,} / 人天

---

## 七、付款方式

| 期別 | 比例 | 觸發條件 | 未稅金額 | 含稅金額 |
|------|------|---------|----------|----------|
| 簽約款 | 30% | M1 合約簽署（{date}） | NTD {amt:,} | NTD {amt_tax:,} |
| 期中報告 | 35% | M2 甲方書面驗收（{date}） | NTD {amt:,} | NTD {amt_tax:,} |
| 期末報告 | 35% | M4 甲方書面驗收（{date}） | NTD {amt:,} | NTD {amt_tax:,} |

- 各期款項應於觸發條件成就後 **30 個日曆天**內完成匯款
- 匯款帳號由乙方另行提供
- 逾期未付，乙方得暫停服務

---

## 八、雙方責任與專案窗口

### 8.1 專案窗口

| | 甲方 | 乙方 |
|--|------|------|
| **主窗口** | {name} {email} | {name} {email}｜{phone} |
| **副窗口** | {name} {email} | {name} |

### 8.2 甲方責任

1. 提供本專案所需之 API 存取帳號、技術文件及測試環境
2. 確保專案窗口每週至少 {N} 小時配合時間
3. 於各工作坊期間安排相關業務及技術人員出席
4. {client-specific responsibility}
5. 依第五條「驗收程序與標準」於時限內回覆驗收結果

### 8.3 乙方責任

1. 依本合約時程交付所有交付項目
2. 所取得之甲方資料僅用於本專案，不得用於其他用途
3. {vendor-specific responsibility}
4. 提供第九條所定之保固服務

---

## 九、品質維護及保固

1. **保固期間**：自 M4 最終驗收日起算 **壹（1）年**
2. **保固範圍**：
   - {item 1} 程式錯誤修復（Bug Fix）
   - 技術文件更新（如因 Bug Fix 而需調整）
3. **不在保固範圍**：
   - 甲方環境變動所致之問題
   - 需求變更或新增功能
   - 第三方系統異常
4. **回應時間**：
   - 嚴重問題：下一個工作日內回應
   - 一般問題：3 個工作日內回應
5. **通報方式**：甲方以電子郵件通知乙方主窗口
6. **保固期滿後**之維護服務，雙方得另行簽署維運合約

---

## 十、智慧財產權

{If NDA exists, reference it. Otherwise specify:}

1. 依賴甲方 API 或甲方技術之專案成果，智慧財產權歸甲方所有
2. 乙方自行開發且不包含甲方技術之通用元件，歸乙方所有
3. 雙方共同客製部分共同所有
4. {專案特定 IP 條款}

---

## 十一、保密義務

1. {Reference NDA or specify standard NDA terms}
2. 乙方人員存取甲方系統之帳號、金鑰，於合約終止後 **10 日內**歸還或銷毀
3. 如發生資安事件，乙方應於知悉後 **24 小時內**以書面通知甲方
4. 本條款與前置 NDA 如有衝突，以較嚴格之條款為準

---

## 十二、變更管理

{Standard change management clause: any scope/timeline change requires written agreement from both parties}

---

## 十三、合約終止

{Standard termination clause: how either party can terminate, what happens to in-progress work and payments}

---

## 簽署

| | 甲方 | 乙方 |
|--|------|------|
| 公司 | {client_name} | {vendor_name} |
| 代表人 | | {representative} |
| 簽署日 | | |
| 用印 | | |
```

---

## Taiwan Business Doc Conventions

| Item | Format |
|------|--------|
| 日期 | 中華民國 {ROC year} 年 {MM} 月 {DD} 日 (ROC = Western - 1911) |
| 金額 | NTD {amount:,}（千分位逗號）—— always note 未稅 / 含稅 |
| 稅率 | 營業稅 5% (Taiwan standard) |
| 雙方稱謂 | 甲方 (client) / 乙方 (vendor) — never use 我方/你方 |
| 數字 | 重要金額用「壹（1）」「貳（2）」等大寫漢字加阿拉伯數字 |
| 期限 | 區分「日曆天 / 工作日」，付款用日曆天，驗收用工作日 |
| 簽核欄位 | 必須包含「公司、代表人、簽署日、用印」四欄 |

---

## Pricing Reference

Common rates (Taiwan AI consulting, 2026):
- 一般工程師: NTD 6,000-8,000 / 人天
- 資深工程師: NTD 10,000-12,000 / 人天
- AI/ML specialist: NTD 12,000-15,000 / 人天
- 顧問/PM: NTD 12,000-18,000 / 人天

Default in this skill: NTD 10,000 / 人天 (blended rate)

---

## After Generation

1. Save to `docs/sow/{client-shortname}-{year}.md`
2. Show user a summary of: 總人天, 總金額, 里程碑日期, 付款條件
3. Ask if any sections need adjustment
4. Offer to convert to .docx via `office-docx` skill if needed
5. If `images/gantt.png` is referenced, generate it from the Mermaid block (use `mmdc` CLI if available)

---

## Reference Implementation

A complete real-world example exists at `~/Documents/Projects/lorien/docs/sow/sabre-2026.md`
(Sabre AI 方案 — 150 人天, NTD 1.5M). Read this file when you need to see how all sections
fit together in a real engagement.
