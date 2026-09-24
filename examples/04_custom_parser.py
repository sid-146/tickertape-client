"""Example 4: Extending with Custom Parsers.

Demonstrates:
- Implementing a custom domain model and parser by subclassing BaseParser.
- Registering custom parsers into the client registry.
- Instantiating and executing registered parsers.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict
from tickertape.parsers import BaseParser, get_parser, register_parser
from tickertape.errors import TickerTapeParseError


# 1. Define custom data model
class StockQuote(BaseModel):
    model_config = ConfigDict(extra="ignore")

    symbol: str
    price: float
    volume: int
    exchange: str = "NSE"


# 2. Implement parser subclassing BaseParser[StockQuote]
class CustomStockParser(BaseParser[StockQuote]):
    """Custom parser for structured stock ticker data."""

    def parse(self, content: Any) -> StockQuote:
        if not isinstance(content, dict):
            raise TickerTapeParseError(
                f"Expected dict input, got {type(content).__name__}"
            )

        try:
            return StockQuote(
                symbol=content["sid"].upper(),
                price=float(content["price"]),
                volume=int(content.get("vol", 0)),
                exchange=content.get("exchange", "NSE"),
            )
        except (KeyError, ValueError) as exc:
            raise TickerTapeParseError(f"Failed to parse StockQuote: {exc}") from exc


def main() -> None:
    print("=" * 60)
    print("Extending the TickerTape Parser Registry")
    print("=" * 60)

    # 3. Register the custom parser
    register_parser("stock_quote", CustomStockParser)
    print("Registered parser 'stock_quote' with CustomStockParser.")

    # 4. Retrieve parser by name from the registry
    parser = get_parser("stock_quote")
    print(f"Retrieved parser from registry: {type(parser).__name__}")

    # 5. Execute parsing
    sample_payload = {
        "sid": "tcs",
        "price": "3940.50",
        "vol": 1284500,
        "exchange": "NSE",
    }
    result = parser.parse(sample_payload)

    print("\nParsed Result:")
    print(f"  Symbol:   {result.symbol}")
    print(f"  Price:    INR {result.price}")
    print(f"  Volume:   {result.volume:,}")
    print(f"  Exchange: {result.exchange}")


if __name__ == "__main__":
    main()
