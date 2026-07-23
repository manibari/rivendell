---
name: tw-company-lookup
description: >
  Query Taiwan's official business registry (findbiz.nat.gov.tw) using Playwright
  to retrieve company registration data: basic info, directors, managers, factories,
  and change history. Accepts company name or 統一編號 (tax ID). Returns structured
  government-verified data.
  TRIGGER when: user asks to look up a Taiwan company, check company registration,
  verify 負責人/董監事, or says "查公司" / "公司登記" / "統編查詢".
  DO NOT TRIGGER when: researching international companies, stock research
  (use investment-research), or general web scraping (use web-scraper).
tags: [backend, taiwan]
version: 2
source: manual
user_invocable: true
---

# Taiwan Company Lookup

Query Taiwan's official government business registry (經濟部商工登記公示資料查詢服務) via Playwright.

## Data Source

**findbiz.nat.gov.tw** — Ministry of Economic Affairs, Commerce Development Administration.
All data from this source has `[confirmed]` reliability (official government records).

## Usage

```
/tw-company-lookup 奇美食品
/tw-company-lookup 68339681
```

Input can be:
- Company name (Chinese): `智瀚印刷科技有限公司`
- Short name: `奇美食品`
- 統一編號 (tax ID): `68339681`

## Query Script

```python
from playwright.sync_api import sync_playwright
import time
import re

FINDBIZ_URL = 'https://findbiz.nat.gov.tw/fts/query/QueryBar/queryInit.do'
BROWSER_UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)

TABS = ['董監事資料', '經理人資料', '工廠資料', '歷史資料']


def lookup_company(search_term: str) -> dict:
    """
    Query findbiz.nat.gov.tw for a Taiwan company.

    Args:
        search_term: Company name or 統一編號

    Returns:
        dict with keys: basic, directors, managers, factories, history
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=BROWSER_UA,
            viewport={'width': 1280, 'height': 900},
            locale='zh-TW',
        )
        page = ctx.new_page()

        # 1. Load search page
        page.goto(FINDBIZ_URL, wait_until='networkidle', timeout=20000)
        page.wait_for_selector('input[name="qryCond"]', timeout=10000)

        # 2. Search
        page.fill('input[name="qryCond"]', search_term)
        page.click('input[type="submit"], button:has-text("查詢")')
        # Wait for results to appear (look for result count or detail link)
        page.wait_for_selector('text=/共.*筆/, text=詳細資料, text=查無資料', timeout=15000)

        # 3. Check results count
        body = page.inner_text('body')
        match = re.search(r'共\s*(\d+)\s*筆', body)
        if not match or match.group(1) == '0':
            browser.close()
            return {'error': f'No results for: {search_term}'}

        result_count = int(match.group(1))

        # 4. If multiple results, list them and let user choose
        if result_count > 1:
            # Extract company names from results
            browser.close()
            return {
                'error': f'Multiple results ({result_count}). Refine search or use 統一編號.',
                'results_preview': body[:2000]
            }

        # 5. Click detail and wait for detail page to load
        page.click('text=詳細資料')
        page.wait_for_selector('text=統一編號', timeout=15000)

        results = {}

        # 6. Get basic info
        results['basic'] = page.inner_text('body')

        # 7. Click through tabs — wait for content to load after each click
        for tab in TABS:
            try:
                page.click(f'text={tab}')
                # Wait for tab content: either a data table or "無資料" message
                page.wait_for_selector(
                    'table, text=/無.*資料/, text=/序號/',
                    timeout=10000,
                )
                # Extra short wait for DOM to fully settle after tab switch
                page.wait_for_timeout(500)
                results[tab] = page.inner_text('body')
            except Exception as e:
                results[tab] = f'Error: {e}'

        browser.close()
        return results


def parse_basic_info(text: str) -> dict:
    """Parse basic company info from findbiz text output."""
    info = {}
    patterns = {
        '統一編號': r'統一編號\s+(\d+)',
        '公司名稱': r'公司名稱\s+(.+?)(?:\s+Google|$)',
        '登記現況': r'登記現況\s+(\S+)',
        '資本總額': r'資本總額\(元\)\s+([\d,]+)',
        '實收資本額': r'實收資本額\(元\)\s+([\d,]+)',
        '代表人': r'代表人姓名\s+(\S+)',
        '公司所在地': r'公司所在地\s+(.+?)(?:\s+電子地圖|$)',
        '設立日期': r'核准設立日期\s+(.+?)$',
        '最後變更日期': r'最後核准變更日期\s+(.+?)$',
        '英文名': r'出進口廠商英文名稱：(.+?)\)',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            info[key] = match.group(1).strip()

    # Extract 所營事業
    biz_matches = re.findall(r'([A-Z]\d{6})\s+(.+?)$', text, re.MULTILINE)
    if biz_matches:
        info['所營事業'] = [{'code': code, 'name': name.strip()} for code, name in biz_matches]

    return info


def parse_directors(text: str) -> list[dict]:
    """Parse board of directors from findbiz text output."""
    directors = []
    # Pattern: 序號 職稱 姓名 所代表法人 出資額
    matches = re.findall(
        r'(\d{4})\s+(董事長?|監察人|獨立董事)\s+(\S+)\s*(.*?)\s+([\d,]+)',
        text
    )
    for seq, title, name, rep, shares in matches:
        directors.append({
            'seq': seq,
            'title': title,
            'name': name,
            'representative': rep.strip() if rep.strip() else None,
            'shares': shares,
        })
    return directors


def parse_factories(text: str) -> list[dict]:
    """Parse factory registrations from findbiz text output."""
    factories = []
    # Pattern: 序號 登記編號 工廠名稱 登記現況 核准日期 變更日期
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if re.match(r'^\d+\s+\d{8}', line.strip()):
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                factories.append({
                    'registration_no': parts[1] if len(parts) > 1 else '',
                    'name': parts[2] if len(parts) > 2 else '',
                    'status': parts[3] if len(parts) > 3 else '',
                })
    return factories
```

## Output Format

Present results as a structured table:

```markdown
## 公司登記資料 — [公司名稱]
> 來源：經濟部商工登記公示資料查詢服務 (findbiz.nat.gov.tw)
> 查詢日期：[YYYY-MM-DD]
> 可靠度：[confirmed] (政府官方資料)

### 基本資料
| 項目 | 內容 |
|------|------|
| 統一編號 | |
| 公司名稱 | |
| 英文名 | |
| 登記現況 | |
| 資本總額 | |
| 實收資本額 | |
| 代表人 | |
| 公司所在地 | |
| 設立日期 | |
| 最後變更日期 | |
| 登記機關 | |

### 所營事業
| 代碼 | 名稱 |
|------|------|
| | |

### 董監事
| 序號 | 職稱 | 姓名 | 所代表法人 | 出資額 |
|------|------|------|-----------|--------|
| | | | | |

### 經理人
| 序號 | 姓名 | 到職日期 |
|------|------|---------|
| | | |

### 工廠登記
| 登記編號 | 工廠名稱 | 登記現況 | 核准日期 |
|---------|---------|---------|---------|
| | | | |

### 歷史變更紀錄
| 核准日期 | 變更內容 |
|---------|---------|
| | |
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| findbiz timeout | Increase timeout to 30000ms, retry once |
| Multiple search results | Use 統一編號 instead of company name |
| Empty text after tab click | `wait_for_selector` handles this — waits for table/data before reading. If still empty, increase `wait_for_timeout()` to 1000ms |
| Tab click fails | Tab may not exist for this company (e.g., no factories) — skip gracefully |
| Playwright not installed | `pip install playwright && playwright install chromium` |

## ROC Calendar Conversion

findbiz uses ROC calendar (民國). To convert:
- ROC year + 1911 = Western year
- Example: 093年12月31日 = 2004/12/31
- Example: 114年07月18日 = 2025/07/18
