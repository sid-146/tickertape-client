# Custom Parsers & Extension

`tickertape-client` uses a modular parser registry design. You can register custom scrapers and response parsers without modifying the core client codebase.

---

## The `BaseParser` Interface

All parsers inherit from `BaseParser[T]` and implement the `parse(content)` method:

```python
from typing import Any
from tickertape.parsers import BaseParser
from tickertape.errors import TickerTapeParseError

class MyCustomParser(BaseParser[dict]):
    """Extract custom information from HTML or JSON."""

    def parse(self, content: Any) -> dict:
        if not isinstance(content, dict):
            raise TickerTapeParseError(f"Expected dict, got {type(content).__name__}")
        
        return {
            "processed": True,
            "data": content,
        }
```

---

## Registering and Retrieving Parsers

Use `register_parser()` to add your parser to the global registry, and `get_parser()` to instantiate it by name:

```python
from tickertape.parsers import register_parser, get_parser

# 1. Register under a unique identifier
register_parser("my_custom_type", MyCustomParser)

# 2. Instantiate from registry
parser = get_parser("my_custom_type")

# 3. Execute
result = parser.parse({"key": "value"})
print(result)
```

---

## Built-In Default Parsers

The registry includes the following built-in parsers:

| Registry Key | Parser Class | Status |
| :--- | :--- | :--- |
| `"mf"`, `"mutualfunds"` | `MFParser` | Full implementation (Next.js SSR) |
| `"sitemap"` | `SitemapParser` | Full implementation (XML urlset/sitemapindex) |
| `"stocks"` | `StockParser` | Stub (extensible) |
| `"etf"` | `ETFParser` | Stub (extensible) |
| `"screens"` | `ScreenParser` | Stub (extensible) |
