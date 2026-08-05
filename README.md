# finlib

[![CI](https://github.com/simone-belli/finlib/actions/workflows/ci.yml/badge.svg)](https://github.com/simone-belli/finlib/actions/workflows/ci.yml)

Production-grade Python for financial data modelling.
- Strict type annotations (mypy --strict)
- Protocol-based dependency injection
- structured logging (structlog)
- property-based testing (Hypothesis)

## Design decisions

- **Protocol-based repositories** — `OHLCVRepository` and `TradeRepository` are structural subtypes. Backends (in-memory vs CSV/JSONL) are swappable without touching callers.
- **mypy --strict** clean across `src/` and `tests/`.
- **Async concurrency** — `asyncio.gather` with a rate-limiting `Semaphore`, plus exponential-backoff retry on both sync and async callables.
- **O(1) memory streaming** — OHLCV data is consumed as a generator; no materialising full datasets before processing.
- **Property-based testing** via Hypothesis — invariants on numeric functions (e.g. `maximum_drawdown ≤ 0` for any valid return series).

## Modules

| Module | What it does |
|---|---|
| `models.py` | `Trade` model with Pydantic v2 field constraints |
| `data.py` | Streaming OHLCV parser; validates rows at the ingestion boundary |
| `async_fetch.py` | Async Binance fetcher: aiohttp, asyncio.gather, Semaphore, validated response parsing |
| `decorators.py` | `@retry` / `@async_retry` (exp. backoff), `@timer`, `@deprecated`, `@validate_inputs` |
| `context_managers.py` | `timer` context manager for profiling code blocks |
| `analytics.py` | VWAP; uses `@retry` and `@validate_inputs` to enforce caller contracts |
| `historic_analytics.py` | `resample_dataframe`, `add_rolling_stats` (annualised vol + Sharpe), `maximum_drawdown` |
| `trade_repo.py` | `TradeRepository` Protocol; in-memory and JSONL-backed implementations |
| `ohlcv_repo.py` | `OHLCVRepository` Protocol; in-memory and CSV-backed implementations |
| `portfolio.py` | `PortfolioService` with injected `TradeRepository`; trade management and valuation |
| `report.py` | `daily_trade_summary` — daily notional and trade count aggregated by symbol |
| `config.py` | pydantic-settings config with `.env` support |
| `pipeline/` | CLI entry point, data orchestration, analytics, formatted output |


## Installation

```bash
git clone https://github.com/simone-belli/finlib
cd finlib && poetry install
```

## Portfolio analysis: quick start

Reads historic trades from a JSONL file, fetches OHLCV market data from Binance, caches it locally as CSV, and computes portfolio analytics.

CLI inputs:

1. Trades JSONL file path

2. Quantisation frequency

```bash
poetry run finlib-pipeline ./examples/trades.jsonl 1h
```

### trades.jsonl format

See `examples/trades.jsonl`.

### Example output

```text
2026-07-27T07:28:54.333459Z [info     ] Trades loaded from repo        first_date=22-05-2026 last_date=03-07-2026 num_symbols=3 num_trades=221
2026-07-27T07:28:54.333717Z [info     ] Fetching market data           symbols=['ETHUSDT', 'BNBUSDT', 'BTCUSDT']
2026-07-27T07:28:54.333933Z [info     ] Async fetching Binance data    interval=1h limit=1608 symbol=ETHUSDT
2026-07-27T07:28:54.334235Z [info     ] Async fetching Binance data    interval=1h limit=1608 symbol=BNBUSDT
2026-07-27T07:28:54.334334Z [info     ] Async fetching Binance data    interval=1h limit=1608 symbol=BTCUSDT
2026-07-27T07:28:54.679417Z [info     ] Fetched Binance data           elapsed=0.3s interval=1h symbols=['ETHUSDT', 'BNBUSDT', 'BTCUSDT']
2026-07-27T07:28:54.729248Z [info     ] Storing market data            dataframe_shape=(3000, 12) size=36,000
2026-07-27T07:28:54.758581Z [info     ] adding intervals               last_timestamp='27-07-2026 17:59:59' symbol=ETHUSDT
2026-07-27T07:28:54.761593Z [info     ] adding intervals               last_timestamp='27-07-2026 17:59:59' symbol=BNBUSDT
2026-07-27T07:28:54.762791Z [info     ] adding intervals               last_timestamp='27-07-2026 17:59:59' symbol=BTCUSDT
2026-07-27T07:28:54.763832Z [info     ] New rows added to trade repo   count=0


Market summary
----------------------------------------------------------------------------------------------------

     symbol         timestamp   close rolling_vol rolling_sharpe
62  BNBUSDT  2026-07-28 00:00     575       0.170           0.23
62  BTCUSDT  2026-07-28 00:00  65,385       0.236           2.07
62  ETHUSDT  2026-07-28 00:00   1,969       0.336           3.70


Portfolio market value
----------------------------------------------------------------------------------------------------

                  BNBUSDT     BTCUSDT  ETHUSDT
2026-07-27 07:59  -88,575  -1,111,551  960,896


Portfolio cost basis
----------------------------------------------------------------------------------------------------

                  BNBUSDT    BTCUSDT   ETHUSDT
2026-07-03 23:21  124,373  1,173,382  -827,762


Portfolio PnL
----------------------------------------------------------------------------------------------------

                 BNBUSDT BTCUSDT  ETHUSDT
2026-07-27 07:59  35,798  61,831  133,134

```

## Contributing

See `.github/CONTRIBUTING.md`.
