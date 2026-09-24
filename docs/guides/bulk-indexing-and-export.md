# Bulk Indexing & Exports

To enable instant offline lookups and category peer discovery across all 5,900+ mutual fund schemes in India, `tickertape-client` includes a resumable, concurrent bulk crawler.

---

## Bulk Indexer (`client.mf.build_isin_index`)

The indexer iterates through the mutual funds sitemap, fetches individual fund pages, extracts ISIN and metadata, and batches inserts into SQLite.

### Resumable Indexing

By default (`force_refresh=False`), the indexer checks existing record IDs in SQLite and **only crawls missing schemes**. If stopped, resuming picks up exactly where it left off:

```python
async with TickerTapeClient() as client:
    indexed = await client.mf.build_isin_index(
        concurrency=5,      # Number of concurrent async workers
        delay=0.3,          # Throttle delay (seconds) per request
        limit=50,           # Optional limit (None for all funds)
        force_refresh=False # Resumable mode
    )
    print(f"Indexed {indexed} new funds.")
```

### Full Refresh

To re-download the live XML sitemap and re-crawl all schemes:

```python
indexed = await client.mf.build_isin_index(force_refresh=True)
```

---

## Real-Time Progress Tracking

Attach a callback function to monitor indexing progress:

```python
def on_progress(completed: int, total: int, successful: int, failed: int) -> None:
    pct = (completed / total * 100) if total > 0 else 0
    print(
        f"\rProgress: [{completed}/{total}] {pct:.1f}% | "
        f"Saved: {successful} | Failed: {failed}",
        end="",
        flush=True,
    )

async with TickerTapeClient() as client:
    await client.mf.build_isin_index(
        concurrency=4,
        delay=0.5,
        progress_callback=on_progress,
    )
```

---

## Exporting the SQLite Database

Export the full indexed database to structured JSON or CSV for data science analysis or backup:

```python
from pathlib import Path

export_dir = Path("exports")
table = client.mf.lookup

# Export to JSON
json_path = table.export_json(export_dir / "mutual_funds.json")
print(f"Exported JSON to: {json_path}")

# Export to CSV
csv_path = table.export_csv(export_dir / "mutual_funds.csv")
print(f"Exported CSV to: {csv_path}")
```

### Export Schema

Exported rows contain all fields from the `ISINMapping` model:
- `isin`
- `record_id`
- `slug`
- `name`
- `amc`
- `amc_code`
- `sector`
- `subsector`
- `fund_type`
- `fund_class`
- `plan`
- `option`
- `risk_level`
- `benchmark`
- `url`
- `nav`
- `updated_at`
