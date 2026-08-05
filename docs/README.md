# finlib documentation

Reference documentation for `finlib`, organised by architectural layer. Each page pairs a **reference** (what the component exposes) with the **rationale** (why it is built this way) so the docs double as design notes.

New to the codebase? Read in order: [Architecture](architecture.md) → [Domain model](domain-model.md) → [Repositories](repositories.md), then dip into the rest as needed.

## Foundations

| Doc | What it covers |
|---|---|
| [architecture.md](architecture.md) | The layers (models → repositories → analytics → pipeline/API), how data flows through them, and the principles that shape the design. |
| [domain-model.md](domain-model.md) | The core types — `Trade` and `Portfolio` — positions, and how a portfolio is valued. |

## Data access

| Doc | What it covers |
|---|---|
| [repositories.md](repositories.md) | Protocol-based dependency injection: `TradeRepository` and `OHLCVRepository`, their in-memory and file/SQLite backends, and why structural subtyping is used. |
| [data-ingestion.md](data-ingestion.md) | The streaming OHLCV parser in `data.py`: validation at the ingestion boundary and O(1)-memory generators. |
| [async-and-concurrency.md](async-and-concurrency.md) | The async Binance fetcher (`aiohttp`, `asyncio.gather`, `Semaphore`) and retry/backoff. See also [concurrency_benchmark.md](concurrency_benchmark.md). |

## Computation & delivery

| Doc | What it covers |
|---|---|
| [analytics.md](analytics.md) | VWAP, rolling volatility & Sharpe, maximum drawdown, and resampling. |
| [pipeline.md](pipeline.md) | The CLI entry point, orchestration, and formatted output in `pipeline/`. |
| [http-api.md](http-api.md) | The FastAPI application: `market_data` and `portfolio` routes, dependencies, and schemas. |

## Cross-cutting concerns

| Doc | What it covers |
|---|---|
| [decorators-and-utils.md](decorators-and-utils.md) | `@retry`/`@async_retry`, `@timer`, `@deprecated`, `@validate_inputs`, and the `timer` context manager. |
| [configuration.md](configuration.md) | Settings via `pydantic-settings` and `.env`. |
| [testing.md](testing.md) | Test layout, Hypothesis property-based tests, fixtures, and strategies. |

## Background notes

| Doc | What it covers |
|---|---|
| [concurrency_benchmark.md](concurrency_benchmark.md) | Sequential vs. threading vs. async: measured results and the reasoning behind them. |
