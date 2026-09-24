"""Example 1: Basic Usage of TickerTapeClient.

Demonstrates:
- Initializing the client with custom configuration.
- Working with sitemaps and disk caching.
- Fetching mutual fund details and inspecting parsed attributes.
- Accessing raw Next.js SSR hydration payloads (__NEXT_DATA__).
- Error handling for 404s and HTTP failures.
"""

import asyncio
from pathlib import Path
from tickertape import (
    TickerTapeClient,
    TickerTapeHTTPError,
    TickerTapeNotFoundError,
)


async def main() -> None:
    # 1. Initialize client with custom configuration
    custom_cache = Path(".cache/demo_tickertape")

    async with TickerTapeClient(
        timeout=20.0,
        cache_dir=custom_cache,
        headers={"User-Agent": "TickerTapeClient-Demo/1.0"},
    ) as client:
        print("=" * 60)
        print("1. Sitemap Discovery & Persistent Caching")
        print("=" * 60)

        # Check if sitemap is already cached locally on disk
        is_cached = client.sitemap.is_cached("mf")
        print(f"Is 'mf' sitemap already cached locally? {is_cached}")

        # Fetch sitemap (downloads from live URL on first call, caches to JSON)
        print("Fetching mutual fund sitemap...")
        sitemap_items = await client.sitemap.get("mf")
        print(f"Loaded {len(sitemap_items)} mutual fund URLs from sitemap.")

        # Inspect the first few sitemap entries
        for item in sitemap_items[:3]:
            print(f" - [{item.record_id}] {item.url} (modified: {item.last_modified})")

        # Second call with force_refresh=False reads instantly from local disk cache
        cached_items = await client.sitemap.get("mf", force_refresh=False)
        print(f"Re-loaded from disk cache: {len(cached_items)} items.")

        print("\n" + "=" * 60)
        print("2. Fetching Mutual Fund Details")
        print("=" * 60)

        # Fetch fund by slug or MFID
        fund_slug = "quant-infrastructure-fund-M_QUNG"
        print(f"Fetching details for '{fund_slug}'...")
        fund = await client.mf.get(fund_slug)

        print(f"Fund Name:   {fund.name}")
        print(f"MF ID:       {fund.mf_id}")
        print(f"ISIN:        {fund.isin}")
        print(f"Latest NAV:  INR {fund.nav}")
        print(f"Page Slug:   {fund.slug}")

        # Inspect Security Info
        if fund.security_info:
            sec = fund.security_info
            print("\n[Security Info]")
            print(f"  AMC:        {sec.amc} ({sec.amc_code})")
            print(f"  Sector:     {sec.sector} | Subsector: {sec.subsector}")
            print(f"  Option:     {sec.option}")
            print(f"  1D Change:  {sec.nav_ch_1d}%")

        # Inspect Metadata
        if fund.meta:
            meta = fund.meta
            print("\n[Fund Metadata]")
            print(f"  Benchmark:    {meta.benchmark_index}")
            print(f"  Expense Ratio:{meta.expense_ratio}%")
            print(f"  AUM:          INR {meta.aum} Cr")
            print(f"  Risk Level:   {meta.risk_classification}")
            print(f"  Plan:         {meta.plan} | Type: {meta.fund_type}")

        # Inspect Scorecard Items (Performance, Risk, Cost, etc.)
        if fund.scorecard:
            print(f"\n[Scorecard ({len(fund.scorecard)} metrics)]")
            for card in fund.scorecard:
                print(f"  - {card.name}: tag='{card.tag}' colour='{card.colour}'")

        # Convenience helper to retrieve only ISIN
        isin = await client.mf.get_isin(fund_slug)
        print(f"\nConvenience get_isin(): {isin}")

        print("\n" + "=" * 60)
        print("3. Inspecting Raw Next.js SSR Hydration Data")
        print("=" * 60)

        raw_payload = await client.mf.get_raw(fund_slug)
        top_keys = list(raw_payload.keys())
        print(f"Raw Next.js pageProps keys: {top_keys[:8]}")

        print("\n" + "=" * 60)
        print("4. Error Handling")
        print("=" * 60)

        # 404 Not Found handling
        try:
            await client.mf.get("non-existent-fund-slug-M_NONE")
        except TickerTapeNotFoundError as exc:
            print(f"Caught expected 404: {exc} (Status Code: {exc.status_code})")
        except TickerTapeHTTPError as exc:
            print(f"Caught HTTP Error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
