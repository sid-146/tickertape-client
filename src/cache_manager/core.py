"""Core cache management operations for TickerTape data."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Callable, Optional

from tickertape.client import TickerTapeClient
from tickertape.constants import DEFAULT_CACHE_DIR, SITEMAP_URLS
from tickertape.lookup.indexer import ISINIndexer
from tickertape.lookup.table import ISINLookupTable
from tickertape.storage import SitemapCacheManager


def get_cache_status(cache_dir: Path | str = DEFAULT_CACHE_DIR) -> dict[str, Any]:
    """Inspect local cache directory and return structured status metrics."""
    cache_path = Path(cache_dir)
    storage = SitemapCacheManager(cache_dir=cache_path)

    # 1. Sitemap JSON files
    sitemaps_status: dict[str, dict[str, Any]] = {}
    for cat in SITEMAP_URLS:
        file_path = storage.get_cache_path(cat)
        if file_path.exists() and file_path.stat().st_size > 0:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                raw_date = data.get("fetched_at")
                formatted_date = (
                    datetime.fromisoformat(raw_date).strftime("%Y-%m-%d %H:%M:%S")
                    if raw_date
                    else "Unknown"
                )

                sitemaps_status[cat] = {
                    "cached": True,
                    "count": data.get("count", len(data.get("items", []))),
                    "fetched_at": formatted_date,
                    "size_kb": round(file_path.stat().st_size / 1024, 1),
                    "path": str(file_path),
                }
            except Exception:
                sitemaps_status[cat] = {"cached": True, "error": "Corrupted"}
        else:
            sitemaps_status[cat] = {"cached": False, "count": 0, "size_kb": 0.0}

    # 2. ISIN SQLite database
    db_file = cache_path / "isin_lookup.db"
    db_exists = db_file.exists()
    records = 0
    size_kb = 0.0
    if db_exists:
        try:
            table = ISINLookupTable(cache_dir=cache_path)
            records = table.count()
            size_kb = round(db_file.stat().st_size / 1024, 1)
        except Exception:
            records = 0

    db_status = {
        "exists": db_exists,
        "records": records,
        "size_kb": size_kb,
        "path": str(db_file),
    }

    return {
        "cache_dir": str(cache_path),
        "sitemaps": sitemaps_status,
        "isin_db": db_status,
    }


async def build_sitemap_cache(
    category: str = "mf",
    force: bool = False,
    cache_dir: Path | str = DEFAULT_CACHE_DIR,
) -> int:
    """Fetch live XML sitemap and update the local JSON cache."""
    async with TickerTapeClient(cache_dir=cache_dir) as client:
        if force:
            items = await client.sitemap.refresh(category)
        else:
            items = await client.sitemap.get(category, force_refresh=False)
        return len(items)


async def build_isin_index(
    force: bool = False,
    concurrency: int = 5,
    delay: float = 0.5,
    limit: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, int, int], None]] = None,
    cache_dir: Path | str = DEFAULT_CACHE_DIR,
) -> int:
    """Crawl funds and populate the SQLite ISIN lookup table."""
    async with TickerTapeClient(cache_dir=cache_dir) as client:
        indexer = ISINIndexer(client=client, table=ISINLookupTable(cache_dir=cache_dir))
        return await indexer.build_index(
            force_refresh=force,
            concurrency=concurrency,
            delay=delay,
            limit=limit,
            progress_callback=progress_callback,
        )


def clear_cache(
    target: str = "all",
    category: Optional[str] = None,
    cache_dir: Path | str = DEFAULT_CACHE_DIR,
) -> None:
    """Remove cache files based on target ('all', 'sitemap', or 'isin')."""
    cache_path = Path(cache_dir)
    storage = SitemapCacheManager(cache_dir=cache_path)

    if target in ("sitemap", "all"):
        storage.clear(category)

    if target in ("isin", "all"):
        table = ISINLookupTable(cache_dir=cache_path)
        table.clear()
