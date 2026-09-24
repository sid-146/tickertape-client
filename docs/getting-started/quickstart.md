# Quickstart Guide

This guide will walk you through the essential operations of `tickertape-client` in under 5 minutes.

---

## 1. Initializing the Client

The recommended way to use `TickerTapeClient` is with an async context manager (`async with`):

```python
import asyncio
from tickertape import TickerTapeClient

async def main():
    async with TickerTapeClient() as client:
        print("Connected to TickerTape client!")

asyncio.run(main())
```

> [!TIP]
> The context manager automatically closes the underlying HTTP connection pool when exiting the block.

---

## 2. Working with Sitemaps

TickerTape publishes large XML sitemaps for mutual funds, stocks, and ETFs. `tickertape-client` parses these and caches them locally to avoid redundant network overhead:

```python
async with TickerTapeClient() as client:
    # 1. Fetch mutual fund URLs (live XML fetched once, then persisted to .cache/tickertape)
    urls = await client.sitemap.get("mf")
    print(f"Total Mutual Funds in sitemap: {len(urls)}")

    # 2. Inspect first entry
    first = urls[0]
    print(f"Slug / URL: {first.url}")
    print(f"Record ID:  {first.record_id}")
    print(f"Priority:   {first.priority}")
```

---

## 3. Fetching Mutual Fund Details

Retrieve structured mutual fund data using either a slug or an MFID:

```python
async with TickerTapeClient() as client:
    fund = await client.mf.get("quant-infrastructure-fund-M_QUNG")

    # Core details
    print(f"Scheme Name:  {fund.name}")
    print(f"ISIN:         {fund.isin}")
    print(f"Current NAV:  INR {fund.nav}")

    # Metadata & Ratios
    if fund.meta:
        print(f"Benchmark:    {fund.meta.benchmark_index}")
        print(f"Expense Ratio:{fund.meta.expense_ratio}%")
        print(f"AUM:          INR {fund.meta.aum} Cr")

    # Scorecard ratings
    for card in fund.scorecard:
        print(f"Scorecard -> {card.name}: {card.tag} ({card.colour})")
```

---

## 4. Resolving an ISIN On Demand

If you only have an ISIN string (e.g. from a portfolio statement) and a scheme name hint:

```python
async with TickerTapeClient() as client:
    fund = await client.mf.get_by_isin(
        isin="INF966L01721",
        hint_name="Quant Infrastructure Fund - Growth - Direct Plan",
    )
    if fund:
        print(f"Resolved: {fund.name} (NAV: INR {fund.nav})")
```

---

## 5. Finding Category Peers

Compare schemes in the exact same subsector, plan, and option:

```python
async with TickerTapeClient() as client:
    # Pre-seed or resolve an ISIN first
    peers = client.mf.get_peers(
        isin="INF966L01721",
        match_plan=True,      # Match Direct with Direct
        match_option=True,    # Match Growth with Growth
        limit=5,
    )
    for p in peers:
        print(f"Peer: {p.name} [{p.isin}] (AMC: {p.amc})")
```

---

## Next Steps

Explore the detailed user guides:
- [Client Configuration](../guides/client-configuration.md)
- [Sitemaps & Caching](../guides/sitemaps-and-caching.md)
- [Mutual Funds & SSR Data](../guides/mutual-funds-data.md)
- [ISIN Engine & Peer Discovery](../guides/isin-lookup-and-peers.md)
