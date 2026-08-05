# Repositories

Persistence in `finlib` is defined by two `typing.Protocol`s — `TradeRepository` (`trade_repo.py`) and `OHLCVRepository` (`ohlcv_repo.py`). Each has three interchangeable backends behind an identical method surface. Callers depend only on the Protocol, never on a concrete class, which is what makes storage swappable.

## Why Protocols (structural subtyping)

A `Protocol` describes a *shape*: any class with matching methods satisfies it, with no inheritance and no registration. `InMemoryTradeRepository`, `FileTradeRepository`, and `SQLiteTradeRepository` share no base class, yet all three are accepted anywhere a `TradeRepository` is expected. The benefits:

- **Swappable backends** — the CLI wires file-backed repos; the API wires SQLite; tests use in-memory. No caller changes.
- **Fast tests without mocks** — an in-memory repo is a real, correct implementation, so tests exercise the true code path rather than a stub.
- **Enforced by `mypy --strict`** — the structural match is checked at type-check time, so a backend that drifts from the Protocol fails CI, not production.

`TradeRepository` is `@runtime_checkable`, so `isinstance(x, TradeRepository)` also works at runtime; `OHLCVRepository` is a plain (compile-time) Protocol.

## `TradeRepository`

```python
class TradeRepository(Protocol):
    def add(self, trade: Trade) -> None: ...
    def get_all(self) -> list[Trade]: ...
    def get_by_symbol(self, symbol: str) -> list[Trade]: ...
    def get_extreme_timestamps(self, symbol: str | None = None) -> tuple[datetime | None, datetime | None]: ...
    def get_all_symbols(self) -> set[str]: ...
```

| Backend | Storage | Notes |
|---|---|---|
| `InMemoryTradeRepository` | Python list | Non-persistent; ideal for tests. |
| `FileTradeRepository` | JSONL file | Appends one `Trade.model_dump_json()` per line; reads lazily line by line. |
| `SQLiteTradeRepository` | SQLite table | Creates the `trades` table on first use; `Decimal`s stored as `TEXT` to preserve exactness. |

The shared helper `_get_extreme_timestamps` folds an iterator of trades into `(min, max)` timestamps in a single pass — used by the in-memory and file backends, while SQLite pushes the same work down to `MIN()`/`MAX()` queries.

## `OHLCVRepository`

```python
class OHLCVRepository(Protocol):
    def add_interval(self, data: OHLCVInterval) -> None: ...
    def add_intervals_batch(self, data: pd.DataFrame, columns_map: dict[str, str] | None = None) -> None: ...
    def get_data(self, symbol: str, start=None, end=None) -> pd.DataFrame: ...
    def last_updated(self, symbol: str) -> datetime | None: ...
    def last_timestamp(self, symbol: str) -> datetime | None: ...
```

The stored unit is `OHLCVInterval`, a frozen dataclass (`symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume`) with `to_string`/`from_string` helpers that serialise each field by type. The same three-backend pattern applies: `InMemoryOHLCVRepository`, `FileOHLCVRepository` (CSV with a `last_updated` column), and `SQLiteOHLCVRepository` (separate `ohlcv` and `last_updated` tables).

### `last_updated` vs `last_timestamp` — two different clocks

This distinction drives the pipeline's incremental refetch, so it is worth stating plainly:

- **`last_timestamp(symbol)`** — the newest *bar* timestamp in the data (a fact about the market: "the most recent candle I hold is 17:59").
- **`last_updated(symbol)`** — the wall-clock time the repo was last *written* for that symbol ("I fetched this at 09:03 today").

The pipeline refetches a symbol only when `last_updated` is older than a threshold; on refetch, the batch insert uses `last_timestamp` to keep only newer bars, so overlapping data is deduplicated on write. See [pipeline.md](pipeline.md).

### Incremental batch insert

`add_intervals_batch` accepts a DataFrame and an optional `columns_map` (used to rename e.g. `close_time → timestamp` from the Binance frame). For each symbol it inserts only rows strictly newer than the current `last_timestamp`, so re-ingesting an overlapping fetch is idempotent and cheap. The helper `_reformat_dataframe_for_batch_input` validates the column mapping and projects the frame down to exactly the repository's fields.

## `PortfolioService`

`PortfolioService` (in `trade_repo.py`) is a thin application service constructed with an injected `TradeRepository`. It exposes `record_trade`, `get_notional(symbol)`, `get_position(symbol)`, and `get_summary()` (position + notional per symbol). It holds no data of its own — all state lives in the injected repository — which is dependency injection in its simplest form and the reason the same service works against any backend.

## See also

- [domain-model.md](domain-model.md) — the `Trade` record the trade repositories hold (`OHLCVInterval` is defined and documented above).
- [data-ingestion.md](data-ingestion.md) — the streaming CSV parser used outside the repositories.
- [pipeline.md](pipeline.md) — how the repositories are wired and refreshed end to end.
