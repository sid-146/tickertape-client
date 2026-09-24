"""Example 3: Bulk Indexing and Exporting.

Demonstrates:
- Using the bulk indexer with concurrency controls and rate limiting.
- Attaching a progress callback to track indexing status in real time.
- Resumable indexing behavior (skipping already indexed records).
- Exporting the full SQLite lookup table to structured JSON and CSV files.
"""

import asyncio
from pathlib import Path
from tickertape import TickerTapeClient


def print_progress(completed: int, total: int, successful: int, failed: int) -> None:
    """Real-time progress callback."""
    percent = (completed / total * 100) if total > 0 else 0
    print(
        f"\rProgress: [{completed}/{total}] {percent:.1f}% | "
        f"Success: {successful} | Failed: {failed}",
        end="",
        flush=True,
    )


async def main() -> None:
    cache_dir = Path(".cache/demo_tickertape")
    export_dir = Path("exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    async with TickerTapeClient(cache_dir=cache_dir) as client:
        print("=" * 60)
        print("1. Bulk Indexing with Progress Tracking")
        print("=" * 60)
        print("Starting indexing (limit=5 funds for demonstration)...")

        # build_isin_index fetches the sitemap and crawls funds into SQLite
        # Parameters:
        #   limit: Max funds to process in this run
        #   concurrency: Simultaneous HTTP requests
        #   delay: Throttle in seconds between worker requests
        #   progress_callback: Called on each item completion
        #   force_refresh: False resumes unindexed funds; True refetches live sitemap & reindexes
        indexed_count = await client.mf.build_isin_index(
            limit=25,
            concurrency=2,
            delay=0.3,
            progress_callback=print_progress,
            force_refresh=False,
        )
        print(f"\n\nIndexing run completed: {indexed_count} new funds indexed.")

        table = client.mf.lookup
        print(f"Total funds currently stored in SQLite: {table.count()}")

        print("\n" + "=" * 60)
        print("2. Exporting SQLite Lookup Table to JSON and CSV")
        print("=" * 60)

        json_file = export_dir / "isin_table.json"
        csv_file = export_dir / "isin_table.csv"

        saved_json = table.export_json(json_file)
        print(f"Exported JSON to: {saved_json} ({saved_json.stat().st_size} bytes)")

        saved_csv = table.export_csv(csv_file)
        print(f"Exported CSV to:  {saved_csv} ({saved_csv.stat().st_size} bytes)")

        # Preview CSV header
        if saved_csv.exists() and saved_csv.stat().st_size > 0:
            lines = saved_csv.read_text(encoding="utf-8").splitlines()
            print("\nCSV Header columns:")
            print(f"  {lines[0]}")
            if len(lines) > 1:
                print("Sample row preview:")
                print(f"  {lines[1][:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
