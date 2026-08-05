# Pipeline

The `pipeline/` package is the batch CLI: it wires concrete repositories, fetches and caches market data, computes analytics, and prints tables to stdout. It is the reference example of how the layers below it compose into an end-to-end run. Installed as the `finlib-pipeline` command (see `[tool.poetry.scripts]`).

## Usage

```bash
poetry run finlib-pipeline ./examples/trades.jsonl 1h
```

Two positional arguments: the JSONL trade-repository path, and the market-data quantisation frequency (a Binance interval such as `1h` or `1d`).

## Modules

| Module | Role |
|---|---|
| `cli.py` | Entry point (`main`): argument parsing, logging setup, wiring, and the run sequence. |
| `data.py` | Trade loading and market-data fetch/store/refresh. |
| `analytics.py` | Orchestration of market summary and portfolio performance over the repos. |
| `output.py` | stdout formatting of the result tables. |

## `cli.py` — wiring and sequence

`main` does five things in order:

1. **Parse** `trade_repo_path` and `frequency` (argparse).
2. **Configure logging** — `structlog` with a `ConsoleRenderer` locally or a `JSONRenderer` in production, gated on `settings.environment`, at `settings.log_level` (see [configuration.md](configuration.md)).
3. **Wire repositories** — a `FileTradeRepository` over the given path and a `FileOHLCVRepository` at `data_dir/mkt_data_<freq>.csv`. This is the one place concrete backends are chosen; everything downstream sees only the Protocols.
4. **Fetch & refresh** — `data.fetch_trades` then `data.update_market_data_repo` (below).
5. **Analyse & print** — a market summary, then portfolio market value, cost basis, and cumulative PnL, each under a `_headline_title` banner.

## `data.py` — the fetch/refresh logic

- `fetch_trades(trade_repo)` loads all trades, derives the symbol set and the first/last timestamps, logs a summary, and raises if the repo is empty.
- `fetch_market_data(symbols, interval, start)` is a thin async wrapper over `fetch_binance` ([async-and-concurrency.md](async-and-concurrency.md)).
- `store_market_data(repo, df)` batch-inserts the fetched frame, mapping Binance's `close_time` column to the repo's `timestamp`, and raises on an empty frame.
- `update_market_data_repo(repo, symbols, interval, start, max_update_freq)` is the incremental cache: for each symbol it checks `last_updated`, and only refetches symbols that are missing or staler than `max_update_freq` (the CLI sets this to **1 day**). If nothing is stale it makes no network calls at all — this freshness gate is where the saving comes from. When a refetch does happen the fetch still starts at the first trade, but the repository's batch insert keeps only bars newer than what is cached, so re-fetched rows are deduplicated on write.

This `last_updated` vs `last_timestamp` split is explained in [repositories.md](repositories.md); it is what keeps repeated pipeline runs cheap.

## `analytics.py` — orchestration

Distinct from the pure `finlib.analytics` module, `pipeline.analytics` glues the repos to the computations:

- `compute_market_summary(ohlcv_repo, symbols, window=24)` — for each symbol, pulls data, resamples to daily, adds rolling vol/Sharpe (annualised with `252` intervals/year), and concatenates.
- `get_market_price(ohlcv_repo, symbols, first_ts)` — builds a wide close-price frame (index = timestamps, columns = symbols) for marking to market.
- `compute_portfolio_performance_metrics(trade_repo, ohlcv_repo)` — constructs a `Portfolio`, fetches prices, verifies every held symbol has a price (raises otherwise), and returns `(pnl, market_value, cost_basis)`.

## `output.py` — presentation

- `print_market_summary(df, columns, formatters)` — prints the most recent row per symbol with per-column formatters.
- `print_trading_summary(df, format, axis_format)` — prints the latest row of a per-symbol frame with a formatted datetime axis.

Keeping formatting in its own module means the analytics functions return raw DataFrames and the CLI decides presentation — the same metrics can be rendered differently (or as JSON by the API) without touching the computation.

## Flow diagram

The end-to-end sequence is diagrammed in [architecture.md](architecture.md#pipeline-data-flow).
