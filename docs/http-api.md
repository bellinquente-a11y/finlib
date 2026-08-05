# HTTP API

The `api/` package exposes the same core capabilities as the pipeline over HTTP, built on FastAPI. It reuses the domain types, repositories, and analytics unchanged — the API layer only adds routing, dependency injection, request/response schemas, and authentication.

## Application

`api/apps.py` builds the app and mounts two routers:

```python
app = FastAPI()
app.include_router(market_data.router)
app.include_router(portfolio.router)
```

Run it with uvicorn (a dependency of the project):

```bash
poetry run uvicorn finlib.api.apps:app --reload
```

Interactive docs are then served at `/docs` (Swagger UI) and `/redoc`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/market-data` | Fetch OHLCV bars from Binance for one or more symbols. |
| `POST` | `/trades` | Record a trade (201 Created). |
| `GET` | `/trades` | List all recorded trades. |
| `GET` | `/positions` | Historic position per symbol. |
| `GET` | `/pnl` | Mark-to-market PnL per symbol. |

Every endpoint requires an API key (below).

### `market_data.py`

`GET /market-data` takes `symbols` (repeatable query param), an `interval`, and a `start`, calls `fetch_binance` ([async-and-concurrency.md](async-and-concurrency.md)), and returns a list of `OHLCVBar` schema objects. It is an `async def` route, so FastAPI awaits the fetch directly on the event loop.

### `portfolio.py`

- `POST /trades` — validates the body as a `Trade` (all domain constraints apply) and calls `trade_repo.add`.
- `GET /trades` — returns `trade_repo.get_all()`.
- `GET /positions` — builds a `Portfolio` and returns `historic_position()` as a nested dict.
- `GET /pnl` — returns the PnL frame from `compute_portfolio_performance_metrics`. It carries a `TODO`: prices may be stale, because refresh is deferred to a scheduled ingestion job rather than fetched per request — a deliberate read/write separation, but one to be aware of when reading the numbers.

## Dependency injection — `deps.py`

FastAPI's `Depends` is how repositories reach the routes:

```python
def get_trade_repo() -> TradeRepository:
    return SQLiteTradeRepository(get_settings().data_dir / "trades.db")

def get_market_data_repo() -> OHLCVRepository:
    return SQLiteOHLCVRepository(get_settings().data_dir / "market_data.db")
```

Routes annotate their parameters as `Annotated[TradeRepository, Depends(get_trade_repo)]`, so they receive the **Protocol**, not the concrete class — the same structural-subtyping decoupling used everywhere else ([repositories.md](repositories.md)). The API happens to wire the SQLite backends; a test can override these dependencies with in-memory repos without touching a route. Note the API defaults to SQLite while the [pipeline](pipeline.md) defaults to file-backed repos — same Protocols, different backends, which is the point.

## Authentication — `require_key`

Every route depends on `require_key`, which reads an `X-API-KEY` header (via `APIKeyHeader`, `auto_error=False`) and compares it to `settings.api_key`:

- missing key → `401 Unauthorized`
- wrong key → `403 Forbidden`

The comparison uses `secrets.compare_digest`, a **constant-time** check that does not leak information through timing the way `==` would. The expected key is a `SecretStr` in settings, so it is not accidentally logged (see [configuration.md](configuration.md)).

## Schemas — `schemas.py`

`OHLCVBar` is the API's response model for market data (`symbol`, `open_time`, `close_time`, OHLCV fields, all `> 0`). Keeping a dedicated API schema separate from the internal `OHLCVInterval`/`BinanceDataRow` means the wire contract can evolve independently of the storage and fetch representations.

## See also

- [repositories.md](repositories.md) — the backends behind the injected dependencies.
- [pipeline.md](pipeline.md) — the batch counterpart that shares the same analytics.
