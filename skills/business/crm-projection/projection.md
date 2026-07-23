# CRM Projection — Detailed Workflow

## Step 1: Query Client Data

Run Python to query all active clients with deal aggregation:

```bash
cd ~/Documents/Projects/sales-assistant
python3 -c "
from services.nexus.clients import get_all_clients
import json
clients = get_all_clients()
print(json.dumps(clients, default=str))
"
```

Each client record includes:
- `id`, `name`, `industry`, `status`, `budget_range`, `notes`
- `deal_budget_total` — aggregated from active deals

## Step 2: Query Deal Details (Optional)

For richer projection, query active deals per client:

```bash
python3 -c "
from services.nexus.deals import get_deals_by_client
import json
deals = get_deals_by_client(client_id)
print(json.dumps(deals, default=str))
"
```

Deal fields useful for projection:
- `name`, `stage`, `budget_amount`, `budget_year`, `timeline`, `status`

## Step 3: Cross-Reference Customer Intel

Read `reports/customer-intel/INDEX.md` and parse the table to build a lookup:

```
1. Read reports/customer-intel/INDEX.md
2. Parse markdown table rows
3. Build dict: { company_name: { file, intel_id, created, updated } }
```

Also check for individual report files:
```
Glob reports/customer-intel/*.md (excluding INDEX.md)
```

## Step 4: Generate INDEX.md

Write `materials/clients/INDEX.md`:

```markdown
# 客戶索引

> 自動產生 by `crm-projection` — 請勿手動編輯
>
> 資料來源: nx_client (DB) + customer-intel 報告 (本地)
>
> 最後更新: {ISO datetime}

## Active 客戶

| 客戶名稱 | 產業 | 預算區間 | 進行中案件 | Pipeline 金額 | Intel 報告 |
|----------|------|----------|-----------|--------------|------------|
| {name} | {industry} | {budget_range} | {deal_count} | {deal_budget_total} | [有]({report_path}) or — |

## 統計

- Active 客戶數: {N}
- 有 Intel 報告: {N} / {total}
- Pipeline 總金額: {sum}
- 最近 30 天新增: {N}

## 缺少 Intel 報告的客戶

以下客戶尚未建立 customer-intel 報告，建議優先調查：

| 客戶名稱 | 產業 | Pipeline |
|----------|------|----------|
| {clients without intel reports} |
```

## Step 5: Output Summary

```
=== CRM Projection Summary ===
Date: {today}
Active clients: {N}
Clients with deals: {N}
Clients with intel: {N}
Clients missing intel: {N}
INDEX.md updated: Yes
```

## Error Handling

- If DB connection fails, keep existing INDEX.md and log error
- If customer-intel INDEX.md doesn't exist, skip cross-reference (mark all as "—")
- Always write the timestamp so staleness is visible
