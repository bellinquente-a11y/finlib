# finlib

[![CI](https://github.com/bellinquente-a11y/finlib/actions/workflows/ci.yml/badge.svg)](https://github.com/bellinquente-a11y/finlib/actions/workflows/ci.yml)

Production-grade Python for financial data modelling. 
- Strict type annotations (mypy --strict)
- Protocol-based dependency injection
- structured logging (structlog)
- property-based testing (Hypothesis)

## Design decisions

- **Protocol-based repositories** — `OHLCVRepo` and `TradeRepository` are structural subtypes. Backends (in-memory vs CSV/JSONL) are swappable without touching callers.
- **mypy --strict** clean across `src/` and `tests/`.
- **Async concurrency** — `asyncio.gather` with a rate-limiting `Semaphore`, plus exponential-backoff retry on both sync and async callables.
- **O(1) memory streaming** — OHLCV data is consumed as a generator; no materialising full datasets before processing.
- **Property-based testing** via Hypothesis — invariants on numeric functions (e.g. `maximum_drawdown ≤ 0` for any valid return series).

## Modules

| Module | What it does |
|---|---|
| `models.py` | `Trade` model with Pydantic v2 field constraints |
| `instruments.py` | Instrument hierarchy (ABCs + Protocols); portfolio valuation via structural subtyping |
| `data.py` | Streaming OHLCV parser; validates rows at the ingestion boundary |
| `async_fetch.py` | Async Binance fetcher: aiohttp, asyncio.gather, Semaphore, validated response parsing |
| `decorators.py` | `@retry` / `@async_retry` (exp. backoff), `@timer`, `@deprecated`, `@validate_inputs` |
| `context_managers.py` | `timer` context manager for profiling code blocks |
| `analytics.py` | VWAP; uses `@retry` and `@validate_inputs` to enforce caller contracts |
| `historic_analytics.py` | `resample_dataframe`, `add_rolling_stats` (annualised vol + Sharpe), `maximum_drawdown` |
| `trade_repo.py` | `TradeRepository` Protocol; in-memory and JSONL-backed implementations |
| `ohlcv_repo.py` | `OHLCVRepo` Protocol; in-memory and CSV-backed implementations |
| `portfolio.py` | `PortfolioService` with injected `TradeRepository`; trade management and valuation |
| `report.py` | `daily_trade_summary` — daily notional and trade count aggregated by symbol |
| `config.py` | pydantic-settings config with `.env` support |
| `pipeline/` | CLI entry point, data orchestration, analytics, formatted output |

## Installation

```bash
git clone https://github.com/bellinquente-a11y/finlib
cd finlib && poetry install
```

## Portfolio analysis pipeline

Reads historic trades from a JSONL file, fetches OHLCV market data from Binance, caches it locally as CSV, and computes portfolio analytics.

```bash
poetry run finlib-pipeline ~/data/trades.jsonl 1h
```

### trades.jsonl format

```text
{"symbol": "BTCUSDT", "quantity": "3", "price": "75539.5", "side": "BUY", "timestamp": "2026-05-22T07:08:47.107473Z"}
{"symbol": "BNBUSDT", "quantity": "117", "price": "653.22", "side": "BUY", "timestamp": "2026-05-22T14:37:17.848747Z"}
```

### Example output

```text

INFO:finlib.pipeline.data:Loading trades from the trade repository
INFO:finlib.pipeline.data:Trades loaded    = 221
INFO:finlib.pipeline.data:Symbols          = BTCUSDT, BNBUSDT, ETHUSDT
INFO:finlib.pipeline.data:First time stamp = datetime.datetime(2026, 5, 22, 7, 8, 47, 107473, tzinfo=TzInfo(0))
INFO:finlib.pipeline.data:Fetching 1h market data for symbols: BTCUSDT, BNBUSDT, ETHUSDT from 2026-05-21 07:08:47.107473+00:00
2026-07-07 09:24:19 [info     ] Async fetching Binance data    interval=1h limit=1120 symbol=BTCUSDT
2026-07-07 09:24:19 [info     ] Async fetching Binance data    interval=1h limit=1120 symbol=BNBUSDT
2026-07-07 09:24:19 [info     ] Async fetching Binance data    interval=1h limit=1120 symbol=ETHUSDT
INFO:finlib.pipeline.data:Storing market data in OHLCV repository
2026-07-07 09:24:20 [info     ] adding intervals               symbol=BTCUSDT
2026-07-07 09:24:20 [info     ] adding intervals               symbol=BNBUSDT
2026-07-07 09:24:20 [info     ] adding intervals               symbol=ETHUSDT
2026-07-07 09:24:20 [info     ] Added rows to trade repo       count=3000


     symbol   close rolling_vol rolling_sharpe
38  BTCUSDT  62,583       0.285           0.64
39  BTCUSDT  63,144       0.286           1.10
39  ETHUSDT   1,781       0.399           2.66
39  BNBUSDT     575       0.276          -0.60
40  ETHUSDT   1,786       0.388           1.94
40  BTCUSDT  63,650       0.265           0.14
40  BNBUSDT     590       0.267          -0.92
41  BNBUSDT     587       0.267          -0.98
41  BTCUSDT  64,114       0.266           0.46
41  ETHUSDT   1,803       0.388           2.33


Market value
                 BNBUSDT    BTCUSDT   ETHUSDT
timestamp                                    
2026-07-06 23:59  90,412  1,089,938  -880,069

Cost basis
                   BNBUSDT     BTCUSDT  ETHUSDT
2026-07-03 23:21   24,373   1,173,382  -827,762

PnL
                  BNBUSDT  BTCUSDT  ETHUSDT
timestamp                                  
2026-07-06 23:59   33,961   83,444   52,307

Total PnL =  169,711
```

## Testing

### Full suite with coverage

```bash
poetry run pytest --cov=finlib -v
```

### Type-checking

```bash
poetry run mypy src/ --strict
```

### Linting

```bash
poetry run ruff check src/ tests/ script/
```

### CI

CI enforces ≥80% pytest coverage, mypy --strict, and ruff on every push.
