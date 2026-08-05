# Data ingestion

`data.py` is the streaming CSV parser: it turns rows on disk into validated domain objects, one at a time. It is distinct from the repositories (which persist data) and from `async_fetch.py` (which pulls from Binance) — this module is the boundary where *file* data enters the system.

## What it provides

Two generator functions and one record type:

- `OHLCVBar` — a frozen dataclass (`symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume`).
- `stream_ohlcv(path, min_volume=0)` — yields `OHLCVBar`s from a CSV, skipping bars below `min_volume`.
- `stream_trades(path, timestamp_format=...)` — yields validated `Trade`s from a CSV.

```python
from pathlib import Path
from finlib.data import stream_ohlcv

for bar in stream_ohlcv(Path("prices.csv"), min_volume=1000):
    ...  # one OHLCVBar at a time; the whole file is never held in memory
```

## Streaming, and why it matters

Both functions are generators built on `csv.DictReader`. They `yield` one record per row inside a `with open(...)` block, so **only a single row is ever in memory** regardless of file size — memory use is O(1) in the number of rows rather than O(n). A one-line change from `return [...]` to `yield ...` is the difference between a parser that must materialise a full dataset before anything downstream runs and one that streams straight into a consumer. `calculate_daily_vwap` (see [analytics.md](analytics.md)) consumes `stream_ohlcv` this way: it folds the bars into a running numerator and volume total without ever building a list.

A consequence worth remembering: the file handle stays open for the life of the generator, and the stream is single-pass. Consume it once; wrap it in `list(...)` only if you genuinely need random access and the data fits in memory.

## Validation at the boundary

Ingestion is where untrusted text becomes typed values, so conversion and validation happen here rather than deeper in:

- Numeric fields are parsed straight into `Decimal`, so exactness is preserved from the first moment the data is read (see the `Decimal` rationale in [domain-model.md](domain-model.md)).
- `stream_trades` constructs a real `Trade`, so every Pydantic constraint (`quantity > 0`, `price > 0`, valid `side`, symbol length) is enforced on ingest — a malformed row raises immediately, at the boundary, instead of surfacing as a puzzling error later.
- `min_volume` filtering is applied inside `stream_ohlcv`, so thin bars are dropped before a consumer ever sees them.
- A missing file raises `ValueError` up front rather than yielding nothing.

This is the "validate at the boundary" principle from [architecture.md](architecture.md): once a record has been yielded by this module, the rest of the system can treat it as well-formed.

## Relationship to the repositories

`data.py` reads *ad-hoc* CSV files (for example a day of prices for a VWAP calculation). The [repositories](repositories.md) are the managed, queryable stores that back the pipeline and API. The market-data path that feeds the repositories comes from Binance and is validated separately — see [async-and-concurrency.md](async-and-concurrency.md).
