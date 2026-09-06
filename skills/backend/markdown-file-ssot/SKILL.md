---
name: markdown-file-ssot
loop: dev
pdca: do
description: Markdown File SSOT - Use Markdown files with YAML frontmatter as a data SSOT. TRIGGER when storing semi-structured domain data where humans need to edit files directly AND code needs to query/filter them. DO NOT TRIGGER when data requires relational queries, high write concurrency, or strict schema enforcement.
version: 1.0.0
---

# Markdown File SSOT

Use Markdown files with YAML frontmatter as a data SSOT — readable by humans and code alike. No database table needed. Works well for semi-structured data (tenders, subsidies, case studies, knowledge base) that requires both manual editing and programmatic access.

**TRIGGER when**: storing semi-structured domain data where humans need to edit files directly AND code needs to query/filter them — e.g., government tenders, sales materials, knowledge articles, product catalog.

## When to Use vs Database

| Factor | Markdown SSOT | Database Table |
|--------|--------------|----------------|
| Human editing | ✅ Easy (any editor) | ❌ Requires UI/SQL |
| Git history | ✅ Full diff history | ❌ No native diff |
| Query complexity | ⚠️ In-memory filter only | ✅ SQL joins, aggregates |
| Volume | Up to ~1,000 files | Unlimited |
| Schema evolution | ✅ Add fields freely | ⚠️ Migration needed |
| Transactions | ❌ No | ✅ Yes |

## File Structure

```
materials/
  tenders/cases/         ← one .md file per tender
  subsidies/programs/    ← one .md file per subsidy
  case-studies/          ← one .md file per case study
```

## Frontmatter Schema Design

```yaml
---
# Required (used as unique key)
job_number: "1130104W1"

# Display fields
title: "AI 智慧影像辨識系統建置"
unit_name: "國立臺灣大學"

# Controlled vocabulary fields (enable filtering)
status: active          # active | closed | awarded
category: 勞務類844-資料庫服務
type: 公開招標

# Dates in ISO 8601
deadline: "2026-04-15"
scraped_date: "2026-03-18"

# Numeric (not string) for budget calculations
budget: 3000000

# Arrays for multi-value tags
tags: [AI, 影像辨識, 資訊服務]
---

# Markdown body here
```

## Parser Pattern

```python
import yaml
import time
from datetime import date, datetime
from pathlib import Path

CASES_DIR = Path(__file__).resolve().parent.parent.parent / "materials" / "tenders" / "cases"

# TTL cache to avoid re-reading files on every request
_cache: dict[str, tuple[float, object]] = {}
_TTL = 300  # 5 minutes

def _cached(key: str, fn):
    now = time.time()
    if key in _cache and now - _cache[key][0] < _TTL:
        return _cache[key][1]
    val = fn()
    _cache[key] = (now, val)
    return val

def _parse_file(path: Path) -> dict | None:
    """Parse a single markdown file. Returns None on error or missing required field."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    if not text.startswith("---"):
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        fm = yaml.safe_load(parts[1])
    except Exception:
        return None

    if not isinstance(fm, dict) or not fm.get("job_number"):
        return None  # missing required key

    # Compute derived fields
    days_left = None
    if deadline := fm.get("deadline"):
        try:
            dl = datetime.strptime(str(deadline), "%Y-%m-%d").date()
            days_left = (dl - date.today()).days
        except (ValueError, TypeError):
            pass

    body_md = parts[2].strip()

    return {
        "job_number": str(fm["job_number"]),
        "name": fm.get("title", ""),
        "status": fm.get("status", "active"),
        "deadline": str(deadline) if deadline else None,
        "days_left": days_left,
        "tags": fm.get("tags", []),
        "body_md": body_md,
        "file_path": str(path.relative_to(CASES_DIR.parent.parent.parent)),
    }

def _load_all() -> list[dict]:
    if not CASES_DIR.exists():
        return []
    return [r for p in sorted(CASES_DIR.glob("*.md")) if (r := _parse_file(p))]

def get_all(status: str = "active") -> list[dict]:
    all_items: list[dict] = _cached("all", _load_all)
    result = [t for t in all_items if t["status"] == status]
    result.sort(key=lambda t: t["deadline"] or "9999-99-99")
    return result

def get_one(key: str) -> dict | None:
    all_items: list[dict] = _cached("all", _load_all)
    return next((t for t in all_items if t["job_number"] == key), None)
```

## FastAPI Router Pattern

```python
@router.get("/")
def list_items(status: str = "active"):
    items = get_all(status)
    # Strip body_md from list response (too large)
    return [{k: v for k, v in t.items() if k != "body_md"} for t in items]

@router.get("/{key}")
def get_item(key: str):
    item = get_one(key)
    if not item:
        raise HTTPException(404, "Not found")
    return item
```

## Frontend Markdown Rendering (Next.js)

Install: `npm install react-markdown remark-gfm`

```typescript
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// In component:
<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  components={{
    h2: ({ children }) => (
      <h2 className="text-base font-semibold text-slate-800 dark:text-slate-200 mt-6 mb-2 pb-1 border-b border-slate-200 dark:border-slate-700">
        {children}
      </h2>
    ),
    table: ({ children }) => (
      <div className="overflow-x-auto my-3">
        <table className="w-full text-xs border-collapse">{children}</table>
      </div>
    ),
    td: ({ children }) => (
      <td className="px-3 py-1.5 border border-slate-200 dark:border-slate-700">{children}</td>
    ),
    th: ({ children }) => (
      <th className="px-3 py-1.5 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-left font-medium">
        {children}
      </th>
    ),
  }}
>
  {bodyMd}
</ReactMarkdown>
```

## Cache Invalidation

Always call `_cache.clear()` after writing/updating a file:

```python
def upsert_item(key: str, content: str) -> None:
    path = CASES_DIR / f"{key}.md"
    path.write_text(content, encoding="utf-8")
    _cache.clear()  # ← force reload on next request
```

## File Naming Convention

```
{unique_key}-{sanitized_title}.md
```

Example: `1130104W1-AI智慧影像辨識系統.md`

Sanitize title: `re.sub(r"[^\w\u4e00-\u9fff]", "", title)[:20]`
