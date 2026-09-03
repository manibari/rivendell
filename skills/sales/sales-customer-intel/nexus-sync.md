# Nexus Sync & Enrichment

How to sync md reports to Nexus intel API, handle conversational enrichment (Phase 2), and maintain data integrity.

---

## Phase 2: Conversational Enrichment

When user provides new information via chat, update BOTH md and Nexus.

### Trigger Patterns

- "奇美的 IT 主管叫林志明" → update 三、關鍵人物
- "把 deal potential 改成 high" → update 八、風險評估
- "他們預算大概 500 萬" → update 四、財務狀況
- "剛開完會，他們對 IoT 很有興趣" → update 二、近期動態 + 六、痛點

### Update Procedure

```
1. Identify which section(s) to update
2. Read current md file
3. Edit the relevant section (preserve other sections)
4. GET /api/nx/intel/{intel_id} → read existing parsed_json
5. Parse updated md → generate ONLY the changed fields
6. Merge: existing parsed_json + changed fields (shallow merge, changed fields win)
7. PATCH /api/nx/intel/{intel_id} with merged parsed_json
8. POST /api/nx/intel/{intel_id}/materialize (if new contacts/entities)
9. Confirm changes to user
```

### Merge Rules

- **Shallow merge**: only top-level keys are replaced, not deep-merged
- **Never delete keys**: if a field exists in Nexus but not in md, keep it (may have been added by materialize)
- **`notes` is append-only**: new notes are appended with timestamp, never overwritten
- **`_customer_intel` is deep-merged**: sub-keys like `recent_news` are replaced individually

```python
# Merge example
import json

existing = json.loads(intel_record['parsed_json'])
changes = {'pain_points': ['new_pain'], 'budget': '500萬'}
merged = {**existing, **changes}  # shallow merge, changes win

# For notes: append instead of replace
if 'notes' in changes and 'notes' in existing:
    merged['notes'] = existing['notes'] + '\n---\n' + changes['notes']
```

---

## Section → parsed_json Field Mapping

| md Section | parsed_json Fields |
|-----------|-------------------|
| 一、公司概覽 | `company_name`, `industry`, `industry_label`, `company_address`, `company_website`, `team_size` |
| 三、關鍵人物 | `contact_name`, `contact_title`, `contact_email`, `contact_phone`, `decision_maker` |
| 四、財務狀況 | `budget` |
| 六、痛點與挑戰 | `pain_points` |
| 八、風險評估 | `deal_potential` |
| 全域 | `notes` (append-style) |

### Field Extraction Rules

| Field | Source in md | Example |
|-------|-------------|---------|
| `company_address` | 一、公司概覽 → 總部 row | `"台南市仁德區仁愛里機場路 1008 號"` |
| `company_website` | 一、公司概覽 → 官方網站 row | `"https://www.chimeifood.com.tw/"` |
| `team_size` | 一、公司概覽 → 員工規模 row (number or range string) | `"6-50"` or `"500+"` |

---

## Multiple Contacts Strategy

md 的「三、關鍵人物」section 可列出多位人物（已支援），但 parsed_json 的 `contact_name` / `contact_title` 只放**主要聯絡人**（通常是決策者或我方接觸窗口）。

**Rules:**
1. `contact_name` + `contact_title` = 主要聯絡人（一位）
2. `decision_maker` = 最終決策者（可能與主要聯絡人不同）
3. 其他關鍵人物 → 寫入 `_customer_intel.key_people` array
4. materialize 只為主要聯絡人建立 contact entity
5. 其他聯絡人需要在 Nexus 中建立 → 使用者手動操作或後續由 agent 協助

**Contact selection priority:**
1. 使用者指定的聯絡窗口 (highest)
2. 總經理/CEO（日常營運決策者）
3. 董事長（最終決策者 → 放 `decision_maker`）
4. IT 主管（如果我方產品是 IT 相關）

---

## Re-materialize Rules

Only re-materialize when:
- New contact added (creates contact entity)
- Company name changed (unlikely but possible)
- Decision maker changed

Do NOT re-materialize for:
- Notes update
- Pain points change
- Deal potential change
→ These only need `PATCH` on the intel record.

---

## Nexus API Quick Reference

```bash
# Create intel record (Phase 1)
curl -X POST http://localhost:8002/api/nx/intel/ \
  -H "Content-Type: application/json" \
  -d '{"raw_input": "[report content]", "parsed_json": "{...}"}'

# Update intel parsed_json (Phase 2/3)
curl -X PATCH http://localhost:8002/api/nx/intel/{intel_id} \
  -H "Content-Type: application/json" \
  -d '{"parsed_json": "{...updated json...}"}'

# Re-materialize (only when new entities)
curl -X POST http://localhost:8002/api/nx/intel/{intel_id}/materialize
```

### Finding the Intel ID

The md report header should include the Nexus intel ID after initial sync:

```markdown
> 調查日期：2026-03-15
> Nexus Intel ID：24
```

If missing, search by company name:
```bash
curl -s http://localhost:8002/api/nx/intel/ | python3 -c "
import json, sys
for i in json.load(sys.stdin):
    if '[company_name]' in (i.get('raw_input') or ''):
        print(f'Intel ID: {i[\"id\"]}')
"
```

---

## nx_intel JSON Format

Auto-generated from md report during Nexus sync:

```json
{
  "role": "client",
  "company_name": "[正式名稱]",
  "company_address": "[總部地址]",
  "company_website": "[官方網站 URL]",
  "team_size": "[員工規模]",
  "industry": "[industry_code]",
  "industry_label": "[產業中文名]",
  "pain_points": ["[pain1]", "[pain2]"],
  "contact_name": "[key_contact]",
  "contact_title": "[title]",
  "decision_maker": "[decision_maker]",
  "competitors": "[competitor1, competitor2]",
  "_customer_intel": {
    "report_date": "[YYYY-MM-DD]",
    "company_overview": "[summary]",
    "revenue": "[if known]",
    "employee_count": "[if known]",
    "recent_news": [{"date": "", "event": "", "reliability": ""}],
    "key_people": [{"name": "", "title": "", "reliability": ""}],
    "sales_strategy": {
      "entry_points": [],
      "risks": [],
      "meeting_talking_points": []
    }
  }
}
```

Top-level fields follow `INTEL_PARSE_PROMPT` schema for materialize compatibility.
Extended data in `_customer_intel` sub-object (underscore prefix avoids schema conflicts).
