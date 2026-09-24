# Mutual Funds & Next.js SSR Data

TickerTape mutual fund pages are server-side rendered (SSR) with Next.js. Rather than parsing brittle DOM elements, `tickertape-client` extracts and deserializes the embedded `<script id="__NEXT_DATA__">` JSON payload.

This delivers structured, high-fidelity data that matches the official web application.

---

## Extracting Fund Details

Use `client.mf.get()` with a slug or MFID:

```python
async with TickerTapeClient() as client:
    fund = await client.mf.get("quant-infrastructure-fund-M_QUNG")
```

The resulting `MutualFundDetail` model contains several structured sections.

---

## Data Structure Breakdown

### 1. Primary Identifiers & Pricing

```python
print(f"Name:    {fund.name}")
print(f"MF ID:   {fund.mf_id}")     # e.g., 'M_QUNG'
print(f"ISIN:    {fund.isin}")      # e.g., 'INF966L01721'
print(f"NAV:     INR {fund.nav}")   # e.g., 46.1284
print(f"Slug:    {fund.slug}")
```

### 2. Security Information (`fund.security_info`)

Captures fund house details, categorization, and short-term movements:

```python
if fund.security_info:
    sec = fund.security_info
    print(f"AMC Name:     {sec.amc}")
    print(f"AMC Code:     {sec.amc_code}")      # e.g., 'ES'
    print(f"Sector:       {sec.sector}")        # e.g., 'Equity'
    print(f"Subsector:    {sec.subsector}")     # e.g., 'Sectoral Fund - Infrastructure'
    print(f"Option:       {sec.option}")        # e.g., 'Growth' or 'IDCW'
    print(f"1-Day Change: {sec.nav_ch_1d}%")
```

### 3. Granular Metadata (`fund.meta`)

Contains regulatory classifications, benchmarks, expenses, and asset sizing:

```python
if fund.meta:
    meta = fund.meta
    print(f"Benchmark:      {meta.benchmark_index}")      # e.g., 'Nifty Infrastructure - TRI'
    print(f"Expense Ratio:  {meta.expense_ratio}%")        # e.g., 0.65
    print(f"AUM:            INR {meta.aum} Cr")            # e.g., 3145.81
    print(f"Risk Profile:   {meta.risk_classification}")   # e.g., 'Very High'
    print(f"Plan:           {meta.plan}")                  # e.g., 'Direct' or 'Regular'
    print(f"Fund Type:      {meta.fund_type}")             # e.g., 'Equity'
    print(f"CAMS Code:      {meta.cams_code}")
    print(f"RTA Code:       {meta.rta_scheme_code}")
```

### 4. Scorecard Evaluations (`fund.scorecard`)

TickerTape computes quantitative scorecards across key investment dimensions:

```python
for item in fund.scorecard:
    print(f"{item.name}:")
    print(f"  Rating Tag:  {item.tag}")         # 'High', 'Avg', 'Low'
    print(f"  Colour Code: {item.colour}")      # 'green', 'yellow', 'red'
    print(f"  Description: {item.description}")
```

Typically includes:
- **Performance:** Return consistency and category alpha.
- **Risk:** Volatility, downside protection, Sharpe ratio.
- **Cost:** Expense ratio comparison against peer averages.
- **Composition:** Concentration in top 10 holdings and market-cap spread.
- **Red Flags:** Manager churn or portfolio red flags.

---

## Convenience Helpers

### Fast ISIN Extraction

```python
# Fetches the fund and returns only the ISIN string
isin = await client.mf.get_isin("quant-infrastructure-fund-M_QUNG")
print(f"ISIN: {isin}")
```

### Raw Next.js Props Inspection

To inspect unmodeled keys in the hydration payload (like FAQ items, peer tickers, or chart data):

```python
raw_props = await client.mf.get_raw("quant-infrastructure-fund-M_QUNG")
print(f"Available top-level sections: {list(raw_props.keys())}")
```
