# Installation

`tickertape-client` requires **Python 3.10+** and modern asynchronous event loop support.

---

## Installing via Package Managers

### With `pip`

```bash
pip install tickertape-client
```

### With `uv`

```bash
uv add tickertape-client
```

### With `poetry`

```bash
poetry add tickertape-client
```

---

## Dependencies

The package has minimal dependencies to keep your environment lean:

| Dependency | Purpose | Minimum Version |
| :--- | :--- | :--- |
| `httpx` | Asynchronous HTTP client & connection pooling | `>=0.27.0` |
| `pydantic` | Data validation and type enforcement | `>=2.0.0` |
| `beautifulsoup4` | Fast HTML parsing to locate SSR `<script id="__NEXT_DATA__">` | `>=4.12.0` |

---

## Verifying Installation

Verify the installation in your terminal:

```bash
python -c "import tickertape; print(tickertape.__all__)"
```

You should see the exported symbols, including `TickerTapeClient`, `ISINLookupTable`, and `MutualFundDetail`.
