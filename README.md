# tickertape-client

[![PyPI version](https://img.shields.io/pypi/v/tickertape-client.svg)](https://pypi.org/project/tickertape-client/)
[![Python Versions](https://img.shields.io/pypi/pyversions/tickertape-client.svg)](https://pypi.org/project/tickertape-client/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

An unofficial, asynchronous, typed Python SDK and client for [TickerTape](https://www.tickertape.in) featuring persistent caching, Next.js hydration payload extraction, and a high-performance SQLite-backed ISIN lookup engine.

> [!NOTE]
> **Disclaimer:** This project is an **unofficial** community SDK/client and is not affiliated with, endorsed by, sponsored by, or associated with TickerTape or its parent companies. All product names, logos, and brands are property of their respective owners.

---

## Features

- **Asynchronous & Fast:** Built on top of `httpx` and `asyncio` for non-blocking HTTP requests and concurrent scraping.
- **Sitemap Discovery & Caching:** Automatic fetching, XML parsing (`<urlset>` and `<sitemapindex>`), and local JSON disk caching of TickerTape sitemaps.
- **Deep Mutual Fund Extraction:** Parses Next.js SSR hydration payloads (`__NEXT_DATA__`) into typed Pydantic models with NAV, expense ratios, AUM, scorecard metrics, and AMC details.
- **ISIN Resolution & Lookup Engine:**
    - Fast, indexed SQLite database mapping mutual fund ISINs (e.g. `INF966L01721`) to TickerTape records.
    - Targeted on-demand fuzzy resolver with candidate scoring and live verification.
    - Query peer mutual funds and cluster schemes by sector, subsector, plan (`Direct`/`Regular`), option (`Growth`/`IDCW`), and benchmark.
- **Resumable Bulk Indexer:** Crawl thousands of sitemap URLs with configurable concurrency, rate limiting, and progress tracking callbacks.
- **Extensible Architecture:** Modular parser registry pattern (`BaseParser`, `register_parser`) with stubs for future asset types (stocks, ETFs, screens).
- **Fully Typed:** Strict type hints and Pydantic v2 validation models.

---

## Installation

```bash
pip install tickertape-client
```

Or using `uv`:

```bash
uv add tickertape-client
```

---

## Quickstart

```python
import asyncio
from tickertape import TickerTapeClient

async def main():
    async with TickerTapeClient() as client:
        # 1. Fetch parsed sitemap URLs (cached locally on disk after first call)
        sitemap_items = await client.sitemap.get("mf")
        print(f"Found {len(sitemap_items)} mutual fund URLs in sitemap")

        # 2. Fetch mutual fund details by slug or MFID
        fund = await client.mf.get("quant-infrastructure-fund-M_QUNG")
        print(f"Fund: {fund.name}")
        print(f"ISIN: {fund.isin} | NAV: INR {fund.nav}")
        if fund.meta:
            print(f"Benchmark: {fund.meta.benchmark_index}")
            print(f"Expense Ratio: {fund.meta.expense_ratio}%")
            print(f"AUM: INR {fund.meta.aum} Cr")

        # 3. Resolve and fetch fund details directly by ISIN
        fund_by_isin = await client.mf.get_by_isin(
            isin="INF966L01721",
            hint_name="Quant Infrastructure Fund",
        )
        if fund_by_isin:
            print(f"Resolved from ISIN: {fund_by_isin.name}")

        # 4. Find peer funds in the same category
        peers = client.mf.get_peers("INF966L01721", limit=5)
        for peer in peers:
            print(f"Peer: {peer.name} ({peer.isin})")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Runnable Example Scripts

The [`examples/`](examples/) directory contains ready-to-run demonstration scripts for every feature:

| Example Script                                                                       | Description                                                                      |
| :----------------------------------------------------------------------------------- | :------------------------------------------------------------------------------- |
| [`examples/all_features_demo.py`](examples/all_features_demo.py)                     | **Complete Tour:** Runs through every single feature and function in one script. |
| [`examples/01_basic_usage.py`](examples/01_basic_usage.py)                           | Client options, sitemap caching, fund extraction, raw props, error handling.     |
| [`examples/02_isin_lookup_and_peers.py`](examples/02_isin_lookup_and_peers.py)       | Targeted ISIN resolution, SQLite CRUD/batch ops, peer clustering, filtering.     |
| [`examples/03_bulk_indexing_and_export.py`](examples/03_bulk_indexing_and_export.py) | Resumable bulk indexer with progress callback, exporting to JSON & CSV.          |
| [`examples/04_custom_parser.py`](examples/04_custom_parser.py)                       | Subclassing `BaseParser`, registry extension, custom data model extraction.      |

Run any example directly with `uv`:

```bash
uv run python examples/all_features_demo.py
```

---

## Detailed Feature Reference

### 1. `TickerTapeClient` Lifecycle & Configuration

```python
from pathlib import Path
from tickertape import TickerTapeClient

# Custom configuration options
client = TickerTapeClient(
    base_url="https://www.tickertape.in",
    timeout=30.0,
    cache_dir=Path(".cache/tickertape"),
    headers={"User-Agent": "MyCustomBot/1.0"},
)

# Async context manager ensures graceful connection cleanup
async with client:
    # Direct raw request helper if needed:
    html = await client.request("GET", "/mutualfunds/quant-infrastructure-fund-M_QUNG")
```

### 2. Sitemaps (`client.sitemap`)

Manage TickerTape's XML sitemaps with local JSON caching:

```python
# Load mutual fund sitemap (uses local cache if present, otherwise fetches live XML)
items = await client.sitemap.get("mf")

# Bypass cache and force a live download + update local cache
refreshed = await client.sitemap.refresh("mf")

# Inspect parsed sitemap records
for item in items[:5]:
    print(item.record_id, item.url, item.last_modified, item.priority)

# Parse a sitemap index (<sitemapindex>) containing child sitemaps
references = await client.sitemap.get_references("https://example.com/sitemap_index.xml")

# Check cache status & clear cache
is_cached = client.sitemap.is_cached("mf")
client.sitemap.clear_cache("mf")  # or client.sitemap.clear_cache() for all
```

Supported default sitemap categories: `"mf"`, `"stocks"`, `"etf"`, `"us-stocks"`, `"us-etf"`.

### 3. Mutual Funds (`client.mf`)

Extract structured data from HTML and embedded `__NEXT_DATA__` JSON hydration payloads:

```python
# Fetch complete mutual fund detail
fund = await client.mf.get("quant-infrastructure-fund-M_QUNG")

# Core identifiers & NAV
print(fund.mf_id, fund.name, fund.isin, fund.nav)

# Security-level info
if fund.security_info:
    print(fund.security_info.amc, fund.security_info.nav_ch_1d, fund.security_info.option)

# Granular fund metadata
if fund.meta:
    print(fund.meta.benchmark_index, fund.meta.expense_ratio, fund.meta.aum)

# Scorecard items (Performance, Risk, Cost, etc.)
for item in fund.scorecard:
    print(item.name, item.tag, item.colour)

# Convenience helper to fetch just the ISIN
isin = await client.mf.get_isin("quant-infrastructure-fund-M_QUNG")

# Raw Next.js pageProps dictionary
raw_props = await client.mf.get_raw("quant-infrastructure-fund-M_QUNG")
```

### 4. ISIN Targeted Resolution

Resolve an ISIN directly using the SQLite lookup table or on-demand fuzzy sitemap slug matching:

```python
# Resolves ISIN via SQLite table first; if not indexed yet, uses hint_name to match
# candidate URLs in the sitemap, fetches the page, verifies ISIN, and saves to SQLite.
fund = await client.mf.get_by_isin(
    isin="INF966L01721",
    hint_name="Quant Infrastructure Fund - Growth - Direct Plan",
)
```

### 5. Persistent SQLite Lookup Table (`client.mf.lookup`)

Fast local database (`.cache/tickertape/isin_lookup.db`) with auto-migration and indexing:

```python
table = client.mf.lookup

# Query single record by ISIN (case-insensitive)
mapping = table.get("INF966L01721")

# Query by TickerTape record_id
mapping = table.get_by_record_id("M_QUNG")

# Batch query multiple ISINs
results = await client.mf.get_cached_by_isin_batch(["INF966L01721", "INF209K01157"])

# Upsert single or batch records
table.upsert(mapping)
table.upsert_batch([mapping1, mapping2])

# Export database to JSON or CSV
table.export_json("exports/funds.json")
table.export_csv("exports/funds.csv")

# Clear table
table.clear()
```

### 6. Peer & Category Clustering

Cluster funds and find comparable peers using classification tags:

```python
# Find peers matching same subsector, plan (Direct/Regular), and option (Growth/IDCW)
peers = client.mf.get_peers("INF966L01721", match_plan=True, match_option=True, limit=10)

# Filter indexed funds by classification attributes
large_caps = client.mf.find_funds(subsector="Large Cap Fund", plan="Direct", option="Growth")
nifty_funds = client.mf.find_funds(benchmark="Nifty 50 - TRI")
hdfc_funds = client.mf.find_funds(amc="HDFC")
```

### 7. Resumable Bulk Indexing

Asynchronously crawl and index mutual funds in bulk:

```python
def progress(completed, total, successful, failed):
    print(f"\rIndexed {completed}/{total} | Success: {successful} | Failed: {failed}", end="")

# Resumable crawl: skips record_ids already present in SQLite database
indexed = await client.mf.build_isin_index(
    concurrency=5,      # Concurrent workers
    delay=0.5,          # Throttle delay (seconds) per worker
    limit=100,          # Optional batch limit
    progress_callback=progress,
    force_refresh=False,
)

# Force re-download of sitemap XML and re-index all funds:
indexed = await client.mf.build_isin_index(force_refresh=True)
```

### 8. Custom Parser Extension

Extend the client pipeline with custom parsers for new content types:

```python
from tickertape.parsers import BaseParser, get_parser, register_parser

class CustomStockParser(BaseParser[dict]):
    def parse(self, content):
        # Extract custom fields from HTML or JSON
        return {"custom_parsed": True}

# Register by name
register_parser("custom_stock", CustomStockParser)

# Instantiate anywhere
parser = get_parser("custom_stock")
result = parser.parse({"raw": "data"})
```

### 9. Error Handling

Focused and practical exception hierarchy:

```python
from tickertape.errors import (
    TickerTapeError,          # Base exception
    TickerTapeHTTPError,      # HTTP 4xx/5xx or network failures
    TickerTapeNotFoundError,  # Specific HTTP 404 (subclass of HTTPError)
    TickerTapeParseError,     # Failed to parse XML, HTML, or Next.js JSON
)

try:
    fund = await client.mf.get("unknown-slug")
except TickerTapeNotFoundError as exc:
    print(f"404 Not Found: {exc.status_code}")
except TickerTapeParseError as exc:
    print(f"Parsing failed: {exc}")
except TickerTapeHTTPError as exc:
    print(f"HTTP error: {exc.status_code}")
```

---

## Data Models

All models are built with Pydantic v2 and allow ignoring unrecognized extra attributes:

- `MutualFundDetail`: Complete mutual fund entity (`mf_id`, `name`, `isin`, `slug`, `nav`, `security_info`, `meta`, `scorecard`, `raw_props`).
- `MFSecurityInfo`: Core security fields (`mf_id`, `name`, `amc`, `nav_close`, `sector`, `subsector`, etc.).
- `MFMeta`: In-depth fund metadata (`benchmark_index`, `fund_type`, `risk_classification`, `expense_ratio`, `aum`, etc.).
- `MFScorecardItem`: Scorecard metrics (`name`, `tag`, `colour`, `description`).
- `ISINMapping`: SQLite-persisted ISIN record with classification attributes for peer clustering.
- `SitemapURL`: Parsed `<url>` sitemap record (`record_id`, `url`, `last_modified`, `change_frequency`, `priority`).

---

## Development & Testing

Clone the repository and install dependencies with `uv`:

```bash
git clone https://github.com/sid-146/tickertape-client.git
cd tickertape-client
uv sync
```

Run test suite:

```bash
uv run pytest
```

Build distributions:

```bash
uv build
```

Verify distribution metadata:

```bash
uvx twine check dist/*
```

---

## Publishing to PyPI

### Automated Releases via GitHub Actions

This repository is configured with GitHub Actions to publish automatically when a GitHub Release is published, or manually via **Actions > Publish to PyPI**.
See [PyPI Publishing Guide](docs/guides/pypi-publishing.md) for details on setting up PyPI Trusted Publishing (OIDC).

### Manual Publishing via CLI

```bash
# Upload to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/ --token <TEST_PYPI_TOKEN>

# Upload to Production PyPI
uv publish --token <PYPI_TOKEN>
```

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

---

## Disclaimer

This software is an unofficial, community-driven client library. It is neither created, maintained, endorsed, nor supported by TickerTape or its affiliates. Use this tool responsibly, in compliance with all applicable terms of service and rate limits.
