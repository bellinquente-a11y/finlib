# Contributing to finlib

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
| `instruments.py` | Instrument hierarchy (ABCs + Protocols); portfolio valuation via structural subtyping |
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

## Setup

```bash
git clone https://github.com/simone-belli/finlib
cd finlib
poetry install --with dev
pre-commit install && pre-commit run --all-files
```

## Quick start

```bash
poetry run finlib-pipeline ./examples/trades.jsonl 1h
```

## Testing & Quality

### Principles

- unit tests to test behaviour
- hypothesis tests to test invariants
- fake what we own; mock what we don't

### Full suite with coverage (pytest)

pytest + pytest-asyncio; property-based tests (Hypothesis) for portfolio invariants and position sizing

```bash
poetry run pytest --cov=finlib -v
```

### Type-checking (mypy)

```bash
poetry run mypy src/ --strict
```

### Linting (ruff)

Extended checks: E,F,I,B,UP,SIM,RET.

```bash
poetry run ruff check src/ tests/ script/
```

### pre-commit

Enforcement of linting, format, mypy --strict.

### CI

CI enforces ≥85% pytest coverage, mypy --strict, and ruff on every push.
