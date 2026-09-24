"""Example 2: ISIN Lookup, Targeted Resolution, and Peer Clustering.

Demonstrates:
- Resolving mutual fund details using standard ISIN strings (e.g. 'INF966L01721').
- Using the targeted resolver with hint names for fast candidate matching.
- Working directly with the SQLite ISIN lookup table (single and batch operations).
- Finding peer mutual funds in the same category/subsector.
- Querying funds using classification attributes (sector, benchmark, AMC).
"""

import asyncio
from pathlib import Path
from tickertape import TickerTapeClient
from tickertape.lookup.models import ISINMapping


async def main() -> None:
    cache_dir = Path(".cache/demo_tickertape")

    async with TickerTapeClient(cache_dir=cache_dir) as client:
        print("=" * 60)
        print("1. Targeted ISIN Resolution")
        print("=" * 60)

        isin = "INF966L01721"
        hint = "Quant Infrastructure Fund - Growth - Direct Plan"

        print(f"Resolving ISIN '{isin}' with hint '{hint}'...")
        # get_by_isin checks SQLite first; if missing, searches sitemap slugs and verifies
        fund = await client.mf.get_by_isin(isin=isin, hint_name=hint)
        if fund:
            print("Successfully resolved fund:")
            print(f"  Name: {fund.name}")
            print(f"  ISIN: {fund.isin}")
            print(f"  NAV:  INR {fund.nav}")
        else:
            print("Could not resolve ISIN.")

        print("\n" + "=" * 60)
        print("2. SQLite Lookup Table Direct Operations")
        print("=" * 60)

        table = client.mf.lookup
        print(f"Current total funds indexed in SQLite table: {table.count()}")

        # Inserting sample peer records into the table for demonstration
        sample_mappings = [
            ISINMapping(
                isin="INF209K01157",
                record_id="M_ABSL",
                slug="aditya-birla-sun-life-infrastructure-fund-M_ABSL",
                name="Aditya Birla Sun Life Infrastructure Fund - Direct - Growth",
                amc="Aditya Birla Sun Life Mutual Fund",
                sector="Equity",
                subsector="Sectoral Fund - Infrastructure",
                plan="Direct",
                option="Growth",
                benchmark="Nifty Infrastructure - TRI",
                url="https://www.tickertape.in/mutualfunds/aditya-birla-sun-life-infrastructure-fund-M_ABSL",
                nav=62.45,
            ),
            ISINMapping(
                isin="INF174K01LS2",
                record_id="M_ICIC",
                slug="icici-prudential-infrastructure-fund-M_ICIC",
                name="ICICI Prudential Infrastructure Fund - Direct - Growth",
                amc="ICICI Prudential Mutual Fund",
                sector="Equity",
                subsector="Sectoral Fund - Infrastructure",
                plan="Direct",
                option="Growth",
                benchmark="Nifty Infrastructure - TRI",
                url="https://www.tickertape.in/mutualfunds/icici-prudential-infrastructure-fund-M_ICIC",
                nav=185.12,
            ),
            ISINMapping(
                isin="INF200K01UT4",
                record_id="M_SBII",
                slug="sbi-infrastructure-fund-M_SBII",
                name="SBI Infrastructure Fund - Regular - Growth",
                amc="SBI Mutual Fund",
                sector="Equity",
                subsector="Sectoral Fund - Infrastructure",
                plan="Regular",
                option="Growth",
                benchmark="Nifty Infrastructure - TRI",
                url="https://www.tickertape.in/mutualfunds/sbi-infrastructure-fund-M_SBII",
                nav=42.30,
            ),
            ISINMapping(
                isin="INF846K01164",
                record_id="M_AXIS",
                slug="axis-bluechip-fund-M_AXIS",
                name="Axis Bluechip Fund - Direct - Growth",
                amc="Axis Mutual Fund",
                sector="Equity",
                subsector="Large Cap Fund",
                plan="Direct",
                option="Growth",
                benchmark="Nifty 50 - TRI",
                url="https://www.tickertape.in/mutualfunds/axis-bluechip-fund-M_AXIS",
                nav=55.10,
            ),
        ]

        table.upsert_batch(sample_mappings)
        print(f"Updated total funds in SQLite: {table.count()}")

        # Fetch single record by ISIN (case-insensitive)
        rec = table.get("inf209k01157")
        if rec:
            print(f"\nFetched by ISIN: {rec.name} (Slug: {rec.slug})")

        # Fetch record by TickerTape record_id
        rec_by_id = table.get_by_record_id("M_ICIC")
        if rec_by_id:
            print(f"Fetched by record_id: {rec_by_id.name} (ISIN: {rec_by_id.isin})")

        # Batch fetch multiple ISINs
        batch_results = await client.mf.get_cached_by_isin_batch(
            ["INF209K01157", "INF174K01LS2", "NON_EXISTENT_ISIN"]
        )
        print(f"\nBatch lookup found {len(batch_results)} of 3 queried ISINs:")
        for isin_key, mapping in batch_results.items():
            print(f"  - {isin_key} -> {mapping.name} (NAV: INR {mapping.nav})")

        print("\n" + "=" * 60)
        print("3. Finding Category Peers")
        print("=" * 60)

        # Find peers for Aditya Birla Infra (Direct, Growth)
        # matches plan='Direct' and option='Growth' in the same subsector
        peers = client.mf.get_peers("INF209K01157", match_plan=True, match_option=True)
        print(
            "Peers for 'INF209K01157' (Sectoral Fund - Infrastructure, Direct, Growth):"
        )
        for p in peers:
            print(f"  - {p.name} [{p.isin}] (AMC: {p.amc}, NAV: INR {p.nav})")

        print("\n" + "=" * 60)
        print("4. Attribute Filtering")
        print("=" * 60)

        # Find funds by benchmark
        nifty_infra_funds = client.mf.find_funds(benchmark="Nifty Infrastructure - TRI")
        print(
            f"Funds benchmarked against 'Nifty Infrastructure - TRI': {len(nifty_infra_funds)}"
        )
        for f in nifty_infra_funds:
            print(f"  - {f.name} (Plan: {f.plan}, Option: {f.option})")

        # Find funds by AMC search
        sbi_funds = client.mf.find_funds(amc="SBI")
        print(f"\nFunds under 'SBI' AMC: {len(sbi_funds)}")
        for f in sbi_funds:
            print(f"  - {f.name} (ISIN: {f.isin})")


if __name__ == "__main__":
    asyncio.run(main())
