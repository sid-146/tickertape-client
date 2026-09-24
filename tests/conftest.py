"""Pytest fixtures for tickertape-client tests."""

from pathlib import Path
import pytest


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary cache directory for TickerTape client tests."""
    return tmp_path / "tickertape_cache"


@pytest.fixture
def sample_json_path() -> Path:
    """Path to sample mutual fund response JSON."""
    return Path(__file__).parent / "sample_mf_parser_response.json"
