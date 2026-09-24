# ISIN Lookup & Peer Clustering

Portfolio management tools and brokers identify mutual funds by their **ISIN** (International Securities Identification Number), e.g. `INF966L01721`. However, TickerTape uses URL slugs (e.g. `quant-infrastructure-fund-M_QUNG`).

`tickertape-client` provides a high-performance **SQLite Lookup Engine** and **Targeted On-Demand Resolver** to bridge this gap.

---

## Targeted On-Demand Resolver

When you query a fund by ISIN using `client.mf.get_by_isin()`:

1. **Step 1 (Database Check):** Checks the persistent SQLite database for the ISIN.
2. **Step 2 (Targeted Sitemap Search):** If not yet indexed, uses `hint_name` tokens to score candidate URLs from the cached sitemap.
3. **Step 3 (Live Verification & Persistence):** Fetches the top candidates, verifies the actual ISIN in the SSR data, saves the mapping to SQLite, and returns the parsed fund.

```python
async with TickerTapeClient() as client:
    fund = await client.mf.get_by_isin(
        isin="INF966L01721",
        hint_name="Quant Infrastructure Fund - Growth - Direct Plan",
    )
    if fund:
        print(f"Resolved ISIN: {fund.name} (NAV: INR {fund.nav})")
```

---

## Persistent SQLite Lookup Table (`client.mf.lookup`)

The lookup table resides in `.cache/tickertape/isin_lookup.db`. It auto-migrates columns and maintains indexes for rapid queries.

### Basic CRUD

```python
table = client.mf.lookup

# Total indexed funds
print(f"Total entries: {table.count()}")

# Fetch single mapping by ISIN (case-insensitive)
mapping = table.get("INF966L01721")
if mapping:
    print(f"Found: {mapping.name} (Slug: {mapping.slug})")

# Fetch mapping by TickerTape record ID
mapping = table.get_by_record_id("M_QUNG")

# Clear table
table.clear()
```

### Batch Operations

```python
# Batch lookup returns a dict {isin: ISINMapping}
results = await client.mf.get_cached_by_isin_batch([
    "INF966L01721",
    "INF209K01157",
    "INF174K01LS2",
])

for isin, rec in results.items():
    print(f"{isin} -> {rec.name} (NAV: INR {rec.nav})")
```

---

## Category Peer Clustering

Compare schemes belonging to the exact same investment category:

```python
# Finds peer funds in the same subsector
peers = client.mf.get_peers(
    isin="INF966L01721",
    match_plan=True,      # Compare Direct with Direct only
    match_option=True,    # Compare Growth with Growth only
    limit=10,
)

for peer in peers:
    print(f"Peer: {peer.name} | AMC: {peer.amc} | NAV: INR {peer.nav}")
```

---

## Filtering Funds by Attributes

Query indexed schemes matching specific financial criteria:

```python
# Find large cap direct growth funds
large_caps = client.mf.find_funds(
    subsector="Large Cap Fund",
    plan="Direct",
    option="Growth",
)

# Find funds by benchmark index
nifty_funds = client.mf.find_funds(
    benchmark="Nifty 50 - TRI",
)

# Search funds by AMC name
hdfc_funds = client.mf.find_funds(
    amc="HDFC",
)
```
