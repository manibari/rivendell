# Research Guide (Phase 1)

Detailed search strategies and collection steps for customer intelligence.

---

## Step 1: Input & Disambiguation

Accept: `company_name` (required), `industry` / `region` (optional)

### Disambiguation Strategy

```
WebSearch: "[company_name] company"
WebSearch: "[company_name] [industry] [region]"   # if hints provided
```

- If results are ambiguous (multiple companies with same name), ask the user
- Once confirmed, record: official name, English name, official website URL
- **Language detection**: TW/Chinese company → bilingual search; international → English-primary

### For Taiwan Companies: Use `tw-company-lookup` Skill (Mandatory)

Use the **tw-company-lookup** skill to query findbiz.nat.gov.tw (official government registry). This retrieves:
- 統一編號, 公司名稱, 代表人, 資本總額, 實收資本額
- 登記現況, 設立日期, 最後變更日期
- 所營事業資料 (all business categories)
- 董監事名單 + 持股
- 經理人名單
- 工廠登記 + 狀態
- 歷史變更紀錄 (ownership changes, capital changes)

**Reliability**: findbiz data = `[confirmed]` (government source)

---

## Step 2: Company Overview (WebSearch + WebFetch)

```
WebSearch: "[company_name] about company products services"
WebSearch: "[company_name] 公司 產品 服務"          # for TW companies
WebSearch: "[company_name] revenue employees size"
WebSearch: "[company_name] Wikipedia"
WebFetch: [official about page]
```

If WebFetch fails (anti-scraping), use the **web-scraper** skill as fallback.

**Collect:**
- Official name / English name
- Founded year
- HQ location + factory locations
- Employee count
- Main products/services
- B2B/B2C orientation
- Group/parent company affiliation

---

## Step 3: Deep Intel Collection

### 3a. Recent News (past 6-12 months)

```
WebSearch: "[company_name] news 2026"
WebSearch: "[company_name] 新聞 2025 2026"          # TW companies
WebSearch: "[company_name] press release"
```

WebFetch notable articles for details.

### 3b. Key Leadership & Decision Makers

```
WebSearch: "[company_name] CEO CTO leadership team"
WebSearch: "[company_name] 董事長 總經理 管理層"     # TW companies
WebSearch: "[company_name] [representative_name]"   # from findbiz
```

### 3c. Financial Status

```
WebSearch: "[company_name] revenue funding financial"
WebSearch: "[company_name] 營收 資本額 財報"         # TW companies
WebSearch: "[company_name] crunchbase"               # for startups
```

For TW listed companies: check 公開資訊觀測站 (MOPS).

### 3d. Industry Position & Competitors

```
WebSearch: "[company_name] competitors market share"
WebSearch: "[company_name] vs [known_competitor]"
WebSearch: "[industry] 台灣 市場 主要廠商"           # TW market context
```

### 3e. Technology Stack (optional, from job postings & tech blogs)

```
WebSearch: "[company_name] engineering blog technology stack"
WebSearch: "[company_name] jobs software engineer"
```

---

## Step 4: Pain Points & Opportunity Analysis

```
WebSearch: "[company_name] challenges problems"
WebSearch: "[company_name] digital transformation"
WebSearch: "[industry] trends challenges 2026"
```

**Analysis angles:**
- Challenges inferred from news
- Tech gaps inferred from job postings
- Industry pressure from market trends
- Mapping pain points → our capabilities

---

## Step 5: Report Output

Output the report to terminal AND save to file:

```
~/Documents/Projects/sales-assistant/reports/customer-intel/[company_name]_[YYYY-MM-DD].md
```

Create the directory if it doesn't exist.

---

## Adaptive Strategy: Small vs Large Companies

Information depth varies dramatically by company size. Adapt expectations:

### Small Companies (capital < NT$50M, employees < 50)

- **News**: Likely none. Skip if first search returns nothing.
- **Leadership**: Only 負責人 from findbiz. No media interviews.
- **Financials**: Only registered capital. No revenue data.
- **Competitors**: Infer from industry + region.
- **Pain points**: Heavily rely on inference from industry trends, website quality, and job postings.
- **Strategy**: Focus on what IS available — official registry, website analysis, industry context.

### Large Companies (capital > NT$100M, employees > 100)

- **News**: Multiple sources. Prioritize business media (今周刊, 天下, 商周, HBR Taiwan).
- **Leadership**: Full board from findbiz + media profiles.
- **Financials**: Listed companies → MOPS; unlisted → infer from news, investments, expansion.
- **Competitors**: Named in industry reports.
- **Pain points**: Directly mentioned in interviews or analyst reports.
- **Strategy**: Go deeper — read the actual articles via WebFetch for nuance.
