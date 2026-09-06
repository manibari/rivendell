---
name: metadata-workshop
loop: sales
pdca: plan
description: >
  Run Metadata Workshop with a consulting client — convert business knowledge into
  YAML schemas (the moat: 2nd same-industry client gets ≥70% reuse). Verticals:
  廠務 (PI/SCADA/MES), ERP, travel.
  TRIGGER: "metadata workshop", "資料梳理", "schema 梳理", "PI tag 梳理", "ERP 欄位定義".
  SKIP: generic DB schema (db-migration); pre-SOW work (discovery-interview + sow-writer).
tags: [docs, workflow, business]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Metadata Workshop

Convert client business knowledge → YAML metadata schemas that let AI agents speak the client's business language.

## Why This Matters

AI sees `TI-101 = 132.5` — meaningless. With metadata schema, AI sees:
> "1號反應槽溫度 132.5°C，超過正常上限 120°C，需立即通知廠務部設備組"

This is the consulting moat: same-industry second client = 80% schema reuse.

## When to Run

- After SOW is signed (this is part of M2 in standard SOW timeline)
- 2-4 hours per data source (split into multiple sessions if needed)
- Participants: 業務使用者（懂語意）+ IT（懂結構）

## Pre-Workshop Checklist

- [ ] 客戶提供 API 文件 / 系統清單 / 欄位說明（任何格式）
- [ ] 確認參與者：**懂業務的人**（不是 IT！）+ IT（懂系統結構）
- [ ] 準備空白 schema 範本（依垂直選擇 — 見下方）
- [ ] 準備範例 API response（讓客戶看真實資料更容易討論）
- [ ] 建立 git 分支：`metadata/{client-shortname}-{vertical}`

---

## Workshop Flow

### 第一段：資料來源盤點（30 分鐘）

```markdown
## 列出所有資料來源

| # | 資料來源名稱 | 系統/工具 | 資料類型 | 更新頻率 |
|---|------------|---------|---------|---------|
| 1 | | | | |

## 優先順序
> 這個流程最依賴哪個資料來源？先從它開始梳理。
```

### 第二段：逐欄位 Metadata 定義（60-120 分鐘）

選擇對應垂直的問題清單：

#### 廠務垂直 (OSIsoft PI / SCADA / MES)

對每個 Tag 問 7 個問題：

| Q | 問題 | 範例 | 目的 |
|---|------|------|------|
| Q1 | 業務名稱是什麼？ | `TI-101` → 「1號反應槽入口溫度」 | AI 用業務語言而非代碼 |
| Q2 | 單位是什麼？ | `°C`, `RPM`, `%`, `m³/hr` | 數值描述正確單位 |
| Q3 | 正常運作範圍？ | `80-120°C` | AI 判斷正常/偏高/偏低 |
| Q4 | 緊急臨界值？ | `> 135°C 視為緊急` | 區分注意 vs 緊急 |
| Q5 | 與哪些 tag 關聯？ | `TI-101 偏高時 PI-201 通常也偏高` | 關聯分析 |
| Q6 | 資料負責人？ | `廠務部-設備組` | 異常通知對象 |
| Q7 | 更新頻率？ | `每 5 秒`, `每小時平均值` | Agent 讀取頻率 |

#### ERP / 業務垂直

對每個欄位/狀態碼問 5 個問題：

| Q | 問題 | 範例 |
|---|------|------|
| Q1 | 這個欄位/狀態碼的業務意思？ | `order_status: 3` → 「備貨中」 |
| Q2 | 正常流向？跳號代表什麼？ | `1→2→3→4→5→6 為正常，跳號 = 異常` |
| Q3 | 哪些值/組合需要主動通知？ | `狀態 > 3 天沒更新需通知業務` |
| Q4 | 依賴哪些其他欄位才有意義？ | `delivery_date 要搭配 order_type` |
| Q5 | 資料品質？常見髒資料？ | `customer_name 有時為空或 'N/A'` |

#### Travel 垂直 (e.g., Sabre)

| Q | 問題 |
|---|------|
| Q1 | 系統 entity 名稱（PNR / Booking / Itinerary / Customer）的業務意義？ |
| Q2 | Status code 與業務狀態對應？（confirmed / waitlisted / cancelled / no-show） |
| Q3 | 時區處理？（all UTC? local? mixed?） |
| Q4 | 票務 / 訂位 / 退票的業務規則？ |
| Q5 | 跨系統 ID 對應？（Sabre PNR ↔ 內部訂單 ID） |

### 第三段：輸出格式確認（30 分鐘）

```markdown
| 輸出對象 | 格式 | 語言 | 頻率 |
|---------|------|------|------|
| 廠長 | PDF 日報 | 繁中 | 每日 7:00 |
| 設備主管 | Email 異常通知 | 繁中 | 即時 |
```

請客戶看一份 AI 草稿，確認：
1. 用語是否符合業務習慣？
2. 數值描述方式是否正確？
3. 有沒有遺漏重要資訊？

---

## Output: YAML Schema

Save to `metadata/schemas/{vertical}/{client}-{system}-v1.yaml`.

### 廠務 / OSIsoft PI 範本

```yaml
schema_meta:
  version: "1.0"
  client: "{{CLIENT_NAME}}"
  source_system: "OSIsoft PI"
  industry: "manufacturing"
  created_by: "{{CONSULTANT}}"
  created_at: "{{DATE}}"

entities:
  - entity: "reactor_temps"
    business_name: "反應槽溫度"
    fields:
      - field: "TI-101"
        business_name: "1號反應槽入口溫度"
        unit: "°C"
        normal_range: [80, 120]
        critical_threshold: 135
        description: "主生產線第一段反應槽的即時溫度讀值"
        related_fields:
          - field: "PI-201"
            relationship: "TI-101 偏高時 PI-201 通常也偏高"
        data_owner: "廠務部-設備組"
        update_frequency: "5s"
        notify_on_critical: ["廠務部主管", "值班工程師"]

output_config:
  language: "zh-TW"
  date_format: "YYYY年MM月DD日"
  number_format:
    decimal_places: 1
    use_thousand_separator: true
```

### ERP 範本

```yaml
schema_meta:
  version: "1.0"
  client: "{{CLIENT_NAME}}"
  source_system: "{{ERP_SYSTEM}}"   # SAP / Oracle / 鼎新 / 自建
  api_base_url: "{{API_URL}}"
  industry: "electronics"

entities:
  - entity: "orders"
    business_name: "訂單"
    api_endpoint: "/api/orders"
    fields:
      - field: "order_status"
        business_name: "訂單狀態"
        field_type: status_code
        value_mapping:
          1: "已接單"
          2: "備料中"
          3: "生產中"
          4: "待出貨"
          5: "已出貨"
          6: "已到貨"
          9: "取消"
        normal_flow: [1, 2, 3, 4, 5, 6]
        alert_conditions:
          - condition: "status stays at 2 for > 3 days"
            business_meaning: "備料超過 3 天，需確認供料"
            notify: "採購部"
        data_quality:
          null_handling: "treat_as_unknown"
          known_issues: "舊訂單 status 可能為空"
```

> Reference templates exist at `~/Documents/Projects/lorien/metadata/schemas/`:
> - `manufacturing/osisoft-pi-template.yaml`
> - `erp/erp-api-template.yaml`
> - `travel/sabre-v1.yaml`
> Always check these first before writing from scratch.

---

## Schema 驗收標準

Workshop 結束後，agent 試跑 schema，驗收：

- [ ] Agent 能用業務語言描述（不是原始代碼）
  - ✅ 「1號反應槽溫度偏高（132°C，超過正常上限 120°C）」
  - ❌ 「TI-101 = 132.5」
- [ ] Agent 能正確識別異常並說明嚴重程度
- [ ] Agent 輸出客戶業務人員看得懂（不需 IT 翻譯）
- [ ] Schema 版本完整（git commit + 版本號）
- [ ] 異常通知對象正確

---

## Schema Reuse — 第二個客戶

When starting a same-industry second client:

1. 讀取第一個客戶的 schema（脫敏版）
2. 列出**通用欄位**（業務概念相同，只是命名/單位不同）
3. 列出**客戶特有欄位**（需要新訪談）
4. Workshop 時間從 4 小時降到 1.5 小時

目標複用率：≥ 70%

---

## Common Issues

| 問題 | 處理 |
|------|------|
| 客戶不知道欄位的業務定義 | 找真正懂業務的人（不是 IT）。IT 知道叫什麼，業務人員知道意思 |
| 欄位太多梳理不完 | 先梳理 agent 第一個版本會用到的（10-20 個夠），其他後續補充 |
| 客戶擔心資料外洩 | Schema 只記錄欄位定義，不含實際資料值。Schema 存乙方系統 |
| 客戶提供文件不完整 | 用「逐欄位逼問」+ 範例 API response 引導 |
| 業務和 IT 對欄位意思有分歧 | 記下兩種說法，後續實際數據驗證哪個對 |

---

## Hand-off

After workshop:

1. Commit schema to `metadata/schemas/{vertical}/`
2. 跑一次 agent 試跑驗收（用上面的標準）
3. Show client a 1-page summary of what was captured + how AI will use it
4. 排定下個 workshop（如有多個資料源）

---

## Reference

- Original checklist: `~/Documents/Projects/lorien/docs/templates/metadata-workshop-checklist.md`
- Example schemas: `~/Documents/Projects/lorien/metadata/schemas/`
- Engagement context: `~/Documents/Projects/lorien/docs/requirements/engagement-workflow.md` US-03b
