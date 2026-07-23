---
name: investment-research
description: >
  Continuous portfolio agent: alpha discovery, risk, backtesting, financial analysis.
  Local news_stock + autonomous web search. Monitors holdings, weekly alpha scans,
  rebalancing proposals.
  TRIGGER: "投資研究", "開始研究", "持續追蹤", research stocks / portfolio / backtests.
  SKIP: code debugging (systematic-debugging); UI work.
tags: [workflow, finance]
version: 1
source: manual
user_invocable: true
---

# Investment Research

Structured research workflow for finding alpha and managing risk, powered by the news_stock platform.

## Goals

1. **Find alpha** — identify mispriced opportunities through data-driven analysis
2. **Manage risk** — quantify downside before committing capital

## Research Workflow

```
1. Environment Scan    →  2. Stock Pool     →  3. Alpha Discovery  →  4. Risk Assessment
   (macro + sentiment)     (universe filter)    (signals + scoring)    (drawdown + correlation)

5. Entry/Exit Strategy →  6. Backtesting    →  7. Financial Review  →  8. Report
   (rules + triggers)      (validate edge)     (四大報表)              (final output)
```

---

## Step 1: Environment Scan

Assess the macro backdrop before picking stocks. Use news_stock data directly.

### 1a. Market Cycle Phase

```python
# Read from news_stock macro.db
import sqlite3, os

DB = os.path.expanduser(os.environ.get("NEWS_STOCK_DIR", "~/Documents/Projects/news_stock") + "/macro.db")
conn = sqlite3.connect(DB)

# Latest cycle for US and TW
cycles = conn.execute("""
    SELECT country, phase, composite_score, confidence, date
    FROM market_cycles
    WHERE (country, date) IN (
        SELECT country, MAX(date) FROM market_cycles GROUP BY country
    )
""").fetchall()
for country, phase, score, conf, date in cycles:
    print(f"{country}: {phase} (score={score:.2f}, confidence={conf:.0%}) as of {date}")
```

**Cycle → Allocation mapping** (from `config/macro_indicators.py`):

| Phase | Stocks | Bonds | Cash | Preferred Sectors |
|-------|--------|-------|------|-------------------|
| EXPANSION | 80% | 15% | 5% | Growth, Momentum, Tech |
| PEAK | 55% | 30% | 15% | Defensive, Dividend |
| CONTRACTION | 30% | 45% | 25% | Utilities, Staples, Gold |
| TROUGH | 60% | 25% | 15% | Cyclicals, Value |

### 1b. Key Macro Indicators

```python
# Check latest FRED indicators
indicators = conn.execute("""
    SELECT mi.series_id, mi.name, md.value, md.date
    FROM macro_indicators mi
    JOIN macro_data md ON mi.series_id = md.series_id
    WHERE md.date = (SELECT MAX(date) FROM macro_data WHERE series_id = mi.series_id)
    ORDER BY mi.country, mi.series_id
""").fetchall()
```

**Critical thresholds** (from `config/macro_indicators.py`):
- Yield curve (T10Y2Y) < 0 → inversion warning
- VIX > 25 → elevated fear
- Unemployment > 5% → recession risk
- Fed Funds rising → tightening cycle

### 1c. News Sentiment

```python
NEWS_DB = os.path.expanduser(os.environ.get("NEWS_STOCK_DIR", "~/Documents/Projects/news_stock") + "/news.db")
nconn = sqlite3.connect(NEWS_DB)

# Recent news volume and sentiment keywords
recent = nconn.execute("""
    SELECT source_type, COUNT(*), MIN(published_at), MAX(published_at)
    FROM news
    WHERE published_at >= date('now', '-7 days')
    GROUP BY source_type
""").fetchall()
```

Use WebSearch for breaking news not yet in the database.

---

## Step 2: Stock Pool Selection

Use two sources to build the research universe: **local DB pools** (existing data) and **web discovery** (new opportunities).

### Source A: Local Pools (news_stock finance.db)

```python
FIN_DB = os.path.expanduser(os.environ.get("NEWS_STOCK_DIR", "~/Documents/Projects/news_stock") + "/finance.db")
fconn = sqlite3.connect(FIN_DB)

pools = fconn.execute("""
    SELECT sp.name, sp.description, COUNT(spm.symbol) as size
    FROM stock_pools sp
    LEFT JOIN stock_pool_members spm ON sp.id = spm.pool_id
    GROUP BY sp.id
""").fetchall()
```

**System pools** (7 defined):
- AI Supply Chain (US): ~89 stocks, 18 layers
- AI Supply Chain (TW): ~79 stocks
- Geopolitical: ~31 stocks
- US Sectors (GICS): ~532 stocks
- US Stocks: ~540 stocks
- TW Stocks: ~117 stocks
- ETFs: ~67 stocks

### Source B: Web Discovery (autonomous search)

When the research thesis goes beyond local pools, **actively search for stocks** using WebSearch. This is critical for discovering opportunities not already in the database.

#### Discovery Strategies

| Strategy | Search Queries | Use Case |
|----------|---------------|----------|
| Thematic | `"top [theme] stocks 2026"`, `"[industry] market leaders"` | New sectors or trends not in local pools |
| Screener | `"finviz screener [criteria]"`, `"stock screener PE < 15 ROE > 20"` | Quantitative filtering across all markets |
| Analyst picks | `"Goldman Sachs top picks"`, `"Morningstar 5-star stocks"` | Institutional consensus |
| Insider activity | `"insider buying [sector] SEC filings"` | Smart money signals |
| IPO/emerging | `"recent IPO high growth"`, `"small cap breakout stocks"` | Early-stage opportunities |
| Regional | `"best Japan stocks"`, `"emerging market value stocks"` | Non-US/TW markets |
| ETF holdings | `"[ETF ticker] top holdings"`, `"ARK Invest latest trades"` | Discover via thematic ETF composition |

#### Web Discovery Workflow

```
1. Define thesis → pick 2-3 search strategies above
2. WebSearch → collect candidate tickers + brief rationale
3. For each candidate:
   a. Check if already in local DB → if yes, use local data
   b. If NOT in local DB:
      - WebSearch "[ticker] financials revenue earnings"
      - WebSearch "[ticker] stock analysis bull bear case"
      - Collect: price, PE, revenue growth, margin, recent catalysts
4. Build unified candidate list (local + web-discovered)
5. Clearly label each stock's data source in the report
```

#### Example: Discovering a Robotics Pool

```
WebSearch: "top robotics automation stocks 2026"
WebSearch: "ROBO ETF top 10 holdings"
WebSearch: "industrial automation market leaders revenue growth"

→ Discovers: ISRG, ROK, ABB, FANUY, IRBT, PATH, TER, CGNX
→ Cross-check: TER already in local AI Supply Chain pool
→ New candidates: ISRG, ROK, ABB, FANUY, CGNX (not in local DB)
→ WebSearch each for financials
```

### Pool Selection Logic

```
What is the research thesis?
  → Matches existing pool? → Use local pool (Source A)
  → New theme/sector?     → Web discovery (Source B)
  → Broad exploration?    → Combine both sources
  → Specific region?      → Web discovery for that market
  → "Find me alpha"       → Screen locally first, then expand via web
```

**Always ask**: "Are there opportunities my local DB is missing?" If the thesis is about a trend, sector, or region not well-covered by the 7 local pools, web discovery is mandatory.

### Fundamental Filters (narrow the pool)

For **local** stocks:
```python
candidates = fconn.execute("""
    SELECT w.symbol, w.name, f.*
    FROM fundamentals f
    JOIN watchlist w ON f.symbol = w.symbol
    WHERE f.date = (SELECT MAX(date) FROM fundamentals WHERE symbol = f.symbol)
      AND f.pe_ratio > 0 AND f.pe_ratio < 30
      AND f.roe > 0.15
      AND f.profit_margin > 0.10
    ORDER BY f.roe DESC
""").fetchall()
```

For **web-discovered** stocks, apply the same filters using data from WebSearch:
```
WebSearch: "[ticker] PE ratio ROE profit margin"
→ Parse key metrics → apply same thresholds
→ Flag "data confidence: web" vs "data confidence: local DB" in output
```

Adjust filters based on cycle phase:
- **EXPANSION**: Growth focus (PEG < 1.5, revenue growth > 15%)
- **CONTRACTION**: Value focus (PE < 15, dividend yield > 3%, low debt/equity)

---

## Step 3: Alpha Discovery

Run multi-factor scoring on the filtered pool.

### 3a. Technical Signals

Use `src/strategy/analyzer.py` patterns:

```python
# analyzer.py calculates these for each symbol:
# MA crossover: MA5 > MA20 → BUY signal
# RSI: < 30 → oversold BUY, > 70 → overbought SELL
# MACD: crossover → momentum shift
# BB: price near lower band → potential reversal
# Volume-price breakout: consolidation + volume spike + MACD cross + KD low
```

```python
from src.strategy.analyzer import TechnicalAnalyzer

analyzer = TechnicalAnalyzer(fconn)
for symbol in candidate_symbols:
    result = analyzer.analyze(symbol, period="6mo")
    signals = result['signals']  # List of BUY/SELL with dates and reasons
    indicators = result['indicators']  # RSI, MACD, BB values
```

### 3b. Fundamental Scoring

Apply scoring weights from `config/strategy_constants.py`:

| Factor | Weight | Source |
|--------|--------|--------|
| Cycle fit | 30% | Market phase × sector alignment |
| Moat | 30% | Profit margin, operating margin, ROE, institutional ownership |
| Growth | 25% | PEG ratio, forward PE discount |
| Momentum | 15% | Price trend, volume trend |

**Moat thresholds**:
- Profit margin > 20% → strong moat
- Operating margin > 15% → operational efficiency
- ROE > 20% → capital efficiency
- Institutional ownership > 60% → smart money validation

**Megatrend multipliers** (from `strategy_constants.py`):
- AI: 1.0x, EV: 0.85x, Clean Energy: 0.80x, Biotech: 0.75x
- Declining: Retail, Fossil fuels, Traditional media (penalty)

### 3c. AI Supply Chain Lens

For AI-related research, use the 18-layer taxonomy:

```python
from config.ai_stocks import AI_LAYERS, AI_LAYER_STOCKS, AI_STOCK_DESCRIPTIONS

# Identify which layer a stock belongs to
# Compare performance across layers (upstream vs downstream)
# Find lagging layers that may catch up (mean reversion alpha)
```

### 3d. Cross-reference with News & Web Intelligence

**Local news DB first:**
```python
for symbol in top_candidates:
    news = nconn.execute("""
        SELECT title, source, published_at
        FROM news
        WHERE (title LIKE ? OR content LIKE ?)
          AND published_at >= date('now', '-30 days')
        ORDER BY published_at DESC
        LIMIT 5
    """, (f'%{symbol}%', f'%{symbol}%')).fetchall()
```

**Then actively search the web for each candidate:**
```
For each top candidate:
  WebSearch: "[ticker] earnings report latest"
  WebSearch: "[ticker] analyst price target upgrade downgrade"
  WebSearch: "[ticker] competitive advantage moat analysis"
  WebSearch: "[ticker] risk factors SEC 10-K"

For web-discovered stocks (no local data):
  WebSearch: "[ticker] stock chart technical analysis"
  WebSearch: "[ticker] financial statements revenue profit"
  WebSearch: "[ticker] insider buying institutional ownership"
```

**Synthesize** local DB news + web results into a catalyst summary per stock:
- Recent earnings beat/miss
- Analyst consensus shift
- Upcoming catalysts (product launch, FDA approval, contract win)
- Red flags (insider selling, downgrade, litigation)

---

## Step 4: Risk Assessment

Quantify risk before defining entry/exit rules.

### Key Risk Metrics

| Metric | Formula | Red Flag |
|--------|---------|----------|
| Max Drawdown | Peak-to-trough decline | > 30% |
| Sharpe Ratio | (Return - Rf) / σ | < 0.5 |
| Beta | Covariance with market / market variance | > 1.5 (too volatile) |
| Correlation | Between positions | > 0.8 (concentration risk) |
| VaR (95%) | 5th percentile daily loss | Context-dependent |

**Local stocks** (have price history in DB):
```python
import pandas as pd
import numpy as np

prices = pd.read_sql("""
    SELECT date, close FROM daily_prices
    WHERE symbol = ? AND date >= date('now', '-1 year')
    ORDER BY date
""", fconn, params=(symbol,), parse_dates=['date'])

returns = prices['close'].pct_change().dropna()
sharpe = returns.mean() / returns.std() * np.sqrt(252)
max_dd = (prices['close'] / prices['close'].cummax() - 1).min()
var_95 = returns.quantile(0.05)
```

**Web-discovered stocks** (no local price history):
```
WebSearch: "[ticker] stock performance 1 year return max drawdown"
WebSearch: "[ticker] beta sharpe ratio volatility"
WebSearch: "[ticker] yfinance" → use yfinance to pull price data on the fly:
```
```python
import yfinance as yf
ticker = yf.Ticker("SYMBOL")
hist = ticker.history(period="1y")
# Calculate same metrics as above
```

### Portfolio Correlation Check

```python
# Ensure selected stocks aren't all correlated
portfolio_symbols = ['NVDA', 'AMD', 'TSM']  # example
price_matrix = pd.DataFrame()
for sym in portfolio_symbols:
    df = pd.read_sql(f"""
        SELECT date, close FROM daily_prices
        WHERE symbol = '{sym}' AND date >= date('now', '-1 year')
    """, fconn, parse_dates=['date']).set_index('date')
    price_matrix[sym] = df['close']

corr = price_matrix.pct_change().corr()
# Flag pairs with correlation > 0.8
```

---

## Step 5: Entry/Exit Strategy

Define clear, rule-based triggers. No discretionary decisions.

### Entry Rules (pick combination based on thesis)

| Rule | Condition | Weight |
|------|-----------|--------|
| Trend confirmation | MA5 crosses above MA20 | Required |
| Momentum | RSI between 40-65 (not overbought) | Required |
| Volume | Volume ratio > 1.5 (above 20d avg) | Preferred |
| MACD | Histogram turning positive | Preferred |
| Fundamental | Score in top 20% of pool | Required |

### Exit Rules

| Rule | Condition | Action |
|------|-----------|--------|
| Stop loss | -8% from entry | Sell all |
| Trailing stop | -12% from peak | Sell all |
| Take profit | +25% from entry | Sell 50% |
| Signal reversal | MA5 crosses below MA20 + RSI > 70 | Sell all |
| Time limit | 90 trading days, no +10% | Review/exit |

### Position Sizing

```
Per-position size = Portfolio × Risk_per_trade / (Entry - Stop_loss)
Risk_per_trade = 2% of portfolio (max)
Max positions = 10 (diversification floor)
```

---

## Step 6: Backtesting

Validate the strategy edge using historical data.

### Using news_stock Backtesting Infrastructure

```python
from src.strategy.analyzer import TechnicalAnalyzer
from src.strategy.portfolio_strategy import PortfolioStrategy
from src.strategy.cycle_backtest import CycleBacktester

# Option 1: Technical backtest (single stock)
analyzer = TechnicalAnalyzer(fconn)
result = analyzer.backtest(symbol, strategy="ma_crossover", period="2y")
# Returns: total_return, win_rate, sharpe, max_drawdown, trades

# Option 2: Portfolio strategy backtest
strategy = PortfolioStrategy(fconn)
# Momentum rotation with monthly rebalancing
result = strategy.momentum_rotation(
    symbols=candidate_symbols,
    top_n=5,
    lookback=60,
    rebalance_period=21,
    start_date="2024-01-01"
)

# Option 3: Cycle-based backtest
backtester = CycleBacktester(fconn, conn)  # finance + macro DBs
result = backtester.run(symbols=candidate_symbols, start_date="2023-01-01")
```

### Backtest Validation Checklist

- [ ] Test period includes at least one drawdown > 15%
- [ ] Sharpe ratio > 1.0 (after transaction costs)
- [ ] Win rate > 45% with profit factor > 1.5
- [ ] Max drawdown < 25%
- [ ] No single trade accounts for > 30% of total P&L
- [ ] Results hold across different time windows (walk-forward)
- [ ] Compare vs buy-and-hold benchmark (SPY / 0050)

### Report Backtest Results

```
Strategy: [name]
Period: YYYY-MM-DD to YYYY-MM-DD
Universe: [pool name] ([N] stocks)

| Metric | Strategy | Benchmark (SPY) |
|--------|----------|-----------------|
| Total Return | X% | Y% |
| Annualized Return | X% | Y% |
| Sharpe Ratio | X.XX | Y.YY |
| Max Drawdown | -X% | -Y% |
| Win Rate | X% | — |
| # Trades | N | 1 |
| Profit Factor | X.XX | — |
```

---

## Step 7: Financial Statement Review (四大報表)

Before final conviction, review the company's financial health using fundamental data.

### 四大報表 Analysis Framework

#### 1. 損益表 (Income Statement)

| Metric | Source Field | What to Check |
|--------|-------------|---------------|
| Revenue trend | `revenue` | Growing YoY? Accelerating? |
| Profit margin | `profit_margin` | Stable or expanding? |
| Operating margin | `operating_margin` | > Industry average? |
| EPS growth | `eps_trailing`, `eps_forward` | Forward > Trailing = growth |

#### 2. 資產負債表 (Balance Sheet)

| Metric | Source Field | What to Check |
|--------|-------------|---------------|
| Debt/Equity | `debt_to_equity` | < 1.0 preferred, < 0.5 strong |
| Current ratio | `current_ratio` | > 1.5 = healthy liquidity |
| Book value | `book_value` | P/B < 3 for value |

#### 3. 現金流量表 (Cash Flow Statement)

| Check | Rule |
|-------|------|
| Operating CF | Must be positive and growing |
| FCF | Operating CF - CapEx > 0 |
| FCF yield | FCF / Market cap > 3% is attractive |

#### 4. 權益變動表 (Changes in Equity)

| Check | Rule |
|-------|------|
| Share buybacks | Decreasing share count = shareholder-friendly |
| ROE trend | Stable > 15% over 3+ years |
| Retained earnings | Growing = reinvesting profitably |

### Quick Fundamental Query

```python
# Pull latest fundamentals for a candidate
fund = fconn.execute("""
    SELECT * FROM fundamentals
    WHERE symbol = ?
    ORDER BY date DESC LIMIT 1
""", (symbol,)).fetchone()
```

Use WebSearch to supplement with latest quarterly earnings data and analyst estimates not in the database.

---

## Step 8: Research Report Template

Generate the final report in this structure:

```markdown
# Investment Research Report — [Date]

## Executive Summary
- Market phase: [EXPANSION/PEAK/CONTRACTION/TROUGH]
- Research thesis: [1-2 sentences]
- Top picks: [3-5 symbols with conviction level]

## 1. Macro Environment
- Cycle phase and key indicators
- News sentiment summary
- Risk events on the horizon

## 2. Stock Pool & Screening
- Universe: [pool name], [N] stocks
- Filters applied: [list]
- Survivors: [N] candidates

## 3. Alpha Signals
| Symbol | Score | Technical | Fundamental | Catalyst |
|--------|-------|-----------|-------------|----------|
| ... | | | | |

## 4. Risk Analysis
| Symbol | Beta | Max DD | Sharpe | Correlation |
|--------|------|--------|--------|-------------|
| ... | | | | |

## 5. Strategy & Backtest
- Entry/exit rules
- Backtest results table
- vs Benchmark comparison

## 6. Financial Health (四大報表)
Per-stock financial statement highlights

## 7. Portfolio Construction
| Symbol | Weight | Entry | Stop Loss | Target |
|--------|--------|-------|-----------|--------|
| ... | | | | |

## 8. Risk Disclosure
- Key risks and mitigation
- Scenario analysis (bull/base/bear)

---
_Generated by investment-research skill on [date]_
_Data source: news_stock platform (finance.db, news.db, macro.db)_
```

---

## Continuous Mode — Portfolio Management Agent

This skill is designed to run **continuously**, not just once. When the user says "開始研究" or "持續追蹤", enter continuous mode.

### Operating Loop

```
┌─────────────────────────────────────────────────────┐
│                  CONTINUOUS LOOP                     │
│                                                      │
│  1. MONITOR  → Check portfolio health daily          │
│       ↓                                              │
│  2. SCAN     → Search for new opportunities (web)    │
│       ↓                                              │
│  3. EVALUATE → Score new candidates vs current hold  │
│       ↓                                              │
│  4. REBALANCE → Propose swaps if better alpha found  │
│       ↓                                              │
│  5. REPORT   → Update portfolio dashboard            │
│       ↓                                              │
│  (loop back to 1)                                    │
└─────────────────────────────────────────────────────┘
```

### 1. MONITOR — Portfolio Health Check

Every session, start by assessing current holdings:

```
For each position in portfolio:
  - Current price vs entry → unrealized P&L
  - Hit stop loss? → FLAG for exit
  - Hit take profit? → FLAG for partial exit
  - Technical signal reversal? → FLAG for review
  - Earnings coming up? → WebSearch "[ticker] next earnings date"
  - Breaking news? → WebSearch "[ticker] news today"
```

Output a **Portfolio Health Dashboard**:
```markdown
## Portfolio Health — [Date]

| Symbol | Entry | Current | P&L | Status | Alert |
|--------|-------|---------|-----|--------|-------|
| NVDA | $120 | $135 | +12.5% | ✅ Hold | Earnings in 5 days |
| TSM | $180 | $165 | -8.3% | 🚨 Stop loss hit | EXIT |
| ... | | | | | |

Total P&L: +X%  |  Benchmark (SPY): +Y%  |  Alpha: +Z%
```

### 2. SCAN — Continuous Opportunity Discovery

**Don't wait to be asked.** Proactively search for new alpha:

```
Weekly rotation of discovery themes:
  Week 1: Sector rotation signals
    WebSearch: "sector rotation [month] [year] outperforming"
    WebSearch: "money flow sectors ETF relative strength"

  Week 2: Emerging trends
    WebSearch: "emerging investment themes [year]"
    WebSearch: "new technology stocks breakout"
    WebSearch: "venture capital trending sectors"

  Week 3: Contrarian / Value
    WebSearch: "most undervalued stocks [market]"
    WebSearch: "stocks 52 week low strong fundamentals"
    WebSearch: "insider buying significant [month]"

  Week 4: Global opportunities
    WebSearch: "best performing global markets [year]"
    WebSearch: "Japan stocks momentum"
    WebSearch: "India market top picks"
    WebSearch: "emerging market value opportunities"
```

Also monitor for macro regime changes:
```
WebSearch: "Fed rate decision latest"
WebSearch: "yield curve inversion update"
WebSearch: "VIX spike market fear"
→ If cycle phase changes → trigger full portfolio reassessment
```

### 3. EVALUATE — Compare New vs Current

Score new candidates against current holdings using the same framework:

```
New candidate score > Weakest holding score + 10% margin?
  → YES → Propose swap
  → NO  → Add to watchlist for future review

Also check:
  - Does adding this reduce portfolio correlation? (diversification benefit)
  - Does it align with current cycle phase?
  - Is there a clear catalyst within 90 days?
```

### 4. REBALANCE — Propose Portfolio Changes

Never auto-execute. Always present proposals for user decision:

```markdown
## Rebalance Proposal — [Date]

### Exits (triggered by rules)
| Symbol | Reason | Current P&L |
|--------|--------|-------------|
| TSM | Stop loss -8% | -$1,200 |

### Swaps (better alpha found)
| OUT | IN | Rationale |
|-----|-----|-----------|
| XYZ (score: 62) | ABC (score: 78) | Higher momentum, lower correlation |

### New Additions (from web discovery)
| Symbol | Score | Thesis | Suggested Weight |
|--------|-------|--------|-----------------|
| ISRG | 81 | Robotics surgery leader, 22% rev growth | 8% |

### Do Nothing (current portfolio is optimal)
If no exits triggered and no candidates score significantly higher,
explicitly state: "Portfolio unchanged. No action needed."
```

### 5. REPORT — Cumulative Portfolio Tracking

Maintain a running portfolio state file:

```markdown
# Portfolio State — [Date]

## Current Holdings
| Symbol | Entry Date | Entry Price | Weight | Thesis |
|--------|-----------|-------------|--------|--------|
| ... | | | | |

## Historical Trades
| Date | Action | Symbol | Price | P&L | Reason |
|------|--------|--------|-------|-----|--------|
| ... | | | | | |

## Performance
| Period | Portfolio | Benchmark | Alpha |
|--------|----------|-----------|-------|
| MTD | +X% | +Y% | +Z% |
| YTD | +X% | +Y% | +Z% |

## Asset Allocation (四大報表 summary)
| Category | Current | Target |
|----------|---------|--------|
| Stocks | X% | Y% |
| Bonds/ETF | X% | Y% |
| Cash | X% | Y% |

## Watchlist (from continuous scanning)
| Symbol | Score | Source | Why Watching |
|--------|-------|--------|-------------|
| ... | | Web/Local | |
```

Store this file at: `$NEWS_STOCK_DIR/reports/portfolio-state.md` (default: `~/Documents/Projects/news_stock/reports/portfolio-state.md`)

### Persistence Across Sessions

After each session, save state so the next session picks up where it left off:

```python
import json, os
from datetime import date

STATE_FILE = os.path.expanduser(
    os.environ.get("NEWS_STOCK_DIR", "~/Documents/Projects/news_stock") + "/reports/portfolio-state.json"
)

state = {
    "last_updated": str(date.today()),
    "holdings": [...],        # Current positions
    "watchlist": [...],       # Candidates being tracked
    "alerts": [...],          # Pending alerts
    "scan_rotation": 1,       # Which weekly scan theme is next (1-4)
    "last_scan_date": "...",  # When the last web scan happened
    "trade_history": [...]    # All completed trades
}

with open(STATE_FILE, 'w') as f:
    json.dump(state, f, indent=2, ensure_ascii=False)
```

On session start, **always read this file first** to resume.

---

## Integration with Other Skills

| Skill | How it Integrates |
|-------|-------------------|
| **planning-with-files** | Use for multi-day research projects with progress tracking |
| **office-xlsx** | Export backtest results and portfolio to spreadsheet |
| **office-pdf** | Generate formatted research report PDF |
| **webapp-testing** | Verify news_stock web dashboard displays correctly |
| **dispatching-parallel-agents** | Run multiple stock analyses in parallel |

## Data Freshness

Before starting research, verify data is current:

```python
# Check latest data dates
latest_price = fconn.execute("SELECT MAX(date) FROM daily_prices").fetchone()[0]
latest_news = nconn.execute("SELECT MAX(published_at) FROM news").fetchone()[0]
latest_macro = conn.execute("SELECT MAX(date) FROM macro_data").fetchone()[0]

print(f"Prices: {latest_price}, News: {latest_news}, Macro: {latest_macro}")
# If stale, suggest running collectors first
```

## Web Research

When database data is insufficient, use WebSearch for:
- Breaking news and earnings surprises
- Analyst price targets and consensus estimates
- SEC filings (10-K, 10-Q)
- Industry reports and competitive landscape
- Geopolitical developments affecting positions
- **New stock discovery** (not limited to local database)
- **Global markets** beyond US/TW coverage
