"""Parser registry and exports for TickerTape client."""

from __future__ import annotations

from typing import Type
from tickertape.parsers.base import BaseParser
from tickertape.parsers.etf import ETFParser
from tickertape.parsers.mf import MFParser
from tickertape.parsers.screens import ScreenParser
from tickertape.parsers.sitemap import SitemapParser
from tickertape.parsers.stocks import StockParser

_PARSER_REGISTRY: dict[str, Type[BaseParser]] = {
    "sitemap": SitemapParser,
    "mf": MFParser,
    "mutualfunds": MFParser,
    "stocks": StockParser,
    "etf": ETFParser,
    "screens": ScreenParser,
}


def register_parser(name: str, parser_cls: Type[BaseParser]) -> None:
    """Register a new parser type (e.g., 'stocks', 'etf', 'screens')."""
    _PARSER_REGISTRY[name.lower().strip()] = parser_cls


def get_parser(name: str) -> BaseParser:
    """Instantiate a registered parser by name."""
    parser_cls = _PARSER_REGISTRY.get(name.lower().strip())
    if not parser_cls:
        raise KeyError(
            f"No parser registered for '{name}'. Available parsers: {list(_PARSER_REGISTRY.keys())}"
        )
    return parser_cls()


__all__ = [
    "BaseParser",
    "SitemapParser",
    "MFParser",
    "StockParser",
    "ETFParser",
    "ScreenParser",
    "register_parser",
    "get_parser",
]
