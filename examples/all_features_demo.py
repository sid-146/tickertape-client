"""Comprehensive All-in-One Feature Tour of tickertape-client.

This script executes and demonstrates EVERY major feature and function:
1. Client Lifecycle & Custom Configuration
2. XML Sitemap Discovery, Caching & Index Parsing
3. Mutual Fund Scraping & Next.js SSR Hydration Data
4. ISIN Targeted Resolution
5. SQLite Persistent ISIN Lookup Table Operations (CRUD, Batch)
6. Mutual Fund Peer & Category Clustering
7. Bulk Indexing with Real-Time Progress Callbacks
8. Exporting Data to JSON and CSV
9. Extensible Parser Registry
10. Exception Hierarchy & Error Handling
"""

import asyncio
from pathlib import Path
from typing import Any

from tickertape import (
    BASE_URL,
    BaseParser,
    ISINLookupTable,
    ISINMapping,
    MutualFundDetail,
    TickerTapeClient,
    TickerTapeHTTPError,
    TickerTapeNotFoundError,
    get_parser,
    register_parser,
)


async def main() -> None:
    demo_cache = Path(".cache/all_features_demo")

    print("\n" + "=" * 70)
    print(" TICKERTAPE-CLIENT: FULL FEATURE & FUNCTION TOUR")
    print("=" * 70)

    # -----------------------------------------------------------------------
    # 1. Client Lifecycle & Custom Configuration
    # -----------------------------------------------------------------------
    print("\n[Step 1] Initializing Client with Custom Options...")
    client = TickerTapeClient(
        base_url=BASE_URL,
        timeout=15.0,
        cache_dir=demo_cache,
        headers={"User-Agent": "TickerTapeClient-FullTour/1.0"},
    )
    print(f" -> Base URL:   {client.base_url}")
    print(f" -> Timeout:    {client.timeout}s")
    print(f" -> Cache Path: {client.cache_dir}")

    # Use async context manager
    async with client:
        # -------------------------------------------------------------------
        # 2. Sitemaps: Caching, Parsing & References
        # -------------------------------------------------------------------
        print("\n[Step 2] Sitemap Operations & Persistent Caching...")
        print(f" -> Is 'mf' sitemap already cached? {client.sitemap.is_cached('mf')}")

        try:
            print(" -> Fetching sitemap records for 'mf' (Mutual Funds)...")
            sitemap_urls = await client.sitemap.get("mf")
            print(f" -> Retrieved {len(sitemap_urls)} URLs from sitemap.")
            if sitemap_urls:
                first = sitemap_urls[0]
                print(f"    Sample URL: {first.url}")
                print(f"    Record ID:  {first.record_id}")
                print(
                    f"    Priority:   {first.priority} | Changefreq: {first.change_frequency}"
                )

            # Re-read from cache without network call
            cached_urls = await client.sitemap.get("mf", force_refresh=False)
            print(f" -> Read from disk cache: {len(cached_urls)} items (Instant).")
        except TickerTapeHTTPError as exc:
            print(f" -> [Network notice during sitemap fetch]: {exc}")

        # -------------------------------------------------------------------
        # 3. Mutual Fund Scraping & Next.js Hydration Payloads
        # -------------------------------------------------------------------
        print("\n[Step 3] Fetching Mutual Fund Details & Metadata...")
        fund_slug = "quant-infrastructure-fund-M_QUNG"

        try:
            print(f" -> Fetching '{fund_slug}'...")
            fund: MutualFundDetail = await client.mf.get(fund_slug)

            print(f" -> Scheme Name:  {fund.name}")
            print(f" -> Scheme MF ID: {fund.mf_id}")
            print(f" -> Scheme ISIN:  {fund.isin}")
            print(f" -> Current NAV:  INR {fund.nav}")

            if fund.security_info:
                print(
                    f" -> Security Info: AMC='{fund.security_info.amc}', Sector='{fund.security_info.sector}'"
                )
            if fund.meta:
                print(
                    f" -> Meta: Benchmark='{fund.meta.benchmark_index}', ExpRatio={fund.meta.expense_ratio}%, AUM=INR {fund.meta.aum}Cr"
                )
            if fund.scorecard:
                cards = ", ".join(f"{c.name} ({c.tag})" for c in fund.scorecard[:3])
                print(f" -> Scorecard: {cards}...")

            # Convenience helper
            isin_str = await client.mf.get_isin(fund_slug)
            print(f" -> get_isin() result: {isin_str}")

            # Raw SSR Hydration dictionary
            raw_data = await client.mf.get_raw(fund_slug)
            print(f" -> get_raw() keys: {list(raw_data.keys())[:5]}")

        except TickerTapeHTTPError as exc:
            print(f" -> [Network notice during fund fetch]: {exc}")

        # -------------------------------------------------------------------
        # 4. SQLite Persistent ISIN Lookup Table (Single & Batch Operations)
        # -------------------------------------------------------------------
        print("\n[Step 4] Working with SQLite Persistent Lookup Table...")
        table: ISINLookupTable = client.mf.lookup
        print(f" -> Initial table records count: {table.count()}")

        # Upsert single record
        sample_1 = ISINMapping(
            isin="INF966L01721",
            record_id="M_QUNG",
            slug="quant-infrastructure-fund-M_QUNG",
            name="Quant Infrastructure Fund - Direct Plan - Growth",
            amc="Quant Money Managers Limited",
            sector="Equity",
            subsector="Sectoral Fund - Infrastructure",
            plan="Direct",
            option="Growth",
            benchmark="Nifty Infrastructure - TRI",
            url="https://www.tickertape.in/mutualfunds/quant-infrastructure-fund-M_QUNG",
            nav=45.09,
        )
        table.upsert(sample_1)
        print(" -> Upserted sample fund INF966L01721.")

        # Upsert batch of records
        sample_batch = [
            ISINMapping(
                isin="INF209K01157",
                record_id="M_ABSL",
                slug="aditya-birla-infra-M_ABSL",
                name="Aditya Birla Infrastructure - Direct - Growth",
                amc="Aditya Birla Sun Life AMC",
                sector="Equity",
                subsector="Sectoral Fund - Infrastructure",
                plan="Direct",
                option="Growth",
                benchmark="Nifty Infrastructure - TRI",
                url="https://www.tickertape.in/mutualfunds/aditya-birla-infra-M_ABSL",
                nav=62.45,
            ),
            ISINMapping(
                isin="INF174K01LS2",
                record_id="M_ICIC",
                slug="icici-infra-M_ICIC",
                name="ICICI Prudential Infrastructure - Direct - Growth",
                amc="ICICI Prudential AMC",
                sector="Equity",
                subsector="Sectoral Fund - Infrastructure",
                plan="Direct",
                option="Growth",
                benchmark="Nifty Infrastructure - TRI",
                url="https://www.tickertape.in/mutualfunds/icici-infra-M_ICIC",
                nav=185.12,
            ),
            ISINMapping(
                isin="INF846K01164",
                record_id="M_AXIS",
                slug="axis-bluechip-M_AXIS",
                name="Axis Bluechip Fund - Direct - Growth",
                amc="Axis AMC",
                sector="Equity",
                subsector="Large Cap Fund",
                plan="Direct",
                option="Growth",
                benchmark="Nifty 50 - TRI",
                url="https://www.tickertape.in/mutualfunds/axis-bluechip-M_AXIS",
                nav=55.10,
            ),
        ]
        table.upsert_batch(sample_batch)
        print(f" -> Total indexed mappings now: {table.count()}")

        # Single lookup (case-insensitive)
        rec = table.get("inf966l01721")
        print(f" -> table.get('inf966l01721'): {rec.name if rec else None}")

        # Lookup by TickerTape record ID
        rec_by_id = table.get_by_record_id("M_ABSL")
        print(
            f" -> table.get_by_record_id('M_ABSL'): {rec_by_id.isin if rec_by_id else None}"
        )

        # Batch lookup through resource helper
        batch_lookup = await client.mf.get_cached_by_isin_batch(
            ["INF966L01721", "INF209K01157", "NOT_FOUND"]
        )
        print(f" -> get_cached_by_isin_batch(): Found {len(batch_lookup)} matches:")
        for isin_k, fund_v in batch_lookup.items():
            print(f"    * {isin_k}: {fund_v.name} (NAV: INR {fund_v.nav})")

        # -------------------------------------------------------------------
        # 5. Peer & Category Clustering
        # -------------------------------------------------------------------
        print("\n[Step 5] Peer & Category Clustering...")
        # Get peers matching plan ('Direct') and option ('Growth') in the same subsector
        peers = client.mf.get_peers("INF966L01721", match_plan=True, match_option=True)
        print(
            " -> Peer funds for INF966L01721 (Sectoral Fund - Infrastructure, Direct, Growth):"
        )
        for p in peers:
            print(f"    - {p.name} [{p.isin}] (AMC: {p.amc})")

        # Attribute search
        infra_funds = client.mf.find_funds(subsector="Sectoral Fund - Infrastructure")
        print(
            f" -> find_funds(subsector='Sectoral Fund - Infrastructure'): {len(infra_funds)} funds"
        )

        # -------------------------------------------------------------------
        # 6. Bulk Indexing with Progress Tracking
        # -------------------------------------------------------------------
        print("\n[Step 6] Bulk Indexing Simulation...")

        def progress(done: int, total: int, ok: int, err: int) -> None:
            pct = (done / total * 100) if total else 0
            print(
                f"\r    [Progress] {done}/{total} ({pct:.0f}%) | Success: {ok} | Fail: {err}",
                end="",
            )

        try:
            # Running with limit=3 and force_refresh=False (resumable)
            indexed = await client.mf.build_isin_index(
                limit=3,
                concurrency=2,
                delay=0.1,
                progress_callback=progress,
                force_refresh=False,
            )
            print(f"\n -> Bulk indexer processed {indexed} new records.")
        except Exception as exc:
            print(f"\n -> [Indexer notice]: {exc}")

        # -------------------------------------------------------------------
        # 7. Exporting to JSON & CSV
        # -------------------------------------------------------------------
        print("\n[Step 7] Exporting Lookup Table...")
        export_dir = Path("exports")
        export_dir.mkdir(parents=True, exist_ok=True)

        json_out = table.export_json(export_dir / "tour_export.json")
        csv_out = table.export_csv(export_dir / "tour_export.csv")
        print(f" -> Exported JSON: {json_out} ({json_out.stat().st_size} bytes)")
        print(f" -> Exported CSV:  {csv_out} ({csv_out.stat().st_size} bytes)")

        # -------------------------------------------------------------------
        # 8. Extensible Parser Registry
        # -------------------------------------------------------------------
        print("\n[Step 8] Extending the Parser Registry...")

        class ExampleCustomParser(BaseParser[dict]):
            def parse(self, content: Any) -> dict:
                return {"custom": True, "data": str(content)}

        register_parser("example_parser", ExampleCustomParser)
        instantiated_parser = get_parser("example_parser")
        parsed_custom = instantiated_parser.parse("CustomPayload")
        print(f" -> Custom Parser Output: {parsed_custom}")

        # -------------------------------------------------------------------
        # 9. Exception Hierarchy & Error Handling
        # -------------------------------------------------------------------
        print("\n[Step 9] Error Handling Demonstration...")
        try:
            # Trigger deliberate 404
            await client.request("GET", "/non-existent-endpoint-404")
        except TickerTapeNotFoundError as exc:
            print(f" -> Handled TickerTapeNotFoundError: status_code={exc.status_code}")
        except TickerTapeHTTPError as exc:
            print(f" -> Handled TickerTapeHTTPError: {exc}")

    print("\n" + "=" * 70)
    print(" TOUR COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
