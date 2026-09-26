"""Unit and CLI tests for cache_manager core and rich commands."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest
import respx
import httpx
from rich.console import Console

from cache_manager import commands, core
from tickertape.constants import SITEMAP_URLS
from tickertape.lookup.models import ISINMapping
from tickertape.lookup.table import ISINLookupTable
from tickertape.models import SitemapURL
from tickertape.storage import SitemapCacheManager

SAMPLE_URLSET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://www.tickertape.in/mutualfunds/quant-active-fund-M_ESAF</loc>
        <lastmod>2026-03-01</lastmod>
    </url>
</urlset>
"""


@pytest.fixture
def test_console() -> tuple[Console, io.StringIO]:
    """Provide a Rich console writing to an in-memory buffer."""
    buf = io.StringIO()
    con = Console(file=buf, color_system=None, width=120)
    return con, buf


# =========================================================================
# Core Logic Tests
# =========================================================================


def test_core_get_cache_status_empty(temp_cache_dir: Path):
    status = core.get_cache_status(cache_dir=temp_cache_dir)
    assert status["cache_dir"] == str(temp_cache_dir)
    assert "mf" in status["sitemaps"]
    assert status["sitemaps"]["mf"]["cached"] is False
    assert status["sitemaps"]["mf"]["count"] == 0

    assert status["isin_db"]["exists"] is False
    assert status["isin_db"]["records"] == 0


def test_core_get_cache_status_with_data(temp_cache_dir: Path):
    storage = SitemapCacheManager(cache_dir=temp_cache_dir)
    items = [
        SitemapURL(
            record_id="M_AAA",
            url="https://www.tickertape.in/mutualfunds/fund-a-M_AAA",
        ),
        SitemapURL(
            record_id="M_BBB",
            url="https://www.tickertape.in/mutualfunds/fund-b-M_BBB",
        ),
    ]
    storage.save("mf", items)

    table = ISINLookupTable(cache_dir=temp_cache_dir)
    mapping = ISINMapping(
        isin="INF966L01721",
        record_id="M_QUNG",
        slug="quant-fund-M_QUNG",
        name="Quant Fund",
        url="https://www.tickertape.in/mutualfunds/quant-fund-M_QUNG",
    )
    table.upsert(mapping)

    status = core.get_cache_status(cache_dir=temp_cache_dir)
    assert status["sitemaps"]["mf"]["cached"] is True
    assert status["sitemaps"]["mf"]["count"] == 2
    assert status["sitemaps"]["mf"]["size_kb"] > 0
    assert status["isin_db"]["exists"] is True
    assert status["isin_db"]["records"] == 1


def test_core_get_cache_status_corrupted(temp_cache_dir: Path):
    storage = SitemapCacheManager(cache_dir=temp_cache_dir)
    corrupted_file = storage.get_cache_path("mf")
    corrupted_file.parent.mkdir(parents=True, exist_ok=True)
    corrupted_file.write_text("{invalid json", encoding="utf-8")

    status = core.get_cache_status(cache_dir=temp_cache_dir)
    assert status["sitemaps"]["mf"]["cached"] is True
    assert status["sitemaps"]["mf"]["error"] == "Corrupted"


@pytest.mark.asyncio
@respx.mock
async def test_core_build_sitemap_cache(temp_cache_dir: Path):
    respx.get(SITEMAP_URLS["mf"]).mock(
        return_value=httpx.Response(200, text=SAMPLE_URLSET_XML)
    )

    count = await core.build_sitemap_cache("mf", force=True, cache_dir=temp_cache_dir)
    assert count == 1

    storage = SitemapCacheManager(cache_dir=temp_cache_dir)
    cached = storage.load("mf")
    assert cached is not None
    assert len(cached) == 1
    assert cached[0].record_id == "M_ESAF"


@pytest.mark.asyncio
async def test_core_build_isin_index(temp_cache_dir: Path, monkeypatch):
    mock_build_index = AsyncMock(return_value=5)
    monkeypatch.setattr(
        "tickertape.lookup.indexer.ISINIndexer.build_index", mock_build_index
    )

    cb = MagicMock()
    result = await core.build_isin_index(
        force=True,
        concurrency=3,
        delay=0.1,
        limit=5,
        progress_callback=cb,
        cache_dir=temp_cache_dir,
    )

    assert result == 5
    mock_build_index.assert_awaited_once_with(
        force_refresh=True,
        concurrency=3,
        delay=0.1,
        limit=5,
        progress_callback=cb,
    )


def test_core_clear_cache(temp_cache_dir: Path):
    storage = SitemapCacheManager(cache_dir=temp_cache_dir)
    storage.save("mf", [SitemapURL(record_id="M_1", url="https://example.com/1")])
    storage.save("stocks", [SitemapURL(record_id="S_1", url="https://example.com/2")])

    table = ISINLookupTable(cache_dir=temp_cache_dir)
    table.upsert(
        ISINMapping(
            isin="INF123456789",
            record_id="M_1",
            slug="sample-slug",
            name="Sample",
            url="https://example.com/1",
        )
    )
    assert table.count() == 1

    # Clear only mf sitemap
    core.clear_cache(target="sitemap", category="mf", cache_dir=temp_cache_dir)
    assert not storage.exists("mf")
    assert storage.exists("stocks")
    assert table.count() == 1

    # Clear isin database
    core.clear_cache(target="isin", cache_dir=temp_cache_dir)
    assert table.count() == 0
    assert storage.exists("stocks")

    # Clear all
    core.clear_cache(target="all", cache_dir=temp_cache_dir)
    assert not storage.exists("stocks")


# =========================================================================
# Rich CLI Command Tests
# =========================================================================


def test_cli_status_empty(temp_cache_dir: Path, test_console):
    con, buf = test_console
    commands.main(["status", "--cache-dir", str(temp_cache_dir)], console=con)

    output = buf.getvalue()
    assert "TickerTape Cache Manager" in output
    assert "Sitemaps Cache (JSON)" in output
    assert "ISIN Lookup Engine (SQLite)" in output
    assert "Missing" in output
    assert "Not Initialized" in output


def test_cli_status_populated(temp_cache_dir: Path, test_console):
    con, buf = test_console

    storage = SitemapCacheManager(cache_dir=temp_cache_dir)
    storage.save("mf", [SitemapURL(record_id="M_1", url="https://example.com/1")])

    table = ISINLookupTable(cache_dir=temp_cache_dir)
    table.upsert(
        ISINMapping(
            isin="INF123456789",
            record_id="M_1",
            slug="sample-slug",
            name="Sample Fund",
            url="https://example.com/1",
        )
    )

    commands.main(["status", "--cache-dir", str(temp_cache_dir)], console=con)
    output = buf.getvalue()

    assert "Cached" in output
    assert "Ready" in output
    assert "1 records" in output


@respx.mock
def test_cli_build_sitemap(temp_cache_dir: Path, test_console):
    con, buf = test_console
    respx.get(SITEMAP_URLS["mf"]).mock(
        return_value=httpx.Response(200, text=SAMPLE_URLSET_XML)
    )

    commands.main(
        ["build", "sitemap", "--category", "mf", "--cache-dir", str(temp_cache_dir)],
        console=con,
    )

    output = buf.getvalue()
    assert "Successfully cached" in output
    assert "'mf'" in output


def test_cli_build_index(temp_cache_dir: Path, test_console, monkeypatch):
    con, buf = test_console

    async def fake_build_index(*args, **kwargs):
        cb = kwargs.get("progress_callback")
        if cb:
            cb(1, 1, 1, 0)
        return 1

    monkeypatch.setattr(
        "tickertape.lookup.indexer.ISINIndexer.build_index", fake_build_index
    )

    commands.main(
        [
            "build",
            "index",
            "--limit",
            "1",
            "--concurrency",
            "2",
            "--cache-dir",
            str(temp_cache_dir),
        ],
        console=con,
    )

    output = buf.getvalue()
    assert "Building ISIN Index" in output
    assert "Indexing complete" in output
    assert "1 funds recorded in SQLite" in output


def test_cli_clear_with_yes(temp_cache_dir: Path, test_console):
    con, buf = test_console

    storage = SitemapCacheManager(cache_dir=temp_cache_dir)
    storage.save("mf", [SitemapURL(record_id="M_1", url="https://example.com/1")])

    commands.main(
        ["clear", "--target", "sitemap", "-y", "--cache-dir", str(temp_cache_dir)],
        console=con,
    )

    output = buf.getvalue()
    assert "Successfully purged sitemap cache" in output
    assert not storage.exists("mf")


def test_cli_clear_cancelled_by_prompt(temp_cache_dir: Path, test_console, monkeypatch):
    con, buf = test_console
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *args, **kwargs: False)

    commands.main(
        ["clear", "--target", "all", "--cache-dir", str(temp_cache_dir)],
        console=con,
    )

    output = buf.getvalue()
    assert "Operation cancelled" in output


def test_cli_clear_confirmed_by_prompt(temp_cache_dir: Path, test_console, monkeypatch):
    con, buf = test_console
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *args, **kwargs: True)

    commands.main(
        ["clear", "--target", "all", "--cache-dir", str(temp_cache_dir)],
        console=con,
    )

    output = buf.getvalue()
    assert "Successfully purged all cache" in output


def test_cli_unknown_arguments():
    with pytest.raises(SystemExit):
        commands.main(["invalid_command"])


def test_cli_error_handling(temp_cache_dir: Path, test_console, monkeypatch):
    con, buf = test_console

    def fail_status(*args, **kwargs):
        raise RuntimeError("Disk read error")

    monkeypatch.setattr("cache_manager.core.get_cache_status", fail_status)

    commands.main(["status", "--cache-dir", str(temp_cache_dir)], console=con)

    output = buf.getvalue()
    assert "Error:" in output
    assert "Disk read error" in output
